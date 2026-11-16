from neo4j import Driver

from app.domain.matching.models import Candidate, Job
from app.repositories.candidate_repository import candidate_from_record
from app.repositories.graph import CANDIDATE_PROJECTION, JOB_PROJECTION
from app.repositories.job_repository import job_from_record


class MatchingRepository:
    """Read the base entity and its distinct matches in one managed transaction."""

    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    def for_candidate(self, entity_id: str) -> tuple[Candidate, list[Job]] | None:
        query = (
            "MATCH (c:Candidate {id: $id}) "
            "OPTIONAL MATCH (c)-[:HAS_SKILL]->(:Skill)"
            "<-[:REQUIRES_SKILL|DESIRES_SKILL]-(j:Job) "
            "WITH c, collect(DISTINCT j) AS related RETURN "
            + CANDIDATE_PROJECTION + " AS candidate, "
            "[j IN related | " + JOB_PROJECTION + "] AS jobs"
        )
        with self.driver.session() as session:
            record = session.execute_read(lambda tx: tx.run(query, id=entity_id).single())
        if record is None:
            return None
        return candidate_from_record(record["candidate"]), [job_from_record(j) for j in record["jobs"]]

    def for_job(self, entity_id: str) -> tuple[Job, list[Candidate]] | None:
        query = (
            "MATCH (j:Job {id: $id}) "
            "OPTIONAL MATCH (j)-[:REQUIRES_SKILL|DESIRES_SKILL]->(:Skill)"
            "<-[:HAS_SKILL]-(c:Candidate) "
            "WITH j, collect(DISTINCT c) AS related RETURN "
            + JOB_PROJECTION + " AS job, "
            "[c IN related | " + CANDIDATE_PROJECTION + "] AS candidates"
        )
        with self.driver.session() as session:
            record = session.execute_read(lambda tx: tx.run(query, id=entity_id).single())
        if record is None:
            return None
        return job_from_record(record["job"]), [candidate_from_record(c) for c in record["candidates"]]
