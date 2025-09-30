"""Streamlit authentication helpers using backend JWT endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import streamlit as st

from .api import api_get, api_post


@dataclass
class AuthState:
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[dict] = None


def _state() -> AuthState:
    if "auth" not in st.session_state:
        st.session_state.auth = AuthState()
    return st.session_state.auth


def login(email: str, password: str) -> bool:
    response = api_post("/auth/login", {"email": email, "password": password})
    if response.status_code != 200:
        return False
    tokens = response.json()
    state = _state()
    state.access_token = tokens["access_token"]
    state.refresh_token = tokens["refresh_token"]
    return load_profile()


def refresh() -> bool:
    state = _state()
    if not state.refresh_token:
        return False
    response = api_post("/auth/refresh", {"refresh_token": state.refresh_token})
    if response.status_code != 200:
        return False
    data = response.json()
    state.access_token = data["access_token"]
    state.refresh_token = data["refresh_token"]
    return True


def load_profile() -> bool:
    state = _state()
    if not state.access_token:
        return False
    response = api_get("/users/me", token=state.access_token)
    if response.status_code != 200:
        return False
    state.user = response.json()
    return True


def logout() -> None:
    st.session_state.auth = AuthState()


def current_user() -> Optional[dict]:
    return _state().user


def require_auth() -> bool:
    state = _state()
    if state.access_token and state.user:
        return True
    if state.refresh_token and refresh():
        return True
    return False
