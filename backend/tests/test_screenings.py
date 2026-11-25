import io
import numpy as np
from PIL import Image


def create_test_fundus_image_bytes(is_sharp: bool = True) -> bytes:
    """Creates synthetic fundus image bytes for testing."""
    if is_sharp:
        # High-frequency textured pattern to pass Laplacian focus threshold
        arr = np.zeros((512, 512, 3), dtype=np.uint8)
        arr[:, :, 0] = 180  # Red
        arr[:, :, 1] = 90   # Green
        arr[:, :, 2] = 40   # Blue
        # Draw some bright high-contrast vessels
        for i in range(50, 450, 10):
            arr[i:i+3, :, 1] = 220
            arr[:, i:i+3, 1] = 220
    else:
        # Flat blurry image with zero variance
        arr = np.ones((512, 512, 3), dtype=np.uint8) * 120

    pil_img = Image.fromarray(arr)
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def test_screening_and_image_upload_pipeline(client):
    """Verify screening initialization and fundus image upload with IQA."""
    # 1. Login as PHC worker
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create patient
    p_resp = client.post("/api/v1/patients", json={
        "age_group": "51-65",
        "gender": "FEMALE",
        "diabetes_duration_years": 8
    }, headers=headers)
    patient_id = p_resp.json()["data"]["id"]

    # 3. Create screening
    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OD",
        "dilation_status": "DILATED"
    }, headers=headers)
    assert s_resp.status_code == 201
    screening_id = s_resp.json()["data"]["id"]

    # 4. Upload sharp fundus photo
    sharp_bytes = create_test_fundus_image_bytes(is_sharp=True)
    upload_resp = client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": ("fundus_od.jpg", sharp_bytes, "image/jpeg")},
        headers=headers
    )
    assert upload_resp.status_code == 200
    up_data = upload_resp.json()["data"]
    assert "original_image_url" in up_data
    assert up_data["iqa_result"]["is_acceptable"] is True
    assert up_data["iqa_result"]["iqa_status"] in ["GOOD", "BORDERLINE"]

    # 5. Fetch screening details
    get_resp = client.get(f"/api/v1/screenings/{screening_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["status"] == "IMAGE_UPLOADED"


def test_upload_blurry_image_triggers_iqa_rejection(client):
    """Verify that uploading a blurry fundus triggers IQA_REJECTED status."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    p_resp = client.post("/api/v1/patients", json={
        "age_group": "36-50",
        "gender": "MALE",
        "diabetes_duration_years": 3
    }, headers=headers)
    patient_id = p_resp.json()["data"]["id"]

    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OS"
    }, headers=headers)
    screening_id = s_resp.json()["data"]["id"]

    blurry_bytes = create_test_fundus_image_bytes(is_sharp=False)
    upload_resp = client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": ("blurry_os.jpg", blurry_bytes, "image/jpeg")},
        headers=headers
    )
    assert upload_resp.status_code == 200
    up_data = upload_resp.json()["data"]
    assert up_data["iqa_result"]["iqa_status"] == "REJECT"
    assert up_data["iqa_result"]["is_acceptable"] is False
    assert "MOTION_BLUR" in up_data["iqa_result"]["issues"]


def test_upload_invalid_file_type_returns_400(client):
    """Ensure invalid file formats (.pdf, .txt, .exe) return HTTP 400."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    p_resp = client.post("/api/v1/patients", json={
        "age_group": "36-50",
        "gender": "FEMALE",
        "diabetes_duration_years": 4
    }, headers=headers)
    patient_id = p_resp.json()["data"]["id"]

    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OD"
    }, headers=headers)
    screening_id = s_resp.json()["data"]["id"]

    # Upload invalid text file
    upload_resp = client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": ("malicious_script.sh", b"echo hello", "text/plain")},
        headers=headers
    )
    assert upload_resp.status_code == 400
    assert "Unsupported file format" in upload_resp.json()["detail"]


def test_upload_file_above_15mb_returns_400(client):
    """Ensure files larger than 15 MB return HTTP 400."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    p_resp = client.post("/api/v1/patients", json={
        "age_group": "36-50",
        "gender": "FEMALE",
        "diabetes_duration_years": 4
    }, headers=headers)
    patient_id = p_resp.json()["data"]["id"]

    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OD"
    }, headers=headers)
    screening_id = s_resp.json()["data"]["id"]

    # Generate oversized dummy bytes (> 15MB)
    large_bytes = b"0" * (15 * 1024 * 1024 + 1024)
    upload_resp = client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": ("huge_photo.jpg", large_bytes, "image/jpeg")},
        headers=headers
    )
    assert upload_resp.status_code == 400
    assert "exceeds 15MB" in upload_resp.json()["detail"]

