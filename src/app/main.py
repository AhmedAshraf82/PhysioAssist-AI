"""
FastAPI application entry point for PhysioAssist-AI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.core.config import settings
from src.app.api.routes import health, predictions

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(predictions.router, prefix=settings.API_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    # TODO: Initialize ML models, database connections, etc.


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    print("Shutting down application")
    # TODO: Cleanup resources


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
