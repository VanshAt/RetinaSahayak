import pytest
from backend.tests.test_screenings import create_test_fundus_image_bytes


def _get_worker_auth(client):
    login = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_doctor_auth(client):
    login = client.post("/api/v1/auth/login", json={
        "email": "dr.verma@retinasahayak.in",
        "password": "DoctorDemo123!"
    })
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_admin_auth(client):
    login = client.post("/api/v1/auth/login", json={
        "email": "admin@retinasahayak.in",
        "password": "AdminDemo123!"
    })
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_analyzed_screening(client, image_filename):
    w_headers = _get_worker_auth(client)
    
    # 1. Create Patient
    p_resp = client.post("/api/v1/patients", json={
        "age_group": "51-65",
        "gender": "FEMALE",
        "diabetes_duration_years": 8,
        "known_hypertension": True
    }, headers=w_headers)
    assert p_resp.status_code == 201
    patient_id = p_resp.json()["data"]["id"]

    # 2. Create Screening
    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OD",
        "camera_device_model": "Forus 3nethra Classic"
    }, headers=w_headers)
    assert s_resp.status_code == 201
    screening_id = s_resp.json()["data"]["id"]

    # 3. Upload Image
    img_bytes = create_test_fundus_image_bytes(is_sharp=True)
    client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": (image_filename, img_bytes, "image/jpeg")},
        headers=w_headers
    )

    # 4. Analyze
    analyze_resp = client.post(f"/api/v1/screenings/{screening_id}/analyze", headers=w_headers)
    assert analyze_resp.status_code == 200
    return screening_id, analyze_resp.json()["data"]


# ==========================================
# PART I: TESTS 1 TO 7 - REFERRAL CREATION & PRIORITIES
# ==========================================

def test_referral_creation_and_priority_matrix(client):
    """
    Validates Part I tests:
    1. Referral creation for Grade 2 case (MEDIUM priority).
    2. Referral creation for Grade 3 case (HIGH priority).
    3. Referral creation for Grade 4 case (CRITICAL priority).
    4. Referral creation for uncertain case (REVIEW_REQUIRED priority).
    5. No referral creation for confident Grade 0 case.
    6. No referral creation for confident Grade 1 case.
    7. Priority assignment validation.
    """
    d_headers = _get_doctor_auth(client)

    # 1. Grade 0 Confident -> NO referral
    scr_0, data_0 = _create_analyzed_screening(client, "sample_grade_0_normal.jpg")
    assert data_0["predicted_grade"] == 0
    assert data_0["referable_status"] == "NON_REFERABLE"
    assert data_0["referral_id"] is None

    # 2. Grade 1 Confident -> NO referral
    scr_1, data_1 = _create_analyzed_screening(client, "sample_grade_1_mild.jpg")
    assert data_1["predicted_grade"] == 1
    assert data_1["referable_status"] == "NON_REFERABLE"
    assert data_1["referral_id"] is None

    # 3. Grade 2 Confident -> REFERRAL with MEDIUM priority
    scr_2, data_2 = _create_analyzed_screening(client, "sample_grade_2_moderate.jpg")
    assert data_2["predicted_grade"] == 2
    assert data_2["referable_status"] == "REFERABLE"
    ref_id_2 = data_2["referral_id"]
    assert ref_id_2 is not None

    ref_detail_2 = client.get(f"/api/v1/ophthalmologist/referrals/{ref_id_2}", headers=d_headers).json()["data"]
    assert ref_detail_2["priority"] == "MEDIUM"

    # 4. Grade 3 Confident -> REFERRAL with HIGH priority
    scr_3, data_3 = _create_analyzed_screening(client, "sample_grade_3_severe.jpg")
    assert data_3["predicted_grade"] == 3
    ref_id_3 = data_3["referral_id"]
    ref_detail_3 = client.get(f"/api/v1/ophthalmologist/referrals/{ref_id_3}", headers=d_headers).json()["data"]
    assert ref_detail_3["priority"] == "HIGH"

    # 5. Grade 4 Confident -> REFERRAL with CRITICAL priority
    scr_4, data_4 = _create_analyzed_screening(client, "sample_grade_4_pdr.jpg")
    assert data_4["predicted_grade"] == 4
    ref_id_4 = data_4["referral_id"]
    ref_detail_4 = client.get(f"/api/v1/ophthalmologist/referrals/{ref_id_4}", headers=d_headers).json()["data"]
    assert ref_detail_4["priority"] == "CRITICAL"

    # 6. Uncertain Case -> REFERRAL with REVIEW_REQUIRED priority
    scr_u, data_u = _create_analyzed_screening(client, "sample_uncertain_case.jpg")
    assert data_u["uncertainty_status"] == "UNCERTAIN"
    ref_id_u = data_u["referral_id"]
    ref_detail_u = client.get(f"/api/v1/ophthalmologist/referrals/{ref_id_u}", headers=d_headers).json()["data"]
    assert ref_detail_u["priority"] == "REVIEW_REQUIRED"


