from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_candidate_service
from app.schemas.candidate import CandidateSchema
from app.schemas.common import Identifier
from app.services.candidate_service import CandidateService

router = APIRouter(prefix="/candidates", tags=["Candidatos"])
Service = Annotated[CandidateService, Depends(get_candidate_service)]


@router.post("", response_model=CandidateSchema, status_code=201,
             responses={200: {"model": CandidateSchema, "description": "Candidato actualizado"}},
             summary="Crear o actualizar un candidato")
def upsert_candidate(payload: CandidateSchema, response: Response, service: Service) -> CandidateSchema:
    candidate, created = service.upsert(payload.to_domain())
    response.status_code = 201 if created else 200
    return CandidateSchema.from_domain(candidate)


@router.get("/{id}", response_model=CandidateSchema, summary="Consultar un candidato")
def get_candidate(id: Identifier, service: Service) -> CandidateSchema:
    return CandidateSchema.from_domain(service.get(id))
