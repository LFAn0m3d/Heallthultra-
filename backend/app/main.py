"""FastAPI application entrypoint for HealthUltra."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import audit, models, schemas, security
from .db import SessionLocal, get_db
from .logic import trends, triage


app = FastAPI(title="HealthUltra API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    models.Base.metadata.create_all(bind=models.engine)
    with SessionLocal() as db:
        security.ensure_default_roles(db)
        _ensure_measurements(db)


def _ensure_measurements(db: Session) -> None:
    for definition in schemas.DEFAULT_MEASUREMENTS:
        exists = (
            db.query(models.MeasurementDefinition)
            .filter(models.MeasurementDefinition.code == definition.code)
            .first()
        )
        if not exists:
            db.add(models.MeasurementDefinition(**definition.model_dump()))
    db.flush()


@app.get("/health", response_model=Dict[str, str])
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/meta", response_model=schemas.DocumentationInfo)
def meta() -> schemas.DocumentationInfo:
    return schemas.DocumentationInfo()


@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.UserOut:
    role = (
        db.query(models.Role)
        .filter(models.Role.name == payload.role)
        .one_or_none()
    )
    if role is None:
        raise HTTPException(status_code=400, detail="Invalid role")

    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=payload.email,
        hashed_password=security.hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        dob=payload.dob,
        sex=payload.sex,
        phone=payload.phone,
        chronic_conditions=payload.chronic_conditions,
        habits=payload.habits,
        role=role,
    )
    db.add(user)
    db.flush()

    for med in payload.medications:
        db.add(models.Medication(user=user, **med.model_dump()))
    for allergy in payload.allergies:
        db.add(models.Allergy(user=user, **allergy.model_dump()))
    for history in payload.histories:
        db.add(models.ClinicalHistoryEntry(user=user, **history.model_dump()))

    audit.log_event(db, user=user, action="register", resource_type="user", resource_id=str(user.id))
    return schemas.UserOut.model_validate(user)


@app.post("/auth/login", response_model=schemas.TokenPair)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)) -> schemas.TokenPair:
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = security.create_access_token(subject=user.id, version=user.token_version)
    refresh = security.create_refresh_token(subject=user.id, version=user.token_version)
    audit.log_event(db, user=user, action="login", resource_type="user", resource_id=str(user.id))
    return schemas.TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=schemas.access_token_expiry_seconds(),
    )


@app.post("/auth/refresh", response_model=schemas.TokenPair)
def refresh_token(payload: schemas.RefreshRequest, db: Session = Depends(get_db)) -> schemas.TokenPair:
    data = security.decode_token(payload.refresh_token)
    if data.type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user = db.get(models.User, data.sub)
    if not user or user.token_version != data.version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    access = security.create_access_token(subject=user.id, version=user.token_version)
    refresh = security.create_refresh_token(subject=user.id, version=user.token_version)
    audit.log_event(db, user=user, action="token_refresh", resource_type="user", resource_id=str(user.id))
    return schemas.TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=schemas.access_token_expiry_seconds(),
    )


@app.get("/users/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(security.get_current_user)) -> schemas.UserOut:
    return schemas.UserOut.model_validate(current_user)


@app.post("/measurement-definitions", response_model=schemas.MeasurementDefinitionOut)
def create_measurement_definition(
    payload: schemas.MeasurementDefinitionCreate,
    db: Session = Depends(get_db),
    actor: models.User = Depends(security.require_roles(["clinician", "admin"])),
) -> schemas.MeasurementDefinitionOut:
    if db.query(models.MeasurementDefinition).filter(models.MeasurementDefinition.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Measurement already exists")
    definition = models.MeasurementDefinition(**payload.model_dump())
    db.add(definition)
    db.flush()
    audit.log_event(db, user=actor, action="create_measurement", resource_type="measurement", resource_id=str(definition.id))
    return schemas.MeasurementDefinitionOut.model_validate(definition)


@app.get("/measurement-definitions", response_model=List[schemas.MeasurementDefinitionOut])
def list_measurements(
    db: Session = Depends(get_db),
    _: models.User = Depends(security.require_roles(["clinician", "admin", "patient"])),
) -> List[schemas.MeasurementDefinitionOut]:
    definitions = db.execute(select(models.MeasurementDefinition)).scalars().all()
    return [schemas.MeasurementDefinitionOut.model_validate(d) for d in definitions]


@app.post("/episodes", response_model=schemas.EpisodeOut, status_code=status.HTTP_201_CREATED)
def create_episode(
    payload: schemas.EpisodeCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.require_roles(["clinician", "admin", "patient"])),
) -> schemas.EpisodeOut:
    owner_id = payload.user_id or user.id
    if user.role.name == "patient" and owner_id != user.id:
        raise HTTPException(status_code=403, detail="Patients can only create their own episodes")
    owner = db.get(models.User, owner_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="User not found")

    episode = models.Episode(
        user=owner,
        domain=payload.domain,
        primary_symptom=payload.primary_symptom,
        severity_0_10=payload.severity_0_10,
        notes=payload.notes,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        status=payload.status,
    )
    db.add(episode)
    db.flush()
    audit.log_event(db, user=user, action="create_episode", resource_type="episode", resource_id=str(episode.id))
    return schemas.EpisodeOut.model_validate(episode)


@app.get("/episodes", response_model=List[schemas.EpisodeOut])
def list_episodes(
    db: Session = Depends(get_db),
    user: models.User = Depends(security.require_roles(["clinician", "admin", "patient"])),
    user_id: int | None = None,
) -> List[schemas.EpisodeOut]:
    target_id = user_id or user.id
    if user.role.name == "patient" and target_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    stmt = select(models.Episode).where(models.Episode.user_id == target_id)
    episodes = db.execute(stmt).scalars().all()
    return [schemas.EpisodeOut.model_validate(ep) for ep in episodes]


@app.post("/observations", response_model=schemas.ObservationOut, status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: schemas.ObservationCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.require_roles(["clinician", "admin", "patient"])),
) -> schemas.ObservationOut:
    episode = db.get(models.Episode, payload.episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    if user.role.name == "patient" and episode.user_id != user.id:
        raise HTTPException(status_code=403, detail="Patients can only update their own episodes")

    definition = (
        db.query(models.MeasurementDefinition)
        .filter(models.MeasurementDefinition.code == payload.measurement_code)
        .one_or_none()
    )
    if definition is None:
        raise HTTPException(status_code=404, detail="Measurement definition missing")

    observation = models.Observation(
        episode=episode,
        definition=definition,
        recorded_at=payload.recorded_at,
        value_number=payload.value if isinstance(payload.value, (int, float)) else None,
        value_text=str(payload.value) if not isinstance(payload.value, (int, float)) else None,
        unit=payload.unit or definition.unit,
        source=payload.source,
        context=payload.context,
    )
    db.add(observation)
    db.flush()
    audit.log_event(
        db,
        user=user,
        action="create_observation",
        resource_type="observation",
        resource_id=str(observation.id),
        details={"measurement": payload.measurement_code},
    )
    return schemas.ObservationOut(
        id=observation.id,
        episode_id=observation.episode_id,
        measurement_code=definition.code,
        recorded_at=observation.recorded_at,
        value_number=observation.value_number,
        value_text=observation.value_text,
        unit=observation.unit,
        source=observation.source,
        context=observation.context,
    )


@app.get("/episodes/{episode_id}/observations", response_model=List[schemas.ObservationOut])
def list_observations(
    episode_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.require_roles(["clinician", "admin", "patient"])),
) -> List[schemas.ObservationOut]:
    episode = db.get(models.Episode, episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    if user.role.name == "patient" and episode.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    observations = (
        db.execute(
            select(models.Observation).where(models.Observation.episode_id == episode_id)
        )
        .scalars()
        .all()
    )
    result = []
    for obs in observations:
        result.append(
            schemas.ObservationOut(
                id=obs.id,
                episode_id=obs.episode_id,
                measurement_code=obs.definition.code,
                recorded_at=obs.recorded_at,
                value_number=obs.value_number,
                value_text=obs.value_text,
                unit=obs.unit,
                source=obs.source,
                context=obs.context,
            )
        )
    return result


@app.post("/analyze", response_model=schemas.AnalyzeOut)
async def analyze(payload: schemas.AnalyzeIn, db: Session = Depends(get_db)) -> schemas.AnalyzeOut:
    computation = triage.analyze(payload)
    external_advice = None
    if payload.allow_external_fallback:
        external_advice = (
            await _fallback_to_external(payload)
        ).get("advice")

    if payload.episode_id:
        episode = db.get(models.Episode, payload.episode_id)
        if episode:
            episode.last_triage_level = computation.level
            recommendation = models.Recommendation(
                episode=episode,
                generated_at=datetime.utcnow(),
                triage_level=computation.level,
                score=computation.score,
                rationale=computation.rationale,
                actions={"labels": [a.label for a in computation.actions]},
            )
            db.add(recommendation)
            audit.log_event(
                db,
                user=None,
                action="analyze_episode",
                resource_type="episode",
                resource_id=str(episode.id),
                details={"triage_level": computation.level},
            )

    return schemas.AnalyzeOut(
        triage_level=computation.level,
        score=computation.score,
        actions=computation.actions,
        rationale=computation.rationale,
        hints=computation.hints,
        score_breakdown=computation.score_breakdown,
        external_advice=external_advice,
    )


async def _fallback_to_external(payload: schemas.AnalyzeIn) -> Dict[str, str]:
    from .http_utils import safe_post

    # Example payload transformation for external CDS
    cds_payload = {
        "symptoms": payload.symptoms,
        "vitals": [{"code": v.measurement_code, "value": v.value} for v in payload.vitals],
        "medications": payload.medications,
        "alerts": payload.alerts,
    }
    return await safe_post("https://clinical-decision.example.com/api/triage", json=cds_payload)


@app.post("/trend", response_model=schemas.TrendOut)
def analyze_trend(
    payload: schemas.TrendRequest,
    db: Session = Depends(get_db),
    _actor: models.User = Depends(security.require_roles(["clinician", "admin", "patient"])),
) -> schemas.TrendOut:
    definition = (
        db.query(models.MeasurementDefinition)
        .filter(models.MeasurementDefinition.code == payload.measurement_code)
        .one_or_none()
    )
    if definition is None:
        raise HTTPException(status_code=404, detail="Unknown measurement")

    stmt = select(models.Observation).where(models.Observation.episode_id == payload.episode_id)
    stmt = stmt.where(models.Observation.measurement_definition_id == definition.id)
    if payload.days:
        start = datetime.utcnow() - timedelta(days=payload.days)
        stmt = stmt.where(models.Observation.recorded_at >= start)
    stmt = stmt.order_by(models.Observation.recorded_at.asc())
    observations = db.execute(stmt).scalars().all()

    points = []
    values = []
    for obs in observations:
        if obs.value_number is None:
            continue
        points.append((obs.recorded_at, obs.value_number))
        values.append(obs.value_number)

    slope = trends.linear_slope(points)
    ewma_values = trends.ewma(values)
    trend_label = trends.interpret_trend(payload.measurement_code, slope)
    response_points = [schemas.TrendPoint(date=p[0], value=p[1]) for p in points]

    return schemas.TrendOut(
        metric=payload.measurement_code,
        points=response_points,
        ewma=ewma_values,
        slope_per_day=slope,
        trend=trend_label,
        confidence=trends.confidence_from_points(points),
        unit=definition.unit,
    )


@app.post("/external/wearables", response_model=List[schemas.ObservationOut])
def sync_wearable(
    payload: schemas.ExternalSyncRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.require_roles(["clinician", "admin", "patient"])),
) -> List[schemas.ObservationOut]:
    episode = db.get(models.Episode, payload.episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if user.role.name == "patient" and episode.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    created: List[schemas.ObservationOut] = []
    for measurement in payload.measurements:
        observation_payload = schemas.ObservationCreate(
            episode_id=payload.episode_id,
            measurement_code=measurement.measurement_code,
            recorded_at=measurement.recorded_at,
            value=measurement.value,
            unit=None,
            source=measurement.source,
            context={"device_id": payload.device_id, **measurement.context},
        )
        created.append(create_observation(observation_payload, db=db, user=user))

    audit.log_event(
        db,
        user=user,
        action="sync_wearable",
        resource_type="device",
        resource_id=payload.device_id,
        details={"count": len(created)},
    )
    return created


@app.get("/audit/logs", response_model=List[schemas.AuditLogOut])
def get_audit_logs(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(security.require_roles(["admin"])),
) -> List[schemas.AuditLogOut]:
    logs = db.execute(select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100)).scalars().all()
    return [schemas.AuditLogOut.model_validate(log) for log in logs]


@app.get("/summary/{user_id}", response_model=schemas.HealthSummaryOut)
def summary(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(security.require_roles(["clinician", "admin"])),
) -> schemas.HealthSummaryOut:
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    episodes = db.execute(select(models.Episode).where(models.Episode.user_id == user_id)).scalars().all()
    recommendations = (
        db.execute(select(models.Recommendation).join(models.Episode).where(models.Episode.user_id == user_id))
        .scalars()
        .all()
    )

    return schemas.HealthSummaryOut(
        user=schemas.UserOut.model_validate(user),
        episodes=[schemas.EpisodeOut.model_validate(ep) for ep in episodes],
        recommendations=[
            schemas.RecommendationHistoryOut(
                generated_at=rec.generated_at,
                triage_level=rec.triage_level,
                score=rec.score,
                rationale=rec.rationale,
                actions=rec.actions,
            )
            for rec in recommendations
        ],
    )


@app.get("/analytics/provincial", response_model=schemas.ProvincialAnalyticsOut)
def provincial_analytics(
    db: Session = Depends(get_db),
    _: models.User = Depends(security.require_roles(["clinician", "admin"])),
) -> schemas.ProvincialAnalyticsOut:
    metrics: List[schemas.ProvincialMetric] = []
    definitions = db.execute(select(models.MeasurementDefinition)).scalars().all()
    for definition in definitions:
        stmt = (
            select(models.Observation)
            .where(models.Observation.measurement_definition_id == definition.id)
            .order_by(models.Observation.recorded_at.asc())
        )
        observations = db.execute(stmt).scalars().all()
        numeric_points = [
            schemas.TrendPoint(date=obs.recorded_at, value=obs.value_number)
            for obs in observations
            if obs.value_number is not None
        ]
        if not numeric_points:
            continue
        average = sum(p.value for p in numeric_points) / len(numeric_points)
        latest = numeric_points[-1].value if numeric_points else None
        slope = trends.linear_slope([(p.date, p.value) for p in numeric_points])
        trend_label = trends.interpret_trend(definition.code, slope)
        hint = triage.provincial_hints(numeric_points)
        metrics.append(
            schemas.ProvincialMetric(
                measurement_code=definition.code,
                average=average,
                latest=latest,
                trend=trend_label,
                hint=hint,
            )
        )
    return schemas.ProvincialAnalyticsOut(metrics=metrics)
