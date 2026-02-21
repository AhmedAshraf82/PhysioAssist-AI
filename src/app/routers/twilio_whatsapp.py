import logging
from xml.sax.saxutils import escape

from fastapi import APIRouter, Form
from fastapi.responses import Response

from src.app.routers.prediagnose import process_prediagnose_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/twilio", tags=["Twilio WhatsApp"])


@router.post("/whatsapp")
async def twilio_whatsapp_webhook(
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

    try:
        if not user_text:
            reply = (
                "Please send your question as text so I can help with your physiotherapy issue."
            )
        else:
            chat_response = await process_prediagnose_message(
                chat_id=f"twilio_{user_id}",
                message=user_text,
                user_id=f"twilio:{user_id}",
            )
            reply = chat_response.response

    except Exception as e:
        logger.exception("Twilio WhatsApp processing failed for %s: %s", MessageSid, str(e))
        reply = "Sorry, I had a temporary issue. Please try again in a moment."

    safe_reply = escape(reply[:1500])
    twiml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response>"
        f"<Message>{safe_reply}</Message>"
        "</Response>"
    )
    return Response(content=twiml, media_type="application/xml")
