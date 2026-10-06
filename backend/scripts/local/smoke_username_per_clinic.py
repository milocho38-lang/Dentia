from __future__ import annotations

import os
from uuid import UUID, uuid4

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.services.bootstrap_service import BootstrapInput, bootstrap_installation


BASE_URL = os.environ.get("DENTIA_SMOKE_BASE_URL", "http://127.0.0.1:13101")
DATABASE_URL = os.environ["DATABASE_URL"]
PASSWORD = "DentiaSmokePassword2026!"
CHANGED_PASSWORD = "DentiaSmokeChanged2026!"
RUN_ID = os.environ.get("DENTIA_SMOKE_RUN_ID", uuid4().hex[:8])
SHARED_EMAIL = f"username-smoke-shared-{RUN_ID}@example.test"


def require(response: httpx.Response, status: int) -> dict:
    if response.status_code != status:
        raise RuntimeError(
            f"{response.request.method} {response.request.url}: "
            f"expected {status}, got {response.status_code}: {response.text}"
        )
    return response.json()


def login(identifier_field: str, identifier: str, password: str) -> tuple[str, str]:
    response = httpx.post(
        f"{BASE_URL}/api/auth/login",
        json={identifier_field: identifier, "password": password},
        timeout=20,
    )
    payload = require(response, 200)
    refresh_token = response.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise RuntimeError("Login smoke did not return a refresh cookie.")
    return payload["access_token"], refresh_token


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def complete_initial_password_change(token: str) -> str:
    response = httpx.post(
        f"{BASE_URL}/api/auth/change-password",
        headers=headers(token),
        json={
            "current_password": PASSWORD,
            "new_password": CHANGED_PASSWORD,
            "confirm_password": CHANGED_PASSWORD,
        },
        timeout=20,
    )
    return require(response, 200)["access_token"]


def company_payload(name: str, username: str) -> dict:
    return {
        "company_name": name,
        "company_type": "Clínica",
        "tax_id": f"SMOKE-{username.upper()}",
        "phone": None,
        "email": f"contacto-{username}@example.test",
        "address": "Calle Smoke 123",
        "city": "Bogotá",
        "country": "Colombia",
        "timezone": "America/Bogota",
        "admin_name": f"Administradora {name}",
        "admin_username": username,
        "admin_email": SHARED_EMAIL,
        "admin_password": PASSWORD,
    }


def create_tenant_user(token: str, username: str) -> dict:
    options = require(
        httpx.get(
            f"{BASE_URL}/api/users/access-options",
            headers=headers(token),
            timeout=20,
        ),
        200,
    )
    secretary_role = next(role for role in options["roles"] if role["code"] == "SECRETARY")
    site = options["sites"][0]
    return require(
        httpx.post(
            f"{BASE_URL}/api/users",
            headers=headers(token),
            json={
                "name": f"Cuenta {username}",
                "username": username,
                "email": "secretaria-compartida@example.test",
                "phone": None,
                "role_ids": [secretary_role["id"]],
                "site_ids": [site["id"]],
                "default_site_id": site["id"],
            },
            timeout=20,
        ),
        201,
    )


