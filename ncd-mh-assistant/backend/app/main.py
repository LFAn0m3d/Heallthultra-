"""FastAPI application entrypoint for the NCD/MH assistant."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .logic.triage import analyze_case
from .logic.trends import build_trend_points, ewma, interpret_trend, linear_slope
from .models import Episode, Observation
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ObservationCreate,
    ObservationResponse,
    TrendRequest,
    TrendResponse,
)

app = FastAPI(title="NCD & Mental Health Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", response_model=Dict[str, str])
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    return analyze_case(payload)


@app.post("/observe", response_model=ObservationResponse)
def record_observation(
    payload: ObservationCreate, db: Session = Depends(get_db)
) -> ObservationResponse:
    episode = None
    if payload.episode_id is not None:
        episode = db.get(Episode, payload.episode_id)
        if episode is None:
            raise HTTPException(status_code=404, detail="Episode not found")
    elif payload.episode is not None:
        episode_data = payload.episode
        episode = Episode(
            user_id=episode_data.user_id,
            domain=episode_data.domain,
            started_at=episode_data.started_at or datetime.utcnow(),
            primary_symptom=episode_data.primary_symptom,
            severity_0_10=episode_data.severity_0_10,
            notes=episode_data.notes,
        )
        db.add(episode)
        db.commit()
        db.refresh(episode)
    else:
        raise HTTPException(status_code=400, detail="episode_id or episode data is required")

    observation = Observation(
        episode_id=episode.id,
        date=payload.date or datetime.utcnow(),
        bp_sys=payload.bp_sys,
        bp_dia=payload.bp_dia,
        hr=payload.hr,
        weight=payload.weight,
        waist=payload.waist,
        glucose=payload.glucose,
        phq9=payload.phq9,
        gad7=payload.gad7,
        isi=payload.isi,
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)

    values: Dict[str, Any] = {
        "bp_sys": observation.bp_sys,
        "bp_dia": observation.bp_dia,
        "hr": observation.hr,
        "weight": observation.weight,
        "waist": observation.waist,
        "glucose": observation.glucose,
        "phq9": observation.phq9,
        "gad7": observation.gad7,
        "isi": observation.isi,
    }

    return ObservationResponse(
        id=observation.id,
        episode_id=observation.episode_id,
        date=observation.date,
        values=values,
    )


@app.post("/trend", response_model=TrendResponse)
def trend_summary(
    payload: TrendRequest, db: Session = Depends(get_db)
) -> TrendResponse:
    metric_attr = getattr(Observation, payload.metric)
    records = (
        db.query(Observation.date, metric_attr)
        .filter(Observation.episode_id == payload.episode_id)
        .order_by(Observation.date.asc())
        .all()
    )

    points = build_trend_points(records)
    values = [point.value for point in points]
    ewma_value = ewma(values) if values else None
    slope_value = (
        linear_slope([(point.date, point.value) for point in points]) if points else None
    )
    trend_label, confidence = interpret_trend(payload.metric, slope_value, len(points))

    return TrendResponse(
        points=points,
        ewma=ewma_value,
        slope_per_day=slope_value,
        trend=trend_label,
        confidence=confidence,
    )
