from typing import Any

from neo4j import Driver, ManagedTransaction

from app.domain.matching.models import Candidate
from app.repositories.graph import CANDIDATE_PROJECTION, link_named, merge_entity


def candidate_from_record(data: dict[str, Any]) -> Candidate:
    return Candidate(data["id"], data["name"], data["location"], data["yearsOfExperience"],
                     tuple(sorted(data["skills"], key=str.lower)), data["preferredWorkMode"],
                     data.get("expectedSalary"))


class CandidateRepository:
    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    def get(self, entity_id: str) -> Candidate | None:
        with self.driver.session() as session:
            record = session.execute_read(lambda tx: tx.run(
                "MATCH (c:Candidate {id: $id}) RETURN " + CANDIDATE_PROJECTION + " AS data",
                id=entity_id).single())
        return candidate_from_record(record["data"]) if record else None

    def upsert(self, candidate: Candidate) -> tuple[Candidate, bool]:
        with self.driver.session() as session:
            return session.execute_write(self._write, candidate)

    @staticmethod
    def _write(tx: ManagedTransaction, candidate: Candidate) -> tuple[Candidate, bool]:
        created = merge_entity(tx, "Candidate", candidate.id, {
            "name": candidate.name, "yearsOfExperience": candidate.years_of_experience,
            "expectedSalary": candidate.expected_salary,
        })
        tx.run("MATCH (c:Candidate {id: $id}) "
               "OPTIONAL MATCH (c)-[r:HAS_SKILL|LIVES_IN|PREFERS]->() DELETE r",
               id=candidate.id).consume()
        link_named(tx, "Candidate", candidate.id, "HAS_SKILL", "Skill", candidate.skills)
        link_named(tx, "Candidate", candidate.id, "LIVES_IN", "Location", (candidate.location,))
        tx.run("MATCH (c:Candidate {id: $id}) MERGE (m:WorkMode {name: $mode}) "
               "MERGE (c)-[:PREFERS]->(m)", id=candidate.id,
               mode=candidate.preferred_work_mode).consume()
        record = tx.run("MATCH (c:Candidate {id: $id}) RETURN " + CANDIDATE_PROJECTION + " AS data",
                        id=candidate.id).single(strict=True)
        return candidate_from_record(record["data"]), created

    def for_job(self, job_id: str) -> list[Candidate]:
        with self.driver.session() as session:
            records = session.execute_read(lambda tx: list(tx.run(
                "MATCH (j:Job {id: $id})-[:REQUIRES_SKILL|DESIRES_SKILL]->(:Skill)"
                "<-[:HAS_SKILL]-(c:Candidate) WITH DISTINCT c RETURN " +
                CANDIDATE_PROJECTION + " AS data", id=job_id)))
        return [candidate_from_record(r["data"]) for r in records]
