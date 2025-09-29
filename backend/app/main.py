"""FastAPI application entrypoint."""
from __future__ import annotations

from datetime import date, timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .logic.trends import confidence_from_points, ewma, interpret_trend, linear_slope
from .logic.triage import mock_condition_hints, triage_level_from_inputs
from . import models, schemas


app = FastAPI(title="AI Health Assistant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/observe")
def create_observation(payload: schemas.ObservationIn, db: Session = Depends(get_db)):
    episode = db.get(models.Episode, payload.episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")

    observation_data = payload.model_dump()
    observation = models.Observation(**observation_data)
    db.add(observation)
    db.flush()

    return {
        "id": observation.id,
        "episode_id": observation.episode_id,
        "date": observation.date,
        "data": {k: getattr(observation, k) for k in observation_data if k not in {"episode_id", "date"}},
    }


@app.post("/analyze", response_model=schemas.AnalyzeOut)
def analyze(payload: schemas.AnalyzeIn):
    data = payload.model_dump()
    triage_level, actions, rationale = triage_level_from_inputs(data)
    hints = mock_condition_hints(data)
    return schemas.AnalyzeOut(
        triage_level=triage_level,
        actions=actions,
        rationale=rationale,
        hints=hints,
    )


@app.post("/trend", response_model=schemas.TrendOut)
def analyze_trend(payload: schemas.TrendRequest, db: Session = Depends(get_db)):
    stmt = select(models.Observation).where(models.Observation.episode_id == payload.episode_id)
    if payload.days:
        start_date = date.today() - timedelta(days=payload.days)
        stmt = stmt.where(models.Observation.date >= start_date)

    stmt = stmt.order_by(models.Observation.date.asc())
    observations: List[models.Observation] = db.execute(stmt).scalars().all()

    metric_values = []
    points = []
    for obs in observations:
        value = getattr(obs, payload.metric)
        if value is None:
            continue
        metric_values.append(value)
        points.append((obs.date, value))

    slope = linear_slope(points) if points else 0.0
    trend_label = interpret_trend(payload.metric, slope)
    ewma_values = ewma(metric_values) if metric_values else []

    response_points = [schemas.TrendPoint(date=p[0], value=p[1]) for p in points]
    confidence = confidence_from_points(points)

    return schemas.TrendOut(
        metric=payload.metric,
        points=response_points,
        ewma=ewma_values,
        slope_per_day=slope,
        trend=trend_label,
        confidence=confidence,
    )


@app.on_event("startup")
def ensure_tables_exist():
    # Importing models already creates tables via metadata.create_all
    from . import models  # noqa: F401

    _ = models  # keep reference for linters
