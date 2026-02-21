import logging
from xml.sax.saxutils import escape

import httpx
from fastapi import APIRouter, BackgroundTasks, Form
from fastapi.responses import Response

from src.app.core.config import settings
from src.app.routers.prediagnose import process_prediagnose_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/twilio", tags=["Twilio WhatsApp"])


def _has_twilio_outbound_config() -> bool:
    return bool(
        settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_WHATSAPP_NUMBER
    )


async def _send_twilio_whatsapp_message(to_number: str, body: str) -> None:
    if not _has_twilio_outbound_config():
        logger.warning("Twilio outbound config missing; cannot send async reply")
        return

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_WHATSAPP_NUMBER
    assert account_sid and auth_token and from_number

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {
        "To": to_number,
        "From": from_number,
        "Body": body[:1500],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, data=data, auth=(account_sid, auth_token))

    if response.status_code >= 400:
        logger.error("Twilio outbound send failed: %s", response.text)


async def _process_and_send_reply(user_id: str, user_text: str, message_sid: str) -> None:
    try:
        chat_response = await process_prediagnose_message(
            chat_id=f"twilio_{user_id}",
            message=user_text,
            user_id=f"twilio:{user_id}",
        )
        await _send_twilio_whatsapp_message(user_id, chat_response.response)
    except Exception as e:
        logger.exception("Twilio WhatsApp processing failed for %s: %s", message_sid, str(e))


@router.post("/whatsapp")
async def twilio_whatsapp_webhook(
    background_tasks: BackgroundTasks,
    Body: str = Form(default=""),
    From: str = Form(default=""),
    MessageSid: str = Form(default=""),
):
    """
    Twilio WhatsApp webhook endpoint.

    Twilio posts inbound WhatsApp messages as form-data.
    We return TwiML XML directly so Twilio sends the reply to the same user.
    """
    user_text = (Body or "").strip()
    user_id = (From or "").strip()

    if not user_id:
        twiml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Avoid Twilio webhook timeout by acknowledging immediately.
    # Real bot reply is sent in background via Twilio REST API.
    if not user_text:
        fallback = "Please send your question as text so I can help with your physiotherapy issue."
        safe_reply = escape(fallback)
        twiml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Response>"
            f"<Message>{safe_reply}</Message>"
            "</Response>"
        )
        return Response(content=twiml, media_type="application/xml")

    background_tasks.add_task(_process_and_send_reply, user_id, user_text, MessageSid)

    twiml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>"
    return Response(content=twiml, media_type="application/xml")
