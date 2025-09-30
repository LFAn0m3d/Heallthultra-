"""Interactive AI consult page."""
from __future__ import annotations

import streamlit as st

from utils import api as api_utils
from utils import auth as auth_utils


st.title("AI consult studio")

if not auth_utils.require_auth():
    st.warning("Please authenticate on the main dashboard first.")
    st.stop()

user = auth_utils.current_user()
token = auth_utils._state().access_token  # type: ignore[attr-defined]

st.write("สร้างแบบจำลองคำแนะนำเฉพาะบุคคล")

episodes_resp = api_utils.api_get("/episodes", token=token)
if episodes_resp.status_code != 200:
    st.error("Cannot load episodes: %s" % episodes_resp.text)
    st.stop()

episodes = episodes_resp.json()
episode_options = {f"#{ep['id']} – {ep['primary_symptom']}": ep for ep in episodes}
choice = st.selectbox("Episode", options=list(episode_options.keys())) if episode_options else None

if not choice:
    st.info("No episodes available for consult.")
    st.stop()

episode = episode_options[choice]

symptom = st.text_area("Describe current symptoms", value=episode.get("primary_symptom", ""))
severity = st.slider("Symptom severity", 0, 10, episode.get("severity_0_10") or 0)
comorbidities = st.text_input("Known comorbidities", value=user.get("chronic_conditions") or "")
medications = st.text_input("Current medications (comma separated)", value="")
allergies = st.text_input("Allergies", value="")
allow_external = st.checkbox("Enable external CDS", value=True)

if st.button("Generate recommendations"):
    vitals = []
    for code in ["bp_sys", "bp_dia", "glucose", "hr"]:
        trend_resp = api_utils.api_post(
            "/trend",
            {"episode_id": episode["id"], "measurement_code": code, "days": 14},
            token=token,
        )
        if trend_resp.status_code == 200 and trend_resp.json().get("points"):
            vitals.append({"measurement_code": code, "value": trend_resp.json()["points"][-1]["value"]})

    payload = {
        "episode_id": episode["id"],
        "symptoms": [symptom],
        "severity_0_10": severity,
        "comorbidities": [c.strip() for c in comorbidities.split(",") if c.strip()],
        "medications": [m.strip() for m in medications.split(",") if m.strip()],
        "allergies": [a.strip() for a in allergies.split(",") if a.strip()],
        "allow_external_fallback": allow_external,
        "vitals": vitals,
    }

    response = api_utils.api_post("/analyze", payload, token=token)
    if response.status_code != 200:
        st.error("Consult failed: %s" % response.text)
    else:
        result = response.json()
        st.success(f"Triage level: {result['triage_level'].title()} (score {result['score']:.1f})")
        st.write(result["rationale"])
        st.write("### Recommended actions")
        for action in result["actions"]:
            st.write(f"- **{action['urgency'].title()}** – {action['label']}")
        st.write("### Clinical hints")
        for hint in result["hints"]:
            st.write(f"- {hint}")
        if result.get("external_advice"):
            st.info(f"External CDS advice: {result['external_advice']}")
