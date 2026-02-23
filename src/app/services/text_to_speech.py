import logging

import httpx

from src.app.core.config import settings

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """Text-to-speech service backed by OpenAI audio speech API."""

    SUPPORTED_MODELS = {
        "gpt-4o-mini-tts",
        "gpt-4o-tts",
    }

    @classmethod
    def resolve_model(cls, model_override: str | None = None) -> str:
        model = (model_override or settings.TTS_MODEL or "gpt-4o-mini-tts").strip()
        if model not in cls.SUPPORTED_MODELS:
            logger.warning(
                "Unsupported TTS model '%s'. Falling back to gpt-4o-mini-tts.",
                model,
            )
            return "gpt-4o-mini-tts"
        return model

    @staticmethod
    def _resolve_format(format_override: str | None = None) -> str:
        fmt = (format_override or settings.TTS_AUDIO_FORMAT or "ogg").strip().lower()
        supported = {"mp3", "wav", "opus", "aac", "flac", "pcm", "ogg"}
        if fmt not in supported:
            return "ogg"
        return fmt

    @staticmethod
    def _resolve_mime(audio_format: str) -> str:
        if audio_format in {"ogg", "opus"}:
            return "audio/ogg"
        if audio_format == "mp3":
            return "audio/mpeg"
        if audio_format == "wav":
            return "audio/wav"
        if audio_format == "aac":
            return "audio/aac"
        if audio_format == "flac":
            return "audio/flac"
        if audio_format == "pcm":
            return "audio/pcm"
        return "audio/ogg"

    @staticmethod
    def _resolve_mime_from_response(
        content_type_header: str | None,
        requested_audio_format: str,
    ) -> str:
        content_type = (content_type_header or "").split(";")[0].strip().lower()
        if content_type.startswith("audio/"):
            return content_type
        return TextToSpeechService._resolve_mime(requested_audio_format)

    @classmethod
    async def synthesize(
        cls,
        text: str,
        model_override: str | None = None,
        voice_override: str | None = None,
        format_override: str | None = None,
    ) -> tuple[bytes, str] | None:
        if not text.strip():
            logger.warning("TTS Service: empty text input, skipping synthesis")
            return None
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is missing; TTS cannot run")
            return None

        model = cls.resolve_model(model_override)
        voice = (voice_override or settings.TTS_VOICE or "alloy").strip()
        audio_format = cls._resolve_format(format_override)

        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "format": audio_format,
        }

        logger.info(
            "TTS Service: synthesize start (model=%s, voice=%s, format=%s, text_len=%s)",
            model,
            voice,
            audio_format,
            len(text),
        )

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response_content_type: str | None = None
            try:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers=headers,
                    json=payload,
                )
                response_content_type = response.headers.get("content-type")
                logger.info(
                    "TTS Service: OpenAI response status=%s content_type=%s",
                    response.status_code,
                    response_content_type,
                )
                response.raise_for_status()
                audio_bytes = response.content
            except httpx.HTTPStatusError as exc:
                response_body = exc.response.text if exc.response is not None else ""
                logger.error(
                    "TTS Service: OpenAI HTTP error status=%s body=%s",
                    exc.response.status_code if exc.response is not None else "unknown",
                    (response_body[:500] if response_body else ""),
                )

                # Auto-fallback for unavailable model access (common in some accounts/environments).
                if (
                    exc.response is not None
                    and exc.response.status_code == 404
                    and model != "gpt-4o-mini-tts"
                    and (
                        "model_not_found" in response_body
                        or "does not exist" in response_body
                        or "do not have access" in response_body
                    )
                ):
                    logger.warning(
                        "TTS Service: model '%s' unavailable; retrying with fallback model 'gpt-4o-mini-tts'",
                        model,
                    )
                    fallback_payload = {
                        "model": "gpt-4o-mini-tts",
                        "voice": voice,
                        "input": text,
                        "format": audio_format,
                    }
                    retry_response = await client.post(
                        "https://api.openai.com/v1/audio/speech",
                        headers=headers,
                        json=fallback_payload,
                    )
                    response_content_type = retry_response.headers.get("content-type")
                    logger.info(
                        "TTS Service: fallback OpenAI response status=%s content_type=%s",
                        retry_response.status_code,
                        response_content_type,
                    )
                    retry_response.raise_for_status()
                    audio_bytes = retry_response.content
                else:
                    raise
            except Exception:
                logger.exception("TTS Service: unexpected exception during OpenAI TTS request")
                raise

        if not audio_bytes:
            logger.warning("TTS Service: OpenAI returned empty audio bytes")
            return None

        resolved_mime = cls._resolve_mime_from_response(response_content_type, audio_format)
        if resolved_mime != cls._resolve_mime(audio_format):
            logger.warning(
                "TTS Service: MIME mismatch detected (requested_format=%s expected_mime=%s actual_mime=%s)",
                audio_format,
                cls._resolve_mime(audio_format),
                resolved_mime,
            )

        logger.info("TTS Service: synthesize success (audio_bytes=%s)", len(audio_bytes))
        return audio_bytes, resolved_mime
