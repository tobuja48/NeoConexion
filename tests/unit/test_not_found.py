from app.core.exceptions import NotFound

def test_not_found_has_safe_public_contract():
    error = NotFound("Candidato")
    assert error.status == 404
    assert error.code == "NOT_FOUND"
    assert error.details is None
