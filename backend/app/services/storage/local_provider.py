import os
from pathlib import Path
from backend.app.core.config import settings
from backend.app.services.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Stores files on the local file system (Default / Offline-Ready)."""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or settings.LOCAL_STORAGE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # Ensure standard folders exist
        for folder in ["raw_images", "enhanced", "heatmaps", "overlays", "reports"]:
            (self.base_dir / folder).mkdir(parents=True, exist_ok=True)

    def save_file(self, file_bytes: bytes, destination_rel_path: str, content_type: str = "image/jpeg") -> str:
        # Standardize path
        clean_rel = destination_rel_path.lstrip("/\\")
        full_path = self.base_dir / clean_rel
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_bytes)
        return clean_rel.replace("\\", "/")

    def get_file(self, file_path: str) -> bytes:
        clean_rel = file_path.lstrip("/\\")
        full_path = self.base_dir / clean_rel
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(full_path, "rb") as f:
            return f.read()

    def get_url(self, file_path: str) -> str:
        clean_rel = file_path.lstrip("/\\").replace("\\", "/")
        return f"{settings.API_V1_PREFIX}/storage/{clean_rel}"

    def delete_file(self, file_path: str) -> bool:
        clean_rel = file_path.lstrip("/\\")
        full_path = self.base_dir / clean_rel
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def get_provider_name(self) -> str:
        return "LOCAL_STORAGE_PROVIDER"
