"""Test configuration and fixtures."""
from __future__ import annotations

from datetime import datetime
from typing import Dict
from uuid import uuid4

import pytest
from .utils import SimpleASGITestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import deps
from app.db import Base
from app.main import app
from app.models import User
from app.services import hash_password

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides = {}
app.dependency_overrides[deps.get_db] = override_get_db
app.dependency_overrides[deps.get_db_session] = override_get_db


@pytest.fixture()
def client(db_session):
    return SimpleASGITestClient(app)


@pytest.fixture()
def user_payload() -> Dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "email": f"test_{unique}@example.com",
        "password": "supersecret",
        "name": "Test User",
    }


@pytest.fixture()
def create_user(db_session: Session, user_payload: Dict[str, str]):
    user = User(
        id=uuid4(),
        email=user_payload["email"],
        password_hash=hash_password(user_payload["password"]),
        name=user_payload["name"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    return user
