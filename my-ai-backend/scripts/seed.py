"""Seed script to populate sample data."""
from __future__ import annotations

import asyncio
from uuid import uuid4

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Episode, Observation, Recommendation, User
from app.services import hash_password


async def seed():
    session = SessionLocal()
    try:
        result = session.execute(select(User).where(User.email == "demo@health.ai"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid4(),
                email="demo@health.ai",
                password_hash=hash_password("DemoPass123"),
                name="Demo Patient",
                chronic_conditions=["hypertension"],
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        episode = Episode(
            id=uuid4(),
            user_id=user.id,
            domain="NCD",
            primary_symptom="High blood pressure",
            severity_0_10=7,
            notes="Frequent headaches",
        )
        session.add(episode)
        session.commit()
        session.refresh(episode)

        observation = Observation(
            id=uuid4(),
            episode_id=episode.id,
            vitals={"bp_sys": 165, "bp_dia": 102},
            symptom_scores={"headache": 6},
            interventions=["amlodipine"],
        )
        session.add(observation)
        session.commit()

        recommendation = Recommendation(
            id=uuid4(),
            episode_id=episode.id,
            triage_level="urgent",
            condition_hints=["Hypertension crisis"],
            rationale="Elevated blood pressure readings",
            actions=["Schedule primary care visit", "Review medications"],
        )
        session.add(recommendation)
        session.commit()
        print("Seed data inserted")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(seed())
