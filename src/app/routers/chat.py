import base64
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.app.core.config import settings
from src.app.models.channel_models import MessageType
from src.app.models.chat_models import ChatMessage, ChatResponse, MultimodalChatResponse
from src.app.services.channels.adapters.web_adapter import (
    to_unified_message,
    to_unified_multimodal_message,
)
from src.app.services.chats.chat_service import (
    persist_unified_chat_turn,
    process_unified_chat_message,
)
from src.app.services.db_handler.chat_session_handler import ChatSessionHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(msg: ChatMessage):
    try:
        unified = to_unified_message(msg)
        outbound = await process_unified_chat_message(unified)

        logger.info(
            "Chat: outbound ready (chat_id=%s, type=%s, should_send_voice=%s, has_voice_audio=%s)",
            unified.chat_id,
            unified.message_type.value,
            outbound.should_send_voice,
            bool(outbound.voice_audio),
        )

        message_count = persist_unified_chat_turn(
            unified=unified,
            outbound=outbound,
            fallback_user_text=msg.message,
            user_mime_type=unified.message_type.value.upper(),
        )

        return ChatResponse(
            chat_id=unified.chat_id,
            response=outbound.text,
            message_count=message_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.post("/multimodal", response_model=MultimodalChatResponse)
async def chat_multimodal_endpoint(
    message: str = Form(default=""),
    chat_id: str | None = Form(default=None),
    user_id: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    try:
        text = (message or "").strip() or None

        media_bytes: bytes | None = None
        mime_type: str | None = None
        message_type = MessageType.TEXT

        if file is not None:
            media_bytes = await file.read()
            mime_type = (file.content_type or "").strip() or None

            if mime_type and mime_type.startswith("image/"):
                message_type = MessageType.IMAGE
            elif mime_type and mime_type.startswith("audio/"):
                message_type = MessageType.AUDIO
            else:
                message_type = MessageType.UNKNOWN

        if not text and media_bytes is None:
            raise HTTPException(status_code=400, detail="Provide text and/or a file")

        unified = to_unified_multimodal_message(
            chat_id=chat_id,
            user_id=user_id,
            message_type=message_type,
            text=text,
            media_bytes=media_bytes,
            mime_type=mime_type,
        )

        outbound = await process_unified_chat_message(unified)

        fallback_user_text = text or f"[{message_type.value} message]"
        message_count = persist_unified_chat_turn(
            unified=unified,
            outbound=outbound,
            fallback_user_text=fallback_user_text,
            user_mime_type=message_type.value.upper(),
        )

        reply_audio_base64: str | None = None
        reply_audio_mime_type: str | None = None
        reply_type = "text"

        if outbound.should_send_voice and outbound.voice_audio:
            reply_audio_base64 = base64.b64encode(outbound.voice_audio).decode("utf-8")
            reply_audio_mime_type = outbound.voice_mime_type or "audio/ogg"
            reply_type = "audio"

        logger.info(
            "Chat multimodal: response payload (chat_id=%s, reply_type=%s, has_audio_base64=%s)",
            unified.chat_id,
            reply_type,
            bool(reply_audio_base64),
        )

        return MultimodalChatResponse(
            chat_id=unified.chat_id,
            response=outbound.text,
            message_count=message_count,
            reply_type=reply_type,
            reply_audio_base64=reply_audio_base64,
            reply_audio_mime_type=reply_audio_mime_type,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing multimodal chat: {str(e)}",
        )


@router.get("/{chat_id}/history")
async def get_chat_history(chat_id: str):
    try:
        with ChatSessionHandler() as handler:
            session = handler.get_session(chat_id)

        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        messages = session.get("messages", [])
        history = []
        for message in messages:
            history.append(
                {
                    "role": message.get("role", "unknown"),
                    "content": message.get("content", ""),
                    "mime_type": message.get("mime_type", "TEXT"),
                    "timestamp": message.get("timestamp"),
                }
            )

        return {"chat_id": chat_id, "message_count": len(history), "history": history}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving chat history: {str(e)}"
        )


@router.delete("/{chat_id}")
async def delete_chat_session(chat_id: str):
    try:
        with ChatSessionHandler() as handler:
            success = handler.delete_session(chat_id)

        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")

        return {"message": f"Chat session {chat_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting chat session: {str(e)}"
        )


@router.get("/sessions")
async def list_chat_sessions():
    try:
        with ChatSessionHandler() as handler:
            sessions = handler.list_sessions()

            session_list = []
            for session in sessions:
                resolved_chat_id = session.get("chat_id")
                session_list.append(
                    {
                        "chat_id": resolved_chat_id,
                        "message_count": handler.get_message_count(resolved_chat_id)
                        if resolved_chat_id
                        else 0,
                        "created_at": session.get("created_at"),
                        "updated_at": session.get("updated_at"),
                    }
                )

        return {"session_count": len(session_list), "sessions": session_list}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing sessions: {str(e)}"
        )


@router.delete("/sessions/all")
async def delete_all_chat_sessions():
    try:
        with ChatSessionHandler() as handler:
            deleted_count = handler.delete_many({})

        return {
            "message": "All chat sessions deleted successfully",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting all chat sessions: {str(e)}",
        )


@router.get("/user/{user_id}/latest")
async def get_latest_user_session(user_id: str):
    try:
        with ChatSessionHandler() as handler:
            session = handler.get_latest_session(user_id)

        if not session:
            raise HTTPException(status_code=404, detail="No chat session found for user")

        return {
            "chat_id": session.get("chat_id"),
            "user_id": session.get("user_id"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "message_count": len(session.get("messages", [])),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving latest user session: {str(e)}",
        )
