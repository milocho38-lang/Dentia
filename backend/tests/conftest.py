from __future__ import annotations

import asyncio
import os
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from tests.security_guard import TestDatabaseTarget, assert_safe_test_database


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "dentia-test-secret-that-is-long-enough-for-local-tests")
os.environ.setdefault("DENTIA_TEST_DATABASE_CONFIRMATION", "DENTIA_TEST_DATABASE_CONFIRMED")
os.environ.setdefault("CONSENT_ACCEPTANCE_ENABLED", "true")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
assert_safe_test_database(
    TestDatabaseTarget(
        database_url=DATABASE_URL,
        app_env=os.environ.get("APP_ENV"),
        confirmation=os.environ.get("DENTIA_TEST_DATABASE_CONFIRMATION"),
    )
)

TEST_STORAGE_ROOT = Path(os.environ.get("DENTIA_TEST_STORAGE_ROOT", "/tmp/dentia-security-storage")).resolve()
os.environ.setdefault("BRANDING_STORAGE_DIR", str(TEST_STORAGE_ROOT / "branding"))
os.environ.setdefault("CONSENT_FINAL_STORAGE_DIR", str(TEST_STORAGE_ROOT / "consents"))

from app.main import create_app  # noqa: E402
from app.database.session import get_db  # noqa: E402
from tests.factories import build_security_world  # noqa: E402


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _truncate_database() -> None:
    with engine.begin() as connection:
        table_names = connection.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename <> 'alembic_version'
                """
            )
        ).scalars().all()
        if table_names:
            quoted = ", ".join(f'"{name}"' for name in table_names)
            connection.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    _truncate_database()
    TEST_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    yield
    _truncate_database()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app():
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    application.dependency_overrides[get_db] = override_get_db
    return application


class ApiClient:
    def __init__(self, app) -> None:
        self.app = app

    def request(self, method: str, url: str, *, token: str | None = None, **kwargs) -> httpx.Response:
        async def _request() -> httpx.Response:
            headers = dict(kwargs.pop("headers", {}) or {})
            if token:
                headers["Authorization"] = f"Bearer {token}"
            transport = httpx.ASGITransport(app=self.app, raise_app_exceptions=False)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                return await client.request(method, url, headers=headers, **kwargs)

        return asyncio.run(_request())

    def get(self, url: str, *, token: str | None = None, **kwargs) -> httpx.Response:
        return self.request("GET", url, token=token, **kwargs)

    def post(self, url: str, *, token: str | None = None, **kwargs) -> httpx.Response:
        return self.request("POST", url, token=token, **kwargs)

    def patch(self, url: str, *, token: str | None = None, **kwargs) -> httpx.Response:
        return self.request("PATCH", url, token=token, **kwargs)

    def put(self, url: str, *, token: str | None = None, **kwargs) -> httpx.Response:
        return self.request("PUT", url, token=token, **kwargs)

    def delete(self, url: str, *, token: str | None = None, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, token=token, **kwargs)


@pytest.fixture
def api_client(app) -> ApiClient:
    return ApiClient(app)


@pytest.fixture
def security_world(db_session: Session):
    return build_security_world(db_session, TEST_STORAGE_ROOT)
