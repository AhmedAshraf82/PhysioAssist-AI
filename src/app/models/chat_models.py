from typing import Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Request model for chat messages."""

    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_123",
                "message": "Hello! Can you help me with my physiotherapy questions?",
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat messages."""

    chat_id: str
    response: str
    message_count: int


class MultimodalChatResponse(ChatResponse):
    """Response model for multimodal chat with optional audio reply payload."""

    reply_type: str = "text"
    reply_audio_base64: Optional[str] = None
    reply_audio_mime_type: Optional[str] = None


class PrediagnoseAIResult(BaseModel):
    """Internal model carrying prediagnosis AI output and token usage."""

    response: str
    llm_prompt_tokens: int = 0
    llm_completion_tokens: int = 0
    llm_cost_usd: float = 0.0
