from dataclasses import replace

import pytest

from app.domain.matching.engine import score
from app.domain.matching.models import Candidate, Job
from app.domain.matching.normalization import key, unique_names
from app.domain.matching.weights import Weights

C = Candidate("c", "Ana", " Bogotá ", 5, ("Python", "Docker"), "remote")
J = Job("j", "ACME", "Backend", "bogotá", "remote", 3, ("python ",), ("Docker",))


def test_perfect_match() -> None:
    result = score(C, J, Weights())
    assert result.match_score == 100
    assert result.missing_skills == ()
    assert result.matching_skills == ("python", "Docker")
    assert "Experiencia suficiente (5 años vs 3 requeridos)" in result.explanations


@pytest.mark.parametrize("candidate,job,expected", [
    (replace(C, skills=()), J, 50.0),
    (replace(C, years_of_experience=1.5), J, 87.5),
    (replace(C, location="Lima"), J, 100.0),
    (replace(C, preferred_work_mode="any"), replace(J, work_mode="onsite"), 100.0),
    (replace(C, skills=()), replace(J, required_skills=(), desired_skills=()), 100.0),
    (replace(C, skills=()), replace(J, required_skills=()), 100.0),
    (replace(C, skills=("Python",)), J, 85.0),
    (replace(C, skills=("Python",)), replace(J, desired_skills=()), 100.0),
    (C, replace(J, work_mode="hybrid"), 95.0),
    (C, replace(J, work_mode="onsite", location="Lima"), 75.0),
    (replace(C, years_of_experience=0), replace(J, required_experience=0), 100.0),
])
def test_cases(candidate: Candidate, job: Job, expected: float) -> None:
    assert score(candidate, job, Weights()).match_score == expected


def test_missing_and_insufficient_explanations() -> None:
    result = score(replace(C, skills=(), years_of_experience=1), J, Weights())
    assert result.missing_skills == ("python",)
    assert any("insuficiente" in e for e in result.explanations)
    assert any("faltantes: python" in e for e in result.explanations)


def test_normalization() -> None:
    assert key(" Python ") == "python"
    assert unique_names(["Python", "python ", " Docker "]) == ("Python", "Docker")


@pytest.mark.parametrize("value", [-1, 2, float("nan"), float("inf"), 0.51])
def test_invalid_weights(value: float) -> None:
    with pytest.raises(ValueError):
        Weights(skills=value)


def test_injected_weights() -> None:
    assert score(replace(C, skills=()), J, Weights(0, 1, 0, 0)).match_score == 100
