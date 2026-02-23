import hashlib
import hmac
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from src.app.core.config import settings
from src.app.routers.prediagnose import process_prediagnose_message
from src.app.services.channels.adapters.whatsapp_adapter import to_unified_message
from src.app.services.channels.orchestrator import process_unified_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp"])


def _messages_endpoint() -> str:
    return (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )


def _media_endpoint() -> str:
    return (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/media"
    )


def _graph_api_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


async def _send_payload(payload: dict[str, Any]) -> httpx.Response:
    async with httpx.AsyncClient(timeout=30.0) as client:
        return await client.post(
            _messages_endpoint(),
            json=payload,
            headers=_graph_api_headers(),
        )


def _graph_auth_headers_only() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
    }


async def upload_whatsapp_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise ValueError(
            "Missing WhatsApp config: WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID"
        )

    extension = (mime_type.split("/")[-1] if "/" in mime_type else "ogg").split(";")[0]
    filename = f"reply.{extension or 'ogg'}"

    files = {
        "file": (filename, audio_bytes, mime_type),
    }
    data = {
        "type": mime_type,
        "messaging_product": "whatsapp",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            _media_endpoint(),
            data=data,
            files=files,
            headers=_graph_auth_headers_only(),
        )

    if response.status_code >= 400:
        logger.error("Failed uploading WhatsApp audio: %s", response.text)
        raise HTTPException(
            status_code=502,
            detail="Failed uploading WhatsApp audio media",
        )

    payload = response.json()
    media_id = payload.get("id") if isinstance(payload, dict) else None
    if not media_id:
        raise HTTPException(status_code=502, detail="WhatsApp media upload returned no id")
    return str(media_id)


async def send_whatsapp_audio(to_wa_id: str, media_id: str) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "audio",
        "audio": {"id": media_id},
    }

    response = await _send_payload(payload)
    if response.status_code >= 400:
        logger.error("Failed sending WhatsApp audio message: %s", response.text)
        raise HTTPException(
            status_code=502,
            detail="Failed sending WhatsApp audio via Graph API",
        )


def _is_outside_24h_window(error_payload: dict[str, Any]) -> bool:
    err = error_payload.get("error", {}) if isinstance(error_payload, dict) else {}
    code = err.get("code")
    subcode = err.get("error_subcode")
    message = str(err.get("message", "")).lower()
    return (
        code == 131047
        or subcode == 2494010
        or "24-hour" in message
        or "24 hour" in message
    )


async def send_whatsapp_template(
    to_wa_id: str,
    template_name: str,
    language_code: str = "en_US",
) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }

    response = await _send_payload(payload)
    if response.status_code >= 400:
        logger.error("Failed sending WhatsApp template: %s", response.text)
        raise HTTPException(
            status_code=502,
            detail="Failed sending WhatsApp template via Graph API",
        )


async def send_whatsapp_text(to_wa_id: str, text: str) -> None:
    """Send a WhatsApp text reply using Cloud API with optional template fallback."""
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise ValueError(
            "Missing WhatsApp config: WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID"
        )

    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "text",
        "text": {"body": text[:4096]},
    }

    response = await _send_payload(payload)

    if response.status_code >= 400:
        error_payload: dict[str, Any] = {}
        try:
            error_payload = response.json()
        except Exception:
            error_payload = {}

        if (
            settings.WHATSAPP_ENABLE_TEMPLATE_FALLBACK
            and settings.WHATSAPP_FALLBACK_TEMPLATE_NAME
            and _is_outside_24h_window(error_payload)
        ):
            logger.info("Outside 24h window, sending fallback template")
            await send_whatsapp_template(
                to_wa_id=to_wa_id,
                template_name=settings.WHATSAPP_FALLBACK_TEMPLATE_NAME,
                language_code=settings.WHATSAPP_FALLBACK_TEMPLATE_LANG,
            )
            return

        logger.error("Failed sending WhatsApp message: %s", response.text)
        raise HTTPException(
            status_code=502,
            detail="Failed sending WhatsApp message via Graph API",
        )


@router.get("", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Meta webhook verification endpoint."""
    if (
        hub_mode == "subscribe"
        and hub_verify_token
        and settings.WHATSAPP_VERIFY_TOKEN
        and hmac.compare_digest(hub_verify_token, settings.WHATSAPP_VERIFY_TOKEN)
    ):
        return hub_challenge or ""

    raise HTTPException(status_code=403, detail="Webhook verification failed")


def _is_valid_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Validate X-Hub-Signature-256 if secret is configured."""
    if not settings.WHATSAPP_WEBHOOK_SECRET:
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.WHATSAPP_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    received = signature_header.replace("sha256=", "", 1)
    return hmac.compare_digest(received, expected)


@router.post("")
async def handle_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
):
    """Receive inbound WhatsApp messages and reply using prediagnose chat flow."""
    raw_body = await request.body()
    if not _is_valid_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()

    entries = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])

            # Ignore status updates and non-message events
            if not messages:
                continue

            for message in messages:
                unified = to_unified_message(message)

                if not unified:
                    continue

                logger.info(
                    "WhatsApp webhook: inbound parsed (chat_id=%s, type=%s, media_id=%s)",
                    unified.chat_id,
                    unified.message_type.value,
                    bool(unified.media_id),
                )

                try:
                    outbound = await process_unified_message(
                        incoming=unified,
                        ai_processor=process_prediagnose_message,
                    )
                    logger.info(
                        "WhatsApp webhook: outbound generated (chat_id=%s, should_send_voice=%s, has_voice_audio=%s)",
                        unified.chat_id,
                        outbound.should_send_voice,
                        bool(outbound.voice_audio),
                    )
                    recipient_wa_id = str(unified.metadata.get("whatsapp_from", "")).strip()
                    if not recipient_wa_id:
                        logger.warning("WhatsApp webhook: missing recipient_wa_id for chat_id=%s", unified.chat_id)
                        continue

                    if outbound.should_send_voice and outbound.voice_audio:
                        try:
                            logger.info("WhatsApp webhook: uploading voice reply for %s", recipient_wa_id)
                            media_id = await upload_whatsapp_audio(
                                outbound.voice_audio,
                                outbound.voice_mime_type or "audio/ogg",
                            )
                            logger.info("WhatsApp webhook: sending audio message media_id=%s", media_id)
                            await send_whatsapp_audio(recipient_wa_id, media_id)
                            continue
                        except Exception as voice_error:
                            logger.exception(
                                "Voice reply failed, falling back to text for %s: %s",
                                recipient_wa_id,
                                str(voice_error),
                            )

                    logger.info("WhatsApp webhook: sending text fallback for %s", recipient_wa_id)
                    await send_whatsapp_text(recipient_wa_id, outbound.text)
                except Exception as e:
                    logger.exception("Failed to process WhatsApp message: %s", str(e))

    return {"status": "ok"}
