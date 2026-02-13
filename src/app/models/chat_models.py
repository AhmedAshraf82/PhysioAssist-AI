from typing import Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Request model for chat messages."""

    chat_id: Optional[str] = None
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Hello! Can you help me with my physiotherapy questions?",
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat messages."""

    chat_id: str
    response: str
    message_count: int
