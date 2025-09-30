from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend.app import main, models, schemas, security


def _register(db, email: str, role: str = "patient") -> models.User:
    payload = schemas.UserCreate(
        email=email,
        password="Secret123!",
        role=role,
        histories=[
            schemas.ClinicalHistoryIn(
                title="Baseline",
                description="Initial registration",
                recorded_at=datetime.utcnow(),
            )
        ],
    )
    user_out = main.register_user(payload, db)
    return db.get(models.User, user_out.id)


def _login(user: models.User) -> schemas.TokenPair:
    return schemas.TokenPair(
        access_token=security.create_access_token(subject=user.id, version=user.token_version),
        refresh_token=security.create_refresh_token(subject=user.id, version=user.token_version),
        expires_in=schemas.access_token_expiry_seconds(),
    )


def test_authentication_flow(db_session):
    user = _register(db_session, "alice@example.com")
    tokens = _login(user)

    payload = schemas.RefreshRequest(refresh_token=tokens.refresh_token)
    refreshed = main.refresh_token(payload, db_session)
    assert refreshed.access_token


def test_full_clinical_workflow(db_session):
    clinician = _register(db_session, "clinician@example.com", role="clinician")
    patient = _register(db_session, "patient@example.com", role="patient")

    episode_in = schemas.EpisodeCreate(domain="NCD", primary_symptom="Chest pain", severity_0_10=6, user_id=patient.id)
    episode = main.create_episode(episode_in, db_session, user=clinician)

    measurement = schemas.ObservationCreate(
        episode_id=episode.id,
        measurement_code="bp_sys",
        value=150,
        recorded_at=datetime.utcnow(),
        source="clinic",
    )
    observation = main.create_observation(measurement, db_session, user=clinician)
    assert observation.measurement_code == "bp_sys"

    measurement_late = schemas.ObservationCreate(
        episode_id=episode.id,
        measurement_code="bp_sys",
        value=160,
        recorded_at=datetime.utcnow() + timedelta(hours=1),
        source="clinic",
    )
    main.create_observation(measurement_late, db_session, user=clinician)

    trend = main.analyze_trend(
        schemas.TrendRequest(episode_id=episode.id, measurement_code="bp_sys", days=7),
        db_session,
        _actor=clinician,
    )
    assert trend.points

    analyze_payload = schemas.AnalyzeIn(
        episode_id=episode.id,
        symptoms=["chest tightness"],
        severity_0_10=7,
        vitals=[schemas.AnalyzeVital(measurement_code="bp_sys", value=180)],
        comorbidities=["htn"],
    )
    result = asyncio.run(main.analyze(analyze_payload, db_session))
    assert result.triage_level in {"yellow", "orange", "red"}

    wearable_payload = schemas.ExternalSyncRequest(
        device_id="device-123",
        episode_id=episode.id,
        measurements=[
            schemas.ExternalMeasurement(
                measurement_code="hr",
                recorded_at=datetime.utcnow(),
                value=105,
                source="wearable",
            )
        ],
    )
    wearable = main.sync_wearable(wearable_payload, db_session, user=patient)
    assert wearable[0].measurement_code == "hr"

    analytics = main.provincial_analytics(db_session, _=clinician)
    assert analytics.metrics
def test_audit_log_access_control(db_session):
    admin = _register(db_session, "admin@example.com", role="admin")
    audit_entries = main.get_audit_logs(db_session, _admin=admin)
    assert audit_entries[0].action == "register"

    patient = _register(db_session, "user@example.com")
    guard = security.require_roles(["admin"])
    with pytest.raises(HTTPException):
        guard(patient)


def test_patient_cannot_access_other_episode(db_session):
    clinician = _register(db_session, "clinician2@example.com", role="clinician")
    pat1 = _register(db_session, "pat1@example.com")
    pat2 = _register(db_session, "pat2@example.com")

    episode = main.create_episode(
        schemas.EpisodeCreate(domain="NCD", primary_symptom="Dizziness", user_id=pat1.id),
        db_session,
        user=clinician,
    )

    with pytest.raises(HTTPException):
        main.list_observations(episode.id, db_session, user=pat2)