def main() -> None:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with Session(engine) as session:
        platform_user = session.scalar(
            select(User).where(User.normalized_username == "platform.smoke")
        )
        if platform_user is None:
            bootstrap_installation(
                session,
                BootstrapInput(
                    company_name="Dentia Smoke Platform",
                    company_slug="dentia-smoke-platform",
                    site_name="Sede Smoke",
                    admin_name="Platform Smoke",
                    admin_username="platform.smoke",
                    admin_email="platform-smoke@example.test",
                    admin_password=PASSWORD,
                ),
            )

    platform_token, _ = login("identifier", "  PLATFORM.SMOKE  ", PASSWORD)
    legacy_token, _ = login("email", "  PLATFORM.SMOKE  ", PASSWORD)
    if platform_token == legacy_token:
        raise RuntimeError("Independent logins unexpectedly returned the same access token.")

    company_a = require(
        httpx.post(
            f"{BASE_URL}/api/platform/companies",
            headers=headers(platform_token),
            json=company_payload(f"Smoke A {RUN_ID}", f"admin.smoke-a-{RUN_ID}"),
            timeout=30,
        ),
        201,
    )
    company_b = require(
        httpx.post(
            f"{BASE_URL}/api/platform/companies",
            headers=headers(platform_token),
            json=company_payload(f"Smoke B {RUN_ID}", f"admin.smoke-b-{RUN_ID}"),
            timeout=30,
        ),
        201,
    )
    admin_a_token, _ = login("identifier", f"admin.smoke-a-{RUN_ID}", PASSWORD)
    admin_b_token, _ = login("identifier", f"admin.smoke-b-{RUN_ID}", PASSWORD)
    admin_a_token = complete_initial_password_change(admin_a_token)
    admin_b_token = complete_initial_password_change(admin_b_token)

    user_a = create_tenant_user(admin_a_token, f"secretaria.smoke-a-{RUN_ID}")
    user_b = create_tenant_user(admin_b_token, f"secretaria.smoke-b-{RUN_ID}")
    user_a_id = user_a["user"]["id"]
    user_b_id = user_b["user"]["id"]
    for token, user_id in ((admin_a_token, user_a_id), (admin_b_token, user_b_id)):
        require(
            httpx.post(
                f"{BASE_URL}/api/users/{user_id}/activate",
                headers=headers(token),
                timeout=20,
            ),
            200,
        )

    _, refresh_a = login(
        "identifier", f"secretaria.smoke-a-{RUN_ID}", user_a["temporary_password"]
    )
    _, refresh_b = login(
        "identifier", f"secretaria.smoke-b-{RUN_ID}", user_b["temporary_password"]
    )
    require(
        httpx.post(
            f"{BASE_URL}/api/users/{user_a_id}/reset-password",
            headers=headers(admin_a_token),
            timeout=20,
        ),
        200,
    )
    require(
        httpx.post(
            f"{BASE_URL}/api/auth/refresh",
            cookies={settings.refresh_cookie_name: refresh_a},
            timeout=20,
        ),
        401,
    )
    require(
        httpx.post(
            f"{BASE_URL}/api/auth/refresh",
            cookies={settings.refresh_cookie_name: refresh_b},
            timeout=20,
        ),
        200,
    )
    require(
        httpx.post(
            f"{BASE_URL}/api/users/{user_b_id}/reset-password",
            headers=headers(admin_a_token),
            timeout=20,
        ),
        404,
    )

    suffix = "@example.test"
    historical_username = f"{'h' * (320 - len(suffix))}{suffix}"
    with Session(engine) as session:
        historical_user = session.get(User, UUID(user_a_id))
        if historical_user is None:
            raise RuntimeError("Historical smoke user was not found.")
        historical_user.username = historical_username
        historical_user.normalized_username = historical_username.casefold()
        session.commit()
    updated = require(
        httpx.patch(
            f"{BASE_URL}/api/users/{user_a_id}",
            headers=headers(admin_a_token),
            json={
                "name": "Cuenta histórica actualizada",
                "username": historical_username,
                "email": "secretaria-compartida@example.test",
                "phone": None,
            },
            timeout=20,
        ),
        200,
    )
    if updated["username"] != historical_username:
        raise RuntimeError("Historical 320-character username changed unexpectedly.")

    with Session(engine) as session:
        users = list(
            session.scalars(
                select(User).where(User.normalized_email == SHARED_EMAIL)
            )
        )
        if len(users) != 2 or len({user.company_id for user in users}) != 2:
            raise RuntimeError("Shared company-admin contact email invariant failed.")

    print(
        "username-per-clinic live smoke OK: legacy/current login, companies, "
        "shared emails, reset isolation and historical username"
    )


if __name__ == "__main__":
    main()
