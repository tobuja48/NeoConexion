"""Scoped integration cleanup; never clears application entities outside the test prefix."""
from neo4j import Driver


def cleanup_test_data(driver: Driver, prefix: str) -> None:
    if not prefix.startswith("test-neoconexion-") or len(prefix) < 25:
        raise ValueError("Unsafe test prefix")
    with driver.session() as session:
        session.run("MATCH (n) WHERE (n:Candidate OR n:Job) AND n.id STARTS WITH $prefix "
                    "DETACH DELETE n", prefix=prefix).consume()
        session.run("MATCH (n) WHERE (n:Skill OR n:Location OR n:Company) "
                    "AND n.key STARTS WITH $prefix AND NOT (n)--() DELETE n",
                    prefix=prefix).consume()


def entity_count(driver: Driver, entity_id: str) -> int:
    with driver.session() as session:
        return session.run("MATCH (n) WHERE (n:Candidate OR n:Job) AND n.id = $id "
                           "RETURN count(n) AS count", id=entity_id).single(strict=True)["count"]


def relation_count(driver: Driver, entity_id: str) -> int:
    with driver.session() as session:
        return session.run("MATCH (n)-[r]-() WHERE (n:Candidate OR n:Job) AND n.id = $id "
                           "RETURN count(r) AS count", id=entity_id).single(strict=True)["count"]


def constraint_names(driver: Driver) -> set[str]:
    with driver.session() as session:
        return {record["name"] for record in session.run("SHOW CONSTRAINTS YIELD name RETURN name")}
