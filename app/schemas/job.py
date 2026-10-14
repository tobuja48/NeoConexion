from typing import Self

from pydantic import Field, field_validator, model_validator

from app.domain.matching.models import Job
from app.domain.matching.normalization import key, unique_names
from app.schemas.common import Identifier, Name, NonNegative, PublicModel, Skill, WorkMode


class JobSchema(PublicModel):
    id: Identifier = Field(examples=["j-456"])
    company: Name = Field(examples=["ACME"])
    title: Name = Field(examples=["Desarrollador Backend"])
    description: str | None = Field(default=None, max_length=5000, examples=["API en Python"])
    location: Name = Field(examples=["Bogotá"])
    work_mode: WorkMode = Field(examples=["remote"])
    required_experience: NonNegative = Field(examples=[3])
    required_skills: list[Skill] = Field(max_length=100, examples=[["Python"]])
    desired_skills: list[Skill] = Field(default_factory=list, max_length=100, examples=[["Docker"]])

    @field_validator("required_skills", "desired_skills")
    @classmethod
    def deduplicate(cls, value: list[str]) -> list[str]:
        return list(unique_names(value))

    @field_validator("work_mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: object) -> object:
        return key(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def mandatory_takes_precedence(self) -> Self:
        required = {key(s) for s in self.required_skills}
        self.desired_skills = [s for s in self.desired_skills if key(s) not in required]
        return self

    def to_domain(self) -> Job:
        return Job(self.id, self.company, self.title, self.location, self.work_mode.value,
                   self.required_experience, tuple(self.required_skills),
                   tuple(self.desired_skills), self.description)

    @classmethod
    def from_domain(cls, value: Job) -> "JobSchema":
        return cls(id=value.id, company=value.company, title=value.title, description=value.description,
                   location=value.location, work_mode=value.work_mode,
                   required_experience=value.required_experience,
                   required_skills=list(value.required_skills), desired_skills=list(value.desired_skills))
