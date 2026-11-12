import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from neo4j.exceptions import ServiceUnavailable

from app.core.exceptions import NotFound, register_handlers
from app.core.logging import RequestLoggingMiddleware, install_request_logging


@pytest.mark.parametrize("exception,status,code", [
    (NotFound("Candidato"), 404, "NOT_FOUND"),
    (ServiceUnavailable("secret Cypher"), 503, "DB_UNAVAILABLE"),
    (RuntimeError("secret data"), 500, "INTERNAL_ERROR"),
])
def test_safe_error_envelope(exception: Exception, status: int, code: str) -> None:
    app = FastAPI()
    register_handlers(app)
    install_request_logging(app)

    @app.get("/fail")
    def fail() -> None:
        raise exception

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/fail")
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert "secret" not in response.text
    assert response.headers["X-Request-ID"]


@pytest.mark.parametrize("fail_after_start", [False, True])
def test_streaming_body_is_forwarded_without_replacing_a_started_response(fail_after_start, caplog):
    messages = []

    async def send(message):
        messages.append(message)

    async def receive():
        raise AssertionError("The logger must not consume the request body")

    async def stream(scope, receive, send):
        await send({"type": "http.response.start", "status": 206, "headers": []})
        await send({"type": "http.response.body", "body": b"first", "more_body": True})
        assert len(messages) == 2  # Chunks reach the client before the stream finishes.
        if fail_after_start:
            raise RuntimeError("private-stream-data")
        await send({"type": "http.response.body", "body": b"last", "more_body": False})

    scope = {"type": "http", "method": "GET", "path": "/stream", "headers": []}

    async def run():
        if fail_after_start:
            with pytest.raises(RuntimeError, match="private-stream-data"):
                await RequestLoggingMiddleware(stream)(scope, receive, send)
        else:
            await RequestLoggingMiddleware(stream)(scope, receive, send)

    asyncio.run(run())
    assert sum(m["type"] == "http.response.start" for m in messages) == 1
    assert messages[0]["status"] == 206
    assert dict(messages[0]["headers"])[b"x-request-id"].decode() == scope["state"]["request_id"]
    assert b"".join(m.get("body", b"") for m in messages) == (b"first" if fail_after_start else b"firstlast")
    assert "private-stream-data" not in caplog.text
