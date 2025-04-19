from fastapi import APIRouter, Body, HTTPException, Response, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Tuple
import tempfile
import os
import re
import json
import markdown
from io import BytesIO
import torch
import soundfile as sf
from tqdm import tqdm
import time
import logging
from openai import OpenAI

# Kokoro imports - using try/except to handle potential import issues
try:
    from kokoro import KPipeline
    KOKORO_AVAILABLE = True
except ImportError:
    # KOKORO_AVAILABLE = False
    logging.warning("Kokoro not available. Using fallback TTS.")

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Default model for OpenAI
DEFAULT_MODEL = "gpt-4.1-nano"

# System prompts
SYS_PROMPT_PREPROCESSOR = """
You are a professional text pre-processor. Your job is to clean up raw text data taken from markdown documents. The cleaned text will be used by a podcast scriptwriter.

IMPORTANT INSTRUCTIONS:

- DO NOT summarize the content in any way.
- DO NOT interpret or infer meaning.
- DO NOT shorten or rephrase for brevity.
- DO NOT add any acknowledgments or explanations.
- DO NOT use markdown formatting or special characters.
- DO NOT use headings, bullet points, or lists.
- DO NOT add or remove capitalizations unless absolutely necessary for grammar.

YOUR TASK:

- Aggressively remove any fluff, latex math ($...$ or \\[...\\]), or irrelevant details.
- Remove unnecessary newlines and fix broken sentence flow.
- Correct formatting issues to make the text more readable and flowing for a human writer.
- If the sentence is unclear or garbled, attempt to rewrite it for clarity, but preserve all original meaning.
- Start the output directly with the cleaned text. Return **only the cleaned text**, nothing else.

This is not a summarization task. You are not allowed to shorten, interpret, or reduce the text in any form.

Begin processing the following raw text:
"""

SYS_PROMPT_DIALOGUE = """
You are an internationally acclaimed, Oscar-winning screenwriter who has worked with multiple award-winning podcasters.

Your job is to transform the provided podcast transcript into a captivating dialogue for an AI Text-To-Speech pipeline. This is for a conversation between two speakers, where Speaker 1 is the teacher, and Speaker 2 is the curious student.

Speaker 1 and Speaker 2 will be simulated by different voice engines:
- Speaker 1: Leads the conversation and explains the topic in-depth with incredible anecdotes, analogies, and real-world examples. Speaker 1 is a captivating teacher who always delivers clear, insightful, and engaging explanations without interruptions.
- Speaker 2: Is new to the topic and plays the role of the curious student. Speaker 2 keeps the conversation engaging by asking follow-up questions, showing excitement, confusion, and curiosity. Speaker 2 will often interrupt with questions, get excited, or ask for further clarifications. Make sure Speaker 2 provides wild tangents or interesting observations during their interruptions.
  
Make sure to include realistic anecdotes, analogies, and real-world examples in the questions and answers. Speaker 2's questions should lead to engaging, deeper discussions, with interesting confirmation questions, wild tangents, and more. Speaker 1 will use expressions like "umm", "hmm", uhhhhhhhhh but only these expressions. DO NOT use other types of expressions for Speaker 2. Keep the interruptions realistic and fluid.

For Speaker 2, avoid using any symbols or punctuation other than normal letters. The speech should be clear, direct, and without any unnecessary fillers or punctuation. The TTS engine for Speaker 2 cannot process symbols well, so no symbols like question marks, exclamation marks, or any others should be used.

It should be a real, dynamic podcast with every fine nuance documented in as much detail as possible. The conversation should feel authentic, engaging, and full of energy. Welcome the listeners with a fun and catchy overview and keep the content borderline clickbait in style, ensuring it's entertaining.

never use symbols of any type only words
Rewriting the provided transcript into dialogue:
- Always begin your response directly with Speaker 1.
- The conversation should include the fine nuances of speech, as well as interruptions, real-world analogies, and examples.
- Ensure that the dialogue feels like a natural, engaging podcast.

Strictly return your response as a list of tuples, like this:

[
    ("Speaker 1", "Welcome to the podcast Today we are diving into the fascinating world of AI and its incredible impact on society I am your host and I'll be guiding you through all the exciting details"),
    ("Speaker 2", "Wow That sounds really interesting laughs So what exactly is AI How does it work"),
    ("Speaker 1", "Great question AI or Artificial Intelligence is the simulation of human intelligence in machines It learns adapts and processes data just like we do but it can do it much faster and more accurately"),
    ("Speaker 2", "Hmm thats cool So its like having a robot that can think for itself But what does it mean for us Can it replace humans")
]
"""

class PodcastRequest(BaseModel):
    content: str
    language: Optional[str] = "en"
    speed: Optional[float] = 1.0

def preprocess_text(text: str) -> str:
    """Preprocess markdown text using OpenAI to clean it for podcast conversion"""
    try:
        logger.info("Preprocessing text for podcast conversion")
        user_prompt = f"{SYS_PROMPT_PREPROCESSOR}\n\n{text}"
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        processed_text = response.choices[0].message.content.strip()
        logger.info("Text preprocessing complete")
        return processed_text
    except Exception as e:
        logger.error(f"Error in text preprocessing: {str(e)}")
        raise

