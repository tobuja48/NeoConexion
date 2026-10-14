import pytest

pytestmark = pytest.mark.integration


def test_diagnosis_explains_missing_required_skills(client, candidate_data, job_data, prefix):
    job_data["requiredSkills"].append(prefix + "SQL")
    assert client.post("/api/v1/candidates", json=candidate_data).status_code == 201
    assert client.post("/api/v1/jobs", json=job_data).status_code == 201
    response = client.get(f"/api/v1/candidates/{candidate_data['id']}/jobs/{job_data['id']}/diagnosis")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["missingSkills"] == [prefix + "SQL"]
    assert data["passesSkillPrefilter"] is True
    assert data["breakdown"]["skills"] == 65
    assert data["matchScore"] == 82.5
    assert data["explanations"]
    assert data["candidateId"] == candidate_data["id"]


def test_diagnosis_works_even_without_graph_prefilter_match(client, candidate_data, job_data, prefix):
    candidate_data["skills"] = []
    assert client.post("/api/v1/candidates", json=candidate_data).status_code == 201
    assert client.post("/api/v1/jobs", json=job_data).status_code == 201
    data = client.get(f"/api/v1/candidates/{candidate_data['id']}/jobs/{job_data['id']}/diagnosis").json()
    assert data["passesSkillPrefilter"] is False
    assert data["missingSkills"] == job_data["requiredSkills"]
    assert data["matchingSkills"] == []
    assert data["breakdown"]["skills"] == 0
    assert client.get(f"/api/v1/candidates/{candidate_data['id']}/recommendations").json()["total"] == 0


@pytest.mark.parametrize("missing", ["candidate", "job"])
def test_diagnosis_reports_missing_entities(client, candidate_data, job_data, prefix, missing):
    assert client.post("/api/v1/candidates", json=candidate_data).status_code == 201
    assert client.post("/api/v1/jobs", json=job_data).status_code == 201
    candidate_id = prefix + "absent" if missing == "candidate" else candidate_data["id"]
    job_id = prefix + "absent" if missing == "job" else job_data["id"]
    response = client.get(f"/api/v1/candidates/{candidate_id}/jobs/{job_id}/diagnosis")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
