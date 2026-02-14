"""
Core configuration settings for PhysioAssist-AI
"""
import os
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
    
    # RAG Search Configuration
    INDEX_NAME: str = "physio_info"
    RAG_TOP_K: int = 3  
    SEARCH_SERVICE_TYPE: str = "elasticsearch"  # or "pinecone", "weaviate", etc.
    
    # Elasticsearch Configuration
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_SCHEME: str = "https"
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env


settings = Settings()
