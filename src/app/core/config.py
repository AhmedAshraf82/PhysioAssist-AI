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
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Project Paths
    ROOT_DIR: Path = Path(__file__).parent.parent.parent.parent
    MODEL_DIR: Path = ROOT_DIR / "models"
    DATA_DIR: Path = ROOT_DIR / "data"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
