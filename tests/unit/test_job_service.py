from unittest.mock import Mock
import pytest
from app.core.exceptions import NotFound
from app.services.job_service import JobService

def test_job_service_converts_absence_to_not_found():
    repo = Mock(); repo.get.return_value = None
    with pytest.raises(NotFound):
        JobService(repo).get("missing")
