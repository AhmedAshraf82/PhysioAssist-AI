import logging
import json
import re

import httpx

from src.app.core.config import settings
from src.app.models.audio_models import TTSVoice

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """Text-to-speech service backed by OpenAI audio speech API."""

    SUPPORTED_MODELS = {
        "gpt-4o-mini-tts",
        "gpt-4o-tts",
    }

    SUPPORTED_VOICES = {voice.value for voice in TTSVoice}

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

    @classmethod
    def _resolve_voice(cls, voice_override: str | None = None) -> str:
        configured_voice = settings.TTS_VOICE.value if isinstance(settings.TTS_VOICE, TTSVoice) else str(settings.TTS_VOICE)
        voice = (voice_override or configured_voice or TTSVoice.ALLOY.value).strip().lower()
        if voice not in cls.SUPPORTED_VOICES:
            logger.warning(
                "Unsupported TTS voice '%s'. Falling back to 'alloy'.",
                voice,
            )
            return TTSVoice.ALLOY.value
        return voice

    @staticmethod
    def _resolve_speed(speed_override: float | None = None) -> float:
        raw_speed = speed_override if speed_override is not None else settings.TTS_SPEED
        try:
            speed = float(raw_speed)
        except (TypeError, ValueError):
            logger.warning("Invalid TTS speed '%s'. Falling back to 1.15.", raw_speed)
            return 1.15

        # Keep a safe range for speech synthesis speed.
        if speed < 0.5:
            logger.warning("TTS speed %s too low. Clamping to 0.5.", speed)
            return 0.5
        if speed > 2.0:
            logger.warning("TTS speed %s too high. Clamping to 2.0.", speed)
            return 2.0
        return speed

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
        speed_override: float | None = None,
        format_override: str | None = None,
    ) -> tuple[bytes, str] | None:
        result, _ = await cls.synthesize_with_usage(
            text=text,
            model_override=model_override,
            voice_override=voice_override,
            speed_override=speed_override,
            format_override=format_override,
        )
        return result

    @staticmethod
    def _parse_usage_header(raw_header: str | None) -> dict[str, int]:
        if not raw_header:
            return {"text_input_tokens": 0, "audio_output_tokens": 0}

        try:
            payload = json.loads(raw_header)
        except Exception:
            return {"text_input_tokens": 0, "audio_output_tokens": 0}

        if not isinstance(payload, dict):
            return {"text_input_tokens": 0, "audio_output_tokens": 0}

        text_input = payload.get("text_input_tokens")
        if not isinstance(text_input, (int, float)):
            text_input = payload.get("input_tokens")

        audio_output = payload.get("audio_output_tokens")
        if not isinstance(audio_output, (int, float)):
            audio_output = payload.get("output_audio_tokens")

        return {
            "text_input_tokens": int(text_input) if isinstance(text_input, (int, float)) else 0,
            "audio_output_tokens": int(audio_output) if isinstance(audio_output, (int, float)) else 0,
        }

    @staticmethod
    def _estimate_text_input_tokens(text: str) -> int:
        """Estimate text tokens when provider usage metadata is unavailable."""
        cleaned = (text or "").strip()
        if not cleaned:
            return 0

        # Practical approximation for English-like text: ~4 chars/token.
        return max(1, int(round(len(cleaned) / 4)))

    @staticmethod
    def _estimate_audio_output_tokens(text: str, speed: float) -> int:
        """
        Estimate audio tokens from spoken duration.

        Heuristic:
        - Speech rate baseline: ~150 words/min at speed=1.0
        - Audio tokenization baseline: ~50 audio tokens/sec (20ms per token)
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return 0

        words = re.findall(r"\S+", cleaned)
        word_count = len(words)
        effective_speed = speed if speed > 0 else 1.0

        # Avoid division by zero and unrealistic tiny durations.
        words_per_minute = max(60.0, 150.0 * effective_speed)
        duration_seconds = max(0.2, (word_count / words_per_minute) * 60.0)

        return max(1, int(round(duration_seconds * 50.0)))

    @classmethod
    def _finalize_usage(
        cls,
        usage_data: dict[str, int],
        text: str,
        speed: float,
    ) -> dict[str, int]:
        """Fill missing usage values with estimated non-zero fallbacks."""
        text_input_tokens = int(usage_data.get("text_input_tokens", 0) or 0)
        audio_output_tokens = int(usage_data.get("audio_output_tokens", 0) or 0)

        if text_input_tokens <= 0:
            text_input_tokens = cls._estimate_text_input_tokens(text)
        if audio_output_tokens <= 0:
            audio_output_tokens = cls._estimate_audio_output_tokens(text, speed)

        return {
            "text_input_tokens": text_input_tokens,
            "audio_output_tokens": audio_output_tokens,
        }

    @classmethod
    async def synthesize_with_usage(
        cls,
        text: str,
        model_override: str | None = None,
        voice_override: str | None = None,
        speed_override: float | None = None,
        format_override: str | None = None,
    ) -> tuple[tuple[bytes, str] | None, dict[str, int]]:
        if not text.strip():
            logger.warning("TTS Service: empty text input, skipping synthesis")
            return None, {"text_input_tokens": 0, "audio_output_tokens": 0}
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is missing; TTS cannot run")
            return None, {"text_input_tokens": 0, "audio_output_tokens": 0}

        model = cls.resolve_model(model_override)
        voice = cls._resolve_voice(voice_override)
        speed = cls._resolve_speed(speed_override)
        audio_format = cls._resolve_format(format_override)

        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "speed": speed,
            "format": audio_format,
        }

        logger.info(
            "TTS Service: synthesize start (model=%s, voice=%s, speed=%s, format=%s, text_len=%s)",
            model,
            voice,
            speed,
            audio_format,
            len(text),
        )

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response_content_type: str | None = None
            usage_header: str | None = None
            try:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers=headers,
                    json=payload,
                )
                response_content_type = response.headers.get("content-type")
                usage_header = response.headers.get("openai-usage") or response.headers.get("x-openai-usage")
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
                        "speed": speed,
                        "format": audio_format,
                    }
                    retry_response = await client.post(
                        "https://api.openai.com/v1/audio/speech",
                        headers=headers,
                        json=fallback_payload,
                    )
                    response_content_type = retry_response.headers.get("content-type")
                    usage_header = retry_response.headers.get("openai-usage") or retry_response.headers.get("x-openai-usage")
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
            return None, {"text_input_tokens": 0, "audio_output_tokens": 0}

        resolved_mime = cls._resolve_mime_from_response(response_content_type, audio_format)
        if resolved_mime != cls._resolve_mime(audio_format):
            logger.warning(
                "TTS Service: MIME mismatch detected (requested_format=%s expected_mime=%s actual_mime=%s)",
                audio_format,
                cls._resolve_mime(audio_format),
                resolved_mime,
            )

        logger.info("TTS Service: synthesize success (audio_bytes=%s)", len(audio_bytes))
        usage_data = cls._parse_usage_header(usage_header)
        usage_data = cls._finalize_usage(usage_data, text=text, speed=speed)
        return (audio_bytes, resolved_mime), usage_data
