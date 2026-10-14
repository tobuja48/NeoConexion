from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.neo4j_driver import get_driver
from app.main import app
from app.repositories.test_support import cleanup_test_data


@pytest.fixture
def prefix() -> str:
    return "test-neoconexion-" + uuid4().hex + "-"


@pytest.fixture
def client(prefix: str) -> Iterator[TestClient]:
    # Real lifespan and real DB. A missing Neo4j fails instead of silently skipping tests.
    with TestClient(app) as test_client:
        test_client.headers["X-API-Key"] = get_settings().api_key.get_secret_value()
        cleanup_test_data(get_driver(), prefix)
        try:
            yield test_client
        finally:
            cleanup_test_data(get_driver(), prefix)


@pytest.fixture
def candidate_data(prefix: str) -> dict:
    return {"id": prefix + "c", "name": "Ana", "location": prefix + "Bogotá",
            "yearsOfExperience": 5, "skills": [prefix + "Python", prefix + "Docker"],
            "preferredWorkMode": "remote", "expectedSalary": 5000000}


@pytest.fixture
def job_data(prefix: str) -> dict:
    return {"id": prefix + "j", "company": prefix + "ACME", "title": "Backend",
            "location": prefix + "Bogotá", "workMode": "remote", "requiredExperience": 3,
            "requiredSkills": [prefix + "Python"], "desiredSkills": [prefix + "Docker"]}
