import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Centralised application settings loaded from environment variables / .env file."""

    # Application
    APP_NAME: str = "IdentityX API"
    APP_DESCRIPTION: str = "AI-Based Identity & Document Screening"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./identityx.db"

    # CORS — comma-separated origins or "*"
    CORS_ORIGINS: str = "*"

    # Blockchain (optional — falls back to simulated mode)
    BLOCKCHAIN_RPC_URL: str = ""
    CONTRACT_ADDRESS: str = ""
    PRIVATE_KEY: str = ""

    # OCR
    OCR_GPU: bool = False
    OCR_LANGUAGES: str = "en"

    # Face verification
    FACE_MODEL: str = "VGG-Face"
    FACE_DETECTOR: str = "mtcnn"
    FACE_THRESHOLD_RELAX: float = 0.15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance so .env is read only once."""
    return Settings()
