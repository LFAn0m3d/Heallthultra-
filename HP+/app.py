"""Streamlit dashboard for HealthUltra."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import altair as alt
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils import api as api_utils
from utils import auth as auth_utils


st.set_page_config(page_title="HealthUltra", layout="wide")
st.title("HealthUltra – Integrated Care Dashboard")


def _login_view() -> None:
    with st.form("login_form"):
        st.subheader("Secure login")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in")
    if submit:
        if not auth_utils.login(email, password):
            st.error("Invalid credentials or server unreachable.")
        else:
            st.success("Authenticated successfully.")
            st.experimental_rerun()


def _episodes(token: str) -> List[Dict[str, Any]]:
    response = api_utils.api_get("/episodes", token=token)
    if response.status_code != 200:
        st.error("Unable to fetch episodes: %s" % response.text)
        return []
    return response.json()


def _measurements(token: str) -> List[Dict[str, Any]]:
    response = api_utils.api_get("/measurement-definitions", token=token)
    if response.status_code != 200:
        st.error("Unable to fetch measurement metadata")
        return []
    return response.json()


def _render_vitals(token: str, episode: Dict[str, Any], measurements: Dict[str, Dict[str, Any]]) -> None:
    cols = st.columns(3)
    for idx, metric in enumerate(["bp_sys", "bp_dia", "glucose", "hr"]):
        definition = measurements.get(metric)
        if not definition:
            continue
        trend_payload = {"episode_id": episode["id"], "measurement_code": metric, "days": 30}
        trend_response = api_utils.api_post("/trend", trend_payload, token=token)
        if trend_response.status_code != 200 or not trend_response.json()["points"]:
            continue
        body = trend_response.json()
        df = pd.DataFrame(body["points"])
        df["date"] = pd.to_datetime(df["date"])
        chart = (
            alt.Chart(df)
            .mark_line()
            .encode(x="date:T", y="value:Q")
            .properties(height=180, title=f"{definition['name']} ({body['trend']})")
        )
        cols[idx % len(cols)].altair_chart(chart, use_container_width=True)


def _render_recommendation_form(token: str, episode: Dict[str, Any]) -> None:
    st.subheader("AI-guided consult")
    with st.form(f"consult_{episode['id']}"):
        symptom = st.text_input("Primary concern", value=episode.get("primary_symptom", ""))
        severity = st.slider("Severity", min_value=0, max_value=10, value=episode.get("severity_0_10") or 0)
        allow_external = st.checkbox("Allow external CDS fallback", value=True)
        submitted = st.form_submit_button("Analyze")
    if submitted:
        vitals = []
        for code in ["bp_sys", "bp_dia", "glucose", "hr"]:
            latest = api_utils.api_post(
                "/trend",
                {"episode_id": episode["id"], "measurement_code": code, "days": 7},
                token=token,
            ).json()
            if latest.get("points"):
                vitals.append({"measurement_code": code, "value": latest["points"][-1]["value"]})

        payload = {
            "episode_id": episode["id"],
            "symptoms": [symptom],
            "severity_0_10": severity,
            "allow_external_fallback": allow_external,
            "vitals": vitals,
        }
        response = api_utils.api_post("/analyze", payload, token=token)
        if response.status_code != 200:
            st.error("Unable to analyze: %s" % response.text)
        else:
            data = response.json()
            st.write(f"Triage level: :{_color_for_level(data['triage_level'])}[{data['triage_level'].title()}]")
            st.write(data["rationale"])
            st.write("Actions:")
            for action in data["actions"]:
                st.write(f"- ({action['urgency']}) {action['label']}")
            if data.get("external_advice"):
                st.info(f"External CDS: {data['external_advice']}")


def _color_for_level(level: str) -> str:
    return {
        "green": "green",
        "yellow": "orange",
        "orange": "orange",
        "red": "red",
    }.get(level, "blue")


if not auth_utils.require_auth():
    _login_view()
    st.stop()

user = auth_utils.current_user()
if not user:
    _login_view()
    st.stop()

token = auth_utils._state().access_token  # type: ignore[attr-defined]

st_autorefresh(interval=60_000, limit=None, key="health_refresh")

with st.sidebar:
    st.subheader(f"Welcome, {user.get('first_name') or user['email']}")
    st.write(f"Role: {user['role']['name'].title()}")
    if st.button("Logout"):
        auth_utils.logout()
        st.experimental_rerun()

measurements = {m["code"]: m for m in _measurements(token)}
episodes = _episodes(token)

if not episodes:
    st.info("No clinical episodes yet. Create one via the clinician portal.")
else:
    for episode in episodes:
        container = st.container()
        container.header(f"Episode #{episode['id']} – {episode['domain']}")
        col1, col2 = container.columns([2, 1])
        col1.write(f"Primary symptom: {episode['primary_symptom']}")
        col1.write(f"Started: {datetime.fromisoformat(episode['started_at']).strftime('%Y-%m-%d %H:%M')}")
        col2.metric("Severity", episode.get("severity_0_10") or 0)
        if episode.get("last_triage_level"):
            col2.metric("Last triage", episode["last_triage_level"].title())
        _render_vitals(token, episode, measurements)
        _render_recommendation_form(token, episode)