def generate_podcast_dialogue(processed_text: str) -> List[Tuple[str, str]]:
    """Generate podcast dialogue using OpenAI"""
    try:
        logger.info("Generating podcast dialogue")
        messages = [
            {"role": "system", "content": SYS_PROMPT_DIALOGUE},
            {"role": "user", "content": processed_text}
        ]
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        generated_content = response.choices[0].message.content.strip()
        
        # Clean up the response and parse it as Python code
        cleaned = generated_content.replace('```python', '').replace('```', '').strip()
        
        # Parse the output as a list of tuples
        try:
            dialogue = eval(cleaned)
            logger.info(f"Generated dialogue with {len(dialogue)} segments")
            return dialogue
        except:
            logger.error("Failed to parse dialogue output as Python data structure")
            # Fallback: Return a simple dialogue if parsing fails
            return [
                ("Speaker 1", "Welcome to this podcast. I'll be discussing the content you requested."),
                ("Speaker 2", "Sounds interesting Tell me more about it")
            ]
    except Exception as e:
        logger.error(f"Error in dialogue generation: {str(e)}")
        raise

def generate_audio(dialogue: List[Tuple[str, str]]) -> torch.Tensor:
    """Generate audio from dialogue using Kokoro TTS"""
    if not KOKORO_AVAILABLE:
        raise HTTPException(status_code=500, detail="TTS system (Kokoro) not available")
    
    try:
        logger.info("Initializing TTS pipeline")
        pipeline = KPipeline(lang_code='a')
        
        def text_to_audio_speaker1(text):
            audios = []
            generator = pipeline(text, voice='af_nova')
            for _, (_, _, audio) in enumerate(generator):
                audios.append(audio)
            return torch.cat(audios, dim=0)
        
        def text_to_audio_speaker2(text):
            audios = []
            generator = pipeline(text, voice='hm_omega')
            for _, (_, _, audio) in enumerate(generator):
                audios.append(audio)
            return torch.cat(audios, dim=0)
        
        logger.info(f"Generating audio for {len(dialogue)} dialogue segments")
        audio_segments = []
        
        for speaker, text in dialogue:
            if speaker == 'Speaker 1':
                audio = text_to_audio_speaker1(text)
            elif speaker == 'Speaker 2':
                audio = text_to_audio_speaker2(text)
            else:
                continue
            audio_segments.append(audio)
        
        if not audio_segments:
            raise ValueError("No audio segments were generated")
        
        # Concatenate all audio segments
        full_audio = torch.cat(audio_segments, dim=0).squeeze()
        logger.info("Audio generation complete")
        return full_audio
    
    except Exception as e:
        logger.error(f"Error in audio generation: {str(e)}")
        raise

def generate_dialogue_text(dialogue: List[Tuple[str, str]]) -> str:
    """Convert dialogue list to a formatted text for text-to-speech fallback"""
    output = ""
    for speaker, text in dialogue:
        output += f"{speaker}: {text}\n\n"
    return output

@router.post("")
async def create_podcast(request: PodcastRequest = Body(...)):
    """
    Create a podcast (audio file) from markdown content using OpenAI and Kokoro TTS
    """
    try:
        # Step 1: Preprocess the text
        processed_text = preprocess_text(request.content)
        
        # Step 2: Generate dialogue
        dialogue = generate_podcast_dialogue(processed_text)
        
        # Return the dialogue as JSON for debugging if needed
        dialogue_formatted = generate_dialogue_text(dialogue)
        
        # Step 3: Try to generate audio using Kokoro if available
        if KOKORO_AVAILABLE:
            try:
                audio = generate_audio(dialogue)
                
                # Step 4: Convert to WAV for streaming
                logger.info("Converting audio to WAV format")
                audio_buffer = BytesIO()
                
                # Convert PyTorch tensor to NumPy array and save as WAV
                sample_rate = 24000  # Kokoro uses 24kHz sample rate
                sf.write(audio_buffer, audio.numpy(), sample_rate, format='wav')
                
                # Reset buffer position to start
                audio_buffer.seek(0)
                
                # Return the audio file as a streaming response
                logger.info("Sending audio to client")
                return StreamingResponse(
                    audio_buffer,
                    media_type="audio/wav",
                    headers={
                        "Content-Disposition": f"attachment; filename=podcast.wav"
                    }
                )
            except Exception as e:
                logger.error(f"Kokoro TTS failed: {str(e)}. Using fallback method.")
                # Continue with fallback
        
        # Step 3 (Fallback): Return the dialogue as a text file if audio generation fails
        logger.info("Using fallback method: returning dialogue text")
        text_buffer = BytesIO(dialogue_formatted.encode('utf-8'))
        
        # Return the text file as a streaming response
        return StreamingResponse(
            text_buffer,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=podcast_dialogue.txt"
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to create podcast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create podcast: {str(e)}") 