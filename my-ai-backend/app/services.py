"""Business logic services for authentication and recommendation generation."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import base64
import hashlib
import hmac
import json
import logging
import secrets

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    httpx = None  # type: ignore

from . import models, schemas
from .settings import get_settings

settings = get_settings()

logger = logging.getLogger("healthai")


# Authentication helpers

def hash_password(password: str) -> str:
    """Hash a plain password using PBKDF2."""

    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""

    try:
        salt, stored_hash = hashed_password.split("$", 1)
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return hmac.compare_digest(stored_hash, derived.hex())


def _encode_token(payload: Dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    segments = []
    for segment in (header, payload):
        json_bytes = json.dumps(segment, separators=(",", ":"), default=str).encode("utf-8")
        segments.append(base64.urlsafe_b64encode(json_bytes).rstrip(b"="))
    signing_input = b".".join(segments)
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    segments.append(base64.urlsafe_b64encode(signature).rstrip(b"="))
    return b".".join(segments).decode("utf-8")


def _decode_token(token: str, secret: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid token format") from exc
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = base64.urlsafe_b64encode(
        hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    ).rstrip(b"=")
    if expected_sig.decode("utf-8") != signature_b64.rstrip("="):
        raise ValueError("Signature mismatch")
    padded_payload = payload_b64 + "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded_payload).decode("utf-8"))
    return payload


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"exp": int(expire.timestamp()), "sub": subject, "type": "access", "jti": secrets.token_hex(8)}
    return _encode_token(payload, settings.jwt_secret_key)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes)
    )
    payload = {"exp": int(expire.timestamp()), "sub": subject, "type": "refresh", "jti": secrets.token_hex(8)}
    return _encode_token(payload, settings.jwt_refresh_secret_key)


def decode_token(token: str, *, token_type: str) -> schemas.TokenPayload:
    """Decode a JWT and validate its type."""

    secret = settings.jwt_secret_key if token_type == "access" else settings.jwt_refresh_secret_key
    payload = _decode_token(token, secret)
    if payload.get("type") != token_type:
        raise ValueError("Invalid token type")
    if payload.get("exp") and datetime.utcnow().timestamp() > float(payload["exp"]):
        raise ValueError("Token expired")
    return schemas.TokenPayload(**payload)


# Recommender logic

def _mh_rules(latest_observation: Optional[models.Observation]) -> Dict[str, Any]:
    """Determine MH triage level based on mental health scales."""

    triage = "self-care"
    rationale_parts: List[str] = []
    if not latest_observation:
        rationale_parts.append("No recent observations; defaulting to self-care")
        return {"triage": triage, "rationale": "; ".join(rationale_parts)}

    scales = latest_observation.mh_scales or {}
    phq9 = scales.get("phq9", 0)
    gad7 = scales.get("gad7", 0)
    if phq9 >= 20 or gad7 >= 15:
        triage = "emergency"
        rationale_parts.append("Severe depressive/anxiety symptoms detected (PHQ-9/GAD-7)")
    elif phq9 >= 15 or gad7 >= 13:
        triage = "urgent"
        rationale_parts.append("Moderate to severe symptoms; recommend urgent follow-up")
    elif phq9 >= 10 or gad7 >= 10:
        triage = "primary-care"
        rationale_parts.append("Mild to moderate symptoms; schedule primary care or therapy visit")
    else:
        rationale_parts.append("Scores within mild range; continue self-care strategies")

    return {"triage": triage, "rationale": "; ".join(rationale_parts)}


def _ncd_rules(latest_observation: Optional[models.Observation]) -> Dict[str, Any]:
    """Determine NCD triage level based on vitals."""

    triage = "self-care"
    rationale_parts: List[str] = []
    if not latest_observation:
        rationale_parts.append("No recent vitals; defaulting to self-care")
        return {"triage": triage, "rationale": "; ".join(rationale_parts)}

    vitals = latest_observation.vitals or {}
    bp_sys = vitals.get("bp_sys", 0)
    bp_dia = vitals.get("bp_dia", 0)
    glucose = vitals.get("glucose", 0)
    if bp_sys > 180 or bp_dia > 120:
        triage = "emergency"
        rationale_parts.append("Hypertensive crisis detected")
    elif bp_sys > 160 or bp_dia > 100:
        triage = "urgent"
        rationale_parts.append("Severely elevated blood pressure")
    elif glucose > 300:
        triage = "urgent"
        rationale_parts.append("High glucose level")
    elif bp_sys > 140 or bp_dia > 90 or glucose > 200:
        triage = "primary-care"
        rationale_parts.append("Above target vitals; primary care visit recommended")
    else:
        rationale_parts.append("Vitals within acceptable range")

    return {"triage": triage, "rationale": "; ".join(rationale_parts)}


def _trend_analysis(observations: List[models.Observation]) -> str:
    """Analyze symptom score trend to provide context."""

    if len(observations) < 2:
        return "Trend data insufficient"

    latest = observations[-1].symptom_scores or {}
    previous = observations[-2].symptom_scores or {}
    worsening = sum(latest.values()) > sum(previous.values())
    return "Symptoms worsening" if worsening else "Symptoms stable or improving"


async def _call_external_model(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Optionally call an external ML model service if configured."""

    if not settings.model_endpoint or httpx is None:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:  # type: ignore[attr-defined]
            response = await client.post(str(settings.model_endpoint), json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:  # pragma: no cover - network failures
        logger.warning("External model call failed: %s", exc)
        return None


async def predict_recommendation(
    episode: models.Episode,
    observations: List[models.Observation],
) -> schemas.RecommendationCreate:
    """Generate a recommendation using rule-based heuristics or an external model."""

    observations_sorted = sorted(observations, key=lambda obs: obs.date)
    latest_observation = observations_sorted[-1] if observations_sorted else None

    external_payload = {
        "episode": {
            "id": str(episode.id),
            "domain": episode.domain,
            "severity": episode.severity_0_10,
            "primary_symptom": episode.primary_symptom,
        },
        "observations": [
            {
                "id": str(obs.id),
                "date": obs.date.isoformat(),
                "symptom_scores": obs.symptom_scores,
                "vitals": obs.vitals,
                "mh_scales": obs.mh_scales,
                "interventions": obs.interventions,
            }
            for obs in observations_sorted
        ],
    }

    external_result = await _call_external_model(external_payload)
    if external_result:
        logger.info("Using external model output for recommendation")
        triage = external_result.get("triage_level", "self-care")
        rationale = external_result.get("rationale", "External model response")
        condition_hints = external_result.get("condition_hints", [])
        actions = external_result.get("actions", [])
    else:
        if episode.domain == "MH":
            mh_result = _mh_rules(latest_observation)
            triage = mh_result["triage"]
            rationale = mh_result["rationale"]
            condition_hints = ["Possible depressive or anxiety episode"]
        else:
            ncd_result = _ncd_rules(latest_observation)
            triage = ncd_result["triage"]
            rationale = ncd_result["rationale"]
            condition_hints = ["Chronic condition flare"]

        trend = _trend_analysis(observations_sorted)
        interventions = latest_observation.interventions if latest_observation else []
        actions = [
            trend,
            "Review interventions: " + ", ".join(interventions or ["None recorded"]),
        ]

    recommendation = schemas.RecommendationCreate(
        episode_id=episode.id,
        triage_level=triage,
        condition_hints=condition_hints,
        rationale=rationale,
        actions=actions,
    )

    return recommendation
