"""Pydantic schemas for request and response models."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ObservationIn(BaseModel):
    episode_id: int
    date: date = Field(description="Date of the observation")
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    hr: Optional[float] = None
    weight: Optional[float] = None
    waist: Optional[float] = None
    glucose: Optional[float] = None
    phq9: Optional[float] = None
    gad7: Optional[float] = None
    isi: Optional[float] = None


class AnalyzeIn(BaseModel):
    age: int
    sex: Literal["M", "F", "O"]
    domain: Literal["NCD", "MH"]
    primary_symptom: str
    duration_days: Optional[int] = None
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    glucose: Optional[float] = None
    phq9: Optional[float] = None
    gad7: Optional[float] = None
    isi: Optional[float] = None
    red_flag_answers: Dict[str, bool] = Field(default_factory=dict)
    self_harm: Optional[bool] = None


class AnalyzeOut(BaseModel):
    triage_level: Literal["เขียว", "เหลือง", "ส้ม", "แดง"]
    actions: List[str]
    rationale: str
    hints: List[str]


class TrendRequest(BaseModel):
    episode_id: int
    metric: Literal[
        "bp_sys",
        "bp_dia",
        "hr",
        "weight",
        "waist",
        "glucose",
        "phq9",
        "gad7",
        "isi",
    ]
    days: Optional[int] = Field(default=30, ge=1, description="Number of days to look back")


class TrendPoint(BaseModel):
    date: date
    value: float


class TrendOut(BaseModel):
    metric: str
    points: List[TrendPoint]
    ewma: Optional[List[float]]
    slope_per_day: float
    trend: Literal["ดีขึ้น", "ทรงตัว", "แย่ลง"]
    confidence: Literal["ต่ำ", "กลาง", "สูง"]
