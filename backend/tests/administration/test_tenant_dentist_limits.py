from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select

from app.models.agenda import Dentist
from app.models.associations import RolePermission
from app.models.audit_event import AuditEvent
from app.models.permission import Permission
from app.models.role import Role
from app.services.tenant_dentist_quota import active_dentist_count


LIMIT_MESSAGE = "Has alcanzado el límite de odontólogos de tu plan."


def _role(db_session, company_id, code: str) -> Role:
    role = db_session.scalar(
        select(Role).where(Role.company_id == company_id, Role.code == code)
    )
    assert role is not None
    return role


def _payload(tenant, role_ids: list[str], suffix: str) -> dict:
    return {
        "name": f"Usuario Cupo {suffix}",
        "email": f"usuario-cupo-{suffix}@example.test",
        "phone": None,
        "role_ids": role_ids,
        "site_ids": [str(tenant.site_1.id)],
        "default_site_id": str(tenant.site_1.id),
    }


def _create_with_roles(api_client, db_session, tenant, role_codes, suffix):
    return api_client.post(
        "/api/users",
        token=tenant.admin.token,
        json=_payload(
            tenant,
            [str(_role(db_session, tenant.company.id, code).id) for code in role_codes],
            suffix,
        ),
    )


def _activate(api_client, tenant, user_id):
    return api_client.post(
        f"/api/users/{user_id}/activate",
        token=tenant.admin.token,
    )


def _assign_roles(api_client, db_session, tenant, user_id, role_codes):
    return api_client.put(
        f"/api/users/{user_id}/roles",
        token=tenant.admin.token,
        json={
            "role_ids": [
                str(_role(db_session, tenant.company.id, code).id)
                for code in role_codes
            ]
        },
    )


def _dentist_profile(db_session, tenant, user_id):
    return db_session.scalar(
        select(Dentist).where(
            Dentist.company_id == tenant.company.id,
            Dentist.user_id == user_id,
        )
    )


