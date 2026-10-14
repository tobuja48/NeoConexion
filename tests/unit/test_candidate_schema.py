import pytest
from pydantic import ValidationError
from app.schemas.candidate import CandidateSchema

def test_registration_normalizes_skills():
    model = CandidateSchema(id="c", name="Ana", location="Bogotá", yearsOfExperience=2,
                            skills=["Python", "python "], preferredWorkMode=" ANY ")
    assert model.to_domain().skills == ("Python",)
    assert model.preferred_work_mode == "any"

def test_empty_identifier_is_rejected():
    with pytest.raises(ValidationError):
        CandidateSchema(id=" ", name="Ana", location="Bogotá", yearsOfExperience=2,
                        skills=[], preferredWorkMode="any")
