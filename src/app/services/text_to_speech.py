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

    @classmethod
    async def synthesize(
        cls,
        text: str,
        model_override: str | None = None,
        voice_override: str | None = None,
        format_override: str | None = None,
    ) -> tuple[bytes, str] | None:
        if not text.strip():
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

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            audio_bytes = response.content

        if not audio_bytes:
            return None

        return audio_bytes, cls._resolve_mime(audio_format)
