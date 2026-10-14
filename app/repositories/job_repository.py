from typing import Any

from neo4j import Driver, ManagedTransaction

from app.domain.matching.models import Job
from app.domain.matching.normalization import key
from app.repositories.graph import JOB_PROJECTION, link_named, merge_entity


def job_from_record(data: dict[str, Any]) -> Job:
    return Job(data["id"], data["company"], data["title"], data["location"], data["workMode"],
               data["requiredExperience"], tuple(sorted(data["requiredSkills"], key=str.lower)),
               tuple(sorted(data["desiredSkills"], key=str.lower)), data.get("description"))


class JobRepository:
    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    def get(self, entity_id: str) -> Job | None:
        with self.driver.session() as session:
            record = session.execute_read(lambda tx: tx.run(
                "MATCH (j:Job {id: $id}) RETURN " + JOB_PROJECTION + " AS data",
                id=entity_id).single())
        return job_from_record(record["data"]) if record else None

    def upsert(self, job: Job) -> tuple[Job, bool]:
        with self.driver.session() as session:
            return session.execute_write(self._write, job)

    @staticmethod
    def _write(tx: ManagedTransaction, job: Job) -> tuple[Job, bool]:
        created = merge_entity(tx, "Job", job.id, {
            "title": job.title, "description": job.description,
            "requiredExperience": job.required_experience,
        })
        tx.run("MATCH (j:Job {id: $id}) "
               "OPTIONAL MATCH (j)-[r:REQUIRES_SKILL|DESIRES_SKILL|LOCATED_IN|OFFERS_MODE]->() "
               "DELETE r", id=job.id).consume()
        tx.run("MATCH (j:Job {id: $id}) OPTIONAL MATCH (:Company)-[r:POSTED]->(j) DELETE r",
               id=job.id).consume()
        link_named(tx, "Job", job.id, "REQUIRES_SKILL", "Skill", job.required_skills)
        link_named(tx, "Job", job.id, "DESIRES_SKILL", "Skill", job.desired_skills)
        link_named(tx, "Job", job.id, "LOCATED_IN", "Location", (job.location,))
        tx.run("MATCH (j:Job {id: $id}) MERGE (m:WorkMode {name: $mode}) "
               "MERGE (j)-[:OFFERS_MODE]->(m) MERGE (co:Company {key: $company_key}) "
               "ON CREATE SET co.name = $company MERGE (co)-[:POSTED]->(j)",
               id=job.id, mode=job.work_mode, company_key=key(job.company), company=job.company).consume()
        record = tx.run("MATCH (j:Job {id: $id}) RETURN " + JOB_PROJECTION + " AS data",
                        id=job.id).single(strict=True)
        return job_from_record(record["data"]), created

    def for_candidate(self, candidate_id: str) -> list[Job]:
        with self.driver.session() as session:
            records = session.execute_read(lambda tx: list(tx.run(
                "MATCH (c:Candidate {id: $id})-[:HAS_SKILL]->(:Skill)"
                "<-[:REQUIRES_SKILL|DESIRES_SKILL]-(j:Job) WITH DISTINCT j RETURN " +
                JOB_PROJECTION + " AS data", id=candidate_id)))
        return [job_from_record(r["data"]) for r in records]
