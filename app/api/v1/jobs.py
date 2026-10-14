from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_job_service
from app.schemas.common import Identifier
from app.schemas.job import JobSchema
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Vacantes"])
Service = Annotated[JobService, Depends(get_job_service)]


@router.post("", response_model=JobSchema, status_code=201,
             responses={200: {"model": JobSchema, "description": "Vacante actualizada"}},
             summary="Crear o actualizar una vacante")
def upsert_job(payload: JobSchema, response: Response, service: Service) -> JobSchema:
    job, created = service.upsert(payload.to_domain())
    response.status_code = 201 if created else 200
    return JobSchema.from_domain(job)


@router.get("/{id}", response_model=JobSchema, summary="Consultar una vacante")
def get_job(id: Identifier, service: Service) -> JobSchema:
    return JobSchema.from_domain(service.get(id))
