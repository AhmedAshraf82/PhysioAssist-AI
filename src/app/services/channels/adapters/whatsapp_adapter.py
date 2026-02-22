from typing import Any

from src.app.models.channel_models import (
    ChannelType,
    MessageType,
    UnifiedInboundMessage,
)


def _extract_text(message: dict[str, Any]) -> str | None:
    message_type = message.get("type")

    if message_type == "text":
        return message.get("text", {}).get("body", "").strip() or None

    if message_type == "button":
        return message.get("button", {}).get("text", "").strip() or None

    if message_type == "interactive":
        interactive = message.get("interactive", {})
        interactive_type = interactive.get("type")
        if interactive_type == "button_reply":
            return (
                interactive.get("button_reply", {}).get("title", "").strip() or None
            )
        if interactive_type == "list_reply":
            return interactive.get("list_reply", {}).get("title", "").strip() or None

    if message_type in {"image", "video", "document"}:
        media_payload = message.get(message_type, {})
        caption = media_payload.get("caption", "").strip()
        if caption:
            return caption

    return None


def _to_message_type(raw_type: str | None) -> MessageType:
    if raw_type == "text":
        return MessageType.TEXT
    if raw_type == "image":
        return MessageType.IMAGE
    if raw_type == "audio":
        return MessageType.AUDIO
    if raw_type == "video":
        return MessageType.VIDEO
    if raw_type == "document":
        return MessageType.DOCUMENT
    return MessageType.UNKNOWN


def to_unified_message(message: dict[str, Any]) -> UnifiedInboundMessage | None:
    user_wa_id = message.get("from")
    if not user_wa_id:
        return None

    raw_type = message.get("type")
    message_type = _to_message_type(raw_type)
    media_payload = message.get(raw_type or "", {}) if raw_type else {}
    media_id = media_payload.get("id") if isinstance(media_payload, dict) else None
    mime_type = media_payload.get("mime_type") if isinstance(media_payload, dict) else None

    return UnifiedInboundMessage(
        channel=ChannelType.WHATSAPP,
        message_type=message_type,
        user_id=f"wa:{user_wa_id}",
        chat_id=f"wa_{user_wa_id}",
        text=_extract_text(message),
        media_id=media_id,
        mime_type=mime_type,
        metadata={
            "whatsapp_from": user_wa_id,
            "whatsapp_message_id": message.get("id"),
            "whatsapp_type": raw_type,
        },
    )
