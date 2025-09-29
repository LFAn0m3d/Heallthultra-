"""Recommendation service tests."""
from datetime import datetime

from .utils import SimpleASGITestClient as TestClient


def authenticate(client: TestClient, user_payload):
    client.post("/auth/register", json=user_payload)
    login_resp = client.post(
        "/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]}
    )
    return login_resp.json()["access_token"]


def test_generate_recommendation_for_mh(client: TestClient, user_payload):
    token = authenticate(client, user_payload)
    headers = {"Authorization": f"Bearer {token}"}
    episode_payload = {
        "domain": "MH",
        "primary_symptom": "Low mood",
        "severity_0_10": 8,
        "notes": "Persistent sadness",
    }
    episode_resp = client.post("/episodes", json=episode_payload, headers=headers)
    episode_id = episode_resp.json()["id"]

    observation_payload = {
        "date": datetime.utcnow().isoformat(),
        "mh_scales": {"phq9": 22, "gad7": 16},
        "symptom_scores": {"mood": 8},
        "interventions": ["therapy"]
    }
    client.post(f"/episodes/{episode_id}/observations", json=observation_payload, headers=headers)

    rec_resp = client.post(f"/recommendations/{episode_id}/recommend", headers=headers)
    assert rec_resp.status_code == 201, rec_resp.text
    rec_data = rec_resp.json()
    assert rec_data["triage_level"] in {"urgent", "emergency"}
    assert "rationale" in rec_data
