from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    Centralized configuration for the app.
    Loads values from environment variables and `.env` file automatically.
    """

    # Model settings
    blip_model: str = "Salesforce/blip-image-captioning-base"
    qa_model: str = "distilbert-base-cased-distilled-squad"

    # CORS origins (raw string from env, e.g., "http://localhost:3000,http://127.0.0.1:5173")
    cors_origins: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS origins string to a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # Server settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # Default allowed origins (development mode)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # API Keys
    UNSPLASH_ACCESS_KEY: str = ""  # Unsplash API Key
    OPENAI_API_KEY: str = ""       # OpenAI API Key

    # File upload settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]

    # Storage settings
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_prefix = ""   # no prefix needed (can read directly from .env)
        env_file = ".env"
        extra = "allow"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings object so it's initialized only once.
    """
    settings = Settings()

    # Ensure upload directory exists
    if not os.path.exists(settings.UPLOAD_DIR):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    return settings


# app/core/exceptions.py
class APIKeyMissingError(Exception):
    pass

class ImageProcessingError(Exception):
    pass

class ExternalAPIError(Exception):
    pass

class OCRProcessingError(Exception):
    pass

class UnsupportedImageFormatError(Exception):
    pass

class ImageTooLargeError(Exception):
    pass