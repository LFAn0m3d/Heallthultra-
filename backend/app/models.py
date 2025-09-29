"""SQLAlchemy ORM models for the HealthUltra platform."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, engine


class Role(Base):
    """User role used for RBAC enforcement."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role")


class User(Base):
    """Application user record."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(Enum("M", "F", "O", name="sex"), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    chronic_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    habits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    role: Mapped[Role] = relationship(back_populates="users")
    episodes: Mapped[List["Episode"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    medications: Mapped[List["Medication"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    allergies: Mapped[List["Allergy"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    histories: Mapped[List["ClinicalHistoryEntry"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")


class Medication(Base):
    """Historical record of patient medications."""

    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    started_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    stopped_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    user: Mapped[User] = relationship(back_populates="medications")


class Allergy(Base):
    """Allergy record including severity and reaction description."""

    __tablename__ = "allergies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    substance: Mapped[str] = mapped_column(String(255), nullable=False)
    reaction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    user: Mapped[User] = relationship(back_populates="allergies")


class ClinicalHistoryEntry(Base):
    """Past medical history entries for reference in triage."""

    __tablename__ = "clinical_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[User] = relationship(back_populates="histories")


class Episode(Base):
    """Clinical episode representing a symptom cluster or visit."""

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(Enum("NCD", "MH", "ACUTE", name="episode_domain"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    primary_symptom: Mapped[str] = mapped_column(String(255), nullable=False)
    severity_0_10: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("active", "resolved", "archived", name="episode_status"),
        default="active",
        nullable=False,
    )
    last_triage_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    user: Mapped[User] = relationship(back_populates="episodes")
    observations: Mapped[List["Observation"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )


class MeasurementDefinition(Base):
    """Metadata describing each measurement captured for observations."""

    __tablename__ = "measurement_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)

    observations: Mapped[List["Observation"]] = relationship(back_populates="definition")


class Observation(Base):
    """Discrete measurement captured for an episode."""

    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    measurement_definition_id: Mapped[int] = mapped_column(
        ForeignKey("measurement_definitions.id", ondelete="RESTRICT"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    value_number: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)

    episode: Mapped[Episode] = relationship(back_populates="observations")
    definition: Mapped[MeasurementDefinition] = relationship(back_populates="observations")


class Recommendation(Base):
    """Stores personalized recommendations generated by the engine."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    triage_level: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    actions: Mapped[dict] = mapped_column(JSON, default=dict)

    episode: Mapped[Episode] = relationship(back_populates="recommendations")


class AuditLog(Base):
    """Audit trail of user activity for compliance."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[Optional[User]] = relationship(back_populates="audit_logs")


# Create tables when module is imported
Base.metadata.create_all(bind=engine)
