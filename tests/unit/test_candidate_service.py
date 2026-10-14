from unittest.mock import Mock
import pytest
from app.core.exceptions import NotFound
from app.services.candidate_service import CandidateService

def test_candidate_service_converts_absence_to_not_found():
    repo = Mock(); repo.get.return_value = None
    with pytest.raises(NotFound):
        CandidateService(repo).get("missing")
    repo.get.assert_called_once_with("missing")
