"""
Core configuration settings for PhysioAssist-AI
"""
import os
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
from src.app.models.audio_models import TTSVoice

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    APP_NAME: str = "PhysioAssist-AI"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    
    # Project Paths
    ROOT_DIR: Path = Path(__file__).parent.parent.parent.parent
    
    # RAG Search Configuration
    INDEX_NAME: str = "physio_info"
    RAG_TOP_K: int = 3  
    SEARCH_SERVICE_TYPE: str = "elasticsearch"  # or "pinecone", "weaviate", etc.
    
    # Elasticsearch Configuration
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9201
    ELASTICSEARCH_SCHEME: str = "http"
    ELASTIC_CERT_PATH: str = os.path.join(ROOT_DIR, "certs/elasticsearch/elastic-cert.crt")
    
    
    # OpenSearch Configuration
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9201
    OPENSEARCH_SCHEME: str = "https"
    OPENSEARCH_CERT_PATH: str = os.path.join(ROOT_DIR, "certs/opensearch/root-ca.pem")
    
    


    # Embedding Configuration
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI embedding model
    EMBEDDING_PROVIDER: str = "openai"  # 'openai' or 'bedrock'
    VECTOR_DIMENSIONS: int = 1536  # 1536 for text-embedding-3-small/ada-002, 3072 for text-embedding-3-large

    # MongoDB Configuration (loaded from .env)
    MONGODB_CONNECTION_STRING: str
    MONGODB_DATABASE_NAME: str
    MONGODB_COLLECTION_NAME: str = "injuries"  # Default collection name for injuries
    
    # API Keys (optional - will be loaded from .env if present)
    OPENAI_API_KEY: str | None = None
    GROK_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # LLM defaults (used when not explicitly passed to agent factory)
    LLM_PROVIDER: str = "openai"
    MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 0

    # WhatsApp Cloud API Configuration
    WHATSAPP_VERIFY_TOKEN: str | None = None
    WHATSAPP_ACCESS_TOKEN: str | None = None
    WHATSAPP_PHONE_NUMBER_ID: str | None = None
    WHATSAPP_API_VERSION: str = "v22.0"
    WHATSAPP_WEBHOOK_SECRET: str | None = None
    WHATSAPP_ENABLE_TEMPLATE_FALLBACK: bool = True
    WHATSAPP_FALLBACK_TEMPLATE_NAME: str | None = None
    WHATSAPP_FALLBACK_TEMPLATE_LANG: str = "en_US"
    WHATSAPP_STT_ENDPOINT: str | None = None
    WHATSAPP_VISION_ENDPOINT: str | None = None
    WHATSAPP_TTS_ENDPOINT: str | None = None
    WHATSAPP_ENABLE_VOICE_REPLY: bool = True
    VOICE_REPLY_ON_AUDIO_INPUT: bool = True

    # Speech-to-Text (OpenAI)
    STT_MODEL: str = "gpt-4o-transcribe"  # gpt-4o-transcribe | gpt-4o-mini-transcribe | whisper-1
    STT_LANGUAGE: str | None = None
    STT_PROMPT: str | None = (
        "Medical physiotherapy context: injuries, pain locations, symptoms, movement limits, "
        "and treatment exercises. Keep anatomical and injury terms accurate."
        "Egyptian Arabic or English language"
    )

    # Text-to-Speech (OpenAI)
    TTS_MODEL: str = "gpt-4o-mini-tts"  # gpt-4o-mini-tts | gpt-4o-tts
    TTS_VOICE: TTSVoice = TTSVoice.ASH
    TTS_SPEED: float = 1.45
    TTS_AUDIO_FORMAT: str = "ogg"

    # Twilio WhatsApp Configuration
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_WHATSAPP_NUMBER: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env


settings = Settings()
