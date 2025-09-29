# HealthUltra Backend

The HealthUltra backend is a FastAPI service that provides secure clinical data management, triage scoring, recommendation workflows, and audit logging suitable for HIPAA-style traceability.

## Features

- **JWT authentication** with refresh tokens and role-based access control (RBAC) for patients, clinicians, and administrators.
- **Clinical data model** including users, medications, allergies, clinical history, measurement definitions, episodes, observations, recommendations, and audit trails.
- **Triage & recommendation engine** combining vital-sign thresholds, comorbidities, medication/allergy interactions, and optional external CDS fallbacks.
- **External data ingestion** endpoints for wearables or lab integrations with offline-safe HTTP helpers.
- **Comprehensive logging** to track user activity and data access.
- **Automated testing** with unit, integration, and Streamlit UI regression suites.

## Project Structure

```
backend/
  README.md
  requirements.txt
  run.sh
  app/
    main.py              # FastAPI routes and dependency wiring
    db.py                # SQLAlchemy engine/session setup
    models.py            # ORM models for the clinical schema
    schemas.py           # Pydantic request/response models
    security.py          # JWT + password hashing utilities
    audit.py             # Audit logging helper
    http_utils.py        # Offline-safe HTTP helpers
    logic/
      triage.py          # Advanced triage scoring
      trends.py          # Trend analytics helpers
    tests/
      conftest.py        # Test DB fixture
      test_endpoints.py  # Integration and RBAC tests
```

## Getting Started

### 1. Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file if you want to override defaults:

```
DATABASE_URL=sqlite:///./app.db
HEALTHULTRA_SECRET=change-me
```

### 2. Running the API

```bash
./run.sh
```

This loads environment variables (if present) and launches `uvicorn` with hot reload enabled.

### 3. Docker

An example `docker run` invocation:

```bash
docker build -t healthultra-backend .
docker run -p 8000:8000 -e HEALTHULTRA_SECRET=supersecret healthultra-backend
```

### 4. Key Endpoints

| Method | Path | Description | Roles |
| ------ | ---- | ----------- | ----- |
| `POST` | `/auth/register` | Create a new user with role + optional meds/allergies/history | Public |
| `POST` | `/auth/login` | Issue access & refresh tokens | Public |
| `POST` | `/auth/refresh` | Refresh tokens using long-lived token | Authenticated |
| `GET` | `/users/me` | Profile for current user | Any |
| `POST` | `/episodes` | Create a clinical episode | Patient (self), Clinician, Admin |
| `GET` | `/episodes` | List episodes for current user (or specified patient for clinicians) | Patient/Clinician/Admin |
| `POST` | `/observations` | Record a measurement for an episode | Patient (self), Clinician, Admin |
| `GET` | `/episodes/{id}/observations` | Retrieve detailed observations | Patient (self), Clinician, Admin |
| `POST` | `/trend` | Trend analytics for measurements | Patient/Clinician/Admin |
| `POST` | `/analyze` | Advanced triage & personalized recommendations | Any |
| `POST` | `/external/wearables` | Sync external device measurements | Patient (self), Clinician, Admin |
| `GET` | `/analytics/provincial` | Aggregated provincial metrics | Clinician/Admin |
| `GET` | `/audit/logs` | View latest audit entries | Admin |
| `GET` | `/summary/{user_id}` | Holistic patient summary (clinician view) | Clinician/Admin |

Each authenticated request must include an `Authorization: Bearer <token>` header. Access tokens are valid for 30 minutes; refresh tokens for 7 days by default.

### 5. External CDS Fallback

The triage endpoint can forward anonymized payloads to an external clinical decision support (CDS) service when `allow_external_fallback=true`. External calls rely on the async helpers in `http_utils.py`, gracefully degrading to an offline response if the external API is unreachable.

## Testing

Run both backend and Streamlit regression suites with:

```bash
pytest
```

The test suite covers:

- Authentication & token refresh flows.
- Episode/observation CRUD with RBAC enforcement.
- Triage scoring, wearable sync, provincial analytics, and audit logging.
- Streamlit dashboards via `streamlit.testing.AppTest` to guarantee UI components render and interact with the mocked backend.

## API Documentation

Interactive docs are available once the server is running:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Use the `/meta` endpoint to inspect authentication policies (token TTLs, password policy) programmatically.

## Integrating External Data Sources

External systems can push device data by calling `/external/wearables` with a batch of measurements. For periodic polling or CDS integrations, reuse the offline-safe helpers in `http_utils.py` to avoid blocking when a remote service is unavailable.

## Compliance & Audit

All user actions that mutate or access sensitive resources record an entry in `audit_logs`. Administrators can retrieve the most recent 100 entries via `/audit/logs` to support compliance reviews.