# ==========================================
# PART I: TESTS 8 TO 10 - QUEUE RBAC & DETAILS
# ==========================================

def test_ophthalmologist_queue_access_and_rbac(client):
    """
    8. Ophthalmologist can access referral queue.
    9. PHC worker cannot access referral queue (403 Forbidden).
    10. Ophthalmologist can view referral details.
    """
    # Create a referable case
    scr_id, data = _create_analyzed_screening(client, "sample_grade_3_severe.jpg")
    ref_id = data["referral_id"]

    # PHC worker attempt -> 403 Forbidden
    w_headers = _get_worker_auth(client)
    forbidden_resp = client.get("/api/v1/ophthalmologist/referrals", headers=w_headers)
    assert forbidden_resp.status_code == 403

    # Ophthalmologist attempt -> 200 OK
    d_headers = _get_doctor_auth(client)
    queue_resp = client.get("/api/v1/ophthalmologist/referrals", headers=d_headers)
    assert queue_resp.status_code == 200
    queue_data = queue_resp.json()["data"]
    assert "items" in queue_data
    assert any(item["referral_id"] == ref_id for item in queue_data["items"])

    # View case details
    detail_resp = client.get(f"/api/v1/ophthalmologist/referrals/{ref_id}", headers=d_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["referral_id"] == ref_id
    assert detail["screening_id"] == scr_id
    assert "class_probabilities" in detail
    assert "inference_engine" in detail
    assert "clinical_explanation" in detail
    assert "recommended_action" in detail
    assert "audit_trail" in detail


# ==========================================
# PART I: TESTS 11 TO 13 - CLINICAL REVIEW
# ==========================================

def test_clinical_review_submission_and_grade_modification(client):
    """
    11. Ophthalmologist can submit clinical review.
    12. Clinical review updates referral status.
    13. Modified grade requires final_grade and clinical notes.
    """
    d_headers = _get_doctor_auth(client)
    _, data = _create_analyzed_screening(client, "sample_grade_2_moderate.jpg")
    ref_id = data["referral_id"]

    # Missing clinical notes for MODIFY_GRADE -> 400 Bad Request
    invalid_mod = client.post(f"/api/v1/ophthalmologist/referrals/{ref_id}/review", json={
        "clinical_decision": "MODIFY_GRADE",
        "final_grade": 3,
        "clinical_notes": ""  # Missing
    }, headers=d_headers)
    assert invalid_mod.status_code == 400

    # Missing final_grade for MODIFY_GRADE -> 400 Bad Request
    invalid_grade = client.post(f"/api/v1/ophthalmologist/referrals/{ref_id}/review", json={
        "clinical_decision": "MODIFY_GRADE",
        "final_grade": None,
        "clinical_notes": "Clinical notes present but grade omitted"
    }, headers=d_headers)
    assert invalid_grade.status_code == 400

    # Valid clinical review submission: MODIFY_GRADE with valid grade and notes
    valid_review = client.post(f"/api/v1/ophthalmologist/referrals/{ref_id}/review", json={
        "clinical_decision": "MODIFY_GRADE",
        "final_grade": 3,
        "clinical_notes": "Venous beading identified in inferior nasal quadrant; upgraded to Severe NPDR."
    }, headers=d_headers)
    assert valid_review.status_code == 200
    reviewed_case = valid_review.json()["data"]

    # Verify referral status updated
    assert reviewed_case["current_referral_status"] == "REVIEWED"
    assert reviewed_case["existing_clinical_review"] is not None
    assert reviewed_case["existing_clinical_review"]["final_grade"] == 3
    assert reviewed_case["existing_clinical_review"]["clinical_decision"] == "MODIFY_GRADE"

    # Enforce review can only be submitted once by doctor -> 400 Bad Request
    duplicate_review = client.post(f"/api/v1/ophthalmologist/referrals/{ref_id}/review", json={
        "clinical_decision": "AGREE_WITH_AI",
        "clinical_notes": "Duplicate review attempt."
    }, headers=d_headers)
    assert duplicate_review.status_code == 400


# ==========================================
# PART I: TESTS 14 TO 15 - ESCALATION & CLOSURE
# ==========================================

def test_case_escalation_and_case_closure(client):
    """
    14. Case escalation works and records reason & notes.
    15. Case closure works, sets closed_at/closed_by, and preserves record under CLOSED.
    """
    d_headers = _get_doctor_auth(client)

    # Escalation test
    _, data_esc = _create_analyzed_screening(client, "sample_grade_4_pdr.jpg")
    ref_esc_id = data_esc["referral_id"]

    esc_resp = client.post(f"/api/v1/ophthalmologist/referrals/{ref_esc_id}/escalate", json={
        "escalation_reason": "SUSPECTED_PROLIFERATIVE_DR",
        "clinical_notes": "Neovascularization at disc (NVD) identified. Urgent vitreo-retinal evaluation needed.",
        "target_hospital_name": "Regional Institute of Ophthalmology, BHU Varanasi"
    }, headers=d_headers)
    assert esc_resp.status_code == 200
    esc_data = esc_resp.json()["data"]
    assert esc_data["current_referral_status"] == "ESCALATED"

    # Case closure test
    _, data_close = _create_analyzed_screening(client, "sample_grade_2_moderate.jpg")
    ref_close_id = data_close["referral_id"]

    close_resp = client.post(f"/api/v1/ophthalmologist/referrals/{ref_close_id}/close", json={
        "close_reason": "CLINICALLY_RESOLVED",
        "clinical_notes": "Patient examined in-person at mobile eye clinic. Verified stable, no active intervention required."
    }, headers=d_headers)
    assert close_resp.status_code == 200
    close_data = close_resp.json()["data"]
    assert close_data["current_referral_status"] == "CLOSED"

    # Verify closed referral remains visible under CLOSED filter
    queue_closed = client.get("/api/v1/ophthalmologist/referrals?status=CLOSED", headers=d_headers)
    assert queue_closed.status_code == 200
    closed_items = queue_closed.json()["data"]["items"]
    assert any(item["referral_id"] == ref_close_id for item in closed_items)


# ==========================================
# PART I: TESTS 16 TO 19 - ADMIN OVERSIGHT & SECURITY
# ==========================================

def test_admin_oversight_statistics_and_audit_logging(client):
    """
    16. Admin can view referral statistics.
    17. Admin can view audit logs.
    18. Worker isolation prevents cross-facility access.
    19. Unauthorized access attempts are audit-logged.
    """
    a_headers = _get_admin_auth(client)

    # 16. Admin referral stats
    stats_resp = client.get("/api/v1/admin/referral-stats", headers=a_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()["data"]
    assert "total_referrals" in stats
    assert "critical_cases" in stats
    assert "high_priority_cases" in stats
    assert "ai_doctor_agreement_rate" in stats

    # 17. Admin view audit logs
    audit_resp = client.get("/api/v1/admin/audit-logs", headers=a_headers)
    assert audit_resp.status_code == 200
    audit_items = audit_resp.json()["data"]["items"]
    assert len(audit_items) > 0

    # 18. Worker isolation: worker from Chiraigaon cannot access Ramnagar screening/referral
    w2_login = client.post("/api/v1/auth/login", json={
        "email": "worker.chiraigaon@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    w2_headers = {"Authorization": f"Bearer {w2_login.json()['data']['access_token']}"}

    # Create referral in Ramnagar
    _, data_ramnagar = _create_analyzed_screening(client, "sample_grade_3_severe.jpg")
    ref_id = data_ramnagar["referral_id"]

    # Chiraigaon worker attempts to get case detail -> 403 Forbidden
    cross_access = client.get(f"/api/v1/referrals/{ref_id}", headers=w2_headers)
    assert cross_access.status_code == 403

    # 19. Verify UNAUTHORIZED_ACCESS_ATTEMPT was logged in audit trail
    audit_check = client.get("/api/v1/admin/audit-logs?action=UNAUTHORIZED_ACCESS_ATTEMPT", headers=a_headers)
    assert audit_check.status_code == 200
    unauth_logs = audit_check.json()["data"]["items"]
    assert len(unauth_logs) > 0
    assert any(log["resource_id"] == ref_id for log in unauth_logs)
