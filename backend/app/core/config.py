from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Searchify.AI"
    API_V1_STR: str = "/api/v1"
    
    # JWT
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "your-super-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite default dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # React default
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # FastAPI default
        "http://127.0.0.1:8000",
    ]
    
    # Database
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/searchify"
    )
    
    class Config:
        case_sensitive = True

settings = Settings() 