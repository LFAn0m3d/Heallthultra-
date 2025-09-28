# NCD & Mental Health Assistant – Backend

FastAPI + SQLite backend that powers the NCD/MH assistant MVP. It exposes endpoints for health checks, triage analysis, observation storage, and longitudinal trend summaries.

## Prerequisites
- Python 3.11+
- (Optional) [`python-dotenv`](https://pypi.org/project/python-dotenv/) support via the provided requirements file

## Setup & Run
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # customise if needed
./run.sh
```

The service listens on `http://0.0.0.0:8000` by default. Interactive docs are available at `http://localhost:8000/docs`.

## Environment Variables
- `DATABASE_URL` – SQLAlchemy-compatible URL (defaults to `sqlite:///./data.db`).

## Testing with curl
```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
        "age": 35,
        "sex": "M",
        "domain": "NCD",
        "primary_symptom": "เวียนหัว",
        "duration_days": 3,
        "bp_sys": 182,
        "bp_dia": 121,
        "glucose": 110,
        "red_flag_answers": {"self_harm": false}
      }'
```

## Project Structure
```
app/
  main.py        # FastAPI application wiring
  db.py          # SQLAlchemy engine/session helpers
  models.py      # ORM models for users, episodes, observations
  schemas.py     # Pydantic v2 schemas for requests/responses
  logic/
    triage.py    # Triage scoring and response generation
    trends.py    # EWMA, slope, and trend interpretation helpers
```
