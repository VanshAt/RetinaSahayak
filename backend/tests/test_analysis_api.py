from backend.tests.test_screenings import create_test_fundus_image_bytes


def test_full_analysis_and_explainability_api(client):
    """
    End-to-end integration test:
    Worker logs in -> Creates patient -> Uploads fundus image -> Triggers AI analysis -> Inspects Grad-CAM explainability.
    """
    # 1. Login as PHC worker
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register patient
    p_resp = client.post("/api/v1/patients", json={
        "age_group": "51-65",
        "gender": "MALE",
        "diabetes_duration_years": 14,
        "known_hypertension": True
    }, headers=headers)
    patient_id = p_resp.json()["data"]["id"]

    # 3. Create screening
    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OD",
        "camera_device_model": "Forus 3nethra Classic"
    }, headers=headers)
    screening_id = s_resp.json()["data"]["id"]

    # 4. Upload sharp fundus photo (named with grade_2 cue for testing)
    img_bytes = create_test_fundus_image_bytes(is_sharp=True)
    upload_resp = client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": ("grade_2_moderate_OD.jpg", img_bytes, "image/jpeg")},
        headers=headers
    )
    assert upload_resp.status_code == 200

    # 5. Trigger AI Analysis
    analyze_resp = client.post(f"/api/v1/screenings/{screening_id}/analyze", headers=headers)
    assert analyze_resp.status_code == 200
    data = analyze_resp.json()["data"]

    # Validate ML fields
    assert "predicted_grade" in data
    assert data["predicted_grade"] in [0, 1, 2, 3, 4]
    assert "grade_label" in data
    assert "confidence" in data or "confidence_score" in data
    assert "class_probabilities" in data
    assert len(data["class_probabilities"]) == 5
    assert "is_referable" in data
    assert "referable_status" in data
    assert "is_uncertain" in data
    assert "uncertainty_status" in data
    assert "quality_status" in data
    assert "quality_score" in data
    assert "inference_time" in data
    assert "disclaimer" in data
    assert "dme_risk" in data
    assert "lesion_evidence" in data
    assert "clinical_explanation" in data
    assert "recommended_action" in data

    # Validate Explainability fields
    assert "explainability" in data
    assert "heatmap_url" in data["explainability"]
    assert "overlay_url" in data["explainability"]
    assert data["explainability"]["method"] == "Grad-CAM++"

    # 6. Call Dedicated Explainability Endpoint
    xai_resp = client.get(f"/api/v1/screenings/{screening_id}/explainability", headers=headers)
    assert xai_resp.status_code == 200
    xai_data = xai_resp.json()["data"]
    assert xai_data["screening_id"] == screening_id
    assert "patient_anonymized_id" in xai_data
    assert "original_image_url" in xai_data
    assert "heatmap_url" in xai_data
    assert "overlay_url" in xai_data
    assert "predicted_grade" in xai_data
    assert "grade_label" in xai_data
    assert "confidence" in xai_data
    assert "uncertainty_status" in xai_data
    assert "referable_status" in xai_data
    assert "clinical_explanation" in xai_data
    assert "recommended_action" in xai_data
    assert "inference_engine" in xai_data
    assert "model_version" in xai_data
    assert "inference_time" in xai_data
    assert "disclaimer" in xai_data
    assert "explanation_label" in xai_data
    assert "Simulated explanation" in xai_data["explanation_label"]

