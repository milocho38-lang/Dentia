from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


class UnsafeTestDatabaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class TestDatabaseTarget:
    __test__ = False

    database_url: str
    app_env: str | None
    confirmation: str | None


PRODUCTION_HOST_FRAGMENTS = {
    "dentiapro.com",
    "dentia.app",
    "dentia.co",
}

PRODUCTION_CONTAINER_NAMES = {
    "dentia-db",
}

PRODUCTION_VOLUME_NAMES = {
    "dentia_dentia_db_data",
}


def _redact_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.password:
        return database_url
    netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
    return parsed._replace(netloc=netloc).geturl()


def assert_safe_test_database(target: TestDatabaseTarget) -> None:
    parsed = urlparse(target.database_url)
    db_name = parsed.path.lstrip("/")
    host = parsed.hostname or ""

    failures: list[str] = []
    if target.app_env != "test":
        failures.append("APP_ENV must be exactly 'test'.")
    if target.confirmation != "DENTIA_TEST_DATABASE_CONFIRMED":
        failures.append("DENTIA_TEST_DATABASE_CONFIRMATION is missing or invalid.")
    if parsed.scheme not in {"postgresql", "postgresql+psycopg"}:
        failures.append("Only PostgreSQL test databases are allowed.")
    if not db_name or "test" not in db_name.casefold():
        failures.append("Database name must contain 'test'.")
    if db_name == "dentia":
        failures.append("Database name must not be the production/development database 'dentia'.")
    if any(fragment in host.casefold() for fragment in PRODUCTION_HOST_FRAGMENTS):
        failures.append("Database host looks production-like.")
    if host not in {"localhost", "127.0.0.1", "::1", "dentia-test-db"}:
        failures.append("Database host must be local or the isolated dentia-test-db service.")
    if "env.production" in target.database_url.casefold():
        failures.append("Production env references are not allowed.")

    if failures:
        redacted = _redact_url(target.database_url)
        raise UnsafeTestDatabaseError(
            "Refusing to use unsafe test database target "
            f"{redacted}: " + " ".join(failures)
        )


def assert_safe_compose_names(*, project: str, service: str, volume: str) -> None:
    failures: list[str] = []
    if project == "dentia":
        failures.append("Compose project must not be 'dentia'.")
    if service in PRODUCTION_CONTAINER_NAMES:
        failures.append("Compose service/container must not target dentia-db.")
    if volume in PRODUCTION_VOLUME_NAMES:
        failures.append("Compose volume must not target production DB volume.")
    if "test" not in project or "test" not in service or "test" not in volume:
        failures.append("Compose project, service and volume names must include 'test'.")
    if failures:
        raise UnsafeTestDatabaseError(" ".join(failures))
