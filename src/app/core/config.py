"""
Core configuration settings for PhysioAssist-AI
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    APP_NAME: str = "PhysioAssist-AI"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    
    # Project Paths
    ROOT_DIR: Path = Path(__file__).parent.parent.parent.parent
    USER_CHATS_DIR: Path = ROOT_DIR / "user_chats"
    
    # API Keys (optional - will be loaded from .env if present)
    OPENAI_API_KEY: str | None = None
    GROK_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env


settings = Settings()
