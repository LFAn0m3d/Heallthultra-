"""Utilities for testing without external HTTP client dependencies."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import FastAPI
from starlette.datastructures import Headers


@dataclass
class SimpleResponse:
    status_code: int
    body: bytes
    headers: Headers

    def json(self) -> Any:
        return json.loads(self.body.decode() or "null")

    @property
    def text(self) -> str:
        return self.body.decode()


class SimpleASGITestClient:
    """Minimal synchronous test client for ASGI apps."""

    __test__ = False

    def __init__(self, app: FastAPI):
        self.app = app

    def request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> SimpleResponse:
        headers = headers or {}
        body = b""
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            if "content-type" not in {k.lower() for k in headers}:
                headers = {**headers, "Content-Type": "application/json"}

        async def _send_request():
            response_data: Dict[str, Any] = {}

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            async def send(message):
                message_type = message["type"]
                if message_type == "http.response.start":
                    response_data["status"] = message["status"]
                    response_data["headers"] = Headers(raw=message.get("headers", []))
                elif message_type == "http.response.body":
                    response_data.setdefault("body", b"")
                    response_data["body"] += message.get("body", b"")

            scope = {
                "type": "http",
                "http_version": "1.1",
                "method": method.upper(),
                "path": url,
                "raw_path": url.encode(),
                "query_string": b"",
                "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()],
                "client": ("testclient", 50000),
                "server": ("testserver", 80),
                "scheme": "http",
            }

            await self.app(scope, receive, send)
            return SimpleResponse(
                status_code=response_data.get("status", 500),
                body=response_data.get("body", b""),
                headers=response_data.get("headers", Headers()),
            )

        return asyncio.run(_send_request())

    def get(self, url: str, headers: Optional[Dict[str, str]] = None):
        return self.request("GET", url, headers=headers)

    def post(self, url: str, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
        return self.request("POST", url, json_data=json, headers=headers)

    def close(self):
        pass
