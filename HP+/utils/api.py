"""Helper utilities for talking to the FastAPI backend."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


BACKEND_URL = os.getenv("HEALTHULTRA_API", "http://localhost:8000")


def _url(path: str) -> str:
    return f"{BACKEND_URL.rstrip('/')}/{path.lstrip('/')}"


def api_post(path: str, payload: Dict[str, Any], token: Optional[str] = None) -> requests.Response:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(_url(path), json=payload, headers=headers, timeout=10)


def api_get(path: str, token: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.get(_url(path), headers=headers, params=params, timeout=10)
