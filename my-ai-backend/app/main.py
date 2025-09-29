"""FastAPI application entry point."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, deque
import time

from starlette.middleware.base import BaseHTTPMiddleware

from .routes import auth, episodes, recommendations, users
from .settings import get_settings

settings = get_settings()

logger = logging.getLogger("healthai")
logging.basicConfig(level=logging.INFO)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, calls: int, period: int):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.buckets = defaultdict(deque)

    async def dispatch(self, request, call_next):
        identifier = request.client.host if request.client else "anonymous"
        now = time.monotonic()
        bucket = self.buckets[identifier]
        while bucket and bucket[0] <= now - self.period:
            bucket.popleft()
        if len(bucket) >= self.calls:
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        bucket.append(now)
        response = await call_next(request)
        return response

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    openapi_tags=[
        {"name": "auth", "description": "Authentication operations"},
        {"name": "users", "description": "User profile endpoints"},
        {"name": "episodes", "description": "Manage chronic condition or mental health episodes"},
        {"name": "recommendations", "description": "AI-powered recommendations"},
    ],
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimiterMiddleware, calls=settings.rate_limit_calls, period=settings.rate_limit_period)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Log request lifecycle."""

    logger.info("Handling request: %s %s", request.method, request.url)
    response = await call_next(request)
    logger.info("Completed request: %s %s -> %s", request.method, request.url, response.status_code)
    return response


@app.on_event("startup")
async def startup_event():
    logger.info("Starting %s", settings.app_name)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping %s", settings.app_name)


@app.get("/", tags=["root"])
async def root():
    """Simple health check endpoint."""

    return {"message": "Health AI Assistant API", "docs": "/docs"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(episodes.router)
app.include_router(recommendations.router)
