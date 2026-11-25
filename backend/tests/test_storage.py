import shutil
from pathlib import Path
from backend.app.services.storage.local_provider import LocalStorageProvider
from backend.app.services.storage.factory import get_storage_provider


def test_local_storage_provider_lifecycle():
    """Verify LocalStorageProvider saves, retrieves, and generates URLs."""
    test_dir = Path("./backend/storage/test_tmp").resolve()
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)
    provider = LocalStorageProvider(base_dir=str(test_dir))
    assert provider.get_provider_name() == "LOCAL_STORAGE_PROVIDER"

    test_content = b"fake-retinal-fundus-image-data-12345"
    dest_path = "raw_images/test_patient_OD.jpg"

    saved_path = provider.save_file(test_content, dest_path)
    assert saved_path == "raw_images/test_patient_OD.jpg"

    retrieved_bytes = provider.get_file(saved_path)
    assert retrieved_bytes == test_content

    url = provider.get_url(saved_path)
    assert "/storage/raw_images/test_patient_OD.jpg" in url

    deleted = provider.delete_file(saved_path)
    assert deleted is True


def test_storage_factory_fallback():
    """Verify factory returns LocalStorageProvider when GCS is not enabled."""
    provider = get_storage_provider()
    assert provider is not None
    assert provider.get_provider_name() == "LOCAL_STORAGE_PROVIDER"
