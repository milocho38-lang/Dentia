from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

import pytest
from sqlalchemy import func, select

from app.models.agenda import Dentist
from app.models.associations import UserRole
from app.models.audit_event import AuditEvent
from app.models.auth_session import AuthSession
from app.models.company import Company
from app.models.orthodontics import (
    OrthodonticsDentistAssignment,
    OrthodonticsEntitlement,
)
from app.models.periodontogram import (
    PeriodontogramPilotCompanyGate,
    PeriodontogramPilotDentistAuthorization,
)
from app.models.role import Role
from app.models.user import User


TEST_PASSWORD = "DentiaTestPassword123!"


def _status_path(company_id, action: str) -> str:
    return f"/api/platform/companies/{company_id}/{action}"


def _promote_to_platform_admin(db_session, actor) -> None:
    role = db_session.scalar(
        select(Role).where(
            Role.company_id == actor.user.company_id,
            Role.code == "PLATFORM_ADMIN",
        )
    )
    assert role is not None
    db_session.add(
        UserRole(
            company_id=actor.user.company_id,
            user_id=actor.user.id,
            role_id=role.id,
            created_by=actor.user.id,
        )
    )
    db_session.commit()


def _login(api_client, actor):
    return api_client.post(
        "/api/auth/login",
        json={"email": actor.user.email, "password": TEST_PASSWORD},
    )


def test_platform_admin_deactivates_and_reactivates_another_company(
    api_client,
    db_session,
    security_world,
) -> None:
    company_id = security_world.tenant_a.company.id

    deactivated = api_client.post(
        _status_path(company_id, "deactivate"),
        token=security_world.platform_admin.token,
        json={"reason": "Validación sintética"},
    )
    assert deactivated.status_code == 200, deactivated.text
    assert deactivated.json()["message"] == "Clínica desactivada."
    assert deactivated.json()["company"]["status"] == "Inactiva"
    assert deactivated.json()["company"]["is_active"] is False

    db_session.expire_all()
    company = db_session.get(Company, company_id)
    assert company is not None
    assert company.status == "Inactiva"
    assert company.is_active is False

    reactivated = api_client.post(
        _status_path(company_id, "reactivate"),
        token=security_world.platform_admin.token,
        json={},
    )
    assert reactivated.status_code == 200, reactivated.text
    assert reactivated.json()["message"] == "Clínica reactivada."
    assert reactivated.json()["company"]["status"] == "Activa"
    assert reactivated.json()["company"]["is_active"] is True


def test_deactivation_blocks_tenant_and_reactivation_allows_new_login(
    api_client,
    db_session,
    security_world,
) -> None:
    tenant = security_world.tenant_a
    original_user_state = (tenant.admin.user.status, tenant.admin.user.is_active)

    response = api_client.post(
        _status_path(tenant.company.id, "deactivate"),
        token=security_world.platform_admin.token,
    )
    assert response.status_code == 200, response.text

    denied = api_client.get("/api/auth/me", token=tenant.admin.token)
    assert denied.status_code == 401, denied.text
    blocked_login = _login(api_client, tenant.admin)
    assert blocked_login.status_code == 401, blocked_login.text

    db_session.expire_all()
    user = db_session.get(User, tenant.admin.user.id)
    dentist = db_session.get(Dentist, tenant.dentist_profile.id)
    assert user is not None and (user.status, user.is_active) == original_user_state
    assert dentist is not None and dentist.status == "Activo" and dentist.is_active is True

    reactivated = api_client.post(
        _status_path(tenant.company.id, "reactivate"),
        token=security_world.platform_admin.token,
    )
    assert reactivated.status_code == 200, reactivated.text
    recovered_login = _login(api_client, tenant.admin)
    assert recovered_login.status_code == 200, recovered_login.text
    assert recovered_login.json()["user"]["company_id"] == str(tenant.company.id)


@pytest.mark.parametrize(
    "actor_name",
    ["admin", "dentist_admin", "dentist", "secretary"],
)
def test_tenant_roles_cannot_change_company_status(
    api_client,
    security_world,
    actor_name: str,
) -> None:
    actor = getattr(security_world.tenant_a, actor_name)
    target_id = security_world.tenant_b.company.id

    response = api_client.post(
        _status_path(target_id, "deactivate"),
        token=actor.token,
    )
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "No tienes permisos para realizar esta acción."


