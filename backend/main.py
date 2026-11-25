from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.core.database import Base, engine
from backend.app.db.seed import seed_database
from backend.app.api.v1.router import api_router
from backend.app.services.storage.factory import get_storage_provider
from backend.app.schemas.common import APIResponse, ErrorDetail

# Initialize logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initializes database and seed data on startup."""
    logger.info("Initializing RetinaSahayak Backend Services...")

    # Ensure local storage directories exist
    storage_dir = Path(settings.LOCAL_STORAGE_DIR).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    for folder in ["raw_images", "enhanced", "heatmaps", "overlays", "reports"]:
        (storage_dir / folder).mkdir(parents=True, exist_ok=True)

    # Initialize Database & Seed Demo Data
    try:
        seed_database()
        logger.info("Database initialized and demo data verified.")
    except Exception as e:
        logger.error(f"Failed to seed database during startup: {e}")

    yield

    logger.info("Shutting down RetinaSahayak Backend Services.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Explainable AI for Diabetic Retinopathy Screening in Rural India (SIH26038 | Sponsor: MathWorks)",
    version="1.0.0-SIH2026",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local storage directory for static file access
storage_path = Path(settings.LOCAL_STORAGE_DIR).resolve()
storage_path.mkdir(parents=True, exist_ok=True)
app.mount(f"{settings.API_V1_PREFIX}/storage", StaticFiles(directory=str(storage_path)), name="storage")


# Global Exception Handler for uniform JSON error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred. Please try again.",
                details={"error": str(exc)}
            )
        ).model_dump(mode="json")
    )


# System & Health Check Endpoints
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["System"])
def health_check():
    """Healthcheck endpoint for Cloud Run and local monitoring."""
    return APIResponse(
        success=True,
        data={
            "status": "HEALTHY",
            "environment": settings.ENVIRONMENT,
            "project": settings.PROJECT_NAME,
            "version": "1.0.0-SIH2026"
        }
    )


@app.get(f"{settings.API_V1_PREFIX}/system/provider-status", tags=["System"])
def get_provider_status():
    """Telemetry endpoint reporting active storage, database, and ML providers."""
    storage = get_storage_provider()
    return APIResponse(
        success=True,
        data={
            "app_name": settings.PROJECT_NAME,
            "version": "1.0.0-SIH2026",
            "environment": settings.ENVIRONMENT,
            "storage_provider": storage.get_provider_name(),
            "database_provider": "SQLITE_WAL" if settings.DATABASE_URL.startswith("sqlite") else "CLOUD_SQL_POSTGRES",
            "inference_engine": "MOCK_INFERENCE" if settings.USE_MOCK_INFERENCE else "PYTORCH_EFFICIENTNET",
            "gcp_connected": bool(settings.GCS_BUCKET_NAME and storage.get_provider_name() == "GCS_STORAGE_PROVIDER"),
            "offline_ready": True
        }
    )


# Mount V1 API Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
