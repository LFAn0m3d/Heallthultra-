"""Security utilities for hashing passwords and issuing simple signed tokens."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Sequence

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models, schemas
from .db import get_db


SECRET_KEY = os.getenv("HEALTHULTRA_SECRET", "unsafe-development-key").encode()
ACCESS_TOKEN_EXPIRE_MINUTES = schemas.TOKEN_EXPIRES_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = schemas.REFRESH_EXPIRES_DAYS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 390000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "$".join(
        [
            str(iterations),
            base64.b64encode(salt).decode(),
            base64.b64encode(digest).decode(),
        ]
    )


def verify_password(password: str, hashed: str) -> bool:
    try:
        iterations_str, salt_b64, digest_b64 = hashed.split("$")
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:  # pragma: no cover - malformed hash guard
        return False


def _sign(payload: dict) -> str:
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    signature = hmac.new(SECRET_KEY, data, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(data + b"." + signature).decode()


def _unsign(token: str) -> dict:
    try:
        decoded = base64.urlsafe_b64decode(token.encode())
        data, signature = decoded.rsplit(b".", 1)
        expected = hmac.new(SECRET_KEY, data, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature mismatch")
        return json.loads(data.decode())
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    expire = datetime.now(tz=timezone.utc) + expires_delta
    payload = {**data, "exp": expire.timestamp(), "type": token_type}
    return _sign(payload)


def create_access_token(*, subject: int, version: int) -> str:
    data = {"sub": subject, "version": version}
    return _create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(*, subject: int, version: int) -> str:
    data = {"sub": subject, "version": version}
    return _create_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


def decode_token(token: str) -> schemas.TokenPayload:
    payload = _unsign(token)
    if payload.get("exp") and datetime.now(tz=timezone.utc).timestamp() > payload["exp"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return schemas.TokenPayload(
        sub=payload["sub"],
        exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        type=payload["type"],
        version=payload["version"],
    )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    payload = decode_token(token)
    if payload.type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user = db.get(models.User, payload.sub)
    if not user or user.token_version != payload.version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or token expired")
    return user


def require_roles(roles: Sequence[str]):
    role_set = {r.lower() for r in roles}

    def dependency(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role.name.lower() not in role_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency


def ensure_role_exists(db: Session, name: str) -> models.Role:
    role = db.query(models.Role).filter(models.Role.name == name).one_or_none()
    if role is None:
        role = models.Role(name=name)
        db.add(role)
        db.flush()
    return role


def ensure_default_roles(db: Session) -> None:
    for role_name in ("patient", "clinician", "admin"):
        ensure_role_exists(db, role_name)