def test_deactivation_is_idempotent_and_audited_once_per_transition(
    api_client,
    db_session,
    security_world,
) -> None:
    company_id = security_world.tenant_a.company.id
    token = security_world.platform_admin.token

    first = api_client.post(
        _status_path(company_id, "deactivate"),
        token=token,
        json={"reason": "Piloto finalizado"},
    )
    second = api_client.post(
        _status_path(company_id, "deactivate"),
        token=token,
        json={"reason": "No debe duplicarse"},
    )
    assert first.status_code == second.status_code == 200
    assert second.json()["message"] == "La clínica ya estaba inactiva."

    first_reactivation = api_client.post(
        _status_path(company_id, "reactivate"),
        token=token,
    )
    second_reactivation = api_client.post(
        _status_path(company_id, "reactivate"),
        token=token,
    )
    assert first_reactivation.status_code == second_reactivation.status_code == 200
    assert second_reactivation.json()["message"] == "La clínica ya estaba activa."

    db_session.expire_all()
    events = list(
        db_session.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.company_id == company_id,
                AuditEvent.action.in_(["COMPANY_DEACTIVATED", "COMPANY_REACTIVATED"]),
            )
            .order_by(AuditEvent.occurred_at)
        )
    )
    assert [event.action for event in events] == [
        "COMPANY_DEACTIVATED",
        "COMPANY_REACTIVATED",
    ]
    assert events[0].user_id == security_world.platform_admin.user.id
    assert events[0].entity_id == company_id
    assert events[0].detail == {
        "previous_status": "Activa",
        "previous_is_active": True,
        "new_status": "Inactiva",
        "new_is_active": False,
        "reason": "Piloto finalizado",
    }
    assert events[1].detail == {
        "previous_status": "Inactiva",
        "previous_is_active": False,
        "new_status": "Activa",
        "new_is_active": True,
    }


def test_concurrent_deactivation_serializes_to_one_transition(
    api_client,
    db_session,
    security_world,
) -> None:
    company_id = security_world.tenant_a.company.id
    barrier = Barrier(2)

    def deactivate():
        barrier.wait(timeout=5)
        return api_client.post(
            _status_path(company_id, "deactivate"),
            token=security_world.platform_admin.token,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _index: deactivate(), range(2)))

    assert [response.status_code for response in responses] == [200, 200]
    assert sorted(response.json()["message"] for response in responses) == [
        "Clínica desactivada.",
        "La clínica ya estaba inactiva.",
    ]

    db_session.expire_all()
    assert (
        db_session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.company_id == company_id,
                AuditEvent.action == "COMPANY_DEACTIVATED",
            )
        )
        == 1
    )


def test_deactivation_revokes_sessions_without_changing_users(
    api_client,
    db_session,
    security_world,
) -> None:
    company_id = security_world.tenant_a.company.id
    user_states = {
        user.id: (user.status, user.is_active)
        for user in db_session.scalars(select(User).where(User.company_id == company_id))
    }

    response = api_client.post(
        _status_path(company_id, "deactivate"),
        token=security_world.platform_admin.token,
    )
    assert response.status_code == 200, response.text

    db_session.expire_all()
    sessions = list(
        db_session.scalars(select(AuthSession).where(AuthSession.company_id == company_id))
    )
    assert sessions
    assert all(not item.is_active for item in sessions)
    assert all(item.revoked_at is not None for item in sessions)
    assert all(item.revoke_reason == "COMPANY_DEACTIVATED" for item in sessions)
    assert all(item.revoked_by == security_world.platform_admin.user.id for item in sessions)
    assert {
        user.id: (user.status, user.is_active)
        for user in db_session.scalars(select(User).where(User.company_id == company_id))
    } == user_states


