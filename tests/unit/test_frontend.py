import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize("path,content_type,expected", [
    ("/app/", "text/html", "Conecta Empleos"),
    ("/app/maquina.html", "text/html", "visor independiente"),
    ("/app/observer.js", "javascript", "visualization/requests"),
    ("/app/machine.js", "javascript", "JsonMachine"),
    ("/app/machine.css", "text/css", "prefers-reduced-motion"),
])
def test_frontend_assets_are_served_without_database_lifespan(path, content_type, expected):
    response = TestClient(app).get(path)
    assert response.status_code == 200
    assert content_type in response.headers["content-type"]
    assert expected in response.text


def test_frontend_unknown_path_does_not_return_successful_html():
    assert TestClient(app).get("/app/missing-file.js").status_code == 404


def test_original_vacancy_html_is_byte_for_byte_the_supplied_document():
    from hashlib import sha256

    original_digest = "0177c4ba32f5d6e3acca56a23bbdd2d6b6814ab01d786698603e20bc29462126"
    response = TestClient(app).get("/app/")
    assert sha256(response.content).hexdigest() == original_digest
    assert "machine.js" not in response.text
