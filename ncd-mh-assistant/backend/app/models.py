"""ORM models for the NCD/MH assistant."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dob: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    chronic_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meds: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    habits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    episodes: Mapped[List["Episode"]] = relationship(back_populates="user")


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    domain: Mapped[str] = mapped_column(Enum("NCD", "MH", name="domain_enum"))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    primary_symptom: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    severity_0_10: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[Optional[User]] = relationship(back_populates="episodes")
    observations: Mapped[List["Observation"]] = relationship(back_populates="episode", cascade="all, delete-orphan")


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    episode_id: Mapped[int] = mapped_column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"))
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    bp_sys: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bp_dia: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    waist: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    glucose: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phq9: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gad7: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    isi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    episode: Mapped[Episode] = relationship(back_populates="observations")