def test_company_status_preserves_clinical_and_module_data(
    api_client,
    db_session,
    security_world,
) -> None:
    tenant = security_world.tenant_a
    now = datetime.now(timezone.utc)
    entitlement = OrthodonticsEntitlement(
        company_id=tenant.company.id,
        status="ACTIVE",
        seat_limit=1,
        effective_from=now,
        created_by=security_world.platform_admin.user.id,
        updated_by=security_world.platform_admin.user.id,
    )
    db_session.add(entitlement)
    db_session.flush()
    assignment = OrthodonticsDentistAssignment(
        company_id=tenant.company.id,
        entitlement_id=entitlement.id,
        dentist_id=tenant.dentist_profile.id,
        is_active=True,
        assigned_at=now,
        assigned_by_user_id=security_world.platform_admin.user.id,
    )
    perio_gate = PeriodontogramPilotCompanyGate(
        company_id=tenant.company.id,
        is_enabled=True,
        enabled_at=now,
        enabled_by_user_id=security_world.platform_admin.user.id,
    )
    perio_authorization = PeriodontogramPilotDentistAuthorization(
        company_id=tenant.company.id,
        dentist_id=tenant.dentist_profile.id,
        is_active=True,
        authorized_at=now,
        authorized_by_user_id=security_world.platform_admin.user.id,
    )
    db_session.add_all([assignment, perio_gate, perio_authorization])
    db_session.commit()

    clinical_objects = [
        tenant.patient,
        tenant.appointment,
        tenant.treatment,
        tenant.clinical_record,
        tenant.evolution,
        tenant.odontogram,
        tenant.clinical_document,
    ]
    clinical_state = {
        (type(item), item.id): item.updated_at for item in clinical_objects
    }
    module_state = {
        "entitlement": (entitlement.id, entitlement.status, entitlement.seat_limit),
        "assignment": (assignment.id, assignment.is_active, assignment.revoked_at),
        "perio_gate": (perio_gate.id, perio_gate.is_enabled),
        "perio_authorization": (
            perio_authorization.id,
            perio_authorization.is_active,
            perio_authorization.revoked_at,
        ),
    }

    for action in ("deactivate", "reactivate"):
        response = api_client.post(
            _status_path(tenant.company.id, action),
            token=security_world.platform_admin.token,
        )
        assert response.status_code == 200, response.text

    db_session.expire_all()
    for (model, object_id), updated_at in clinical_state.items():
        persisted = db_session.get(model, object_id)
        assert persisted is not None
        assert persisted.updated_at == updated_at

    persisted_entitlement = db_session.get(OrthodonticsEntitlement, entitlement.id)
    persisted_assignment = db_session.get(OrthodonticsDentistAssignment, assignment.id)
    persisted_gate = db_session.get(PeriodontogramPilotCompanyGate, perio_gate.id)
    persisted_authorization = db_session.get(
        PeriodontogramPilotDentistAuthorization,
        perio_authorization.id,
    )
    assert persisted_entitlement is not None
    assert module_state["entitlement"] == (
        persisted_entitlement.id,
        persisted_entitlement.status,
        persisted_entitlement.seat_limit,
    )
    assert persisted_assignment is not None
    assert module_state["assignment"] == (
        persisted_assignment.id,
        persisted_assignment.is_active,
        persisted_assignment.revoked_at,
    )
    assert persisted_gate is not None
    assert module_state["perio_gate"] == (persisted_gate.id, persisted_gate.is_enabled)
    assert persisted_authorization is not None
    assert module_state["perio_authorization"] == (
        persisted_authorization.id,
        persisted_authorization.is_active,
        persisted_authorization.revoked_at,
    )


def test_platform_admin_cannot_deactivate_own_company(
    api_client,
    db_session,
    security_world,
) -> None:
    company_id = security_world.platform_admin.user.company_id
    response = api_client.post(
        _status_path(company_id, "deactivate"),
        token=security_world.platform_admin.token,
    )
    assert response.status_code == 409, response.text
    assert "bloquearía tu acceso actual de administración de plataforma" in response.text

    db_session.expire_all()
    company = db_session.get(Company, company_id)
    assert company is not None and company.is_active and company.status == "Activa"
    assert (
        db_session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.company_id == company_id,
                AuditEvent.action == "COMPANY_DEACTIVATED",
            )
        )
        == 0
    )


def test_second_platform_admin_can_deactivate_and_reactivate_other_company(
    api_client,
    db_session,
    security_world,
) -> None:
    second_platform_admin = security_world.tenant_b.admin
    _promote_to_platform_admin(db_session, second_platform_admin)
    target_id = security_world.tenant_a.company.id

    deactivated = api_client.post(
        _status_path(target_id, "deactivate"),
        token=second_platform_admin.token,
    )
    assert deactivated.status_code == 200, deactivated.text
    reactivated = api_client.post(
        _status_path(target_id, "reactivate"),
        token=second_platform_admin.token,
    )
    assert reactivated.status_code == 200, reactivated.text

    own_context = api_client.get(
        "/api/auth/me",
        token=second_platform_admin.token,
    )
    assert own_context.status_code == 200, own_context.text
    assert "PLATFORM_ADMIN" in own_context.json()["roles"]


def test_inactive_company_remains_visible_and_reactivatable_from_platform(
    api_client,
    security_world,
) -> None:
    company_id = security_world.tenant_a.company.id
    token = security_world.platform_admin.token
    assert api_client.post(
        _status_path(company_id, "deactivate"),
        token=token,
    ).status_code == 200

    detail = api_client.get(f"/api/platform/companies/{company_id}", token=token)
    listing = api_client.get("/api/platform/companies", token=token)
    assert detail.status_code == 200, detail.text
    assert detail.json()["status"] == "Inactiva"
    listed = next(item for item in listing.json()["items"] if item["id"] == str(company_id))
    assert listed["status"] == "Inactiva"
    assert api_client.post(
        _status_path(company_id, "reactivate"),
        token=token,
    ).status_code == 200


def test_platform_status_access_does_not_grant_cross_tenant_clinical_access(
    api_client,
    security_world,
) -> None:
    company_id = security_world.tenant_a.company.id
    token = security_world.platform_admin.token
    assert api_client.post(
        _status_path(company_id, "deactivate"),
        token=token,
    ).status_code == 200
    assert api_client.post(
        _status_path(company_id, "reactivate"),
        token=token,
    ).status_code == 200

    denied = api_client.get(
        f"/api/patients/{security_world.tenant_a.patient.id}",
        token=token,
    )
    assert denied.status_code == 403, denied.text
