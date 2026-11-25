from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.storage.base import StorageProvider
from backend.app.services.storage.local_provider import LocalStorageProvider


def get_storage_provider() -> StorageProvider:
    """Factory to retrieve active storage provider with automatic local fallback."""
    if settings.STORAGE_PROVIDER.upper() == "GCS" and settings.GCS_BUCKET_NAME:
        try:
            from backend.app.services.storage.gcs_provider import GCSStorageProvider
            return GCSStorageProvider(bucket_name=settings.GCS_BUCKET_NAME)
        except Exception as e:
            logger.warning(f"GCS unavailable ({e}). Automatically using LocalStorageProvider.")
            return LocalStorageProvider()
    return LocalStorageProvider()
