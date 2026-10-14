from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from neo4j import Driver

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.neo4j_driver import get_driver
from app.repositories.candidate_repository import CandidateRepository
from app.services.candidate_service import CandidateService
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.domain.matching.weights import Weights

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(value: Annotated[str | None, Security(api_key_header)] = None) -> None:
    configured = get_settings().api_key.get_secret_value()
    if configured and (value is None or not compare_digest(value.encode(), configured.encode())):
        raise AppError("VALIDATION_ERROR", "API Key inválida o ausente.", 401)


def get_candidate_service(driver: Annotated[Driver, Depends(get_driver)]) -> CandidateService:
    return CandidateService(CandidateRepository(driver))


def get_job_service(driver: Annotated[Driver, Depends(get_driver)]) -> JobService:
    return JobService(JobRepository(driver))


def get_weights() -> Weights:
    return Weights()


def get_matching_service(
    candidates: Annotated[CandidateService, Depends(get_candidate_service)],
    jobs: Annotated[JobService, Depends(get_job_service)],
    weights: Annotated[Weights, Depends(get_weights)],
) -> MatchingService:
    return MatchingService(candidates, jobs, weights)
