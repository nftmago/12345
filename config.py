# app/config.py
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
import os
print("DATABASE_URL:", os.getenv("DATABASE_URL"))
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field

class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., env='DATABASE_URL')
    
    # OpenAI API
    openai_api_key: str
    vision_model: str = "gpt-4o"
    text_model: str = "gpt-4o-mini"
    search_model: str = "gpt-4o-mini"
    
    # JWT Authentication
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Cloudinary
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    
    # Application
    environment: str = "development"
    api_v1_str: str = "/api/v1"
    project_name: str = "AINUT API"
    
    # Caching
    enable_ai_caching: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    max_cache_size: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
