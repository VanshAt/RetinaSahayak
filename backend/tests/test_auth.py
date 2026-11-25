def test_login_success(client):
    """Verify demo worker can authenticate and receive JWT tokens."""
    payload = {
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WorkerDemo123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["role"] == "PHC_WORKER"
    assert data["data"]["user"]["email"] == "worker.ramnagar@retinasahayak.in"


def test_login_invalid_credentials(client):
    """Verify invalid password returns 401."""
    payload = {
        "email": "worker.ramnagar@retinasahayak.in",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_get_current_user_profile(client):
    """Verify /auth/me returns valid user profile when Bearer token is provided."""
    # First login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "dr.verma@retinasahayak.in",
        "password": "DoctorDemo123!"
    })
    token = login_resp.json()["data"]["access_token"]

    # Call /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_data = me_resp.json()["data"]
    assert user_data["role"] == "OPHTHALMOLOGIST"
    assert user_data["email"] == "dr.verma@retinasahayak.in"


def test_token_refresh(client):
    """Verify refresh token endpoint issues new access token."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "admin@retinasahayak.in",
        "password": "AdminDemo123!"
    })
    refresh_token = login_resp.json()["data"]["refresh_token"]

    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()["data"]
