from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import install_cors

ORIGIN = "http://localhost:8010"


def build(origins: list[str]) -> TestClient:
    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    install_cors(app, origins)
    return TestClient(app)


def test_origins_are_parsed_and_trimmed():
    config = Settings(_env_file=None, neo4j_password="x", cors_origins=" http://a.co/ , ,http://b.co")
    assert config.cors_origin_list == ["http://a.co", "http://b.co"]


def test_cors_disabled_by_default():
    assert Settings(_env_file=None, neo4j_password="x").cors_origin_list == []
    response = build([]).get("/ping", headers={"Origin": ORIGIN})
    assert "access-control-allow-origin" not in response.headers


def test_allowed_origin_receives_headers_and_preflight_accepts_api_key():
    client = build([ORIGIN])
    assert client.get("/ping", headers={"Origin": ORIGIN}).headers["access-control-allow-origin"] == ORIGIN
    preflight = client.options("/ping", headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-api-key"})
    assert preflight.status_code == 200
    assert "x-api-key" in preflight.headers["access-control-allow-headers"].lower()


def test_unknown_origin_is_not_allowed():
    response = build([ORIGIN]).get("/ping", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers
