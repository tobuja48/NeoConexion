from app.core.exceptions import NotFound
from app.domain.matching.models import Job
from app.repositories.job_repository import JobRepository


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def get(self, entity_id: str) -> Job:
        job = self.repository.get(entity_id)
        if job is None:
            raise NotFound("Vacante")
        return job

    def upsert(self, job: Job) -> tuple[Job, bool]:
        return self.repository.upsert(job)


    def search(self, query: str, location: str, work_mode: str,
               limit: int, offset: int) -> tuple[int, list[Job]]:
        return self.repository.search(query, location, work_mode, limit, offset)
