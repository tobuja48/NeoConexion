from pydantic import Field

from app.domain.matching.models import MatchResult
from app.schemas.common import PublicModel


class BreakdownSchema(PublicModel):
    skills: float = Field(ge=0, le=100)
    experience: float = Field(ge=0, le=100)
    location: float = Field(ge=0, le=100)
    work_mode: float = Field(ge=0, le=100)


class MatchSchema(PublicModel):
    match_score: float = Field(ge=0, le=100, examples=[87.5])
    breakdown: BreakdownSchema
    matching_skills: list[str]
    missing_skills: list[str]
    explanations: list[str]

    @classmethod
    def from_result(cls, result: MatchResult) -> "MatchSchema":
        b = result.breakdown
        return cls(match_score=result.match_score,
                   breakdown=BreakdownSchema(skills=b.skills, experience=b.experience,
                                              location=b.location, work_mode=b.work_mode),
                   matching_skills=list(result.matching_skills),
                   missing_skills=list(result.missing_skills), explanations=list(result.explanations))


class JobRecommendation(MatchSchema):
    job_id: str
    title: str
    company: str


class CandidateRecommendation(MatchSchema):
    candidate_id: str
    name: str


class CandidateRecommendations(PublicModel):
    candidate_id: str
    total: int = Field(ge=0, description="Resultados que cumplen minScore antes de aplicar limit")
    recommendations: list[JobRecommendation]


class JobCandidates(PublicModel):
    job_id: str
    total: int = Field(ge=0, description="Resultados que cumplen minScore antes de aplicar limit")
    recommendations: list[CandidateRecommendation]


class SkillDiagnosis(MatchSchema):
    candidate_id: str
    job_id: str
    passes_skill_prefilter: bool = Field(description="Comparte al menos una habilidad requerida o deseable")
