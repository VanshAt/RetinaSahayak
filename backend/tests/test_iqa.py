import numpy as np
from backend.app.ml.iqa import evaluate_image_quality
from backend.app.ml.enhancer import enhance_retinal_image


def test_iqa_blurry_image_rejection():
    """Verify that a flat/blurry synthetic image triggers REJECT with MOTION_BLUR."""
    blurry_img = np.ones((512, 512, 3), dtype=np.uint8) * 120
    result = evaluate_image_quality(blurry_img)

    assert result["iqa_status"] == "REJECT"
    assert result["is_acceptable"] is False
    assert "MOTION_BLUR" in result["issues"]
    assert "blurry" in result["actionable_feedback"].lower()


def test_iqa_underexposed_image_rejection():
    """Verify that an extremely dark image triggers REJECT with UNDEREXPOSURE."""
    dark_img = np.zeros((512, 512, 3), dtype=np.uint8)
    dark_img[:50, :50, :] = 10  # Almost pitch black
    result = evaluate_image_quality(dark_img)

    assert result["iqa_status"] == "REJECT"
    assert result["is_acceptable"] is False
    assert "UNDEREXPOSURE" in result["issues"]
    assert "dark" in result["actionable_feedback"].lower()


def test_iqa_low_contrast_detection():
    """Verify that a washed-out low contrast image is identified."""
    # Textured enough to have sharpness but green variance is minimal
    low_contrast_img = np.zeros((512, 512, 3), dtype=np.uint8)
    # Background
    low_contrast_img[:, :] = [90, 80, 70]
    # Small variations that give sharpness variance >= 100 without contrast spread
    for i in range(0, 512, 4):
        low_contrast_img[i:i+2, :, 1] = 95
        low_contrast_img[:, i:i+2, 1] = 95
    result = evaluate_image_quality(low_contrast_img)
    assert result["vessel_contrast_score"] < 0.35
    assert "LOW_CONTRAST" in result["issues"]


def test_borderline_enhancement_output():
    """Verify CLAHE, median denoising, and Ben Graham enhancement runs without errors."""
    synth_img = np.random.randint(40, 160, (512, 512, 3), dtype=np.uint8)
    enhanced = enhance_retinal_image(synth_img)

    assert enhanced.shape == (512, 512, 3)
    assert enhanced.dtype == np.uint8
    assert enhanced is not None


def test_rejection_logic_prevents_grading(client):
    """
    Verify that an image evaluated as REJECT cannot be graded via /analyze
    and returns actionable recapture guidance.
    """
    from backend.tests.test_screenings import create_test_fundus_image_bytes

    # 1. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register patient & screening
    p_resp = client.post("/api/v1/patients", json={
        "age_group": "51-65",
        "gender": "MALE",
        "diabetes_duration_years": 10
    }, headers=headers)
    patient_id = p_resp.json()["data"]["id"]

    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OD"
    }, headers=headers)
    screening_id = s_resp.json()["data"]["id"]

    # 3. Upload rejected blurry photo
    blurry_bytes = create_test_fundus_image_bytes(is_sharp=False)
    up_resp = client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": ("blurry.jpg", blurry_bytes, "image/jpeg")},
        headers=headers
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["data"]["iqa_result"]["iqa_status"] == "REJECT"

    # 4. Attempting to run /analyze must fail with 422 Recapture required
    analyze_resp = client.post(f"/api/v1/screenings/{screening_id}/analyze", headers=headers)
    assert analyze_resp.status_code == 422
    assert "rejected by quality gate" in analyze_resp.json()["detail"].lower()

