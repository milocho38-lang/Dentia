from concurrent.futures import ThreadPoolExecutor

from app.core.security_catalog import ROLES
from app.models.agenda import Dentist, DentistSite
from app.models.audit_event import AuditEvent


def _role_permissions(code: str) -> set[str]:
    return set(next(role.permission_codes for role in ROLES if role.code == code))


def _ensure_dentist(db_session, tenant, actor) -> Dentist:
    dentist = Dentist(
        company_id=tenant.company.id,
        user_id=actor.user.id,
        name=actor.user.name,
        status="Activo",
        is_active=True,
        created_by=tenant.admin.user.id,
    )
    db_session.add(dentist)
    db_session.flush()
    db_session.add(
        DentistSite(
            company_id=tenant.company.id,
            dentist_id=dentist.id,
            site_id=tenant.site_1.id,
            is_active=True,
            created_by=tenant.admin.user.id,
        )
    )
    db_session.commit()
    return dentist


def _enable(api_client, world, *, seats: int = 1):
    return api_client.put(
        f"/api/platform/companies/{world.tenant_a.company.id}/orthodontics-entitlement",
        token=world.platform_admin.token,
        json={"enabled": True, "seat_limit": seats},
    )


def test_authorized_rbac_matrix_has_no_redundant_module_access() -> None:
    platform = _role_permissions("PLATFORM_ADMIN")
    administrator = _role_permissions("ADMINISTRATOR")
    dentist_admin = _role_permissions("DENTIST_ADMIN")
    dentist = _role_permissions("DENTIST")
    secretary = _role_permissions("SECRETARY")
    assert {"orthodontics.entitlement.view", "orthodontics.entitlement.manage"} <= platform
    assert "orthodontics.assignment.manage" not in platform
    assert {"orthodontics.entitlement.view", "orthodontics.assignment.view", "orthodontics.assignment.manage"} <= administrator
    assert {"orthodontics.entitlement.view", "orthodontics.assignment.view", "orthodontics.assignment.manage"} <= dentist_admin
    assert {permission for permission in dentist if permission.startswith("orthodontics.")} == {
        "orthodontics.catalog.view"
    }
    assert not {permission for permission in secretary if permission.startswith("orthodontics.")}
    assert all("orthodontics.module.access" not in role.permission_codes for role in ROLES)


def test_platform_manages_entitlement_without_tenant_clinical_access(api_client, security_world) -> None:
    company_id = security_world.tenant_a.company.id
    initial = api_client.get(
        f"/api/platform/companies/{company_id}/orthodontics-entitlement",
        token=security_world.platform_admin.token,
    )
    assert initial.status_code == 200, initial.text
    assert initial.json()["enabled"] is False
    enabled = _enable(api_client, security_world, seats=3)
    assert enabled.status_code == 200, enabled.text
    assert enabled.json()["seats"] == {"seat_limit": 3, "assigned_active": 0, "available": 3}
    assert api_client.get("/api/orthodontics/access", token=security_world.platform_admin.token).status_code == 403
    assert api_client.put(
        f"/api/platform/companies/{company_id}/orthodontics-entitlement",
        token=security_world.tenant_a.admin.token,
        json={"enabled": True, "seat_limit": 4},
    ).status_code == 403


