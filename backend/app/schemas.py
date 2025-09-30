"""Pydantic schemas for the HealthUltra API."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Literal, Optional, Sequence, Union

from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt, conlist, constr


class TokenPair(BaseModel):
    """JWT access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class TokenPayload(BaseModel):
    sub: int
    exp: datetime
    type: Literal["access", "refresh"]
    version: NonNegativeInt


class RoleOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MedicationIn(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    started_on: Optional[date] = None
    stopped_on: Optional[date] = None


class AllergyIn(BaseModel):
    substance: str
    reaction: Optional[str] = None
    severity: Optional[str] = None


class ClinicalHistoryIn(BaseModel):
    title: str
    description: Optional[str] = None
    recorded_at: datetime


class UserBase(BaseModel):
    email: constr(min_length=3, max_length=255)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    sex: Optional[Literal["M", "F", "O"]] = None
    phone: Optional[str] = None
    chronic_conditions: Optional[str] = None
    habits: Optional[str] = None


class UserCreate(UserBase):
    password: constr(min_length=8)
    role: Literal["patient", "clinician", "admin"] = "patient"
    medications: List[MedicationIn] = Field(default_factory=list)
    allergies: List[AllergyIn] = Field(default_factory=list)
    histories: List[ClinicalHistoryIn] = Field(default_factory=list)


class UserOut(UserBase):
    id: int
    role: RoleOut

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: constr(min_length=3, max_length=255)
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class MeasurementDefinitionCreate(BaseModel):
    code: constr(min_length=1, max_length=64)
    name: str
    unit: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    attributes: Dict[str, Union[str, float, int, bool]] = Field(default_factory=dict)


class MeasurementDefinitionOut(MeasurementDefinitionCreate):
    id: int

    class Config:
        from_attributes = True


class EpisodeCreate(BaseModel):
    domain: Literal["NCD", "MH", "ACUTE"]
    primary_symptom: str
    severity_0_10: Optional[int] = Field(default=None, ge=0, le=10)
    notes: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: Literal["active", "resolved", "archived"] = "active"
    user_id: Optional[int] = Field(default=None, description="If omitted, defaults to caller")


class EpisodeOut(BaseModel):
    id: int
    user_id: int
    domain: str
    primary_symptom: str
    severity_0_10: Optional[int]
    notes: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    last_triage_level: Optional[str]

    class Config:
        from_attributes = True


class ObservationCreate(BaseModel):
    episode_id: PositiveInt
    measurement_code: str
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    value: Union[float, str]
    unit: Optional[str] = None
    source: Optional[str] = None
    context: Dict[str, Union[str, float, int, bool]] = Field(default_factory=dict)


class ObservationOut(BaseModel):
    id: int
    episode_id: int
    measurement_code: str
    recorded_at: datetime
    value_number: Optional[float]
    value_text: Optional[str]
    unit: Optional[str]
    source: Optional[str]
    context: Dict[str, Union[str, float, int, bool]]

    class Config:
        from_attributes = True


class AnalyzeVital(BaseModel):
    measurement_code: str
    value: float


class AnalyzeIn(BaseModel):
    user_id: Optional[int] = None
    episode_id: Optional[int] = None
    vitals: List[AnalyzeVital] = Field(default_factory=list)
    comorbidities: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    severity_0_10: Optional[int] = Field(default=None, ge=0, le=10)
    alerts: List[str] = Field(default_factory=list)
    allow_external_fallback: bool = False


class RecommendationAction(BaseModel):
    label: str
    urgency: Literal["routine", "soon", "urgent", "emergent"]


class AnalyzeOut(BaseModel):
    triage_level: Literal["green", "yellow", "orange", "red"]
    score: float
    actions: List[RecommendationAction]
    rationale: str
    hints: List[str]
    score_breakdown: Dict[str, float]
    external_advice: Optional[str] = None


class TrendPoint(BaseModel):
    date: datetime
    value: float


class TrendRequest(BaseModel):
    episode_id: PositiveInt
    measurement_code: str
    days: Optional[PositiveInt] = Field(default=None, description="Optional time window")


class TrendOut(BaseModel):
    metric: str
    points: List[TrendPoint]
    ewma: List[float]
    slope_per_day: float
    trend: Literal["improving", "stable", "worsening"]
    confidence: Literal["low", "medium", "high"]
    unit: Optional[str] = None


class ExternalMeasurement(BaseModel):
    measurement_code: str
    recorded_at: datetime
    value: Union[float, str]
    source: str
    context: Dict[str, Union[str, float, int, bool]] = Field(default_factory=dict)


class ExternalSyncRequest(BaseModel):
    device_id: str
    episode_id: PositiveInt
    measurements: conlist(ExternalMeasurement, min_length=1)


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Union[str, float, int, bool]]
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationHistoryOut(BaseModel):
    generated_at: datetime
    triage_level: str
    score: float
    rationale: str
    actions: Dict[str, Union[str, Sequence[str]]]


class HealthSummaryOut(BaseModel):
    user: UserOut
    episodes: List[EpisodeOut]
    recommendations: List[RecommendationHistoryOut]


class ProvincialMetric(BaseModel):
    measurement_code: str
    average: float
    latest: Optional[float]
    trend: str
    hint: str


class ProvincialAnalyticsOut(BaseModel):
    metrics: List[ProvincialMetric]


class DocumentationInfo(BaseModel):
    version: str = Field(default="1.0.0")
    access_token_ttl_minutes: int = Field(default=30)
    refresh_token_ttl_days: int = Field(default=7)
    password_policy: str = Field(
        default="Passwords must contain at least 8 characters with mixed complexity."
    )


DEFAULT_MEASUREMENTS: List[MeasurementDefinitionCreate] = [
    MeasurementDefinitionCreate(
        code="bp_sys",
        name="Systolic Blood Pressure",
        unit="mmHg",
        category="vital",
        source="clinical",
        attributes={"normal_min": 90, "normal_max": 120},
    ),
    MeasurementDefinitionCreate(
        code="bp_dia",
        name="Diastolic Blood Pressure",
        unit="mmHg",
        category="vital",
        source="clinical",
        attributes={"normal_min": 60, "normal_max": 80},
    ),
    MeasurementDefinitionCreate(
        code="glucose",
        name="Blood Glucose",
        unit="mg/dL",
        category="lab",
        source="lab",
        attributes={"normal_max": 140},
    ),
    MeasurementDefinitionCreate(
        code="hr",
        name="Heart Rate",
        unit="bpm",
        category="vital",
        source="wearable",
        attributes={"normal_min": 50, "normal_max": 100},
    ),
]


TOKEN_EXPIRES_MINUTES = 30
REFRESH_EXPIRES_DAYS = 7


def access_token_expiry_seconds() -> int:
    return int(timedelta(minutes=TOKEN_EXPIRES_MINUTES).total_seconds())
