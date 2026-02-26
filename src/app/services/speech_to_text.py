import io
import logging
from typing import Any

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
        text, _ = await cls.transcribe_audio_with_usage(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            model_override=model_override,
            language_override=language_override,
            prompt_override=prompt_override,
        )
        return text

    @staticmethod
    def _read_usage_value(usage_obj: Any, *keys: str) -> int:
        if usage_obj is None:
            return 0

        for key in keys:
            value = None
            if isinstance(usage_obj, dict):
                value = usage_obj.get(key)
            else:
                value = getattr(usage_obj, key, None)

            if isinstance(value, (int, float)):
                return int(value)
        return 0

    @classmethod
    async def transcribe_audio_with_usage(
        cls,
        audio_bytes: bytes,
        mime_type: str | None = None,
        model_override: str | None = None,
        language_override: str | None = None,
        prompt_override: str | None = None,
    ) -> tuple[str | None, dict[str, int]]:
        if not audio_bytes:
            return None, {
                "text_input_tokens": 0,
                "text_output_tokens": 0,
                "audio_input_tokens": 0,
            }

        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is missing; STT cannot run")
            return None, {
                "text_input_tokens": 0,
                "text_output_tokens": 0,
                "audio_input_tokens": 0,
            }

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

        usage = getattr(transcription, "usage", None)
        usage_data = {
            "text_input_tokens": cls._read_usage_value(
                usage,
                "text_input_tokens",
                "input_text_tokens",
                "prompt_tokens",
                "input_tokens",
            ),
            "text_output_tokens": cls._read_usage_value(
                usage,
                "text_output_tokens",
                "output_text_tokens",
                "completion_tokens",
                "output_tokens",
            ),
            "audio_input_tokens": cls._read_usage_value(
                usage,
                "audio_input_tokens",
                "input_audio_tokens",
                "audio_tokens",
            ),
        }

        if isinstance(text, str) and text.strip():
            return text.strip(), usage_data
        return None, usage_data
