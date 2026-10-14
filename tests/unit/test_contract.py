import logging

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.dependencies import require_api_key
from app.core.config import get_settings
from app.core.exceptions import register_handlers
from app.core.logging import install_request_logging
from app.main import app
from app.schemas.candidate import CandidateSchema
from app.schemas.job import JobSchema


def test_schema_normalizes_and_deduplicates() -> None:
    candidate = CandidateSchema(id=" c ", name=" Ana ", location=" Bogotá ",
                                yearsOfExperience=1, skills=["Python", "python ", " Docker "],
                                preferredWorkMode=" ANY ")
    assert candidate.skills == ["Python", "Docker"]
    assert candidate.id == "c"
    assert candidate.preferred_work_mode == "any"
    job = JobSchema(id="j", company=" ACME ", title=" Backend ", location="Bogotá",
                    requiredExperience=0, requiredSkills=["Python", "python"],
                    desiredSkills=["PYTHON", "Docker"], workMode=" REMOTE ")
    assert job.required_skills == ["Python"]
    assert job.desired_skills == ["Docker"]
    assert job.company == "ACME"


@pytest.mark.parametrize("value", [float("inf"), float("nan"), -1])
def test_experience_is_finite_nonnegative(value: float) -> None:
    with pytest.raises(ValidationError):
        CandidateSchema(id="c", name="Ana", location="Bogotá", yearsOfExperience=value,
                        skills=[], preferredWorkMode="any")


def test_openapi_documents_success_errors_and_auth() -> None:
    schema = app.openapi()
    for entity in ["candidates", "jobs"]:
        responses = schema["paths"]["/api/v1/" + entity]["post"]["responses"]
        assert set(responses) >= {"200", "201", "404", "422", "500", "503", "401"}
    assert schema["components"]["securitySchemes"]["APIKeyHeader"]["name"] == "X-API-Key"
    assert schema["paths"]["/health"]["get"].get("security") is None


@pytest.mark.parametrize("configured,supplied,expected", [
    ("", None, 200), ("token", None, 401), ("token", "wrong", 401), ("token", "token", 200),
])
def test_optional_api_key(configured: str, supplied: str | None, expected: int,
                          monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", configured)
    monkeypatch.setenv("NEO4J_PASSWORD", "unit-test-unused")
    get_settings.cache_clear()
    local = FastAPI()
    register_handlers(local)
    install_request_logging(local)

    @local.get("/private", dependencies=[Depends(require_api_key)])
    def private() -> dict[str, bool]:
        return {"ok": True}

    try:
        with TestClient(local) as client:
            response = client.get("/private", headers={"X-API-Key": supplied} if supplied else {})
        assert response.status_code == expected
        if expected == 401:
            assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        get_settings.cache_clear()


def test_logs_and_error_do_not_contain_sensitive_data(caplog: pytest.LogCaptureFixture) -> None:
    local = FastAPI()
    register_handlers(local)
    install_request_logging(local)

    @local.get("/people/{id}")
    def fail(id: str) -> None:
        raise RuntimeError("sensitive-private-email")

    with caplog.at_level(logging.INFO, logger="neoconexion"), TestClient(local) as client:
        response = client.get("/people/sensitive-private-email", headers={"X-Request-ID": "untrusted"})
    assert response.status_code == 500
    assert "sensitive-private-email" not in response.text
    assert "sensitive-private-email" not in " ".join(r.message for r in caplog.records
                                                       if r.name == "neoconexion")
    assert response.headers["X-Request-ID"] != "untrusted"
