"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..deps import get_db_session
from ..services import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db_session)):
    existing = crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    password_hash = hash_password(user.password)
    new_user = crud.create_user(db, user, password_hash)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login_user(credentials: schemas.LoginRequest, db: Session = Depends(get_db_session)):
    user = crud.get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)
    return schemas.Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(request: schemas.RefreshRequest):
    from ..services import decode_token

    try:
        payload = decode_token(request.refresh_token, token_type="refresh")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = create_access_token(payload.sub)
    refresh_token = create_refresh_token(payload.sub)
    return schemas.Token(access_token=access_token, refresh_token=refresh_token)
