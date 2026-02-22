from src.app.models.channel_models import (
    ChannelType,
    MessageType,
    UnifiedInboundMessage,
)
from src.app.models.chat_models import ChatMessage


def to_unified_message(payload: ChatMessage) -> UnifiedInboundMessage:
    resolved_user_id = payload.user_id or "web:anonymous"
    resolved_chat_id = payload.chat_id or resolved_user_id

    return UnifiedInboundMessage(
        channel=ChannelType.WEB,
        message_type=MessageType.TEXT,
        user_id=resolved_user_id,
        chat_id=resolved_chat_id,
        text=payload.message,
    )


def to_unified_multimodal_message(
    *,
    chat_id: str | None,
    user_id: str | None,
    message_type: MessageType,
    text: str | None,
    media_bytes: bytes | None,
    mime_type: str | None,
) -> UnifiedInboundMessage:
    resolved_user_id = user_id or "web:anonymous"
    resolved_chat_id = chat_id or resolved_user_id

    return UnifiedInboundMessage(
        channel=ChannelType.WEB,
        message_type=message_type,
        user_id=resolved_user_id,
        chat_id=resolved_chat_id,
        text=text,
        media_bytes=media_bytes,
        mime_type=mime_type,
    )
