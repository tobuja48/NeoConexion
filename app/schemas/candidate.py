from pydantic import Field, field_validator

from app.domain.matching.models import Candidate
from app.domain.matching.normalization import key, unique_names
from app.schemas.common import Identifier, Name, NonNegative, PreferredWorkMode, PublicModel, Skill


class CandidateSchema(PublicModel):
    id: Identifier = Field(examples=["c-123"])
    name: Name = Field(examples=["Ana Pérez"])
    location: Name = Field(examples=["Bogotá"])
    years_of_experience: NonNegative = Field(examples=[5])
    skills: list[Skill] = Field(max_length=100, examples=[["Python", "Docker"]])
    preferred_work_mode: PreferredWorkMode = Field(examples=["remote"])
    expected_salary: NonNegative | None = Field(default=None, examples=[5000000])

    @field_validator("skills")
    @classmethod
    def deduplicate(cls, value: list[str]) -> list[str]:
        return list(unique_names(value))

    @field_validator("preferred_work_mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: object) -> object:
        return key(value) if isinstance(value, str) else value

    def to_domain(self) -> Candidate:
        return Candidate(self.id, self.name, self.location, self.years_of_experience,
                         tuple(self.skills), self.preferred_work_mode.value, self.expected_salary)

    @classmethod
    def from_domain(cls, value: Candidate) -> "CandidateSchema":
        return cls(id=value.id, name=value.name, location=value.location,
                   years_of_experience=value.years_of_experience, skills=list(value.skills),
                   preferred_work_mode=value.preferred_work_mode, expected_salary=value.expected_salary)
