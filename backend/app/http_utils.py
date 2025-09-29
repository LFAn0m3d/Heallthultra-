"""Offline-safe HTTP helpers for integration with external services."""
from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


async def safe_request(
    method: str,
    url: str,
    *,
    json: Optional[Dict[str, Any]] = None,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """Perform an HTTP request but always return a JSON payload."""

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, url, json=json)
            response.raise_for_status()
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return {"status": response.status_code, "text": response.text}
    except Exception as exc:  # pragma: no cover - network failure path
        return {"error": str(exc), "offline": True, "url": url}


async def safe_post(url: str, *, json: Optional[Dict[str, Any]] = None, timeout: float = 5.0) -> Dict[str, Any]:
    return await safe_request("POST", url, json=json, timeout=timeout)


async def safe_get(url: str, *, timeout: float = 5.0) -> Dict[str, Any]:
    return await safe_request("GET", url, timeout=timeout)
