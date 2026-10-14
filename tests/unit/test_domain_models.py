import pytest
from dataclasses import FrozenInstanceError
from app.domain.matching.models import Candidate

def test_candidate_is_immutable():
    candidate = Candidate("c", "Ana", "Bogotá", 2, ("Python",), "any")
    with pytest.raises(FrozenInstanceError):
        candidate.name = "Changed"
    assert candidate.expected_salary is None
