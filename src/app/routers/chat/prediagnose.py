import os
import uuid
from fastapi import APIRouter, HTTPException

from src.app.agents.prediagnosis_agent import PrediagnosisAgent
from src.app.models.chat_models import ChatMessage, ChatResponse
from src.app.services.file_memory.file_memory import FileMemory
from src.app.core.config import settings

# Create router for prediagnose endpoints
router = APIRouter(prefix="/prediagnose", tags=["Prediagnose"])

# Ensure user chats directory exists
os.makedirs(settings.USER_CHATS_DIR, exist_ok=True)


@router.post("", response_model=ChatResponse)
async def prediagnose_chat_endpoint(msg: ChatMessage):
    """
    Prediagnose chat endpoint that:
    1. Creates or loads a chat session
    2. Restores chat history from file
    3. Processes the message with Autogen agent
    4. Saves response back to file
    5. Returns the AI response with chat_id
    """
    try:
        # Create a new unique chat id if none provided
        chat_id = msg.chat_id or str(uuid.uuid4())

        # Path for this chat's memory file
        memory_file = os.path.join(settings.USER_CHATS_DIR, f"{chat_id}.json")

        # Initialize file memory for the session
        file_memory = FileMemory(memory_file)

        # Append the incoming message to memory
        await file_memory.add(msg.message, "user")

        # Create the prediagnosis agent
        prediagnosis_agent = PrediagnosisAgent.create_prediagnose_agent(
            name="PhysioAssist"
        )

        # Build context from memory for the agent
        all_messages = file_memory.get_all_messages()
        context_messages = []

        for mem in all_messages[:-1]:  # Exclude the current message
            role = mem.metadata.get("role", "user")
            if role == "user":
                context_messages.append(f"User: {mem.content}")
            elif role == "assistant":
                context_messages.append(f"Assistant: {mem.content}")

        # Combine context with current message
        if context_messages:
            full_prompt = (
                "Previous conversation:\n"
                + "\n".join(context_messages)
                + f"\n\nUser: {msg.message}"
            )
        else:
            full_prompt = msg.message

        # Run the agent with the task
        task_result = await prediagnosis_agent.run(task=full_prompt)

        # Extract response
        ai_response = task_result.messages[-1].content

        # Save the response to the memory file
        await file_memory.add(ai_response, "assistant")

        # Close memory to ensure everything is saved
        await file_memory.close()

        # Get total message count
        message_count = len(file_memory.get_all_messages())

        return ChatResponse(
            chat_id=chat_id, response=ai_response, message_count=message_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.get("/{chat_id}/history")
async def get_prediagnose_history(chat_id: str):
    """
    Retrieve the full prediagnose chat history for a given chat_id.
    """
    memory_file = os.path.join(settings.USER_CHATS_DIR, f"{chat_id}.json")

    if not os.path.exists(memory_file):
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        file_memory = FileMemory(memory_file)
        all_messages = file_memory.get_all_messages()

        history = []
        for mem in all_messages:
            history.append(
                {
                    "role": mem.metadata.get("role", "unknown"),
                    "content": mem.content,
                    "mime_type": mem.mime_type.name,
                }
            )

        return {"chat_id": chat_id, "message_count": len(history), "history": history}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving chat history: {str(e)}"
        )


@router.delete("/{chat_id}")
async def delete_prediagnose_session(chat_id: str):
    """
    Delete a prediagnose chat session and its history file.
    """
    memory_file = os.path.join(settings.USER_CHATS_DIR, f"{chat_id}.json")

    if not os.path.exists(memory_file):
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        os.remove(memory_file)
        return {"message": f"Chat session {chat_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting chat session: {str(e)}"
        )


@router.get("/sessions")
async def list_prediagnose_sessions():
    """
    List all active prediagnose chat sessions.
    """
    try:
        sessions = []
        for filename in os.listdir(settings.USER_CHATS_DIR):
            if filename.endswith(".json"):
                chat_id = filename[:-5]  # Remove .json extension
                memory_file = os.path.join(settings.USER_CHATS_DIR, filename)
                file_memory = FileMemory(memory_file)
                message_count = len(file_memory.get_all_messages())
                sessions.append({"chat_id": chat_id, "message_count": message_count})

        return {"session_count": len(sessions), "sessions": sessions}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing sessions: {str(e)}"
        )
