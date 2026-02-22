import io
import logging

from openai import AsyncOpenAI

from src.app.core.config import settings

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """Speech-to-text service backed by OpenAI transcription models."""

    SUPPORTED_MODELS = {
        "gpt-4o-transcribe",
        "gpt-4o-mini-transcribe",
        "whisper-1",
    }

    @classmethod
    def resolve_model(cls, model_override: str | None = None) -> str:
        return cls._resolve_model(model_override)

    @classmethod
    def _resolve_model(cls, model_override: str | None = None) -> str:
        model = (model_override or settings.STT_MODEL or "gpt-4o-transcribe").strip()
        if model not in cls.SUPPORTED_MODELS:
            logger.warning(
                "Unsupported STT model '%s'. Falling back to gpt-4o-transcribe.", model
            )
            return "gpt-4o-transcribe"
        return model

    @staticmethod
    def _filename_for_mime(mime_type: str | None) -> str:
        if not mime_type:
            return "audio.ogg"
        extension = mime_type.split("/")[-1].split(";")[0].strip() or "ogg"
        return f"audio.{extension}"

    @classmethod
    async def transcribe_audio(
        cls,
        audio_bytes: bytes,
        mime_type: str | None = None,
        model_override: str | None = None,
        language_override: str | None = None,
        prompt_override: str | None = None,
    ) -> str | None:
        if not audio_bytes:
            return None

        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is missing; STT cannot run")
            return None

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        model = cls._resolve_model(model_override)

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = cls._filename_for_mime(mime_type)

        kwargs: dict[str, object] = {
            "model": model,
            "file": audio_file,
        }

        resolved_language = language_override if language_override is not None else settings.STT_LANGUAGE
        if resolved_language:
            kwargs["language"] = resolved_language

        resolved_prompt = prompt_override if prompt_override is not None else settings.STT_PROMPT
        if resolved_prompt:
            kwargs["prompt"] = resolved_prompt

        transcription = await client.audio.transcriptions.create(**kwargs)
        text = getattr(transcription, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
        return None
