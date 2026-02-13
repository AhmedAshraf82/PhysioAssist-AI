"""
Dependency injection functions for FastAPI
"""
from functools import lru_cache
from src.app.core.config import Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


async def get_current_user():
    """
    Dependency to get current authenticated user
    TODO: Implement authentication logic
    """
    # Placeholder for authentication
    return {"user_id": "sample_user"}
