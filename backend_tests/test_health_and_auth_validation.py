def test_health_endpoint_returns_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert "env" in payload


def test_register_requires_json_body(client):
    response = client.post("/auth/register")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Request body must be JSON"


def test_register_rejects_weak_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "pm@example.com",
            "password": "short",
            "full_name": "Project Manager",
        },
    )

    assert response.status_code == 422
    assert "at least 8 characters" in response.get_json()["error"]


def test_register_rejects_invalid_role(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "strong-pass-123",
            "full_name": "Workshop User",
            "system_role": "invalid-role",
        },
    )

    assert response.status_code == 422
    assert "Invalid role" in response.get_json()["error"]


def test_login_requires_email_and_password(client):
    response = client.post("/auth/login", json={"email": "someone@example.com"})

    assert response.status_code == 422
    assert response.get_json()["error"] == "Email and password are required"
