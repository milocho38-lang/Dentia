from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from sqlalchemy import select

from app.core.config import settings
from app.models.audit_event import AuditEvent
from app.models.auth_attempt import AuthAttempt
from app.models.auth_session import AuthSession
from app.models.role import Role
from app.models.user import User


TEST_PASSWORD = "DentiaTestPassword123!"


def _role_id(db_session, company_id, code: str) -> str:
    role = db_session.scalar(
        select(Role).where(Role.company_id == company_id, Role.code == code)
    )
    assert role is not None
    return str(role.id)


def _create_user(api_client, db_session, tenant, *, username: str, email: str):
    return api_client.post(
        "/api/users",
        token=tenant.admin.token,
        json={
            "name": f"Cuenta {username}",
            "username": username,
            "email": email,
            "phone": None,
            "role_ids": [_role_id(db_session, tenant.company.id, "SECRETARY")],
            "site_ids": [str(tenant.site_1.id)],
            "default_site_id": str(tenant.site_1.id),
        },
    )


def _activate(api_client, tenant, user_id: str):
    response = api_client.post(
        f"/api/users/{user_id}/activate",
        token=tenant.admin.token,
    )
    assert response.status_code == 200, response.text


def test_shared_contact_email_authenticates_independent_tenant_accounts(
    api_client, db_session, security_world
) -> None:
    shared_email = "persona-multiclinica@example.test"
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b

    created_a = _create_user(
        api_client,
        db_session,
        tenant_a,
        username="persona.clinica-a",
        email=shared_email,
    )
    created_b = _create_user(
        api_client,
        db_session,
        tenant_b,
        username="persona.clinica-b",
        email=shared_email.upper(),
    )
    assert created_a.status_code == created_b.status_code == 201
    _activate(api_client, tenant_a, created_a.json()["user"]["id"])
    _activate(api_client, tenant_b, created_b.json()["user"]["id"])

    login_a = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "PERSONA.CLINICA-A",
            "password": created_a.json()["temporary_password"],
        },
    )
    login_b = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "persona.clinica-b",
            "password": created_b.json()["temporary_password"],
        },
    )
    assert login_a.status_code == login_b.status_code == 200
    assert login_a.json()["user"]["company_id"] == str(tenant_a.company.id)
    assert login_b.json()["user"]["company_id"] == str(tenant_b.company.id)
    assert login_a.json()["user"]["id"] != login_b.json()["user"]["id"]


def test_username_is_global_email_is_unique_only_inside_company(
    api_client, db_session, security_world
) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    shared_email = "contacto-compartido@example.test"
    first = _create_user(
        api_client,
        db_session,
        tenant_a,
        username="cuenta.global",
        email=shared_email,
    )
    assert first.status_code == 201, first.text

    same_username_other_tenant = _create_user(
        api_client,
        db_session,
        tenant_b,
        username="  CUENTA.GLOBAL  ",
        email=shared_email,
    )
    assert same_username_other_tenant.status_code == 409

    same_email_same_tenant = _create_user(
        api_client,
        db_session,
        tenant_a,
        username="otra.cuenta",
        email=shared_email.upper(),
    )
    assert same_email_same_tenant.status_code == 409


