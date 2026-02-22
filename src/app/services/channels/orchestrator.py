import logging
import base64
from typing import Awaitable, Callable

import httpx

from src.app.core.config import settings
from src.app.models.channel_models import MessageType, UnifiedInboundMessage, UnifiedOutboundMessage
from src.app.services.channels.media.whatsapp_media_service import WhatsAppMediaService

logger = logging.getLogger(__name__)

AiProcessor = Callable[[str | None, str, str | None], Awaitable[object]]


VOICE_NOTES_COMING_SOON_MESSAGE = "Voice notes support coming soon!"
IMAGE_DESCRIPTION_COMING_SOON_MESSAGE = "Image description support coming soon!"


async def _transcribe_audio(media_bytes: bytes, mime_type: str | None) -> str | None:
    # TODO(STT-1): Replace endpoint call with your production STT model/service.
    # TODO(STT-2): Keep returned contract as plain transcript text.
    # TODO(STT-3): If your STT needs WAV/MP3, add conversion before API/model call.
    if not settings.WHATSAPP_STT_ENDPOINT:
        return None

    files = {
        "file": (
            f"voice_note.{(mime_type or 'audio/ogg').split('/')[-1]}",
            media_bytes,
            mime_type or "audio/ogg",
        )
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(settings.WHATSAPP_STT_ENDPOINT, files=files)
        response.raise_for_status()
        payload = response.json()

    transcript = payload.get("text") if isinstance(payload, dict) else None
    return transcript.strip() if isinstance(transcript, str) and transcript.strip() else None


async def _describe_image(media_bytes: bytes, mime_type: str | None) -> str | None:
    if not settings.WHATSAPP_VISION_ENDPOINT:
        return None

    files = {
        "file": (
            f"image.{(mime_type or 'image/jpeg').split('/')[-1]}",
            media_bytes,
            mime_type or "image/jpeg",
        )
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(settings.WHATSAPP_VISION_ENDPOINT, files=files)
        response.raise_for_status()
        payload = response.json()

    text = payload.get("text") if isinstance(payload, dict) else None
    return text.strip() if isinstance(text, str) and text.strip() else None


async def _synthesize_voice(text: str) -> tuple[bytes, str] | None:
    # TODO(TTS-1): Replace endpoint call with your production TTS model/service.
    # TODO(TTS-2): Return raw audio bytes + mime_type (audio/ogg recommended for WhatsApp).
    if not settings.WHATSAPP_TTS_ENDPOINT:
        return None

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(settings.WHATSAPP_TTS_ENDPOINT, json={"text": text})
        response.raise_for_status()

    content_type = (response.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        payload = response.json()
        if not isinstance(payload, dict):
            return None

        encoded = payload.get("audio_base64")
        mime_type = payload.get("mime_type") or "audio/ogg"
        if not isinstance(encoded, str) or not encoded.strip():
            return None

        try:
            return base64.b64decode(encoded), str(mime_type)
        except Exception:
            return None

    raw = response.content
    if not raw:
        return None
    mime_type = response.headers.get("content-type") or "audio/ogg"
    return raw, mime_type


def _unsupported_message_reply(message_type: MessageType) -> str:
    return (
        f"I received a {message_type.value} message. "
        "Please send your symptom/question as text for now."
    )


async def process_unified_message(
    incoming: UnifiedInboundMessage,
    ai_processor: AiProcessor,
) -> UnifiedOutboundMessage:
    user_text = incoming.text

    # TODO(AUDIO-ENTRY): Main audio-input hook.
    # When STT is ready, keep this branch as the only place converting voice -> text.
    if incoming.message_type == MessageType.AUDIO and not settings.WHATSAPP_STT_ENDPOINT:
        return UnifiedOutboundMessage(text=VOICE_NOTES_COMING_SOON_MESSAGE)

    # TODO(IMAGE-ENTRY): Main image-description hook.
    # When vision is ready, keep this branch as the only place converting image -> text.
    if (
        incoming.message_type == MessageType.IMAGE
        and not user_text
        and not settings.WHATSAPP_VISION_ENDPOINT
    ):
        return UnifiedOutboundMessage(text=IMAGE_DESCRIPTION_COMING_SOON_MESSAGE)

    if not user_text and (incoming.media_id or incoming.media_bytes) and incoming.message_type in {
        MessageType.AUDIO,
        MessageType.IMAGE,
    }:
        try:
            if incoming.media_bytes is not None:
                media_bytes = incoming.media_bytes
                mime_type = incoming.mime_type
            else:
                media_bytes, mime_type = await WhatsAppMediaService.download_media_bytes(
                    incoming.media_id or ""
                )

            if incoming.message_type == MessageType.AUDIO:
                user_text = await _transcribe_audio(media_bytes, mime_type or incoming.mime_type)
            elif incoming.message_type == MessageType.IMAGE:
                user_text = await _describe_image(media_bytes, mime_type or incoming.mime_type)
        except Exception as exc:
            logger.exception("Failed media preprocessing for %s: %s", incoming.chat_id, str(exc))

    if not user_text:
        return UnifiedOutboundMessage(text=_unsupported_message_reply(incoming.message_type))

    chat_response = await ai_processor(
        incoming.chat_id,
        user_text,
        incoming.user_id,
    )

    response_text = getattr(chat_response, "response", "")
    if not isinstance(response_text, str) or not response_text.strip():
        response_text = "I could not generate a response right now. Please try again."

    cleaned_response = response_text.strip()

    if (
        incoming.message_type == MessageType.AUDIO
        and settings.WHATSAPP_ENABLE_VOICE_REPLY
        and settings.WHATSAPP_TTS_ENDPOINT
    ):
        try:
            tts_result = await _synthesize_voice(cleaned_response)
            if tts_result:
                voice_audio, voice_mime_type = tts_result
                return UnifiedOutboundMessage(
                    text=cleaned_response,
                    should_send_voice=True,
                    voice_audio=voice_audio,
                    voice_mime_type=voice_mime_type,
                )
        except Exception as exc:
            logger.exception("Voice synthesis failed for %s: %s", incoming.chat_id, str(exc))

    return UnifiedOutboundMessage(text=cleaned_response)
