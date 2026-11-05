import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize("path,content_type,expected", [
    ("/app/", "text/html", "Conecta Empleos"),
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
