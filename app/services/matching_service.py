from collections.abc import Callable

from app.domain.matching.engine import score
from app.domain.matching.models import Candidate, Job, MatchResult
from app.domain.matching.weights import Weights
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService

Scorer = Callable[[Candidate, Job, Weights], MatchResult]


class MatchingService:
    def __init__(self, candidates: CandidateService, jobs: JobService,
                 weights: Weights, scorer: Scorer = score) -> None:
        self.candidates, self.jobs = candidates, jobs
        self.weights, self.scorer = weights, scorer

    def for_candidate(self, entity_id: str, limit: int,
                      min_score: float) -> tuple[int, list[tuple[Job, MatchResult]]]:
        candidate = self.candidates.get(entity_id)
        pairs = [(job, self.scorer(candidate, job, self.weights))
                 for job in self.jobs.repository.for_candidate(entity_id)]
        return self._rank(pairs, limit, min_score)

    def for_job(self, entity_id: str, limit: int,
                min_score: float) -> tuple[int, list[tuple[Candidate, MatchResult]]]:
        job = self.jobs.get(entity_id)
        pairs = [(candidate, self.scorer(candidate, job, self.weights))
                 for candidate in self.candidates.repository.for_job(entity_id)]
        return self._rank(pairs, limit, min_score)

    @staticmethod
    def _rank[T: (Candidate, Job)](pairs: list[tuple[T, MatchResult]], limit: int,
                                  min_score: float) -> tuple[int, list[tuple[T, MatchResult]]]:
        eligible = [pair for pair in pairs if pair[1].match_score >= min_score]
        eligible.sort(key=lambda pair: (-pair[1].match_score, pair[0].id))
        return len(eligible), eligible[:limit]
