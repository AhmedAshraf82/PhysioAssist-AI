# server.py
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

from src.app.routers import prediagnose, ingestion, search, injuries

load_dotenv()

app = FastAPI(
    title="PhysioAssist AI Chatbot",
    description="Chatbot with persistent session memory using Autogen AgentChat",
    version="1.0.0",
)

# Include routers
app.include_router(prediagnose.router)
app.include_router(ingestion.router)
app.include_router(search.router)
app.include_router(injuries.router)


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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
