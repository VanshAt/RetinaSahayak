from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Abstract interface for storing and retrieving medical images and reports."""

    @abstractmethod
    def save_file(self, file_bytes: bytes, destination_rel_path: str, content_type: str = "image/jpeg") -> str:
        """Saves file bytes and returns the stored path or URI."""
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> bytes:
        """Retrieves raw file bytes."""
        pass

    @abstractmethod
    def get_url(self, file_path: str) -> str:
        """Returns browser-accessible URL for the asset."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Deletes file from storage."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns provider identifier."""
        pass
