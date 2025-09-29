"""Pydantic schemas for request and response models."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TimestampedModel(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: Optional[str] = None
    dob: Optional[date] = None
    sex: Optional[str] = Field(default=None, pattern=r"^(M|F|O)$")
    chronic_conditions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    meds: List[str] = Field(default_factory=list)
    habits: List[str] = Field(default_factory=list)


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserRead(UserBase, TimestampedModel):
    id: UUID


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str


class EpisodeBase(BaseModel):
    domain: str = Field(pattern=r"^(NCD|MH)$")
    started_at: Optional[datetime] = None
    primary_symptom: str = Field(min_length=1)
    severity_0_10: int = Field(ge=0, le=10)
    notes: Optional[str] = None


class EpisodeCreate(EpisodeBase):
    pass


class EpisodeRead(EpisodeBase, TimestampedModel):
    id: UUID
    user_id: UUID


class ObservationBase(BaseModel):
    date: Optional[datetime] = None
    symptom_scores: Dict[str, float] = Field(default_factory=dict)
    side_effects: List[str] = Field(default_factory=list)
    interventions: List[str] = Field(default_factory=list)
    vitals: Dict[str, Any] = Field(default_factory=dict)
    mh_scales: Dict[str, Any] = Field(default_factory=dict)


class ObservationCreate(ObservationBase):
    pass


class ObservationRead(ObservationBase):
    id: UUID
    episode_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationBase(BaseModel):
    triage_level: str = Field(pattern=r"^(self-care|primary-care|urgent|emergency)$")
    condition_hints: List[str] = Field(default_factory=list)
    rationale: str
    actions: List[str] = Field(default_factory=list)


class RecommendationCreate(BaseModel):
    episode_id: UUID
    triage_level: str = Field(pattern=r"^(self-care|primary-care|urgent|emergency)$")
    condition_hints: List[str] = Field(default_factory=list)
    rationale: str
    actions: List[str] = Field(default_factory=list)


class RecommendationRead(RecommendationBase):
    id: UUID
    episode_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EpisodeDetail(EpisodeRead):
    observations: List[ObservationRead] = Field(default_factory=list)
    recommendations: List[RecommendationRead] = Field(default_factory=list)


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class Message(BaseModel):
    message: str
