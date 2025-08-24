from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiohttp
import re
import os
from urllib.parse import quote_plus
import logging
import time
from contextlib import asynccontextmanager

# Import routers
from app.api.routes.images import router as images_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.pdf import router as pdf_router
from app.api.routes.generation import router as gen_router
from app.api.routes.search import router as search_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
class Settings:
    def __init__(self):
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY", "")

def get_settings():
    return Settings()
# Lifespan events for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    """
    # Startup
    logger.info("Starting up Image Understanding MVP...")
    
    # You can add model preloading here if needed
    # from app.services.analysis_service import ensure_models
    # ensure_models()  # Uncomment to preload models at startup
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Image Understanding MVP...")
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Image Understanding MVP",
    description="A comprehensive image analysis API with search, OCR, PDF processing, AI generation, and visual question answering capabilities",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Security middleware - restrict hosts in production
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Change to specific domains in production
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Vue dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        # Add your frontend domains here
        "*"  # Remove this in production!
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time to response headers for monitoring.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 5.0:  # Log requests taking more than 5 seconds
        logger.warning(f"Slow request: {request.method} {request.url} took {process_time:.2f}s")
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "path": str(request.url)
        }
    )

# Include routers
app.include_router(images_router)
app.include_router(analysis_router)
app.include_router(pdf_router)
app.include_router(gen_router)
app.include_router(search_router)

# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing basic API information.
    """
    return {
        "ok": True,
        "name": "Image Understanding MVP",
        "version": "0.2.0",
        "description": "API for image search, OCR, PDF processing, AI generation, and visual question answering",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health"
        },
        "services": {
            "image_search": "/api/search",
            "ocr": "/api/ocr", 
            "vqa": "/api/vqa",
            "caption": "/api/caption",
            "pdf_ocr": "/api/ocr-pdf",
            "ai_generation": "/api/generate"
        }
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Comprehensive health check endpoint.
    """
    try:
        # You can add actual health checks here
        # For example, check database connections, model loading, etc.
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "0.2.0",
            "services": {
                "api": "operational",
                "image_search": "operational", 
                "ocr": "operational",
                "vqa": "operational",
                "pdf_processing": "operational",
                "ai_generation": "operational"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

# Development server info
@app.get("/dev-info", tags=["Development"], include_in_schema=False)
async def dev_info():
    """
    Development information endpoint (hidden from docs).
    """
    import sys
    import platform
    
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "fastapi_version": "Check requirements.txt",
        "run_command": "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
        "docs_url": "http://localhost:8000/docs"
    }

# Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Or for production: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker