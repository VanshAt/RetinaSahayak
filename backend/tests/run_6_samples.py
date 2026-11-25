import os
import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
samples_dir = os.path.join(os.path.dirname(__file__), "samples")

# 1. Login
login = client.post("/api/v1/auth/login", json={
    "email": "worker.ramnagar@retinasahayak.in",
    "password": "WorkerDemo123!"
})
token = login.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

test_cases = [
    ("sample_1_good_quality.jpg", "1. Good Quality Image"),
    ("sample_2_blurry.jpg", "2. Blurry Image (REJECT)"),
    ("sample_3_dark_underexposed.jpg", "3. Dark / Underexposed Image (REJECT)"),
    ("sample_4_low_contrast.jpg", "4. Low-Contrast Image (BORDERLINE)"),
    ("sample_5_borderline.jpg", "5. Borderline Image Requiring Enhancement"),
    ("sample_6_uncertain_case.jpg", "6. Uncertain Prediction Case (<0.65 Confidence)"),
]

print("=" * 80)
print("TESTING 6 SAMPLE FUNDUS IMAGES ON RETINASAHAYAK PIPELINE")
print("=" * 80)

for filename, description in test_cases:
    file_path = os.path.join(samples_dir, filename)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # Create patient
    p = client.post("/api/v1/patients", json={
        "age_group": "51-65",
        "gender": "MALE",
        "diabetes_duration_years": 8
    }, headers=headers).json()["data"]

    # Create screening
    s = client.post("/api/v1/screenings", json={
        "patient_id": p["id"],
        "eye_side": "OD"
    }, headers=headers).json()["data"]

    # Upload
    upload_res = client.post(
        f"/api/v1/screenings/{s['id']}/upload-fundus",
        files={"file": (filename, file_bytes, "image/jpeg")},
        headers=headers
    )
    up_data = upload_res.json()["data"]
    iqa = up_data["iqa_result"]

    print(f"\n>>> CASE: {description}")
    print(f"File: {filename}")
    print(f"IQA Status: {iqa['iqa_status']} | Acceptable: {iqa['is_acceptable']}")
    print(f"IQA Issues: {iqa['issues']}")
    print(f"Recapture Guidance: {iqa['actionable_feedback']}")
    print(f"Enhanced Image URL: {up_data['enhanced_image_url']}")

    if iqa["iqa_status"] == "REJECT":
        # Verify analyze endpoint rejection
        analyze_res = client.post(f"/api/v1/screenings/{s['id']}/analyze", headers=headers)
        print(f"Analyze Endpoint Behavior: HTTP {analyze_res.status_code} ({analyze_res.json()['detail']})")
    else:
        # Run analyze
        analyze_res = client.post(f"/api/v1/screenings/{s['id']}/analyze", headers=headers)
        ana_data = analyze_res.json()["data"]
        print(f"Predicted Grade: {ana_data['predicted_grade']} ({ana_data['grade_name']})")
        print(f"Confidence: {ana_data['confidence']} | Uncertainty Status: {ana_data['uncertainty_status']}")
        print(f"Referable Status: {ana_data['referable_status']} | Triage Urgency: {ana_data['triage_urgency']}")
        print(f"Class Probabilities: {ana_data['class_probabilities']}")
        print(f"Inference Engine: {ana_data['inference_engine']}")
