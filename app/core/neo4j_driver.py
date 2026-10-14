from threading import Lock

from neo4j import Driver, GraphDatabase

from app.core.config import get_settings

_driver: Driver | None = None
_lock = Lock()


def get_driver() -> Driver:
    global _driver
    with _lock:
        if _driver is None:
            settings = get_settings()
            _driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
                connection_timeout=5,
                connection_acquisition_timeout=10,
                max_transaction_retry_time=10,
            )
        return _driver


def close_driver() -> None:
    global _driver
    with _lock:
        if _driver is not None:
            _driver.close()
            _driver = None
