"""Bounded in-memory API traces for the independent local demonstration viewer.

Never records request headers/API keys. Observes ASGI messages without changing
the original frontend, endpoints, body validation or transaction behavior.
"""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import json
from secrets import compare_digest
from threading import Lock
from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings

MAX_BODY = 131072


class TraceStore:
    def __init__(self, capacity: int = 40):
        self.entries: deque[dict] = deque(maxlen=capacity)
        self.version = 0
        self.lock = Lock()
        self.stream_id = uuid4().hex

    def start(self, method: str, path: str) -> dict:
        with self.lock:
            self.version += 1
            entry = {"id": uuid4().hex, "version": self.version, "method": method,
                     "path": path, "started_at": datetime.now(timezone.utc).isoformat(),
                     "state": "pending", "request_body": None, "request_truncated": False,
                     "status": None, "response": None, "response_raw": "",
                     "response_json": False, "response_truncated": False, "request_id": None}
            self.entries.append(entry)
            return entry

    def update(self, entry: dict, **changes):
        with self.lock:
            self.version += 1
            entry.update(changes, version=self.version)

    def read(self, after: int) -> dict:
        with self.lock:
            return {"stream_id": self.stream_id, "cursor": self.version,
                    "requests": deepcopy([e for e in self.entries if e["version"] > after])}


traces = TraceStore()


class VisualizationMiddleware:
    def __init__(self, app: ASGIApp, store: TraceStore = traces):
        self.app, self.store = app, store

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        path = scope.get("path", "")
        watched = any(path == p or path.startswith(p + "/") for p in
                      ("/api/v1/candidates", "/api/v1/jobs"))
        if scope["type"] != "http" or scope.get("method") not in {"GET", "POST"} or not watched:
            return await self.app(scope, receive, send)
        configured = get_settings().api_key.get_secret_value()
        supplied = dict(scope.get("headers", [])).get(b"x-api-key", b"")
        if configured and not compare_digest(configured.encode(), supplied):
            return await self.app(scope, receive, send)
        entry = self.store.start(scope["method"], path)
        began = perf_counter()
        request_buffer, response_buffer = bytearray(), bytearray()
        request_size = response_size = 0

        async def observe_receive():
            nonlocal request_size
            message = await receive()
            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                request_size += len(chunk)
                request_buffer.extend(chunk[:max(0, MAX_BODY - len(request_buffer))])
                if not message.get("more_body", False):
                    body = None
                    if request_size <= MAX_BODY and request_buffer:
                        try:
                            body = json.loads(request_buffer)
                        except (ValueError, UnicodeDecodeError):
                            body = request_buffer.decode("utf-8", errors="replace")
                    self.store.update(entry, request_body=body, request_truncated=request_size > MAX_BODY)
            return message

        async def observe_send(message):
            nonlocal response_size
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                self.store.update(entry, status=message["status"],
                                  request_id=headers.get(b"x-request-id", b"").decode("utf-8", errors="replace") or None)
            elif message["type"] == "http.response.body":
                chunk = message.get("body", b"")
                response_size += len(chunk)
                response_buffer.extend(chunk[:max(0, MAX_BODY - len(response_buffer))])
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                parsed, is_json = None, False
                raw = response_buffer.decode("utf-8", errors="replace") if response_size <= MAX_BODY else ""
                if raw:
                    try:
                        parsed, is_json = json.loads(raw), True
                    except ValueError:
                        pass
                self.store.update(entry, state="completed", response=parsed, response_raw=raw,
                                  response_json=is_json, response_truncated=response_size > MAX_BODY,
                                  duration_ms=round((perf_counter() - began) * 1000, 1))

        try:
            await self.app(scope, observe_receive, observe_send)
        except Exception:
            self.store.update(entry, state="interrupted", duration_ms=round((perf_counter() - began) * 1000, 1))
            raise
