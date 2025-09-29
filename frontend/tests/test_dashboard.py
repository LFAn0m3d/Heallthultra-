from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import pytest

pytest.importorskip("streamlit", reason="streamlit package not available in this environment")
from streamlit.testing.v1 import AppTest


@dataclass
class FakeResponse:
    payload: Dict[str, Any]
    status_code: int = 200

    def json(self) -> Dict[str, Any]:
        return self.payload

    @property
    def text(self) -> str:
        return str(self.payload)


def test_dashboard_renders(monkeypatch):
    now = datetime.utcnow().isoformat()
    app = AppTest.from_file("HP+/app.py")
    monkeypatch.setattr(app.script_module, "st_autorefresh", lambda **_: None)
    api_utils = app.script_module.api_utils
    auth_utils = app.script_module.auth_utils

    def fake_get(path: str, token: str | None = None, params: Dict[str, Any] | None = None) -> FakeResponse:
        if path == "/episodes":
            return FakeResponse([
                {
                    "id": 1,
                    "domain": "NCD",
                    "primary_symptom": "Chest pain",
                    "severity_0_10": 5,
                    "started_at": now,
                    "status": "active",
                    "last_triage_level": "yellow",
                }
            ])
        if path == "/measurement-definitions":
            return FakeResponse(
                [
                    {"code": "bp_sys", "name": "Systolic BP"},
                    {"code": "bp_dia", "name": "Diastolic BP"},
                    {"code": "glucose", "name": "Glucose"},
                    {"code": "hr", "name": "Heart Rate"},
                ]
            )
        return FakeResponse({"metrics": []})

    def fake_post(path: str, payload: Dict[str, Any], token: str | None = None) -> FakeResponse:
        if path == "/trend":
            return FakeResponse({"points": [{"date": now, "value": 150.0}, {"date": now, "value": 160.0}], "trend": "worsening"})
        if path == "/analyze":
            return FakeResponse(
                {
                    "triage_level": "yellow",
                    "score": 45,
                    "actions": [{"label": "Follow up", "urgency": "soon"}],
                    "rationale": "Test rationale",
                    "hints": ["Hint"],
                    "score_breakdown": {"bp_sys": 20},
                }
            )
        return FakeResponse({})

    monkeypatch.setattr(api_utils, "api_get", fake_get)
    monkeypatch.setattr(api_utils, "api_post", fake_post)
    app.session_state["auth"] = auth_utils.AuthState(
        access_token="token",
        refresh_token="token",
        user={"email": "clinician@example.com", "role": {"name": "clinician"}, "first_name": "Dr"},
    )
    app.run()

    assert any("Episode #1" in element.value for element in app.header)


def test_provincial_page_requires_clinician(monkeypatch):
    page = AppTest.from_file("HP+/pages/📍_จังหวัด.py")
    api_utils = page.script_module.api_utils
    auth_utils = page.script_module.auth_utils

    def fake_get(path: str, token: str | None = None, params: Dict[str, Any] | None = None) -> FakeResponse:
        if path == "/analytics/provincial":
            return FakeResponse({"metrics": [{"measurement_code": "bp_sys", "average": 150, "latest": 155, "trend": "worsening", "hint": "Monitor"}]})
        if path == "/episodes":
            return FakeResponse([])
        if path == "/measurement-definitions":
            return FakeResponse([])
        return FakeResponse({})

    monkeypatch.setattr(api_utils, "api_get", fake_get)
    page.session_state["auth"] = auth_utils.AuthState(
        access_token="token",
        refresh_token="token",
        user={"email": "clinician@example.com", "role": {"name": "clinician"}},
    )
    page.run()
    assert "Average vital signs" in page.altair_chart[0].chart.title
