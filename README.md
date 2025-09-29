# HealthUltra Platform

HealthUltra combines a FastAPI backend with a Streamlit dashboard to deliver secure clinical workflows, real-time monitoring, and AI-assisted recommendations for chronic disease management.

## Components

| Directory | Description |
| --------- | ----------- |
| `backend/` | FastAPI service with JWT authentication, RBAC, triage logic, and audit logging. |
| `HP+/` | Streamlit frontend for patients and clinicians with analytics and AI consult tools. |

## Quick Start

1. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```
2. Launch the backend:
   ```bash
   cd backend
   ./run.sh
   ```
3. In another terminal, run the dashboard:
   ```bash
   cd HP+
   streamlit run app.py
   ```

Configure the frontend backend URL via the `HEALTHULTRA_API` environment variable if you are not running on `localhost:8000`.

## Testing

All automated tests can be executed with:

```bash
pytest
```

This runs the backend integration suite as well as the Streamlit regression tests.