def test_business_roles_remain_tenant_scoped_and_administrative_users_do_not_consume_seats(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    other = security_world.tenant_b
    options = api_client.get("/api/users/access-options", token=tenant.admin.token)
    assert options.status_code == 200, options.text
    assert "PLATFORM_ADMIN" not in {role["code"] for role in options.json()["roles"]}
    assert "active_users" not in options.json()
    assert "max_active_users" not in options.json()

    platform_role = _role(db_session, tenant.company.id, "PLATFORM_ADMIN")
    denied_platform = api_client.post(
        "/api/users",
        token=tenant.admin.token,
        json=_payload(tenant, [str(platform_role.id)], "platform-role"),
    )
    assert denied_platform.status_code == 403, denied_platform.text

    other_secretary = _role(db_session, other.company.id, "SECRETARY")
    cross_payload = _payload(tenant, [str(other_secretary.id)], "cross-tenant")
    cross_payload["site_ids"] = [str(other.site_1.id)]
    cross_payload["default_site_id"] = str(other.site_1.id)
    denied_cross = api_client.post(
        "/api/users", token=tenant.admin.token, json=cross_payload
    )
    assert denied_cross.status_code in {400, 403}, denied_cross.text

    assert active_dentist_count(db_session, tenant.company.id) == 1
    for suffix, roles in (
        ("secretary-1", ["SECRETARY"]),
        ("secretary-2", ["SECRETARY"]),
        ("administrator", ["ADMINISTRATOR"]),
    ):
        created = _create_with_roles(
            api_client, db_session, tenant, roles, suffix
        )
        assert created.status_code == 201, created.text
    db_session.expire_all()
    assert active_dentist_count(db_session, tenant.company.id) == 1


def test_self_deactivation_guard_remains_independent_from_dentist_quota(
    api_client, security_world
) -> None:
    tenant = security_world.tenant_a
    response = api_client.post(
        f"/api/users/{tenant.admin.user.id}/deactivate",
        token=tenant.admin.token,
    )
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "No puedes suspender o desactivar tu cuenta."


def test_plan_one_blocks_second_dentist_and_deactivation_releases_seat(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    tenant.company.max_active_dentists = 1
    db_session.commit()

    created = _create_with_roles(
        api_client, db_session, tenant, ["DENTIST"], "dentist-plan-one"
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["user"]["id"]
    profile = db_session.scalar(
        select(Dentist).where(Dentist.user_id == user_id)
    )
    assert profile is not None
    assert active_dentist_count(db_session, tenant.company.id) == 1

    blocked = _activate(api_client, tenant, user_id)
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"] == LIMIT_MESSAGE

    deactivated = api_client.post(
        f"/api/users/{tenant.dentist_admin.user.id}/deactivate",
        token=tenant.admin.token,
    )
    assert deactivated.status_code == 200, deactivated.text
    db_session.expire_all()
    assert active_dentist_count(db_session, tenant.company.id) == 0

    activated = _activate(api_client, tenant, user_id)
    assert activated.status_code == 200, activated.text
    assert active_dentist_count(db_session, tenant.company.id) == 1

    blocked_reactivation = _activate(
        api_client, tenant, tenant.dentist_admin.user.id
    )
    assert blocked_reactivation.status_code == 409, blocked_reactivation.text
    assert blocked_reactivation.json()["detail"] == LIMIT_MESSAGE


def test_role_transitions_preserve_profile_and_synchronize_practicing_status(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    tenant.company.max_active_dentists = 1
    db_session.commit()

    created = _create_with_roles(
        api_client, db_session, tenant, ["DENTIST"], "transition-dentist"
    )
    assert created.status_code == 201, created.text
    transitioning_user_id = created.json()["user"]["id"]
    profile = _dentist_profile(db_session, tenant, transitioning_user_id)
    assert profile is not None
    historical_profile_id = profile.id
    assert profile.is_active is False
    assert profile.status == "Inactivo"

    blocked = _activate(api_client, tenant, transitioning_user_id)
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"] == LIMIT_MESSAGE

    changed_to_secretary = _assign_roles(
        api_client,
        db_session,
        tenant,
        transitioning_user_id,
        ["SECRETARY"],
    )
    assert changed_to_secretary.status_code == 200, changed_to_secretary.text
    db_session.expire_all()
    profile = _dentist_profile(db_session, tenant, transitioning_user_id)
    assert profile is not None
    assert profile.id == historical_profile_id
    assert profile.is_active is False
    assert profile.status == "Inactivo"

    activated_secretary = _activate(api_client, tenant, transitioning_user_id)
    assert activated_secretary.status_code == 200, activated_secretary.text
    db_session.expire_all()
    assert active_dentist_count(db_session, tenant.company.id) == 1
    profile = _dentist_profile(db_session, tenant, transitioning_user_id)
    assert profile is not None and profile.is_active is False

    released = _assign_roles(
        api_client,
        db_session,
        tenant,
        tenant.dentist_admin.user.id,
        ["ADMINISTRATOR"],
    )
    assert released.status_code == 200, released.text
    db_session.expire_all()
    original_profile = _dentist_profile(
        db_session, tenant, tenant.dentist_admin.user.id
    )
    assert original_profile is not None
    assert original_profile.is_active is False
    assert original_profile.status == "Inactivo"
    assert active_dentist_count(db_session, tenant.company.id) == 0

    restored = _assign_roles(
        api_client,
        db_session,
        tenant,
        transitioning_user_id,
        ["DENTIST"],
    )
    assert restored.status_code == 200, restored.text
    db_session.expire_all()
    profile = _dentist_profile(db_session, tenant, transitioning_user_id)
    assert profile is not None
    assert profile.id == historical_profile_id
    assert profile.is_active is True
    assert profile.status == "Activo"
    assert active_dentist_count(db_session, tenant.company.id) == 1

    blocked_conversion = _assign_roles(
        api_client,
        db_session,
        tenant,
        tenant.secretary.user.id,
        ["DENTIST"],
    )
    assert blocked_conversion.status_code == 409, blocked_conversion.text
    assert blocked_conversion.json()["detail"] == LIMIT_MESSAGE
    assert _dentist_profile(db_session, tenant, tenant.secretary.user.id) is None


def test_dentist_admin_stays_clinical_until_all_clinical_capabilities_are_removed(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    tenant.company.max_active_dentists = 1
    db_session.commit()

    combined = _assign_roles(
        api_client,
        db_session,
        tenant,
        tenant.dentist_admin.user.id,
        ["DENTIST", "DENTIST_ADMIN", "ADMINISTRATOR"],
    )
    assert combined.status_code == 200, combined.text
    db_session.expire_all()
    assert active_dentist_count(db_session, tenant.company.id) == 1

    dentist_admin_only = _assign_roles(
        api_client,
        db_session,
        tenant,
        tenant.dentist_admin.user.id,
        ["DENTIST_ADMIN", "ADMINISTRATOR"],
    )
    assert dentist_admin_only.status_code == 200, dentist_admin_only.text
    db_session.expire_all()
    profile = _dentist_profile(db_session, tenant, tenant.dentist_admin.user.id)
    assert profile is not None and profile.is_active is True
    assert active_dentist_count(db_session, tenant.company.id) == 1

    administrator_only = _assign_roles(
        api_client,
        db_session,
        tenant,
        tenant.dentist_admin.user.id,
        ["ADMINISTRATOR"],
    )
    assert administrator_only.status_code == 200, administrator_only.text
    db_session.expire_all()
    profile = _dentist_profile(db_session, tenant, tenant.dentist_admin.user.id)
    assert profile is not None
    assert profile.is_active is False
    assert profile.status == "Inactivo"
    assert active_dentist_count(db_session, tenant.company.id) == 0


def test_dentist_admin_multiple_roles_and_custom_clinical_roles_consume_one_seat(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    tenant.company.max_active_dentists = 3
    db_session.commit()

    multi = _create_with_roles(
        api_client,
        db_session,
        tenant,
        ["ADMINISTRATOR", "DENTIST_ADMIN", "DENTIST"],
        "multi-role-dentist",
    )
    assert multi.status_code == 201, multi.text
    assert _activate(api_client, tenant, multi.json()["user"]["id"]).status_code == 200
    db_session.expire_all()
    assert active_dentist_count(db_session, tenant.company.id) == 2

    custom_admin = Role(
        company_id=tenant.company.id,
        code="CUSTOM_ADMIN_ONLY",
        name="Administrativo personalizado",
        is_system=False,
        created_by=tenant.admin.user.id,
    )
    custom_clinical = Role(
        company_id=tenant.company.id,
        code="CUSTOM_CLINICAL",
        name="Clínico personalizado",
        is_system=False,
        created_by=tenant.admin.user.id,
    )
    db_session.add_all([custom_admin, custom_clinical])
    db_session.flush()
    clinical_permission = db_session.scalar(
        select(Permission).where(Permission.code == "clinical_evolutions.sign")
    )
    assert clinical_permission is not None
    db_session.add(
        RolePermission(
            company_id=tenant.company.id,
            role_id=custom_clinical.id,
            permission_id=clinical_permission.id,
            created_by=tenant.admin.user.id,
        )
    )
    db_session.commit()

    nonclinical = api_client.post(
        "/api/users",
        token=tenant.admin.token,
        json=_payload(tenant, [str(custom_admin.id)], "custom-admin"),
    )
    assert nonclinical.status_code == 201, nonclinical.text
    assert _activate(api_client, tenant, nonclinical.json()["user"]["id"]).status_code == 200
    db_session.expire_all()
    assert active_dentist_count(db_session, tenant.company.id) == 2

    clinical = api_client.post(
        "/api/users",
        token=tenant.admin.token,
        json=_payload(tenant, [str(custom_clinical.id)], "custom-clinical"),
    )
    assert clinical.status_code == 201, clinical.text
    assert _activate(api_client, tenant, clinical.json()["user"]["id"]).status_code == 200
    db_session.expire_all()
    assert active_dentist_count(db_session, tenant.company.id) == 3

    changed_to_nonclinical = _assign_roles(
        api_client,
        db_session,
        tenant,
        clinical.json()["user"]["id"],
        ["CUSTOM_ADMIN_ONLY"],
    )
    assert changed_to_nonclinical.status_code == 200, changed_to_nonclinical.text
    db_session.expire_all()
    profile = _dentist_profile(
        db_session, tenant, clinical.json()["user"]["id"]
    )
    assert profile is not None
    assert profile.is_active is False
    assert profile.status == "Inactivo"
    assert active_dentist_count(db_session, tenant.company.id) == 2


def test_assigning_clinical_capability_cannot_bypass_full_quota(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    tenant.company.max_active_dentists = 1
    db_session.commit()
    dentist_role = _role(db_session, tenant.company.id, "DENTIST")

    response = api_client.put(
        f"/api/users/{tenant.secretary.user.id}/roles",
        token=tenant.admin.token,
        json={"role_ids": [str(dentist_role.id)]},
    )
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == LIMIT_MESSAGE
    assert db_session.scalar(
        select(Dentist.id).where(Dentist.user_id == tenant.secretary.user.id)
    ) is None


def test_platform_changes_dentist_limit_tenant_cannot_and_audit_is_created(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    endpoint = f"/api/platform/companies/{tenant.company.id}/dentist-limit"
    denied = api_client.patch(
        endpoint,
        token=tenant.admin.token,
        json={"max_active_dentists": 3},
    )
    assert denied.status_code == 403, denied.text

    changed = api_client.patch(
        endpoint,
        token=security_world.platform_admin.token,
        json={"max_active_dentists": 3},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["company"]["max_active_dentists"] == 3
    assert changed.json()["company"]["active_dentist_count"] == 1
    audit = db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.company_id == tenant.company.id,
            AuditEvent.action == "COMPANY_DENTIST_LIMIT_CHANGED",
        )
    )
    assert audit is not None


def test_concurrent_dentist_activation_cannot_exceed_plan(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    tenant.company.max_active_dentists = 1
    tenant.dentist_admin.user.status = "Inactivo"
    tenant.dentist_admin.user.is_active = False
    db_session.commit()
    assert active_dentist_count(db_session, tenant.company.id) == 0

    user_ids = []
    for suffix in ("concurrent-a", "concurrent-b"):
        created = _create_with_roles(
            api_client, db_session, tenant, ["DENTIST"], suffix
        )
        assert created.status_code == 201, created.text
        user_ids.append(created.json()["user"]["id"])

    def activate(user_id: str):
        return _activate(api_client, tenant, user_id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(activate, user_ids))

    assert sorted(response.status_code for response in responses) == [200, 409]
    db_session.expire_all()
    assert active_dentist_count(db_session, tenant.company.id) == 1
