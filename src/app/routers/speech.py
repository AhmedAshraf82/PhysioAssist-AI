from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from src.app.core.config import settings
from src.app.services.speech_to_text import SpeechToTextService
from src.app.services.text_to_speech import TextToSpeechService

router = APIRouter(prefix="/speech", tags=["Speech"])


@router.get("/health")
async def speech_health() -> dict:
    """Speech service health/config snapshot."""
    return {
        "status": "healthy",
        "stt_ready": bool(settings.OPENAI_API_KEY),
        "tts_ready": bool(settings.OPENAI_API_KEY),
        "default_stt_model": settings.STT_MODEL,
        "default_tts_model": settings.TTS_MODEL,
        "supported_stt_models": sorted(SpeechToTextService.SUPPORTED_MODELS),
        "supported_tts_models": sorted(TextToSpeechService.SUPPORTED_MODELS),
    }


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str | None = Form(default=None),
    language: str | None = Form(default=None),
    prompt: str | None = Form(default=None),
) -> dict:
    """
    Transcribe uploaded audio with OpenAI STT.

    Accepts multipart form-data:
    - file: audio file (required)
    - model: gpt-4o-transcribe | gpt-4o-mini-transcribe | whisper-1 (optional)
    - language: language code like en/ar (optional)
    - prompt: optional transcription guidance (optional)
    """
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty")

        text = await SpeechToTextService.transcribe_audio(
            audio_bytes=audio_bytes,
            mime_type=file.content_type,
            model_override=(model or None),
            language_override=(language or None),
            prompt_override=(prompt or None),
        )

        if not text:
            raise HTTPException(
                status_code=422,
                detail="No transcription could be generated for this audio",
            )

        return {
            "success": True,
            "text": text,
            "model_used": SpeechToTextService.resolve_model(model),
            "language": language or settings.STT_LANGUAGE,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    model: str | None = Form(default=None),
    voice: str | None = Form(default=None),
    audio_format: str | None = Form(default=None),
):
    """
    Synthesize speech from text with OpenAI TTS.

    Accepts multipart form-data:
    - text: text to synthesize (required)
    - model: gpt-4o-mini-tts | gpt-4o-tts (optional)
    - voice: voice preset (optional)
    - audio_format: ogg/mp3/wav/... (optional)
    """
    try:
        content = (text or "").strip()
        if not content:
            raise HTTPException(status_code=400, detail="text is required")

        result = await TextToSpeechService.synthesize(
            text=content,
            model_override=(model or None),
            voice_override=(voice or None),
            format_override=(audio_format or None),
        )
        if not result:
            raise HTTPException(status_code=422, detail="Could not synthesize speech")

        audio_bytes, mime_type = result
        return Response(content=audio_bytes, media_type=mime_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")
