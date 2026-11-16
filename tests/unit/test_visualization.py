from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr

import app.core.visualization as module
from app.core.visualization import MAX_BODY, TraceStore, VisualizationMiddleware


def build(monkeypatch, key=""):
    monkeypatch.setattr(module, "get_settings", lambda: SimpleNamespace(api_key=SecretStr(key)))
    store = TraceStore()
    app = FastAPI()

    @app.post("/api/v1/candidates", status_code=201)
    def echo(payload: dict):
        return payload

    @app.get("/api/v1/jobs/{id}")
    def missing(id: str):
        raise HTTPException(404, "No existe")

    app.add_middleware(VisualizationMiddleware, store=store)
    return TestClient(app), store


def test_traces_real_body_status_and_response_without_headers(monkeypatch):
    client, store = build(monkeypatch, "private-key")
    payload = {"id": "c", "name": "Ana"}
    response = client.post("/api/v1/candidates", json=payload, headers={"X-API-Key": "private-key"})
    entry = store.read(0)["requests"][0]
    assert response.status_code == entry["status"] == 201
    assert entry["request_body"] == entry["response"] == payload
    assert entry["state"] == "completed"
    assert "private-key" not in str(store.read(0))
    assert client.get("/api/v1/jobs/missing", headers={"X-API-Key": "private-key"}).status_code == 404
    assert store.read(0)["requests"][-1]["status"] == 404


def test_unapproved_requests_and_observer_polling_are_not_recorded(monkeypatch):
    client, store = build(monkeypatch, "private-key")
    client.post("/api/v1/candidates", json={"id": "c"}, headers={"X-API-Key": "wrong"})
    client.get("/api/v1/visualization/requests")
    assert store.read(0)["requests"] == []


def test_large_bodies_are_marked_without_modifying_the_api_response(monkeypatch):
    client, store = build(monkeypatch)
    payload = {"large": "x" * (MAX_BODY + 1)}
    response = client.post("/api/v1/candidates", json=payload)
    assert response.json() == payload
    entry = store.read(0)["requests"][0]
    assert entry["request_truncated"] and entry["response_truncated"]
    assert entry["request_body"] is None and entry["response"] is None


def test_cursor_and_bounded_history():
    store = TraceStore(capacity=2)
    first = store.start("POST", "/api/v1/candidates")
    cursor = store.read(0)["cursor"]
    store.update(first, state="completed", status=201)
    assert store.read(cursor)["requests"][0]["state"] == "completed"
    store.start("GET", "/api/v1/jobs/one")
    store.start("GET", "/api/v1/jobs/two")
    assert len(store.read(0)["requests"]) == 2
    assert first["id"] not in [entry["id"] for entry in store.read(0)["requests"]]


def test_viewer_endpoint_requires_the_configured_api_key(monkeypatch):
    from app.core.config import get_settings
    from app.main import app

    monkeypatch.setenv("API_KEY", "viewer-private-key")
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        assert client.get("/api/v1/visualization/requests").status_code == 401
        response = client.get("/api/v1/visualization/requests", headers={"X-API-Key": "viewer-private-key"})
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert "viewer-private-key" not in response.text
    finally:
        get_settings.cache_clear()
