import uuid
from fastapi import APIRouter, HTTPException

from src.app.agents.prediagnosis_agent import PrediagnosisAgent
from src.app.models.chat_models import ChatMessage, ChatResponse
from src.app.services.db_handler.chat_session_handler import ChatSessionHandler
from src.app.core.config import settings

# Create router for prediagnose endpoints
router = APIRouter(prefix="/prediagnose", tags=["Prediagnose"])


async def process_prediagnose_message(
    chat_id: str | None,
    message: str,
    user_id: str | None = None,
) -> ChatResponse:
    """
    Shared prediagnosis processing logic.

    This function is used by both REST and WhatsApp webhook flows.
    """
    # Create a new unique chat id if none provided
    resolved_chat_id = chat_id or str(uuid.uuid4())

    # Initialize chat session handler
    with ChatSessionHandler() as handler:
        # Add the incoming message to MongoDB
        handler.add_message(resolved_chat_id, message, "user", user_id=user_id)

        # Create the prediagnosis agent
        prediagnosis_agent = PrediagnosisAgent.create_prediagnose_agent(
            name="PhysioAssist"
        )

        # Build context from chat history
        all_messages = handler.get_messages(resolved_chat_id)
        context_messages = []

        for prior_message in all_messages[:-1]:  # Exclude the current message
            role = prior_message.get("role", "user")
            content = prior_message.get("content", "")
            if role == "user":
                context_messages.append(f"User: {content}")
            elif role == "assistant":
                context_messages.append(f"Assistant: {content}")

        # Combine context with current message
        if context_messages:
            full_prompt = (
                "Previous conversation:\n"
                + "\n".join(context_messages)
                + f"\n\nUser: {message}"
            )
        else:
            full_prompt = message

        # Run the agent with the task
        task_result = await prediagnosis_agent.run(task=full_prompt)

        # Extract response
        ai_response = task_result.messages[-1].content

        # Save the response to MongoDB
        handler.add_message(resolved_chat_id, ai_response, "assistant", user_id=user_id)

        # Get total message count
        message_count = handler.get_message_count(resolved_chat_id)

    return ChatResponse(
        chat_id=resolved_chat_id, response=ai_response, message_count=message_count
    )


@router.post("", response_model=ChatResponse)
async def prediagnose_chat_endpoint(msg: ChatMessage):
    """
    Prediagnose chat endpoint that:
    1. Creates or loads a chat session from MongoDB
    2. Restores chat history from MongoDB
    3. Processes the message with Autogen agent
    4. Saves response back to MongoDB
    5. Returns the AI response with chat_id
    """
    try:
        return await process_prediagnose_message(msg.chat_id, msg.message, msg.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.get("/{chat_id}/history")
async def get_prediagnose_history(chat_id: str):
    """
    Retrieve the full prediagnose chat history for a given chat_id from MongoDB.
    """
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
                    "timestamp": message.get("timestamp")
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
async def delete_prediagnose_session(chat_id: str):
    """
    Delete a prediagnose chat session and all its messages from MongoDB.
    """
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
async def list_prediagnose_sessions():
    """
    List all active prediagnose chat sessions from MongoDB.
    """
    try:
        with ChatSessionHandler() as handler:
            sessions = handler.list_sessions()

            # Format response while handler is still open
            session_list = []
            for session in sessions:
                chat_id = session.get("chat_id")
                session_list.append(
                    {
                        "chat_id": chat_id,
                        "message_count": handler.get_message_count(chat_id)
                        if chat_id
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
async def delete_all_prediagnose_sessions():
    """
    Delete all prediagnose chat sessions.
    """
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
    """
    Retrieve the most recent chat session for a user.
    """
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