def test_concurrent_global_username_collision_returns_one_conflict(
    api_client, db_session, security_world
) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    role_a = _role_id(db_session, tenant_a.company.id, "SECRETARY")
    role_b = _role_id(db_session, tenant_b.company.id, "SECRETARY")

    def create(tenant, role_id: str, email: str):
        return api_client.post(
            "/api/users",
            token=tenant.admin.token,
            json={
                "name": "Cuenta concurrente",
                "username": "colision.global",
                "email": email,
                "phone": None,
                "role_ids": [role_id],
                "site_ids": [str(tenant.site_1.id)],
                "default_site_id": str(tenant.site_1.id),
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = [
            executor.submit(
                create, tenant_a, role_a, "colision-a@example.test"
            ),
            executor.submit(
                create, tenant_b, role_b, "colision-b@example.test"
            ),
        ]
    statuses = sorted(response.result().status_code for response in responses)
    assert statuses == [201, 409]


def test_concurrent_company_email_collision_returns_one_conflict(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    role_id = _role_id(db_session, tenant.company.id, "SECRETARY")

    def create(username: str):
        return api_client.post(
            "/api/users",
            token=tenant.admin.token,
            json={
                "name": "Cuenta concurrente",
                "username": username,
                "email": "correo.concurrente@example.test",
                "phone": None,
                "role_ids": [role_id],
                "site_ids": [str(tenant.site_1.id)],
                "default_site_id": str(tenant.site_1.id),
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = [
            executor.submit(create, "correo.concurrente-a"),
            executor.submit(create, "correo.concurrente-b"),
        ]
    statuses = sorted(response.result().status_code for response in responses)
    assert statuses == [201, 409]


def test_conflicting_legacy_and_current_login_identifiers_are_rejected(
    api_client, security_world
) -> None:
    response = api_client.post(
        "/api/auth/login",
        json={
            "identifier": security_world.tenant_a.admin.user.username,
            "email": "otro-identificador@example.test",
            "password": "DentiaTestPassword123!",
        },
    )
    assert response.status_code == 422


def test_legacy_email_alias_and_current_identifier_share_normalization(
    api_client, security_world
) -> None:
    admin = security_world.tenant_a.admin.user

    legacy = api_client.post(
        "/api/auth/login",
        json={
            "email": f"  {admin.username.upper()}  ",
            "password": TEST_PASSWORD,
        },
    )
    current = api_client.post(
        "/api/auth/login",
        json={
            "identifier": f"  {admin.username.upper()}  ",
            "password": TEST_PASSWORD,
        },
    )

    assert legacy.status_code == current.status_code == 200
    assert legacy.json()["user"]["id"] == current.json()["user"]["id"]


def test_failed_login_is_scoped_to_global_username_not_shared_contact_email(
    api_client, db_session, security_world
) -> None:
    shared_email = "rate-limit-shared@example.test"
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    created_a = _create_user(
        api_client,
        db_session,
        tenant_a,
        username="rate-limit.clinica-a",
        email=shared_email,
    )
    created_b = _create_user(
        api_client,
        db_session,
        tenant_b,
        username="rate-limit.clinica-b",
        email=shared_email,
    )
    assert created_a.status_code == created_b.status_code == 201
    user_a_id = created_a.json()["user"]["id"]
    user_b_id = created_b.json()["user"]["id"]
    _activate(api_client, tenant_a, user_a_id)
    _activate(api_client, tenant_b, user_b_id)

    failed = api_client.post(
        "/api/auth/login",
        json={"identifier": "rate-limit.clinica-a", "password": "incorrecta"},
    )
    assert failed.status_code == 401
    db_session.expire_all()
    user_a = db_session.get(User, UUID(user_a_id))
    user_b = db_session.get(User, UUID(user_b_id))
    assert user_a is not None and user_b is not None
    assert user_a.failed_login_attempts == 1
    assert user_b.failed_login_attempts == 0
    attempt = db_session.scalar(
        select(AuthAttempt)
        .where(AuthAttempt.user_id == user_a.id)
        .order_by(AuthAttempt.occurred_at.desc())
    )
    assert attempt is not None
    assert attempt.company_id == tenant_a.company.id

    login_b = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "rate-limit.clinica-b",
            "password": created_b.json()["temporary_password"],
        },
    )
    assert login_b.status_code == 200


def test_admin_reset_revokes_only_same_company_account_refresh_and_audits_target(
    api_client, db_session, security_world
) -> None:
    shared_email = "reset-shared@example.test"
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    created_a = _create_user(
        api_client,
        db_session,
        tenant_a,
        username="reset.clinica-a",
        email=shared_email,
    )
    created_b = _create_user(
        api_client,
        db_session,
        tenant_b,
        username="reset.clinica-b",
        email=shared_email,
    )
    assert created_a.status_code == created_b.status_code == 201
    user_a_id = created_a.json()["user"]["id"]
    user_b_id = created_b.json()["user"]["id"]
    _activate(api_client, tenant_a, user_a_id)
    _activate(api_client, tenant_b, user_b_id)

    login_a = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "reset.clinica-a",
            "password": created_a.json()["temporary_password"],
        },
    )
    login_b = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "reset.clinica-b",
            "password": created_b.json()["temporary_password"],
        },
    )
    assert login_a.status_code == login_b.status_code == 200
    refresh_a = login_a.cookies.get(settings.refresh_cookie_name)
    refresh_b = login_b.cookies.get(settings.refresh_cookie_name)
    assert refresh_a and refresh_b

    user_b = db_session.get(User, UUID(user_b_id))
    assert user_b is not None
    user_b_password_hash = user_b.password_hash
    reset = api_client.post(
        f"/api/users/{user_a_id}/reset-password",
        token=tenant_a.admin.token,
    )
    assert reset.status_code == 200, reset.text

    rejected_a = api_client.post(
        "/api/auth/refresh",
        headers={"Cookie": f"{settings.refresh_cookie_name}={refresh_a}"},
    )
    accepted_b = api_client.post(
        "/api/auth/refresh",
        headers={"Cookie": f"{settings.refresh_cookie_name}={refresh_b}"},
    )
    assert rejected_a.status_code == 401
    assert accepted_b.status_code == 200
    db_session.expire_all()
    user_b = db_session.get(User, UUID(user_b_id))
    assert user_b is not None
    assert user_b.company_id == tenant_b.company.id
    assert user_b.password_hash == user_b_password_hash
    audit = db_session.scalar(
        select(AuditEvent)
        .where(
            AuditEvent.action == "ADMIN_PASSWORD_RESET",
            AuditEvent.entity_id == UUID(user_a_id),
        )
        .order_by(AuditEvent.created_at.desc())
    )
    assert audit is not None
    assert audit.company_id == tenant_a.company.id


