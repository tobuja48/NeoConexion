from typing import Annotated

from fastapi import APIRouter, Depends, Response, Query

from app.api.dependencies import get_job_service
from app.schemas.common import Identifier, WorkMode
from app.schemas.catalog import JobCatalog
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


@router.get("", response_model=JobCatalog, summary="Buscar y filtrar ofertas laborales",
            description="Busca texto en título, descripción o empresa; filtra ciudad exacta y modalidad. Orden por ID.")
def search_jobs(service: Service,
                q: Annotated[str, Query(max_length=200)] = "",
                location: Annotated[str, Query(max_length=200)] = "",
                work_mode: Annotated[WorkMode | None, Query(alias="workMode")] = None,
                limit: Annotated[int, Query(ge=1, le=50)] = 10,
                offset: Annotated[int, Query(ge=0)] = 0) -> JobCatalog:
    total, jobs = service.search(q, location, work_mode.value if work_mode else "", limit, offset)
    return JobCatalog(total=total, limit=limit, offset=offset,
                      items=[JobSchema.from_domain(job) for job in jobs])
