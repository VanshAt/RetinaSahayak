import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "RetinaSahayak"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "local"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # JWT Authentication
    SECRET_KEY: str = "retinasahayak-sih2026-demo-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./retinasahayak.db"

    # Storage Provider: "LOCAL" or "GCS"
    STORAGE_PROVIDER: str = "LOCAL"
    LOCAL_STORAGE_DIR: str = "./backend/storage"

    # Google Cloud Platform (Optional)
    GCP_PROJECT_ID: str = ""
    GCS_BUCKET_NAME: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # ML & Computer Vision
    USE_MOCK_INFERENCE: bool = True
    MODEL_WEIGHTS_PATH: str = "./models/retinasahayak_efficientnet.pt"
    IQA_SHARPNESS_THRESHOLD: float = 100.0
    IQA_MIN_LUMINANCE: float = 28.0
    IQA_MAX_LUMINANCE: float = 230.0
    UNCERTAINTY_CONFIDENCE_THRESHOLD: float = 0.65

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json
            return json.loads(v)
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
