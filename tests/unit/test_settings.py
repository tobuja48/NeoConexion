import pytest
from pydantic import ValidationError
from app.core.config import Settings

def test_secret_is_not_printed():
    config = Settings(_env_file=None, neo4j_password="do-not-print", api_key="private")
    assert "do-not-print" not in repr(config)
    assert config.api_key.get_secret_value() == "private"

def test_invalid_log_level():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, neo4j_password="local", log_level="everything")
