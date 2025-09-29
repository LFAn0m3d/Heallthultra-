"""Episode and observation tests."""
from datetime import datetime

from .utils import SimpleASGITestClient as TestClient


def authenticate(client: TestClient, user_payload):
    client.post("/auth/register", json=user_payload)
    login_resp = client.post(
        "/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]}
    )
    tokens = login_resp.json()
    return tokens["access_token"]


def test_create_episode_and_observation(client: TestClient, user_payload):
    token = authenticate(client, user_payload)
    headers = {"Authorization": f"Bearer {token}"}
    episode_payload = {
        "domain": "NCD",
        "primary_symptom": "High blood pressure",
        "severity_0_10": 6,
        "notes": "Headaches and dizziness",
    }
    episode_resp = client.post("/episodes", json=episode_payload, headers=headers)
    assert episode_resp.status_code == 201, episode_resp.text
    episode = episode_resp.json()

    observation_payload = {
        "date": datetime.utcnow().isoformat(),
        "vitals": {"bp_sys": 150, "bp_dia": 95},
        "symptom_scores": {"headache": 7},
    }
    obs_resp = client.post(
        f"/episodes/{episode['id']}/observations", json=observation_payload, headers=headers
    )
    assert obs_resp.status_code == 201, obs_resp.text
    obs_data = obs_resp.json()
    assert obs_data["episode_id"] == episode["id"]

    list_resp = client.get("/episodes", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    detail_resp = client.get(f"/episodes/{episode['id']}", headers=headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert len(detail_data["observations"]) == 1
