# HealthUltra Streamlit Dashboard

The Streamlit dashboard provides a secure, real-time view of patient episodes, measurements, AI-driven recommendations, and provincial analytics for clinical teams.

## Capabilities

- JWT-based sign-in consuming the FastAPI backend.
- Real-time vitals and trends with auto-refresh via `streamlit-autorefresh`.
- Episode-level AI consult forms that call the triage engine for personalized guidance.
- Provincial analytics page showing aggregated trends across the population (clinician/admin only).
- Smart consult page allowing clinicians to combine comorbidities, medications, and allergies when requesting recommendations.

## Running the Dashboard

```bash
cd HP+
streamlit run app.py
```

Set the backend URL if it is not running on `http://localhost:8000`:

```bash
export HEALTHULTRA_API="https://your-backend.example.com"
```

The application will prompt for email/password credentials. Once authenticated the access token is reused for API calls, and refresh tokens are exchanged automatically when needed.

## Tests

Streamlit components are validated via `pytest` using `streamlit.testing.AppTest`. The tests stub backend calls to ensure the layout renders correctly and access-control guards behave as expected.
