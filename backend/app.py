"""TripMate AI - FastAPI Application Entry Point."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("tripmate")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting TripMate AI Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Server: {settings.backend_host}:{settings.backend_port}")
    yield
    # Shutdown
    logger.info("Shutting down TripMate AI Backend...")


# Create FastAPI app
app = FastAPI(
    title="TripMate AI",
    description="LangGraph-based AI Travel Planner API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================
# Health Check
# ===========================
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
    }


# ===========================
# API Routes (TODO: Phase 1)
# ===========================
# from src.api.chat import router as chat_router
# app.include_router(chat_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.is_development,
    )
