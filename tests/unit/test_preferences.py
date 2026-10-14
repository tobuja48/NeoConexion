from app.domain.matching.preferences import location_score, work_mode_score

def test_remote_does_not_require_same_city():
    assert location_score("Lima", "Bogotá", "remote") == 100
    assert location_score("Lima", "Bogotá", "onsite") == 0

def test_modes_are_normalized():
    assert work_mode_score(" ANY ", "onsite") == 100
    assert work_mode_score("remote", "hybrid") == 50
    assert work_mode_score("remote", "onsite") == 0
