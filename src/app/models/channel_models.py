from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    WHATSAPP = "whatsapp"
    WEB = "web"
    MOBILE = "mobile"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class UnifiedInboundMessage(BaseModel):
    channel: ChannelType
    message_type: MessageType
    user_id: str
    chat_id: str
    text: Optional[str] = None
    media_id: Optional[str] = None
    media_bytes: Optional[bytes] = None
    mime_type: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnifiedOutboundMessage(BaseModel):
    text: str
    should_send_voice: bool = False
    voice_audio: Optional[bytes] = None
    voice_mime_type: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
