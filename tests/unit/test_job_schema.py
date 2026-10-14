from app.schemas.job import JobSchema

def test_required_skill_takes_precedence():
    job = JobSchema(id="j", company="ACME", title="Backend", location="Bogotá", workMode=" REMOTE ",
                    requiredExperience=0, requiredSkills=["Python"], desiredSkills=["python", "Docker"])
    assert job.to_domain().desired_skills == ("Docker",)
    assert job.work_mode == "remote"
