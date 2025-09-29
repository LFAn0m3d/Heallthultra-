"""Recommendation endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..deps import get_current_user, get_db_session
from ..services import predict_recommendation

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=schemas.RecommendationRead, status_code=status.HTTP_201_CREATED)
async def create_recommendation_endpoint(
    recommendation_request: schemas.RecommendationCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    episode = crud.get_episode(db, recommendation_request.episode_id, current_user.id)
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found")

    return crud.create_recommendation(db, episode_id=episode.id, recommendation=recommendation_request)


@router.post("/{episode_id}/recommend", response_model=schemas.RecommendationRead, status_code=status.HTTP_201_CREATED)
async def run_recommender(
    episode_id: UUID,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    episode = crud.get_episode(db, episode_id, current_user.id)
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found")

    observations = crud.get_observations_for_episode(db, episode_id)
    recommendation_data = await predict_recommendation(episode, observations)
    recommendation = crud.create_recommendation(db, episode_id=episode_id, recommendation=recommendation_data)
    return recommendation


@router.get("/{recommendation_id}", response_model=schemas.RecommendationRead)
def get_recommendation(
    recommendation_id: UUID,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    recommendation = crud.get_recommendation(db, recommendation_id)
    if not recommendation or recommendation.episode.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    return recommendation
