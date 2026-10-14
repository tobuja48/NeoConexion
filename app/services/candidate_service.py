from app.core.exceptions import NotFound
from app.domain.matching.models import Candidate
from app.repositories.candidate_repository import CandidateRepository


class CandidateService:
    def __init__(self, repository: CandidateRepository) -> None:
        self.repository = repository

    def get(self, entity_id: str) -> Candidate:
        candidate = self.repository.get(entity_id)
        if candidate is None:
            raise NotFound("Candidato")
        return candidate

    def upsert(self, candidate: Candidate) -> tuple[Candidate, bool]:
        return self.repository.upsert(candidate)
