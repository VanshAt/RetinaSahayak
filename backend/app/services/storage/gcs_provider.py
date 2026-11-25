import os
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.storage.base import StorageProvider


class GCSStorageProvider(StorageProvider):
    """Stores files in Google Cloud Storage buckets (Google Cloud Bonus Integration)."""

    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME is not configured.")

        try:
            from google.cloud import storage
            if settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
                self.client = storage.Client.from_service_account_json(settings.GOOGLE_APPLICATION_CREDENTIALS)
            else:
                self.client = storage.Client(project=settings.GCP_PROJECT_ID or None)
            self.bucket = self.client.bucket(self.bucket_name)
        except Exception as e:
            logger.warning(f"Failed to initialize GCS client: {e}. Fallback to local storage recommended.")
            raise

    def save_file(self, file_bytes: bytes, destination_rel_path: str, content_type: str = "image/jpeg") -> str:
        clean_path = destination_rel_path.lstrip("/\\").replace("\\", "/")
        blob = self.bucket.blob(clean_path)
        blob.upload_from_string(file_bytes, content_type=content_type)
        return clean_path

    def get_file(self, file_path: str) -> bytes:
        clean_path = file_path.lstrip("/\\").replace("\\", "/")
        blob = self.bucket.blob(clean_path)
        return blob.download_as_bytes()

    def get_url(self, file_path: str) -> str:
        clean_path = file_path.lstrip("/\\").replace("\\", "/")
        try:
            # Generate signed URL or public GCS URL
            blob = self.bucket.blob(clean_path)
            return blob.public_url or f"https://storage.googleapis.com/{self.bucket_name}/{clean_path}"
        except Exception:
            return f"https://storage.googleapis.com/{self.bucket_name}/{clean_path}"

    def delete_file(self, file_path: str) -> bool:
        clean_path = file_path.lstrip("/\\").replace("\\", "/")
        blob = self.bucket.blob(clean_path)
        if blob.exists():
            blob.delete()
            return True
        return False

    def get_provider_name(self) -> str:
        return "GCS_STORAGE_PROVIDER"
