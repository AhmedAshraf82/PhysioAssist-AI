# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from src.app.routers import prediagnose, ingestion, search, injuries
from src.app.core.config import settings

load_dotenv()

app = FastAPI(
    title="PhysioAssist AI Chatbot",
    description="Chatbot with persistent session memory using Autogen AgentChat",
    version="1.0.0",
)

allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
