import logging
import base64
from typing import Awaitable, Callable

import httpx

from src.app.core.config import settings
from src.app.models.channel_models import MessageType, UnifiedInboundMessage, UnifiedOutboundMessage
from src.app.services.channels.media.whatsapp_media_service import WhatsAppMediaService
from src.app.services.speech_to_text import SpeechToTextService
from src.app.services.text_to_speech import TextToSpeechService

logger = logging.getLogger(__name__)

AiProcessor = Callable[[str | None, str, str | None], Awaitable[object]]


VOICE_NOTES_COMING_SOON_MESSAGE = "Voice notes support coming soon!"
IMAGE_DESCRIPTION_COMING_SOON_MESSAGE = "Image description support coming soon!"


async def _transcribe_audio(
    media_bytes: bytes,
    mime_type: str | None,
) -> tuple[str | None, dict[str, int]]:
    # Primary path: OpenAI STT service with configurable model.
    if settings.OPENAI_API_KEY:
        logger.info(
            "STT: using OpenAI path (mime_type=%s, bytes=%s)",
            mime_type,
            len(media_bytes),
        )
        return await SpeechToTextService.transcribe_audio_with_usage(media_bytes, mime_type)

    # Backward-compatible fallback: external STT endpoint if configured.
    if not settings.WHATSAPP_STT_ENDPOINT:
        logger.info("STT: skipped (no OPENAI_API_KEY and no WHATSAPP_STT_ENDPOINT)")
        return None, {
            "text_input_tokens": 0,
            "text_output_tokens": 0,
            "audio_input_tokens": 0,
        }

    files = {
        "file": (
            f"voice_note.{(mime_type or 'audio/ogg').split('/')[-1]}",
            media_bytes,
            mime_type or "audio/ogg",
        )
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        logger.info("STT: using fallback endpoint %s", settings.WHATSAPP_STT_ENDPOINT)
        response = await client.post(settings.WHATSAPP_STT_ENDPOINT, files=files)
        response.raise_for_status()
        payload = response.json()

    transcript = payload.get("text") if isinstance(payload, dict) else None
    logger.info("STT: fallback transcript received=%s", bool(transcript))
    return (
        transcript.strip() if isinstance(transcript, str) and transcript.strip() else None,
        {
            "text_input_tokens": 0,
            "text_output_tokens": 0,
            "audio_input_tokens": 0,
        },
    )


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


async def _synthesize_voice(text: str) -> tuple[tuple[bytes, str] | None, dict[str, int]]:
    # Primary path: OpenAI TTS service with configurable model.
    if settings.OPENAI_API_KEY:
        logger.info("TTS: using OpenAI path (text_len=%s)", len(text))
        return await TextToSpeechService.synthesize_with_usage(text)

    # Backward-compatible fallback: external TTS endpoint if configured.
    if not settings.WHATSAPP_TTS_ENDPOINT:
        logger.info("TTS: skipped (no OPENAI_API_KEY and no WHATSAPP_TTS_ENDPOINT)")
        return None, {"text_input_tokens": 0, "audio_output_tokens": 0}

    async with httpx.AsyncClient(timeout=90.0) as client:
        logger.info("TTS: using fallback endpoint %s", settings.WHATSAPP_TTS_ENDPOINT)
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
            return None, {"text_input_tokens": 0, "audio_output_tokens": 0}

        try:
            logger.info("TTS: fallback JSON audio_base64 received")
            return (
                (base64.b64decode(encoded), str(mime_type)),
                {"text_input_tokens": 0, "audio_output_tokens": 0},
            )
        except Exception:
            logger.exception("TTS: failed decoding fallback base64 audio payload")
            return None, {"text_input_tokens": 0, "audio_output_tokens": 0}

    raw = response.content
    if not raw:
        logger.warning("TTS: fallback endpoint returned empty body")
        return None, {"text_input_tokens": 0, "audio_output_tokens": 0}
    mime_type = response.headers.get("content-type") or "audio/ogg"
    logger.info("TTS: fallback raw audio received (bytes=%s, mime_type=%s)", len(raw), mime_type)
    return (raw, mime_type), {"text_input_tokens": 0, "audio_output_tokens": 0}


def _unsupported_message_reply(message_type: MessageType) -> str:
    return (
        f"I received a {message_type.value} message. "
        "Please send your symptom/question as text for now."
    )


def _has_stt_support() -> bool:
    return bool(settings.OPENAI_API_KEY or settings.WHATSAPP_STT_ENDPOINT)


def _has_tts_support() -> bool:
    return bool(settings.OPENAI_API_KEY or settings.WHATSAPP_TTS_ENDPOINT)


async def process_unified_message(
    incoming: UnifiedInboundMessage,
    ai_processor: AiProcessor,
) -> UnifiedOutboundMessage:
    user_text = incoming.text
    metadata: dict[str, object] = {}
    logger.info(
        "UnifiedMessage: start chat_id=%s user_id=%s type=%s has_text=%s has_media_id=%s has_media_bytes=%s",
        incoming.chat_id,
        incoming.user_id,
        incoming.message_type.value,
        bool(user_text and user_text.strip()),
        bool(incoming.media_id),
        incoming.media_bytes is not None,
    )

    # TODO(AUDIO-ENTRY): Main audio-input hook.
    # When STT is ready, keep this branch as the only place converting voice -> text.
    if incoming.message_type == MessageType.AUDIO and not _has_stt_support():
        logger.warning("UnifiedMessage: audio received but STT support disabled")
        return UnifiedOutboundMessage(text=VOICE_NOTES_COMING_SOON_MESSAGE)

    # TODO(IMAGE-ENTRY): Main image-description hook.
    # When vision is ready, keep this branch as the only place converting image -> text.
    if (
        incoming.message_type == MessageType.IMAGE
        and not user_text
        and not settings.WHATSAPP_VISION_ENDPOINT
    ):
        logger.warning("UnifiedMessage: image received but vision endpoint is not configured")
        return UnifiedOutboundMessage(text=IMAGE_DESCRIPTION_COMING_SOON_MESSAGE)

    if not user_text and (incoming.media_id or incoming.media_bytes) and incoming.message_type in {
        MessageType.AUDIO,
        MessageType.IMAGE,
    }:
        try:
            logger.info("UnifiedMessage: media preprocessing started (type=%s)", incoming.message_type.value)
            if incoming.media_bytes is not None:
                media_bytes = incoming.media_bytes
                mime_type = incoming.mime_type
                logger.info(
                    "UnifiedMessage: using in-request media bytes (bytes=%s, mime=%s)",
                    len(media_bytes),
                    mime_type,
                )
            else:
                media_bytes, mime_type = await WhatsAppMediaService.download_media_bytes(
                    incoming.media_id or ""
                )
                logger.info(
                    "UnifiedMessage: downloaded media bytes from WhatsApp (bytes=%s, mime=%s)",
                    len(media_bytes),
                    mime_type,
                )

            if incoming.message_type == MessageType.AUDIO:
                user_text, stt_usage = await _transcribe_audio(media_bytes, mime_type or incoming.mime_type)
                metadata["stt_usage"] = stt_usage
                logger.info("UnifiedMessage: STT completed (has_text=%s)", bool(user_text))
            elif incoming.message_type == MessageType.IMAGE:
                user_text = await _describe_image(media_bytes, mime_type or incoming.mime_type)
                logger.info("UnifiedMessage: vision completed (has_text=%s)", bool(user_text))
        except Exception as exc:
            logger.exception("Failed media preprocessing for %s: %s", incoming.chat_id, str(exc))

    if not user_text:
        logger.warning(
            "UnifiedMessage: no user_text after preprocessing, returning unsupported message for type=%s",
            incoming.message_type.value,
        )
        return UnifiedOutboundMessage(text=_unsupported_message_reply(incoming.message_type))

    metadata["normalized_user_text"] = user_text

    logger.info("UnifiedMessage: invoking ai_processor (chat_id=%s)", incoming.chat_id)
    chat_response = await ai_processor(
        incoming.chat_id,
        user_text,
        incoming.user_id,
    )

    llm_prompt_tokens = int(getattr(chat_response, "llm_prompt_tokens", 0) or 0)
    llm_completion_tokens = int(getattr(chat_response, "llm_completion_tokens", 0) or 0)
    llm_cost_usd = float(getattr(chat_response, "llm_cost_usd", 0.0) or 0.0)
    metadata["llm_usage"] = {
        "prompt_tokens": llm_prompt_tokens,
        "completion_tokens": llm_completion_tokens,
        "cost_usd": llm_cost_usd,
    }

    response_text = getattr(chat_response, "response", "")
    if not isinstance(response_text, str) or not response_text.strip():
        response_text = "I could not generate a response right now. Please try again."

    cleaned_response = response_text.strip()
    logger.info("UnifiedMessage: ai response ready (response_len=%s)", len(cleaned_response))

    should_try_tts = (
        incoming.message_type == MessageType.AUDIO
        and (settings.VOICE_REPLY_ON_AUDIO_INPUT or settings.WHATSAPP_ENABLE_VOICE_REPLY)
        and _has_tts_support()
    )

    logger.info(
        "UnifiedMessage: TTS gate message_type_audio=%s voice_reply_on_audio_input=%s whatsapp_enable_voice_reply=%s has_tts_support=%s => should_try_tts=%s",
        incoming.message_type == MessageType.AUDIO,
        settings.VOICE_REPLY_ON_AUDIO_INPUT,
        settings.WHATSAPP_ENABLE_VOICE_REPLY,
        _has_tts_support(),
        should_try_tts,
    )

    if should_try_tts:
        try:
            logger.info("UnifiedMessage: calling TTS synthesis")
            tts_result, tts_usage = await _synthesize_voice(cleaned_response)
            metadata["tts_usage"] = tts_usage
            if tts_result:
                voice_audio, voice_mime_type = tts_result
                logger.info(
                    "UnifiedMessage: TTS success (bytes=%s, mime=%s)",
                    len(voice_audio),
                    voice_mime_type,
                )
                return UnifiedOutboundMessage(
                    text=cleaned_response,
                    should_send_voice=True,
                    voice_audio=voice_audio,
                    voice_mime_type=voice_mime_type,
                    metadata=metadata,
                )
            logger.warning("UnifiedMessage: TTS returned empty result, falling back to text")
        except Exception as exc:
            logger.exception("Voice synthesis failed for %s: %s", incoming.chat_id, str(exc))

    logger.info("UnifiedMessage: returning text response only")
    return UnifiedOutboundMessage(text=cleaned_response, metadata=metadata)
