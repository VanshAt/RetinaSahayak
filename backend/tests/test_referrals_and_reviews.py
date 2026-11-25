from backend.tests.test_screenings import create_test_fundus_image_bytes


def _setup_analyzed_screening(client):
    """Helper to set up an analyzed screening ready for referral triage."""
    # Worker login
    w_login = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    w_token = w_login.json()["data"]["access_token"]
    w_headers = {"Authorization": f"Bearer {w_token}"}

    # Create patient
    p_resp = client.post("/api/v1/patients", json={
        "age_group": "55-64",
        "gender": "FEMALE",
        "diabetes_duration_years": 8,
        "known_hypertension": True
    }, headers=w_headers)
    patient_id = p_resp.json()["data"]["id"]

    # Create screening
    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OD",
        "camera_device_model": "Forus 3nethra Classic"
    }, headers=w_headers)
    screening_id = s_resp.json()["data"]["id"]

    # Upload fundus photo
    img_bytes = create_test_fundus_image_bytes(is_sharp=True)
    client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": ("grade_3_severe_OD.jpg", img_bytes, "image/jpeg")},
        headers=w_headers
    )

    # Analyze
    analyze_resp = client.post(f"/api/v1/screenings/{screening_id}/analyze", headers=w_headers)
    assert analyze_resp.status_code == 200

    return screening_id, patient_id


def test_referral_triage_queue_and_details(client):
    screening_id, _ = _setup_analyzed_screening(client)

    # 1. Login as Ophthalmologist
    d_login = client.post("/api/v1/auth/login", json={
        "email": "dr.verma@retinasahayak.in",
        "password": "DoctorDemo123!"
    })
    assert d_login.status_code == 200
    d_token = d_login.json()["data"]["access_token"]
    d_headers = {"Authorization": f"Bearer {d_token}"}

    # 2. Query Doctor Referral Queue
    queue_resp = client.get("/api/v1/referrals", headers=d_headers)
    assert queue_resp.status_code == 200
    queue_data = queue_resp.json()["data"]
    assert "items" in queue_data
    assert queue_data["total"] >= 1

    # Find the newly created referral
    ref_match = next((item for item in queue_data["items"] if item["screening_id"] == screening_id), None)
    assert ref_match is not None
    assert ref_match["status"] in ["PENDING", "IN_REVIEW"]
    assert ref_match["clinical_priority"] in ["EMERGENCY", "URGENT", "ROUTINE", "UNCERTAIN_REVIEW"]
    assert ref_match["original_image_url"] is not None
    assert ref_match["heatmap_url"] is not None

    # 3. Retrieve single referral details
    ref_id = ref_match["id"]
    detail_resp = client.get(f"/api/v1/referrals/{ref_id}", headers=d_headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()["data"]
    assert detail_data["id"] == ref_id
    assert detail_data["screening_id"] == screening_id


def test_ophthalmologist_clinical_review_submission(client):
    screening_id, _ = _setup_analyzed_screening(client)

    # Login as Ophthalmologist
    d_login = client.post("/api/v1/auth/login", json={
        "email": "dr.verma@retinasahayak.in",
        "password": "DoctorDemo123!"
    })
    d_token = d_login.json()["data"]["access_token"]
    d_headers = {"Authorization": f"Bearer {d_token}"}

    # Submit official review
    review_resp = client.post("/api/v1/reviews", json={
        "screening_id": screening_id,
        "decision_type": "AGREE_WITH_AI",
        "confirmed_grade": 2,
        "clinical_status": "REFERRED_TERTIARY",
        "clinical_notes": "Clinical confirmation of multiple microaneurysms and hard exudates in macula vicinity.",
        "doctor_digital_signature": "Dr. Verma MBBS MS Ophthalmology"
    }, headers=d_headers)
    assert review_resp.status_code == 200
    rev_data = review_resp.json()["data"]

    assert rev_data["screening_id"] == screening_id
    assert rev_data["confirmed_grade"] == 2
    assert rev_data["decision_type"] == "AGREE_WITH_AI"
    assert "digital_signature_hash" in rev_data
    assert len(rev_data["digital_signature_hash"]) == 64  # SHA-256 hex string


def test_case_escalation_endpoint(client):
    screening_id, _ = _setup_analyzed_screening(client)

    # Doctor login
    d_login = client.post("/api/v1/auth/login", json={
        "email": "dr.verma@retinasahayak.in",
        "password": "DoctorDemo123!"
    })
    d_token = d_login.json()["data"]["access_token"]
    d_headers = {"Authorization": f"Bearer {d_token}"}

    # Get referral ID
    queue_resp = client.get("/api/v1/referrals", headers=d_headers)
    ref_match = next((item for item in queue_resp.json()["data"]["items"] if item["screening_id"] == screening_id), None)
    assert ref_match is not None
    ref_id = ref_match["id"]

    # Escalate case
    esc_resp = client.post(f"/api/v1/referrals/{ref_id}/escalate", json={
        "target_hospital_name": "Regional Institute of Ophthalmology, BHU Varanasi",
        "escalation_reason": "High-risk PDR signs with vitreous haze"
    }, headers=d_headers)
    assert esc_resp.status_code == 200
    esc_data = esc_resp.json()["data"]
    assert esc_data["status"] == "ESCALATED"
    assert esc_data["clinical_priority"] == "EMERGENCY"
    assert esc_data["target_hospital_name"] == "Regional Institute of Ophthalmology, BHU Varanasi"


def test_admin_audit_logs_inspection_and_rbac(client):
    # 1. Worker tries to view audit logs -> 403 Forbidden
    w_login = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    w_token = w_login.json()["data"]["access_token"]
    w_headers = {"Authorization": f"Bearer {w_token}"}

    unauth_resp = client.get("/api/v1/admin/audit-logs", headers=w_headers)
    assert unauth_resp.status_code == 403

    # 2. Admin logs in -> 200 OK
    a_login = client.post("/api/v1/auth/login", json={
        "email": "admin@retinasahayak.in",
        "password": "AdminDemo123!"
    })
    a_token = a_login.json()["data"]["access_token"]
    a_headers = {"Authorization": f"Bearer {a_token}"}

    audit_resp = client.get("/api/v1/admin/audit-logs", headers=a_headers)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()["data"]
    assert "items" in audit_data
    assert audit_data["total"] >= 1

    # Check required audit fields: user ID, user role, action, resource ID, timestamp, status
    first_item = audit_data["items"][0]
    assert "user_id" in first_item
    assert "user_role" in first_item
    assert "action" in first_item
    assert "resource_id" in first_item
    assert "created_at" in first_item
    assert "status" in first_item
    assert first_item["status"] in ["SUCCESS", "FAILURE"]
    assert "payload_hash" in first_item
    assert len(first_item["payload_hash"]) == 64
