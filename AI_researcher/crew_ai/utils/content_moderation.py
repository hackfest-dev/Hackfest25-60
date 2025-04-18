import re
from typing import Dict, Any, List, Tuple, Optional
from crew_ai.config.config import Config
from crew_ai.models.llm_client import get_llm_client

class ContentModerator:
    """Content moderation utility to filter harmful or low-quality content."""
    
    def __init__(self, moderation_level: Optional[str] = None):
        self.moderation_level = moderation_level or Config.CONTENT_MODERATION_LEVEL
        self.llm_client = get_llm_client()
        
        # Initialize harmful content patterns
        self.harmful_patterns = [
            r'\b(porn|xxx|sex|nude|naked|explicit)\b',
            r'\b(hack|crack|pirate|steal|illegal)\b',
            r'\b(terrorist|bomb|kill|murder|suicide)\b',
            r'\b(racist|nazi|white supremac|kkk)\b',
            r'\b(drug|cocaine|heroin|meth)\b'
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.harmful_patterns]
    
    def is_harmful_content(self, text: str) -> bool:
        """Check if the content contains harmful patterns."""
        # Skip empty content
        if not text or len(text.strip()) == 0:
            return True
        
        # Check for harmful patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        
        # For strict moderation, use LLM to check for harmful content
        if self.moderation_level == "strict":
            return self._llm_content_check(text)
        
        return False
    
    def _llm_content_check(self, text: str) -> bool:
        """Use LLM to check if content is harmful."""
        # Truncate text if it's too long
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        prompt = f"""
        Analyze the following content and determine if it contains harmful, explicit, illegal, 
        or otherwise inappropriate content. Respond with only "HARMFUL" or "SAFE".
        
        Content: {text}
        """
        
        system_prompt = """
        You are a content moderation system. Your task is to analyze text and determine if it contains
        harmful, explicit, illegal, or otherwise inappropriate content. Respond with only "HARMFUL" or "SAFE".
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=10
        )
        
        return "HARMFUL" in response.upper()
    
    def calculate_quality_score(self, text: str) -> float:
        """Calculate a quality score for the content using LLM."""
        # Skip empty content
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # For light moderation, use a simple heuristic approach
        if self.moderation_level == "light":
            return self._calculate_basic_quality_score(text)
        
        # For moderate and strict moderation, use LLM
        return self._llm_quality_check(text)
    
    def _calculate_basic_quality_score(self, text: str) -> float:
        """Calculate a basic quality score without using NLP libraries."""
        # Basic quality metrics
        word_count = len(text.split())
        unique_words = set(word.lower() for word in text.split())
        unique_word_count = len(unique_words)
        
        # Calculate base score based on length
        if word_count < 20:
            base_score = 0.2  # Very short content
        elif word_count < 50:
            base_score = 0.4  # Short content
        elif word_count < 200:
            base_score = 0.6  # Medium content
        else:
            base_score = 0.8  # Long content
        
        # Adjust for lexical diversity
        lexical_diversity = unique_word_count / max(1, word_count)
        diversity_score = min(1.0, lexical_diversity * 2)
        
        # Calculate final score
        final_score = (base_score * 0.6) + (diversity_score * 0.4)
        
        return min(1.0, max(0.0, final_score))
    
    def _llm_quality_check(self, text: str) -> float:
        """Use LLM to check content quality."""
        # Truncate text if it's too long
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        prompt = f"""
        Analyze the following content and rate its quality on a scale from 0.0 to 1.0, where:
        - 0.0 means extremely low quality (gibberish, spam, nonsensical)
        - 0.5 means average quality (somewhat informative but not well-structured)
        - 1.0 means high quality (informative, well-structured, valuable)
        
        Respond with ONLY a number between 0.0 and 1.0.
        
        Content: {text}
        """
        
        system_prompt = """
        You are a content quality assessment system. Your task is to analyze text and determine its quality
        on a scale from 0.0 to 1.0. Respond with ONLY a number between 0.0 and 1.0.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=10
        )
        
        try:
            score = float(response.strip())
            return min(1.0, max(0.0, score))
        except ValueError:
            # Default to 0.5 if parsing fails
            return 0.5
    
    def filter_content(self, text: str) -> Tuple[str, float, bool]:
        """Filter and score content, returning the filtered text, quality score, and harmful flag."""
        is_harmful = self.is_harmful_content(text)
        
        if is_harmful:
            return "", 0.0, True
        
        quality_score = self.calculate_quality_score(text)
        
        # Filter out low-quality content based on moderation level
        quality_threshold = {
            "light": 0.2,
            "moderate": 0.4,
            "strict": 0.6
        }.get(self.moderation_level, 0.4)
        
        if quality_score < quality_threshold:
            return "", quality_score, False
        
        return text, quality_score, False
