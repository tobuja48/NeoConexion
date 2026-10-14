from neo4j import Driver

CONSTRAINTS = (
    "CREATE CONSTRAINT candidate_id IF NOT EXISTS FOR (n:Candidate) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT job_id IF NOT EXISTS FOR (n:Job) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT skill_key IF NOT EXISTS FOR (n:Skill) REQUIRE n.key IS UNIQUE",
    "CREATE CONSTRAINT location_key IF NOT EXISTS FOR (n:Location) REQUIRE n.key IS UNIQUE",
    "CREATE CONSTRAINT company_key IF NOT EXISTS FOR (n:Company) REQUIRE n.key IS UNIQUE",
    "CREATE CONSTRAINT work_mode_name IF NOT EXISTS FOR (n:WorkMode) REQUIRE n.name IS UNIQUE",
)


def setup_schema(driver: Driver) -> None:
    with driver.session() as session:
        for query in CONSTRAINTS:
            session.run(query).consume()
