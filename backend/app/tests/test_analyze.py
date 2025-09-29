"""Tests for the /analyze endpoint."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_moderate_severity_promotes_to_yellow():
    payload = {
        "age": 30,
        "sex": "F",
        "domain": "NCD",
        "primary_symptom": "ปวดหัว",
        "severity_0_10": 6,
        "red_flag_answers": {},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["triage_level"] == "เหลือง"
    assert "นัดพบแพทย์ภายใน 24-48 ชั่วโมง" in data["actions"]
    assert "ระดับอาการปานกลาง" in data["rationale"]
