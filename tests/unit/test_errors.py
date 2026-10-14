import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from neo4j.exceptions import ServiceUnavailable

from app.core.exceptions import NotFound, register_handlers
from app.core.logging import install_request_logging


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
