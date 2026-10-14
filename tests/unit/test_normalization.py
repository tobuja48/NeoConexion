from app.domain.matching.normalization import key, unique_names

def test_case_and_whitespace_share_key():
    assert key(" Python ") == key("python")
    assert unique_names(["Python", "python ", " Docker "]) == ("Python", "Docker")

def test_accents_are_not_removed():
    assert key("Bogotá") != key("Bogota")
    assert unique_names([]) == ()
