"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

# Load local overrides when available. The `.env.example` file is documentation
# only and is no longer loaded automatically.
load_dotenv(".env", override=False)


def _get_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_int(value: Optional[str], default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _require_env(name: str) -> str:
    """Return the required environment variable or raise a helpful error."""

    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Environment variable '{name}' is required but not set. "
            "Define it via real environment variables or a local .env file."
        )
    return value


@dataclass
class Settings:
    """Simple settings container."""

    app_name: str = os.getenv("APP_NAME", "HealthAI Assistant API")
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api")
    debug: bool = _get_bool(os.getenv("DEBUG"), False)
    environment: str = os.getenv("ENVIRONMENT", "production")

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    jwt_secret_key: str = field(default_factory=lambda: _require_env("JWT_SECRET_KEY"))
    jwt_refresh_secret_key: str = field(default_factory=lambda: _require_env("JWT_REFRESH_SECRET_KEY"))
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = _get_int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"), 15)
    refresh_token_expire_minutes: int = _get_int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"), 60 * 24 * 30)

    rate_limit_calls: int = _get_int(os.getenv("RATE_LIMIT_CALLS"), 100)
    rate_limit_period: int = _get_int(os.getenv("RATE_LIMIT_PERIOD"), 60)

    model_endpoint: Optional[str] = os.getenv("MODEL_ENDPOINT") or None
    local_model_path: Optional[str] = os.getenv("LOCAL_MODEL_PATH") or None


    def __post_init__(self):
        if self.database_url.startswith('postgresql'):
            try:
                import psycopg2  # type: ignore  # noqa: F401
            except ModuleNotFoundError:
                # Fallback to SQLite when Postgres driver is unavailable (e.g., tests)
                self.database_url = 'sqlite:///./test.db'

@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
