def test_create_anonymized_patient(client):
    """Verify health worker can register an anonymized patient with zero direct PII."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    patient_payload = {
        "age_group": "51-65",
        "gender": "MALE",
        "diabetes_duration_years": 10,
        "known_hypertension": True,
        "phc_location": "Ramnagar PHC"
    }

    response = client.post("/api/v1/patients", json=patient_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert "patient_code" in data
    assert data["patient_code"].startswith("PAT-VNS-")
    assert data["age_group"] == "51-65"
    assert data["gender"] == "MALE"


def test_list_patients(client):
    """Verify paginated listing of patients."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/patients?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "items" in data
    assert data["total"] >= 1


def test_phc_worker_isolation_prevents_cross_health_center_access(client):
    """
    Ensure a PHC worker at Ramnagar cannot access or screen a patient
    belonging to Chiraigaon PHC.
    """
    # 1. Login as Chiraigaon worker
    c_login = client.post("/api/v1/auth/login", json={
        "email": "worker.chiraigaon@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    c_token = c_login.json()["data"]["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}

    # Register patient under Chiraigaon
    p_resp = client.post("/api/v1/patients", json={
        "age_group": "51-65",
        "gender": "FEMALE",
        "diabetes_duration_years": 5,
        "known_hypertension": False
    }, headers=c_headers)
    assert p_resp.status_code == 201
    c_patient_id = p_resp.json()["data"]["id"]

    # Create screening under Chiraigaon
    s_resp = client.post("/api/v1/screenings", json={
        "patient_id": c_patient_id,
        "eye_side": "OD"
    }, headers=c_headers)
    assert s_resp.status_code == 201
    c_screening_id = s_resp.json()["data"]["id"]

    # 2. Login as Ramnagar worker
    r_login = client.post("/api/v1/auth/login", json={
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    })
    r_token = r_login.json()["data"]["access_token"]
    r_headers = {"Authorization": f"Bearer {r_token}"}

    # Ramnagar worker attempts to view Chiraigaon patient -> 403 Forbidden
    patient_get = client.get(f"/api/v1/patients/{c_patient_id}", headers=r_headers)
    assert patient_get.status_code == 403
    assert "another health center" in patient_get.json()["detail"]

    # Ramnagar worker attempts to screen Chiraigaon patient -> 403 Forbidden
    screen_post = client.post("/api/v1/screenings", json={
        "patient_id": c_patient_id,
        "eye_side": "OS"
    }, headers=r_headers)
    assert screen_post.status_code == 403

    # Ramnagar worker attempts to view Chiraigaon screening -> 403 Forbidden
    screen_get = client.get(f"/api/v1/screenings/{c_screening_id}", headers=r_headers)
    assert screen_get.status_code == 403

    # Ramnagar worker attempts to analyze Chiraigaon screening -> 403 Forbidden
    screen_analyze = client.post(f"/api/v1/screenings/{c_screening_id}/analyze", headers=r_headers)
    assert screen_analyze.status_code == 403

