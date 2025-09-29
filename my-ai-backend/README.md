# HealthAI Assistant API

FastAPI backend that analyzes chronic non-communicable disease (NCD) and mental health (MH) episodes. It stores user records, tracks observations, and produces rule-based recommendations with triage levels and rationale. The project is production-ready with JWT authentication, PostgreSQL persistence, alembic migrations, Docker support, and automated tests.

## Features
- FastAPI with modular routing and OpenAPI documentation.
- PostgreSQL persistence via SQLAlchemy ORM and Alembic migrations.
- JWT-based authentication (access + refresh) with bcrypt password hashing.
- Rule-based recommender service with plug-in hook for external ML endpoints.
- Episode, observation, and recommendation management APIs.
- Rate limiting, structured logging, and CORS for localhost development.
- pytest suite covering auth, episodes, and recommender flows.
- Docker Compose stack with Postgres and Adminer.

## Quickstart

### Prerequisites
- Docker and Docker Compose, or Python 3.11 with virtualenv.

### Environment Variables
Copy `.env.example` to `.env` and update secrets:

```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL`: e.g. `postgresql+psycopg2://postgres:postgres@db:5432/healthai`
- `JWT_SECRET_KEY` / `JWT_REFRESH_SECRET_KEY`: long random strings.
- `RATE_LIMIT_CALLS` & `RATE_LIMIT_PERIOD`: integer calls per period (seconds).
- `MODEL_ENDPOINT`: optional external HTTP service for advanced recommendations.

### Run with Docker
```bash
docker-compose up --build
```
FastAPI runs at `http://localhost:8000`. Swagger docs: `http://localhost:8000/docs`.

### Local Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Database Migrations
```bash
alembic upgrade head
# Create new migration
alembic revision --autogenerate -m "message"
```

### Seed Sample Data
```bash
python scripts/seed.py
```

### Tests
```bash
pytest
```

## API Overview

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Obtain access & refresh tokens |
| POST | `/auth/refresh` | Refresh tokens |
| GET | `/users/me` | Current user profile |
| POST | `/episodes` | Create a new episode |
| GET | `/episodes` | List episodes (supports pagination) |
| GET | `/episodes/{id}` | Episode detail with observations & recommendations |
| POST | `/episodes/{id}/observations` | Append an observation |
| POST | `/recommendations` | Create recommendation (manual payload) |
| POST | `/recommendations/{id}/recommend` | Generate recommendation for episode |
| GET | `/recommendations/{id}` | Retrieve recommendation |

### Sample cURL Requests
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123","name":"User"}'

# Login
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123"}' | jq -r '.access_token')

# Create Episode
curl -X POST http://localhost:8000/episodes \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"domain":"NCD","primary_symptom":"Hypertension","severity_0_10":6}'

# Generate Recommendation
curl -X POST http://localhost:8000/recommendations/{episode_id}/recommend \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json"
```

### Postman Collection
Import `HealthAI.postman_collection.json` for ready-made requests.

## Recommender Logic
- **Mental Health**: PHQ-9 ≥ 20 or GAD-7 ≥ 15 triggers emergency triage; moderate scores escalate to urgent/primary care.
- **NCD**: Hypertensive crisis or very high glucose escalates triage.
- Symptom score trends and recorded interventions influence action messages.
- To integrate a real ML model, set `MODEL_ENDPOINT` to a service returning `{triage_level, rationale, condition_hints, actions}`. The rule-based fallback remains active if the call fails.

## Security & Privacy Notes
- **Never store raw passwords**; only hashed values are persisted (bcrypt).
- This project handles sensitive health information. Operators must comply with regulations such as HIPAA or GDPR when deploying.
- Always run behind HTTPS in production, use secure secret management, and enforce proper access controls. Consider externalized rate limiting (e.g., Redis) and audit logging for compliance.

## Project Structure
```
my-ai-backend/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── services.py
│   ├── deps.py
│   ├── db.py
│   ├── settings.py
│   └── routes/
├── alembic/
│   ├── env.py
│   └── versions/
├── scripts/
│   └── seed.py
├── tests/
└── docker-compose.yml
```

## Additional Notes
- Rate limiting is in-memory; for production use a shared backend such as Redis.
- Logging via the standard library; adjust levels or sinks in `app/main.py`.
- The test suite uses SQLite for speed; ensure parity with PostgreSQL before production.
