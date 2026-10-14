from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_matching_service
from app.schemas.common import Identifier
from app.schemas.recommendation import (
    CandidateRecommendation, CandidateRecommendations, JobCandidates, JobRecommendation, MatchSchema,
)
from app.services.matching_service import MatchingService

router = APIRouter(tags=["Recomendaciones"])
Service = Annotated[MatchingService, Depends(get_matching_service)]
Limit = Annotated[int, Query(ge=1, le=50, description="Máximo de resultados")]
MinScore = Annotated[float, Query(alias="minScore", ge=0, le=100, allow_inf_nan=False)]


@router.get("/candidates/{id}/recommendations", response_model=CandidateRecommendations,
            summary="Recomendar vacantes para un candidato",
            description="Prefiltra por habilidades compartidas y ordena por score descendente e ID ascendente.")
def recommend_jobs(id: Identifier, service: Service,
                    limit: Limit = 10, min_score: MinScore = 0) -> CandidateRecommendations:
    total, pairs = service.for_candidate(id, limit, min_score)
    return CandidateRecommendations(candidate_id=id, total=total, recommendations=[
        JobRecommendation(job_id=job.id, title=job.title, company=job.company,
                          **MatchSchema.from_result(result).model_dump()) for job, result in pairs
    ])


@router.get("/jobs/{id}/candidates", response_model=JobCandidates,
            summary="Recomendar candidatos para una vacante",
            description="Prefiltra por habilidades compartidas y ordena por score descendente e ID ascendente.")
def recommend_candidates(id: Identifier, service: Service,
                          limit: Limit = 10, min_score: MinScore = 0) -> JobCandidates:
    total, pairs = service.for_job(id, limit, min_score)
    return JobCandidates(job_id=id, total=total, recommendations=[
        CandidateRecommendation(candidate_id=candidate.id, name=candidate.name,
                                **MatchSchema.from_result(result).model_dump())
        for candidate, result in pairs
    ])