def test_username_change_revokes_only_target_account_sessions(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    target = tenant.secretary.user
    other = tenant.dentist.user
    before_other_sessions = list(
        db_session.scalars(select(AuthSession).where(AuthSession.user_id == other.id))
    )
    assert before_other_sessions
    response = api_client.patch(
        f"/api/users/{target.id}",
        token=tenant.admin.token,
        json={
            "name": target.name,
            "username": "secretaria.renombrada",
            "email": target.email,
            "phone": target.phone,
        },
    )
    assert response.status_code == 200, response.text
    db_session.expire_all()
    target_sessions = list(
        db_session.scalars(select(AuthSession).where(AuthSession.user_id == target.id))
    )
    assert target_sessions
    assert all(item.revoked_at is not None for item in target_sessions)
    for other_session in before_other_sessions:
        db_session.refresh(other_session)
        assert other_session.revoked_at is None


def test_historical_email_username_over_100_chars_does_not_block_profile_edit(
    api_client, db_session, security_world
) -> None:
    target = security_world.tenant_a.secretary.user
    suffix = "@example.test"
    historical_username = f"{'a' * (320 - len(suffix))}{suffix}"
    assert len(historical_username) == 320
    target.username = historical_username
    target.normalized_username = historical_username.casefold()
    db_session.commit()

    response = api_client.patch(
        f"/api/users/{target.id}",
        token=security_world.tenant_a.admin.token,
        json={
            "name": "Secretaría actualizada",
            "username": historical_username,
            "email": target.email,
            "phone": target.phone,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["username"] == historical_username
    db_session.refresh(target)
    assert target.normalized_username == historical_username.casefold()


def test_historical_long_username_cannot_be_replaced_by_another_long_username(
    api_client, db_session, security_world
) -> None:
    target = security_world.tenant_a.secretary.user
    suffix = "@example.test"
    historical_username = f"{'a' * (320 - len(suffix))}{suffix}"
    replacement = f"{'replacement-' * 10}account@example.test"
    assert len(historical_username) == 320
    assert 100 < len(replacement) <= 320
    target.username = historical_username
    target.normalized_username = historical_username.casefold()
    db_session.commit()

    response = api_client.patch(
        f"/api/users/{target.id}",
        token=security_world.tenant_a.admin.token,
        json={
            "name": target.name,
            "username": replacement,
            "email": target.email,
            "phone": target.phone,
        },
    )

    assert response.status_code == 400
    db_session.refresh(target)
    assert target.normalized_username == historical_username.casefold()


def test_shared_email_does_not_expose_cross_tenant_user_management(
    api_client, db_session, security_world
) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    created = _create_user(
        api_client,
        db_session,
        tenant_b,
        username="aislada.clinica-b",
        email="contacto-aislado@example.test",
    )
    assert created.status_code == 201, created.text
    target_id = created.json()["user"]["id"]

    detail = api_client.get(f"/api/users/{target_id}", token=tenant_a.admin.token)
    reset = api_client.post(
        f"/api/users/{target_id}/reset-password",
        token=tenant_a.admin.token,
    )
    assert detail.status_code == reset.status_code == 404
    assert target_id not in detail.text
