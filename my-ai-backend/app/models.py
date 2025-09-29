"""SQLAlchemy ORM models for the Health AI Assistant."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .db import Base

SexEnum = Enum("M", "F", "O", name="sexenum")
DomainEnum = Enum("NCD", "MH", name="domainenum")
TriageEnum = Enum(
    "self-care", "primary-care", "urgent", "emergency", name="triageenum"
)
MeasurementTypeEnum = Enum(
    "bp", "glucose", "weight", "sleep", "mh_scale", name="measurementtypeenum"
)
MeasurementSourceEnum = Enum(
    "manual", "device", "import", name="measurementsourceenum"
)


class User(Base):
    """User model representing a patient or caregiver."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    dob = Column(Date, nullable=True)
    sex = Column(SexEnum, nullable=True)
    chronic_conditions = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    meds = Column(JSON, default=list)
    habits = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    episodes = relationship("Episode", back_populates="user", cascade="all, delete")


class Episode(Base):
    """Episode of care in either NCD or mental health domain."""

    __tablename__ = "episodes"
    __table_args__ = (UniqueConstraint("id", "user_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain = Column(DomainEnum, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    primary_symptom = Column(String(255), nullable=False)
    severity_0_10 = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="episodes")
    observations = relationship(
        "Observation", back_populates="episode", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "Recommendation", back_populates="episode", cascade="all, delete-orphan"
    )


class Observation(Base):
    """Observations recorded for an episode."""

    __tablename__ = "observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    symptom_scores = Column(JSON, default=dict)
    side_effects = Column(JSON, default=list)
    interventions = Column(JSON, default=list)
    vitals = Column(JSON, default=dict)
    mh_scales = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    episode = relationship("Episode", back_populates="observations")


class MeasurementMeta(Base):
    """Metadata for device or manual measurements."""

    __tablename__ = "measurements_meta"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(MeasurementTypeEnum, nullable=False)
    source = Column(MeasurementSourceEnum, nullable=False)
    unit = Column(String(50), nullable=False)


class Recommendation(Base):
    """Recommendation generated for an episode."""

    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    triage_level = Column(TriageEnum, nullable=False)
    condition_hints = Column(JSON, default=list)
    rationale = Column(Text, nullable=False)
    actions = Column(JSON, default=list)

    episode = relationship("Episode", back_populates="recommendations")
