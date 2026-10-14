import pytest
from fastapi.testclient import TestClient

from app.core.neo4j_driver import get_driver
from app.repositories.test_support import entity_count

pytestmark = pytest.mark.integration


def test_upsert_job(client: TestClient, job_data: dict, prefix: str) -> None:
    first = client.post("/api/v1/jobs", json=job_data)
    assert first.status_code == 201, first.text
    assert client.post("/api/v1/jobs", json=job_data).status_code == 200
    assert entity_count(get_driver(), job_data["id"]) == 1
    job_data.update(requiredSkills=[prefix + "Go"], desiredSkills=[], location=prefix + "Lima",
                    company=prefix + "NEW", workMode=" HYBRID ", description="Nueva")
    updated = client.post("/api/v1/jobs", json=job_data)
    assert updated.status_code == 200, updated.text
    fetched = client.get("/api/v1/jobs/" + job_data["id"])
    assert fetched.json() == updated.json()
    assert fetched.json()["company"] == job_data["company"]
    assert fetched.json()["requiredSkills"] == job_data["requiredSkills"]
    assert fetched.json()["desiredSkills"] == []
    assert fetched.json()["location"] == job_data["location"]
    assert fetched.json()["workMode"] == "hybrid"


def test_job_404(client: TestClient, prefix: str) -> None:
    result = client.get("/api/v1/jobs/" + prefix + "missing")
    assert result.status_code == 404
    assert result.json()["error"]["code"] == "NOT_FOUND"


def test_empty_skills_and_zero_experience(client: TestClient, job_data: dict) -> None:
    job_data.update(requiredSkills=[], desiredSkills=[], requiredExperience=0)
    result = client.post("/api/v1/jobs", json=job_data)
    assert result.status_code == 201
    assert result.json()["requiredSkills"] == []
    assert client.get("/api/v1/jobs/" + job_data["id"]).json() == result.json()


@pytest.mark.parametrize("change", [{"id": ""}, {"requiredExperience": -1},
                                  {"workMode": "any"}, {"requiredSkills": [""]},
                                  {"description": "a" * 5001}])
def test_job_validation(client: TestClient, job_data: dict, change: dict) -> None:
    response = client.post("/api/v1/jobs", json=job_data | change)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
