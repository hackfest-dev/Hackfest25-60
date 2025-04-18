import os
import dotenv
from enum import Enum
from typing import Optional

# Load environment variables
dotenv.load_dotenv()

class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    GROQ_AI = "groq_ai"
    OPENROUTER = "openrouter"

class Config:
    """Configuration class for the Crew AI framework."""
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # LLM Configuration
    LLM_PROVIDER: LLMProvider = LLMProvider(os.getenv("LLM_PROVIDER", "ollama"))
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    
    # DuckDuckGo Search Configuration
    DUCKDUCKGO_MAX_RESULTS: int = int(os.getenv("DUCKDUCKGO_MAX_RESULTS", "400"))
    
    # Content Moderation
    CONTENT_MODERATION_LEVEL: str = os.getenv("CONTENT_MODERATION_LEVEL", "strict")
    
    # SQLite Database
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data.db")
    
    # LaTeX Configuration
    LATEX_TEMP_DIR: str = os.getenv("LATEX_TEMP_DIR", "./latex_temp")
    
    @classmethod
    def validate(cls):
        """Validate the configuration."""
        if cls.LLM_PROVIDER == LLMProvider.GROQ_AI and not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when using Groq AI provider")
        
        if cls.LLM_PROVIDER == LLMProvider.OPENROUTER and not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required when using OpenRouter provider")
            
        if cls.CONTENT_MODERATION_LEVEL not in ["light", "moderate", "strict"]:
            raise ValueError("CONTENT_MODERATION_LEVEL must be one of: light, moderate, strict")
