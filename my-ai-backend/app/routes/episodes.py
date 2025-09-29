"""Episode related routes."""
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..deps import get_current_user, get_db_session

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.post("", response_model=schemas.EpisodeRead, status_code=status.HTTP_201_CREATED)
def create_episode(
    episode: schemas.EpisodeCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    return crud.create_episode(db, user_id=current_user.id, episode=episode)


@router.get("", response_model=List[schemas.EpisodeRead])
def list_episodes(
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return crud.list_episodes(db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{episode_id}", response_model=schemas.EpisodeDetail)
def get_episode(
    episode_id: UUID,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    episode = crud.get_episode(db, episode_id=episode_id, user_id=current_user.id)
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found")

    observations = crud.get_observations_for_episode(db, episode_id)
    recommendations = list(episode.recommendations)
    base_detail = schemas.EpisodeDetail.model_validate(episode)
    return base_detail.model_copy(update={
        "observations": [schemas.ObservationRead.model_validate(obs) for obs in observations],
        "recommendations": [schemas.RecommendationRead.model_validate(rec) for rec in recommendations],
    })


@router.post("/{episode_id}/observations", response_model=schemas.ObservationRead, status_code=status.HTTP_201_CREATED)
def add_observation(
    episode_id: UUID,
    observation: schemas.ObservationCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    episode = crud.get_episode(db, episode_id=episode_id, user_id=current_user.id)
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found")

    return crud.create_observation(db, episode_id=episode_id, observation=observation)
