from unittest.mock import Mock
from fastapi.testclient import TestClient
from neo4j.exceptions import ServiceUnavailable
import app.main as module

def test_process_health_is_independent_of_database(monkeypatch):
    driver = Mock(); driver.verify_connectivity.side_effect = ServiceUnavailable("private details")
    monkeypatch.setattr(module, "get_driver", lambda: driver)
    client = TestClient(module.app)
    assert client.get("/health").json() == {"status":"ok"}
    response = client.get("/health/db")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DB_UNAVAILABLE"
    assert "private details" not in response.text
