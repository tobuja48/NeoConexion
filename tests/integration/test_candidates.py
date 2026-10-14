import pytest
from fastapi.testclient import TestClient

from app.core.neo4j_driver import get_driver
from app.repositories.test_support import entity_count

pytestmark = pytest.mark.integration


def test_upsert_candidate(client: TestClient, candidate_data: dict, prefix: str) -> None:
    first = client.post("/api/v1/candidates", json=candidate_data)
    assert first.status_code == 201, first.text
    assert client.post("/api/v1/candidates", json=candidate_data).status_code == 200
    assert entity_count(get_driver(), candidate_data["id"]) == 1
    candidate_data.update(skills=[prefix + " Go ", prefix + " go "],
                          location=prefix + "Lima", preferredWorkMode=" HYBRID ", expectedSalary=None)
    update = client.post("/api/v1/candidates", json=candidate_data)
    assert update.status_code == 200
    fetched = client.get("/api/v1/candidates/" + candidate_data["id"])
    assert fetched.json() == update.json()
    assert len(fetched.json()["skills"]) == 1
    assert fetched.json()["preferredWorkMode"] == "hybrid"
    assert fetched.json()["expectedSalary"] is None
    assert fetched.json()["location"] == prefix + "Lima"


def test_candidate_404(client: TestClient, prefix: str) -> None:
    result = client.get("/api/v1/candidates/" + prefix + "missing")
    assert result.status_code == 404
    assert result.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("change", [{"id": " "}, {"yearsOfExperience": -1},
                                  {"skills": [" "]}, {"preferredWorkMode": "office"},
                                  {"name": "a" * 201}, {"expectedSalary": -1}])
def test_validation(client: TestClient, candidate_data: dict, change: dict) -> None:
    result = client.post("/api/v1/candidates", json=candidate_data | change)
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "VALIDATION_ERROR"
