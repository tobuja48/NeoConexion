import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("direction", ["jobs", "candidates"])
def test_ranking_filters_both_directions(client: TestClient, candidate_data: dict,
                                       job_data: dict, prefix: str, direction: str) -> None:
    if direction == "jobs":
        assert client.post("/api/v1/candidates", json=candidate_data).status_code == 201
        path = f"/api/v1/candidates/{candidate_data['id']}/recommendations"
        base, result_id = job_data, "jobId"
    else:
        assert client.post("/api/v1/jobs", json=job_data).status_code == 201
        path = f"/api/v1/jobs/{job_data['id']}/candidates"
        base, result_id = candidate_data, "candidateId"
    for suffix in ["b", "a", "low", "excluded"]:
        data = base | {"id": prefix + suffix}
        if suffix == "low":
            data["requiredExperience" if direction == "jobs" else "yearsOfExperience"] = (
                10 if direction == "jobs" else 1.5)
        if suffix == "excluded":
            data["requiredSkills" if direction == "jobs" else "skills"] = [prefix + "Rust"]
            if direction == "jobs":
                data["desiredSkills"] = []
        response = client.post("/api/v1/" + direction, json=data)
        assert response.status_code == 201, response.text
    result = client.get(path).json()
    assert result["total"] == 3
    assert [r[result_id] for r in result["recommendations"]] == [prefix + s for s in ["a", "b", "low"]]
    assert [r["matchScore"] for r in result["recommendations"]] == [100, 100, 87.5]
    assert result["recommendations"][0]["breakdown"] == {
        "skills": 100, "experience": 100, "location": 100, "workMode": 100}
    assert result["recommendations"][0]["missingSkills"] == []
    limited = client.get(path, params={"limit": 1, "minScore": 100}).json()
    assert limited["total"] == 2
    assert len(limited["recommendations"]) == 1
    assert limited["recommendations"][0][result_id] == prefix + "a"
    assert client.get(path, params={"minScore": 87.5}).json()["total"] == 3
    for params in [{"limit": 0}, {"limit": 51}, {"minScore": -1}, {"minScore": 101},
                   {"minScore": "nan"}, {"limit": "abc"}]:
        response = client.get(path, params=params)
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_empty_and_missing(client: TestClient, candidate_data: dict, job_data: dict, prefix: str) -> None:
    candidate_data["skills"] = []
    job_data.update(requiredSkills=[], desiredSkills=[])
    assert client.post("/api/v1/candidates", json=candidate_data).status_code == 201
    assert client.post("/api/v1/jobs", json=job_data).status_code == 201
    for path in [f"/api/v1/candidates/{candidate_data['id']}/recommendations",
                 f"/api/v1/jobs/{job_data['id']}/candidates"]:
        result = client.get(path).json()
        assert result["total"] == 0
        assert result["recommendations"] == []
    for path in [f"/api/v1/candidates/{prefix}missing/recommendations",
                 f"/api/v1/jobs/{prefix}missing/candidates"]:
        assert client.get(path).status_code == 404


def test_normalization_and_desired_only_prefilter(client: TestClient, candidate_data: dict,
                                                job_data: dict, prefix: str) -> None:
    candidate_data["skills"] = [" " + prefix.upper() + "DOCKER "]
    assert client.post("/api/v1/candidates", json=candidate_data).status_code == 201
    assert client.post("/api/v1/jobs", json=job_data).status_code == 201
    result = client.get(f"/api/v1/candidates/{candidate_data['id']}/recommendations").json()
    assert result["total"] == 1
    assert result["recommendations"][0]["matchScore"] == 65.0
    assert result["recommendations"][0]["missingSkills"] == [prefix + "Python"]
