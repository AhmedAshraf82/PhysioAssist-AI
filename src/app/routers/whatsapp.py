import hashlib
import hmac
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from src.app.core.config import settings
from src.app.routers.prediagnose import process_prediagnose_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp"])


def _messages_endpoint() -> str:
    return (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
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


def _extract_user_text_from_message(message: dict[str, Any]) -> str | None:
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

    # Support media messages with captions where available
    if message_type in {"image", "video", "document"}:
        media_payload = message.get(message_type, {})
        caption = media_payload.get("caption", "").strip()
        if caption:
            return caption

    return None


def _unsupported_message_reply(message_type: str | None) -> str:
    kind = message_type or "this"
    return (
        f"I received a {kind} message. For now I can reply best to text messages "
        "(or media captions). Please send your symptom/question in text."
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
                user_wa_id = message.get("from")
                message_type = message.get("type")
                user_text = _extract_user_text_from_message(message)

                if not user_wa_id:
                    continue

                try:
                    if not user_text:
                        await send_whatsapp_text(
                            user_wa_id,
                            _unsupported_message_reply(message_type),
                        )
                        continue

                    chat_response = await process_prediagnose_message(
                        chat_id=f"wa_{user_wa_id}",
                        message=user_text,
                        user_id=f"wa:{user_wa_id}",
                    )
                    await send_whatsapp_text(user_wa_id, chat_response.response)
                except Exception as e:
                    logger.exception("Failed to process WhatsApp message: %s", str(e))

    return {"status": "ok"}
