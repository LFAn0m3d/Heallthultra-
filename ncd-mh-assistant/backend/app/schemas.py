"""Pydantic schemas for API I/O."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, PositiveInt


class RedFlagAnswers(BaseModel):
    self_harm: bool = Field(default=False, description="Indicates imminent self-harm risk")


class AnalyzeRequest(BaseModel):
    age: int
    sex: Literal["M", "F", "Other"]
    domain: Literal["NCD", "MH"]
    primary_symptom: str
    duration_days: Optional[int] = Field(default=None, ge=0)
    bp_sys: Optional[float] = Field(default=None, description="Systolic blood pressure")
    bp_dia: Optional[float] = Field(default=None, description="Diastolic blood pressure")
    glucose: Optional[float] = Field(default=None, description="Blood glucose (mg/dL)")
    phq9: Optional[float] = Field(default=None)
    gad7: Optional[float] = Field(default=None)
    weight: Optional[float] = None
    red_flag_answers: RedFlagAnswers = Field(default_factory=RedFlagAnswers)


class AnalyzeResponse(BaseModel):
    triage_level: Literal["แดง", "ส้ม", "เหลือง", "เขียว"]
    actions: List[str]
    rationale: List[str]
    condition_hints: List[str]


class EpisodeReference(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    domain: Literal["NCD", "MH"]
    started_at: Optional[datetime] = None
    primary_symptom: Optional[str] = None
    severity_0_10: Optional[int] = Field(default=None, ge=0, le=10)
    notes: Optional[str] = None


class ObservationCreate(BaseModel):
    episode_id: Optional[int] = Field(default=None, description="Existing episode ID")
    episode: Optional[EpisodeReference] = Field(default=None, description="Data to create a new episode if not referencing an existing one")
    date: Optional[datetime] = Field(default=None, description="Observation datetime (defaults to now)")
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    hr: Optional[float] = None
    weight: Optional[float] = None
    waist: Optional[float] = None
    glucose: Optional[float] = None
    phq9: Optional[float] = None
    gad7: Optional[float] = None
    isi: Optional[float] = None


class ObservationResponse(BaseModel):
    id: PositiveInt
    episode_id: PositiveInt
    date: datetime
    values: Dict[str, Optional[float]]


class TrendRequest(BaseModel):
    episode_id: PositiveInt
    metric: Literal["bp_sys", "bp_dia", "glucose", "weight", "phq9", "gad7"]


class TrendPoint(BaseModel):
    date: datetime
    value: float


class TrendResponse(BaseModel):
    points: List[TrendPoint]
    ewma: Optional[float]
    slope_per_day: Optional[float]
    trend: Literal["ดีขึ้น", "ทรงตัว", "แย่ลง", "ไม่เพียงพอ"]
    confidence: float
