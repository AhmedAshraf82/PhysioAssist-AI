# server.py
import os
import uuid

from fastapi import FastAPI, HTTPException

from src.app.agents.prediagnosis_agent import PrediagnosisAgent
from src.app.models.chat_models import ChatMessage, ChatResponse
from src.app.services.file_memory.file_memory import FileMemory
import uvicorn
from autogen_core.memory import MemoryContent, MemoryMimeType
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="PhysioAssist AI Chatbot",
    description="Chatbot with persistent session memory using Autogen AgentChat",
    version="1.0.0",
)

# Directory to store chat history files
USER_CHATS_DIR = "user_chats"
os.makedirs(USER_CHATS_DIR, exist_ok=True)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "PhysioAssist AI Chatbot API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chatbot-backend"}


@app.post("/prediagnose", response_model=ChatResponse, tags=["Prediagnose"])
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
        memory_file = os.path.join(USER_CHATS_DIR, f"{chat_id}.json")

        # Initialize file memory for the session
        file_memory = FileMemory(memory_file)

        # Append the incoming message to memory
        await file_memory.add(
            MemoryContent(
                content=msg.message,
                mime_type=MemoryMimeType.TEXT,
                metadata={"role": "user"},
            )
        )

        # Create the Autogen assistant with your model
        # Make sure OPENAI_API_KEY is set in your environment


        prediagnosis_agent = PrediagnosisAgent.create_prediagnose_agent(
            name="PhysioAssist",)

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

        # Save the response to the memory file too
        await file_memory.add(
            MemoryContent(
                content=ai_response,
                mime_type=MemoryMimeType.TEXT,
                metadata={"role": "assistant"},
            )
        )

        # Close memory to ensure everything is saved
        await file_memory.close()

        # Get total message count
        message_count = len(file_memory.get_all_messages())

        return ChatResponse(
            chat_id=chat_id, response=ai_response, message_count=message_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.get("/prediagnose/{chat_id}/history", tags=["Prediagnose"])
async def get_prediagnose_history(chat_id: str):
    """
    Retrieve the full prediagnose chat history for a given chat_id.
    """
    memory_file = os.path.join(USER_CHATS_DIR, f"{chat_id}.json")

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


@app.delete("/prediagnose/{chat_id}", tags=["Prediagnose"])
async def delete_prediagnose_session(chat_id: str):
    """
    Delete a prediagnose chat session and its history file.
    """
    memory_file = os.path.join(USER_CHATS_DIR, f"{chat_id}.json")

    if not os.path.exists(memory_file):
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        os.remove(memory_file)
        return {"message": f"Chat session {chat_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting chat session: {str(e)}"
        )


@app.get("/prediagnose/sessions", tags=["Prediagnose"])
async def list_prediagnose_sessions():
    """
    List all active prediagnose chat sessions.
    """
    try:
        sessions = []
        for filename in os.listdir(USER_CHATS_DIR):
            if filename.endswith(".json"):
                chat_id = filename[:-5]  # Remove .json extension
                memory_file = os.path.join(USER_CHATS_DIR, filename)
                file_memory = FileMemory(memory_file)
                message_count = len(file_memory.get_all_messages())
                sessions.append({"chat_id": chat_id, "message_count": message_count})

        return {"session_count": len(sessions), "sessions": sessions}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing sessions: {str(e)}"
        )


if __name__ == "__main__":
    

    uvicorn.run(app, host="0.0.0.0", port=8000)