def test_assignment_seat_accounting_access_and_cross_tenant(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    dentist_profile = tenant.dentist_profile
    second_dentist = _ensure_dentist(db_session, tenant, tenant.dentist)
    assert _enable(api_client, security_world, seats=1).status_code == 200
    assigned = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(dentist_profile.id)},
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["seats"]["available"] == 0
    repeated = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(dentist_profile.id)},
    )
    assert repeated.status_code == 200
    assert repeated.json()["created"] is False
    full = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(second_dentist.id)},
    )
    assert full.status_code == 409
    assert full.json()["detail"]["code"] == "ORTHODONTICS_NO_AVAILABLE_SEATS"
    foreign = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(security_world.tenant_b.dentist_profile.id)},
    )
    assert foreign.status_code == 404
    access = api_client.get("/api/orthodontics/access", token=tenant.dentist_admin.token)
    assert access.status_code == 200 and access.json()["allowed"] is True
    unassigned = api_client.get("/api/orthodontics/access", token=tenant.dentist.token)
    assert unassigned.status_code == 200
    assert unassigned.json()["code"] == "ORTHODONTICS_ASSIGNMENT_INACTIVE"
    revoked = api_client.post(
        f"/api/orthodontics/assignments/{assigned.json()['assignment']['id']}/revoke",
        token=tenant.admin.token,
        json={"reason": "Reasignación de cupo"},
    )
    assert revoked.status_code == 200
    dentist_assigned = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(second_dentist.id)},
    )
    assert dentist_assigned.status_code == 200
    dentist_access = api_client.get("/api/orthodontics/access", token=tenant.dentist.token)
    assert dentist_access.status_code == 200
    assert dentist_access.json()["allowed"] is True
    assert api_client.get("/api/orthodontics/assignments", token=tenant.dentist.token).status_code == 403
    assert api_client.get("/api/orthodontics/assignments", token=tenant.secretary.token).status_code == 403


def test_revoke_is_logical_audited_and_frees_seat(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    assert _enable(api_client, security_world).status_code == 200
    assigned = api_client.post("/api/orthodontics/assignments", token=tenant.dentist_admin.token, json={"dentist_id": str(tenant.dentist_profile.id)})
    assignment_id = assigned.json()["assignment"]["id"]
    revoked = api_client.post(
        f"/api/orthodontics/assignments/{assignment_id}/revoke",
        token=tenant.dentist_admin.token,
        json={"reason": "Cambio de responsable"},
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["assignment"]["assigned"] is False
    assert revoked.json()["seats"]["available"] == 1
    actions = {event.action for event in db_session.query(AuditEvent).filter(AuditEvent.company_id == tenant.company.id)}
    assert {"ORTHODONTICS_ENTITLEMENT_ENABLED", "ORTHODONTICS_SEAT_LIMIT_CHANGED", "ORTHODONTICS_DENTIST_ASSIGNED", "ORTHODONTICS_DENTIST_REVOKED"} <= actions


def test_concurrent_assignment_cannot_exceed_seat_limit(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    second_dentist = _ensure_dentist(db_session, tenant, tenant.dentist)
    assert _enable(api_client, security_world, seats=1).status_code == 200
    dentist_ids = [tenant.dentist_profile.id, second_dentist.id]

    def assign(dentist_id):
        return api_client.post(
            "/api/orthodontics/assignments",
            token=tenant.admin.token,
            json={"dentist_id": str(dentist_id)},
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(assign, dentist_ids))
    assert sorted(statuses) == [200, 409]
    listing = api_client.get("/api/orthodontics/assignments", token=tenant.admin.token)
    assert listing.json()["entitlement"]["seats"]["assigned_active"] == 1


def test_administrator_has_assignment_admin_but_no_clinical_module(api_client, security_world) -> None:
    assert _enable(api_client, security_world).status_code == 200
    assert api_client.get("/api/orthodontics/assignments", token=security_world.tenant_a.admin.token).status_code == 200
    access = api_client.get("/api/orthodontics/access", token=security_world.tenant_a.admin.token)
    assert access.status_code == 200
    assert access.json()["allowed"] is False


def test_user_deactivation_revokes_assignment_without_deleting_history(api_client, db_session, security_world) -> None:
    tenant = security_world.tenant_a
    assert _enable(api_client, security_world).status_code == 200
    assigned = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(tenant.dentist_profile.id)},
    )
    assignment_id = assigned.json()["assignment"]["id"]
    deactivated = api_client.post(
        f"/api/users/{tenant.dentist_admin.user.id}/deactivate",
        token=tenant.admin.token,
    )
    assert deactivated.status_code == 200, deactivated.text
    listing = api_client.get("/api/orthodontics/assignments", token=tenant.admin.token)
    assert listing.json()["entitlement"]["seats"]["assigned_active"] == 0
    from app.models.orthodontics import OrthodonticsDentistAssignment

    historical = db_session.get(OrthodonticsDentistAssignment, assignment_id)
    assert historical is not None
    assert historical.is_active is False
    assert historical.revoked_at is not None
