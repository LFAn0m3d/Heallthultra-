"""Database CRUD operations for the Health AI Assistant."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas


# User operations

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return (
        db.execute(select(models.User).where(models.User.email == email))
        .scalar_one_or_none()
    )


def create_user(db: Session, user: schemas.UserCreate, password_hash: str) -> models.User:
    db_user = models.User(
        email=user.email,
        password_hash=password_hash,
        name=user.name,
        dob=user.dob,
        sex=user.sex,
        chronic_conditions=user.chronic_conditions,
        allergies=user.allergies,
        meds=user.meds,
        habits=user.habits,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Episode operations

def create_episode(db: Session, *, user_id: UUID, episode: schemas.EpisodeCreate) -> models.Episode:
    db_episode = models.Episode(
        user_id=user_id,
        domain=episode.domain,
        started_at=episode.started_at or datetime.utcnow(),
        primary_symptom=episode.primary_symptom,
        severity_0_10=episode.severity_0_10,
        notes=episode.notes,
    )
    db.add(db_episode)
    db.commit()
    db.refresh(db_episode)
    return db_episode


def get_episode(db: Session, episode_id: UUID, user_id: UUID) -> Optional[models.Episode]:
    stmt = select(models.Episode).where(
        models.Episode.id == episode_id, models.Episode.user_id == user_id
    )
    return db.execute(stmt).scalar_one_or_none()


def list_episodes(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 10
) -> List[models.Episode]:
    stmt = (
        select(models.Episode)
        .where(models.Episode.user_id == user_id)
        .order_by(models.Episode.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars())


# Observation operations

def create_observation(
    db: Session, *, episode_id: UUID, observation: schemas.ObservationCreate
) -> models.Observation:
    db_observation = models.Observation(
        episode_id=episode_id,
        date=observation.date or datetime.utcnow(),
        symptom_scores=observation.symptom_scores,
        side_effects=observation.side_effects,
        interventions=observation.interventions,
        vitals=observation.vitals,
        mh_scales=observation.mh_scales,
    )
    db.add(db_observation)
    db.commit()
    db.refresh(db_observation)
    return db_observation


def get_observations_for_episode(db: Session, episode_id: UUID) -> List[models.Observation]:
    stmt = (
        select(models.Observation)
        .where(models.Observation.episode_id == episode_id)
        .order_by(models.Observation.date.asc())
    )
    return list(db.execute(stmt).scalars())


# Recommendation operations

def create_recommendation(
    db: Session, *, episode_id: UUID, recommendation: schemas.RecommendationCreate
) -> models.Recommendation:
    db_recommendation = models.Recommendation(
        episode_id=episode_id,
        triage_level=recommendation.triage_level,
        condition_hints=recommendation.condition_hints,
        rationale=recommendation.rationale,
        actions=recommendation.actions,
    )
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)
    return db_recommendation


def get_recommendation(
    db: Session, recommendation_id: UUID
) -> Optional[models.Recommendation]:
    stmt = select(models.Recommendation).where(models.Recommendation.id == recommendation_id)
    return db.execute(stmt).scalar_one_or_none()
