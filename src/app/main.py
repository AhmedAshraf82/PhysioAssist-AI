# server.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv

from src.app.routers import (
    prediagnose,
    ingestion,
    search,
    injuries,
    whatsapp,
    twilio_whatsapp,
    speech,
)

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
app.include_router(whatsapp.router)
app.include_router(twilio_whatsapp.router)
app.include_router(speech.router)


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


@app.get("/privacy", tags=["Legal"], response_class=HTMLResponse)
async def privacy_policy():
        """Simple privacy policy page for app publishing/review."""
        return """
        <html>
            <head>
                <title>PhysioAssist Privacy Policy</title>
                <meta charset=\"utf-8\" />
            </head>
            <body style=\"font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; line-height: 1.6;\">
                <h1>Privacy Policy</h1>
                <p><strong>Last updated:</strong> 2026-02-24</p>

                <p>
                    This chatbot is operated by V33 Clinic for customer communication and appointment assistance.
                    User messages may be processed by AI systems to provide medical service support.
                </p>

                <h2>What We Collect</h2>
                <ul>
                    <li>Messages you send to the chatbot</li>
                    <li>Basic technical metadata required for service operation</li>
                    <li>Optional voice/audio data when you send voice notes</li>
                </ul>

                <h2>How We Use Data</h2>
                <ul>
                    <li>To answer your inquiries and support physiotherapy-related communication</li>
                    <li>To improve chatbot quality and reliability</li>
                    <li>To maintain service security and prevent abuse</li>
                </ul>

                <h2>Data Sharing</h2>
                <p>
                    We may use trusted service providers (such as messaging and AI platforms)
                    strictly to operate this service.
                </p>

                <h2>Your Rights</h2>
                <p>
                    You may request deletion of your conversation data by contacting us.
                </p>

                <h2>Contact</h2>
                <p>
                    For privacy requests, contact: <a href=\"mailto:privacy@v33clinic.com\">privacy@v33clinic.com</a>
                </p>
            </body>
        </html>
        """


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
