from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.core.neo4j_driver import get_driver
from app.repositories import candidate_repository, job_repository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.repositories.test_support import constraint_names, entity_count, relation_count
from app.schemas.candidate import CandidateSchema
from app.schemas.job import JobSchema

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("kind", ["candidate", "job"])
def test_concurrent_upserts_are_atomic(client: TestClient, candidate_data: dict,
                                      job_data: dict, kind: str) -> None:
    driver = get_driver()
    repository = CandidateRepository(driver) if kind == "candidate" else JobRepository(driver)
    model = (CandidateSchema(**candidate_data).to_domain() if kind == "candidate"
             else JobSchema(**job_data).to_domain())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: repository.upsert(model), range(4)))
    assert sum(created for _, created in results) == 1
    assert entity_count(driver, model.id) == 1
    assert relation_count(driver, model.id) == (4 if kind == "candidate" else 5)


@pytest.mark.parametrize("kind", ["candidate", "job"])
def test_failed_write_rolls_back_relationship_replacement(
    client: TestClient, candidate_data: dict, job_data: dict, kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "/api/v1/" + ("candidates" if kind == "candidate" else "jobs")
    data = candidate_data if kind == "candidate" else job_data
    original = client.post(path, json=data).json()

    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeError("secret failure after deleting old relationships")

    monkeypatch.setattr(candidate_repository if kind == "candidate" else job_repository,
                        "link_named", fail)
    response = client.post(path, json=data | {"location": data["location"] + "new"})
    assert response.status_code == 500
    assert "secret" not in response.text
    assert client.get(path + "/" + data["id"]).json() == original


def test_constraints_created_on_startup(client: TestClient) -> None:
    assert constraint_names(get_driver()) >= {
        "candidate_id", "job_id", "skill_key", "location_key", "company_key", "work_mode_name"}
