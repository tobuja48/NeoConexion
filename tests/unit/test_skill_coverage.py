from app.domain.matching.skills import skill_coverage

def test_weighted_coverage_and_missing():
    result = skill_coverage(("Python",), ("Python", "SQL"), ("Docker",))
    assert result.score == 35
    assert result.missing == ("SQL",)

def test_no_mandatory_skills_and_overlap():
    assert skill_coverage((), (), ("Docker",)).score == 100
    assert skill_coverage(("Python",), ("python",), ("PYTHON",)).score == 100
