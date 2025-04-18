from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import openai
import groq
import requests
import json
import subprocess
import os
import time

from crew_ai.config.config import Config, LLMProvider

class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text from the LLM."""
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for the given text."""
        pass

class OllamaClient(LLMClient):
    """Client for Ollama LLM."""
    
    def __init__(self, model_name: str = None, embedding_model: str = None):
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "granite3.1-dense")
        self.embedding_model = embedding_model or os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        self.base_url = "http://localhost:11434/api"
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{self.base_url}/tags")
            if response.status_code != 200:
                raise ConnectionError("Ollama server is not running")
            
            # Check if the models are available
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            # Check and pull main model if needed
            if self.model_name not in model_names:
                print(f"Model {self.model_name} not found. Pulling it now...")
                subprocess.run(["ollama", "pull", self.model_name], check=True)
            
            # Check and pull embedding model if needed
            if self.embedding_model not in model_names:
                print(f"Embedding model {self.embedding_model} not found. Pulling it now...")
                subprocess.run(["ollama", "pull", self.embedding_model], check=True)
                
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Ollama server is not running. Please start it with 'ollama serve'")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using Ollama."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        response = requests.post(f"{self.base_url}/generate", json=payload)
        if response.status_code != 200:
            raise Exception(f"Error generating text: {response.text}")
        
        return response.json().get("response", "")
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings using Ollama."""
        payload = {
            "model": self.embedding_model,
            "prompt": text,
        }
        
        response = requests.post(f"{self.base_url}/embeddings", json=payload)
        if response.status_code != 200:
            raise Exception(f"Error generating embeddings: {response.text}")
        
        return response.json().get("embedding", [])

class GroqClient(LLMClient):
    """Client for Groq AI API."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = groq.Client(api_key=self.api_key)
        # We'll use Nomic embeddings since Groq doesn't provide embeddings
        self.embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        self.embedding_client = OllamaClient(embedding_model=self.embedding_model)
        
    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using Groq AI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Add retry logic
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Groq API error: {e}. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise e
                        
        except Exception as e:
            print(f"Error generating text with Groq: {e}")
            # Fallback to Ollama if Groq fails
            fallback_client = OllamaClient()
            return fallback_client.generate(prompt, system_prompt, max_tokens)
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings using Nomic embeddings via Ollama."""
        try:
            # Use the Ollama client for embeddings
            return self.embedding_client.embed(text)
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Return a zero vector as fallback
            return [0.0] * 768  # Standard embedding size

class OpenRouterClient(LLMClient):
    """Client for OpenRouter LLM."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = None):
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        self.model_name = model_name or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-opus")
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using OpenRouter."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(f"{self.base_url}/chat/completions", 
                                headers=self.headers, 
                                json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Error generating text: {response.text}")
        
        return response.json()["choices"][0]["message"]["content"]
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings using OpenRouter."""
        payload = {
            "model": "openai/text-embedding-3-small",  # Default embedding model
            "input": text
        }
        
        response = requests.post(f"{self.base_url}/embeddings", 
                                headers=self.headers, 
                                json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Error generating embeddings: {response.text}")
        
        return response.json()["data"][0]["embedding"]

def get_llm_client(provider: Optional[LLMProvider] = None) -> LLMClient:
    """Factory function to get the appropriate LLM client."""
    provider = provider or Config.LLM_PROVIDER
    
    if provider == LLMProvider.OLLAMA:
        return OllamaClient()
    elif provider == LLMProvider.GROQ_AI:
        return GroqClient()
    elif provider == LLMProvider.OPENROUTER:
        return OpenRouterClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
