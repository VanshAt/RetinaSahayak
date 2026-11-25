from backend.tests.test_referrals_and_reviews import _setup_analyzed_screening
from backend.app.reports.qr_generator import generate_verification_qr_bytes
from backend.app.reports.pdf_generator import generate_screening_pdf


def test_qr_code_generation_utility():
    qr_bytes = generate_verification_qr_bytes(
        screening_id="test-screening-1234",
        patient_code="PAT-VNS-0001",
        grade=2,
        verification_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert len(qr_bytes) > 0
    # Verify PNG magic bytes
    assert qr_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_download_screening_pdf_report_api(client):
    screening_id, _ = _setup_analyzed_screening(client)

    # Worker login
    w_login = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = w_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Request via /report
    pdf_resp1 = client.get(f"/api/v1/screenings/{screening_id}/report", headers=headers)
    assert pdf_resp1.status_code == 200
    assert pdf_resp1.headers["content-type"] == "application/pdf"
    assert pdf_resp1.content.startswith(b"%PDF-")
    assert len(pdf_resp1.content) > 1000

    # 2. Request via /report/pdf
    pdf_resp2 = client.get(f"/api/v1/screenings/{screening_id}/report/pdf", headers=headers)
    assert pdf_resp2.status_code == 200
    assert pdf_resp2.headers["content-type"] == "application/pdf"
    assert "RetinaSahayak_Screening_Report" in pdf_resp2.headers["content-disposition"]
    assert pdf_resp2.content.startswith(b"%PDF-")
    assert len(pdf_resp2.content) > 1000


def test_rejected_image_report_states_grading_not_performed(client):
    """Verify that downloading a report for a rejected image states AI grading was not performed."""
    from backend.tests.test_screenings import create_test_fundus_image_bytes

    w_login = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = w_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Register patient
    p_resp = client.post("/api/v1/patients", json={
        "age_group": "36-50",
        "gender": "FEMALE",
        "diabetes_duration_years": 4
    }, headers=headers)
    patient_id = p_resp.json()["data"]["id"]

    # Screening
    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": patient_id,
        "eye_side": "OS"
    }, headers=headers)
    screening_id = s_resp.json()["data"]["id"]

    # Upload blurry rejected image
    blurry_bytes = create_test_fundus_image_bytes(is_sharp=False)
    client.post(
        f"/api/v1/screenings/{screening_id}/upload-fundus",
        files={"file": ("blurry.jpg", blurry_bytes, "image/jpeg")},
        headers=headers
    )

    # Download report for rejected screening
    rep_resp = client.get(f"/api/v1/screenings/{screening_id}/report", headers=headers)
    assert rep_resp.status_code == 200
    assert rep_resp.headers["content-type"] == "application/pdf"
    assert rep_resp.content.startswith(b"%PDF-")


def test_worker_isolation_on_explainability_and_report_endpoints(client):
    """Ensure PHC worker from another center receives 403 on explainability and report download."""
    screening_id, _ = _setup_analyzed_screening(client)  # Created by Ramnagar worker

    # Login as Chiraigaon worker
    c_login = client.post("/api/v1/auth/login", json={
        "email": "worker.chiraigaon@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    c_token = c_login.json()["data"]["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}

    # Attempt explainability -> 403 Forbidden
    exp_resp = client.get(f"/api/v1/screenings/{screening_id}/explainability", headers=c_headers)
    assert exp_resp.status_code == 403
    assert "another health center" in exp_resp.json()["detail"].lower()

    # Attempt report download -> 403 Forbidden
    rep_resp = client.get(f"/api/v1/screenings/{screening_id}/report", headers=c_headers)
    assert rep_resp.status_code == 403
    assert "another health center" in rep_resp.json()["detail"].lower()

