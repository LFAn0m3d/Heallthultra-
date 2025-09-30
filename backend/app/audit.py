"""Audit logging helpers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from . import models


def log_event(
    db: Session,
    *,
    user: Optional[models.User],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> models.AuditLog:
    """Persist an audit log entry."""

    entry = models.AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        created_at=datetime.now(tz=timezone.utc),
    )
    db.add(entry)
    db.flush()
    return entry
