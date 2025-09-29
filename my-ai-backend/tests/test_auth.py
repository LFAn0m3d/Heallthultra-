"""Auth endpoint tests."""
from .utils import SimpleASGITestClient as TestClient


def test_register_and_login(client: TestClient, user_payload):
    response = client.post("/auth/register", json=user_payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == user_payload["email"]

    login_resp = client.post(
        "/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]}
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    refresh_resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_resp.status_code == 200
    refreshed = refresh_resp.json()
    assert refreshed["access_token"] != tokens["access_token"]
