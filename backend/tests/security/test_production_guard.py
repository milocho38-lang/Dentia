from __future__ import annotations

import pytest

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
