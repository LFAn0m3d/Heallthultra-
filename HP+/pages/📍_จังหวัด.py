"""Provincial analytics page."""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from utils import api as api_utils
from utils import auth as auth_utils


st.title("Provincial intelligence")

if not auth_utils.require_auth():
    st.warning("Please log in from the main dashboard.")
    st.stop()

user = auth_utils.current_user()
if user["role"]["name"] == "patient":
    st.info("Provincial analytics are available to clinicians and administrators only.")
    st.stop()

token = auth_utils._state().access_token  # type: ignore[attr-defined]
response = api_utils.api_get("/analytics/provincial", token=token)
if response.status_code != 200:
    st.error("Unable to load analytics: %s" % response.text)
    st.stop()

payload = response.json()
if not payload["metrics"]:
    st.info("No aggregated data available yet.")
    st.stop()

df = pd.DataFrame(payload["metrics"])

chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(x="measurement_code", y="average", color="trend")
    .properties(title="Average vital signs by measurement")
)
st.altair_chart(chart, use_container_width=True)

with st.expander("Detailed recommendations"):
    for row in payload["metrics"]:
        st.write(f"**{row['measurement_code']}**: {row['hint']} (trend: {row['trend']})")
