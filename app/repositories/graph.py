from typing import Any
from uuid import uuid4

from neo4j import ManagedTransaction

from app.domain.matching.normalization import display, key

CANDIDATE_PROJECTION = """c { .id, .name, .yearsOfExperience, .expectedSalary,
 location: head([(c)-[:LIVES_IN]->(l:Location) | l.name]),
 preferredWorkMode: head([(c)-[:PREFERS]->(m:WorkMode) | m.name]),
 skills: [(c)-[:HAS_SKILL]->(s:Skill) | s.name] }"""

JOB_PROJECTION = """j { .id, .title, .description, .requiredExperience,
 company: head([(co:Company)-[:POSTED]->(j) | co.name]),
 location: head([(j)-[:LOCATED_IN]->(l:Location) | l.name]),
 workMode: head([(j)-[:OFFERS_MODE]->(m:WorkMode) | m.name]),
 requiredSkills: [(j)-[:REQUIRES_SKILL]->(s:Skill) | s.name],
 desiredSkills: [(j)-[:DESIRES_SKILL]->(s:Skill) | s.name] }"""


def merge_entity(tx: ManagedTransaction, label: str, entity_id: str,
                 properties: dict[str, Any]) -> bool:
    """Acquire a node lock and determine creation atomically, including concurrent upserts."""
    assert label in {"Candidate", "Job"}
    token = uuid4().hex
    record = tx.run(
        f"MERGE (n:{label} {{id: $id}}) ON CREATE SET n._created = $token "
        "SET n += $properties, n._lock = $token "
        "WITH n, coalesce(n._created = $token, false) AS created "
        "REMOVE n._created, n._lock RETURN created",
        id=entity_id, token=token, properties=properties,
    ).single(strict=True)
    return bool(record["created"])


def link_named(tx: ManagedTransaction, label: str, entity_id: str,
               relation: str, target: str, names: tuple[str, ...]) -> None:
    allowed = {("Candidate", "HAS_SKILL", "Skill"), ("Candidate", "LIVES_IN", "Location"),
               ("Job", "REQUIRES_SKILL", "Skill"), ("Job", "DESIRES_SKILL", "Skill"),
               ("Job", "LOCATED_IN", "Location")}
    assert (label, relation, target) in allowed
    tx.run(
        f"MATCH (n:{label} {{id: $id}}) UNWIND $names AS item "
        f"MERGE (t:{target} {{key: item.key}}) ON CREATE SET t.name = item.name "
        f"MERGE (n)-[:{relation}]->(t)",
        id=entity_id, names=[{"key": key(n), "name": display(n)} for n in sorted(names, key=key)],
    ).consume()
