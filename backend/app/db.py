"""Database configuration module."""
from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base class for SQLAlchemy models."""


def get_db():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
