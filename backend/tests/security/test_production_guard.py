from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from tests.security_guard import (
    TestDatabaseTarget,
    UnsafeTestDatabaseError,
    assert_safe_compose_names,
    assert_safe_test_database,
)


def test_accepts_isolated_local_test_database() -> None:
    assert_safe_test_database(
        TestDatabaseTarget(
            database_url="postgresql+psycopg://dentia_test:pw@127.0.0.1:55432/dentia_test",
            app_env="test",
            confirmation="DENTIA_TEST_DATABASE_CONFIRMED",
        )
    )


@pytest.mark.parametrize(
    ("database_url", "app_env", "confirmation"),
    [
        ("postgresql+psycopg://dentia:pw@127.0.0.1:5432/dentia", "test", "DENTIA_TEST_DATABASE_CONFIRMED"),
        ("postgresql+psycopg://dentia_test:pw@dentiapro.com:5432/dentia_test", "test", "DENTIA_TEST_DATABASE_CONFIRMED"),
        ("postgresql+psycopg://dentia_test:pw@db.internal:5432/dentia_test", "test", "DENTIA_TEST_DATABASE_CONFIRMED"),
        ("postgresql+psycopg://dentia_test:pw@127.0.0.1:55432/dentia_test", "production", "DENTIA_TEST_DATABASE_CONFIRMED"),
        ("postgresql+psycopg://dentia_test:pw@127.0.0.1:55432/dentia_test", "test", None),
    ],
)
def test_rejects_unsafe_database_targets(database_url: str, app_env: str, confirmation: str | None) -> None:
    with pytest.raises(UnsafeTestDatabaseError):
        assert_safe_test_database(
            TestDatabaseTarget(
                database_url=database_url,
                app_env=app_env,
                confirmation=confirmation,
            )
        )


def test_rejects_production_compose_names() -> None:
    with pytest.raises(UnsafeTestDatabaseError):
        assert_safe_compose_names(
            project="dentia",
            service="dentia-db",
            volume="dentia_dentia_db_data",
        )


def test_accepts_test_compose_names() -> None:
    assert_safe_compose_names(
        project="dentia-test",
        service="dentia-test-db",
        volume="dentia-test_dentia_test_db_data",
    )


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "local",
        "database_url": "postgresql+psycopg://dentia_test:pw@127.0.0.1:55432/dentia_test",
        "jwt_secret": "FictionalJWTSecretForProductionGuardChecks2026",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize("value", [0, 6])
def test_rejects_unsafe_refresh_race_grace(value: int) -> None:
    with pytest.raises(
        ValidationError,
        match="REFRESH_TOKEN_RACE_GRACE_SECONDS must be between 1 and 5",
    ):
        _settings(refresh_token_race_grace_seconds=value)


@pytest.mark.parametrize("value", [1, 2, 5])
def test_accepts_bounded_refresh_race_grace(value: int) -> None:
    configured = _settings(refresh_token_race_grace_seconds=value)
    assert configured.refresh_token_race_grace_seconds == value
