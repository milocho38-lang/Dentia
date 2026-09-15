from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.agenda import Appointment, Dentist, DentistSite
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalTimelineEvent
from app.models.orthodontics import OrthodonticCase


def _enable(api_client, world, tenant=None, *, seats: int = 1):
    tenant = tenant or world.tenant_a
    return api_client.put(
        f"/api/platform/companies/{tenant.company.id}/orthodontics-entitlement",
        token=world.platform_admin.token,
        json={"enabled": True, "seat_limit": seats},
    )


def _assign(api_client, tenant, dentist_id):
    return api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(dentist_id)},
    )


def _prepare(api_client, world, tenant=None, *, seats: int = 1):
    tenant = tenant or world.tenant_a
    enabled = _enable(api_client, world, tenant, seats=seats)
    assert enabled.status_code == 200, enabled.text
    assigned = _assign(api_client, tenant, tenant.dentist_profile.id)
    assert assigned.status_code == 200, assigned.text
    return tenant


def _create(api_client, tenant, **payload):
    return api_client.post(
        f"/api/patients/{tenant.patient.id}/orthodontics/cases",
        token=tenant.dentist_admin.token,
        json=payload,
    )


def _second_dentist(db_session, tenant, *, site=None) -> Dentist:
    dentist = Dentist(
        company_id=tenant.company.id,
        user_id=tenant.dentist.user.id,
        name=tenant.dentist.user.name,
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
            site_id=(site or tenant.site_1).id,
            is_active=True,
            created_by=tenant.admin.user.id,
        )
    )
    db_session.commit()
    return dentist


def test_case_access_requires_entitlement_assignment_clinical_actor_and_tenant(
    api_client, security_world
) -> None:
    tenant = security_world.tenant_a
    path = f"/api/patients/{tenant.patient.id}/orthodontics"
    assert api_client.get(path, token=tenant.dentist_admin.token).status_code == 403

    _prepare(api_client, security_world)
    assert api_client.get(path, token=tenant.dentist_admin.token).status_code == 200
    assert api_client.get(path, token=tenant.dentist.token).status_code == 403
    assert api_client.get(path, token=tenant.admin.token).status_code == 403
    assert api_client.get(path, token=tenant.secretary.token).status_code == 403
    assert api_client.get(path, token=security_world.platform_admin.token).status_code == 403
    create_path = f"/api/patients/{tenant.patient.id}/orthodontics/cases"
    assert api_client.post(create_path, token=tenant.dentist.token, json={}).status_code == 403
    assert api_client.post(create_path, token=tenant.admin.token, json={}).status_code == 403
    assert api_client.post(create_path, token=tenant.secretary.token, json={}).status_code == 403
    assert api_client.post(create_path, token=security_world.platform_admin.token, json={}).status_code == 403

    other = _prepare(api_client, security_world, security_world.tenant_b)
    wrong_tenant = api_client.get(path, token=other.dentist_admin.token)
    assert wrong_tenant.status_code == 404
    assert wrong_tenant.json()["detail"]["code"] == "ORTHODONTICS_PATIENT_WRONG_TENANT"
    case = _create(api_client, tenant).json()["case"]
    assert api_client.get(
        f"/api/orthodontics/cases/{case['id']}",
        token=other.dentist_admin.token,
    ).status_code == 404
    assert api_client.patch(
        f"/api/orthodontics/cases/{case['id']}",
        token=other.dentist_admin.token,
        json={"row_version": case["row_version"], "treatment_plan": "No permitido"},
    ).status_code == 404


def test_case_create_summary_and_general_timeline_are_real_and_audited(
    api_client, db_session, security_world
) -> None:
    tenant = _prepare(api_client, security_world)
    future = datetime.now(timezone.utc) + timedelta(days=10)
    appointment = Appointment(
        company_id=tenant.company.id,
        patient_id=tenant.patient.id,
        dentist_id=tenant.dentist_profile.id,
        site_id=tenant.site_1.id,
        appointment_type_id=tenant.appointment_type.id,
        starts_at=future,
        ends_at=future + timedelta(minutes=30),
        reason="Control de Ortodoncia",
        status="Programada",
        created_by=tenant.dentist_admin.user.id,
        updated_by=tenant.dentist_admin.user.id,
    )
    db_session.add(appointment)
    db_session.commit()

    created = _create(
        api_client,
        tenant,
        treatment_plan="Alineación y nivelación",
        current_appliance_summary="Brackets instalados",
    )
    assert created.status_code == 201, created.text
    case = created.json()["case"]
    assert case["status"] == "DRAFT"
    assert case["responsible_dentist_id"] == str(tenant.dentist_profile.id)

    workspace = api_client.get(
        f"/api/patients/{tenant.patient.id}/orthodontics",
        token=tenant.dentist_admin.token,
    )
    assert workspace.status_code == 200, workspace.text
    body = workspace.json()
    assert body["record_label"] == "Historia clínica de Ortodoncia"
    assert body["active_case"]["treatment_plan"] == "Alineación y nivelación"
    assert body["summary"]["case"]["current_appliance_summary"] == "Brackets instalados"
    assert body["summary"]["last_visit"] is None
    assert body["summary"]["what_was_done"] is None
    assert body["summary"]["next_session_instructions"] is None
    assert body["summary"]["next_clinical_control"] is None
    assert body["summary"]["active_alerts"] == []
    assert body["summary"]["next_appointment"]["id"] == str(appointment.id)

    actions = {
        item.action
        for item in db_session.scalars(
            select(AuditEvent).where(AuditEvent.entity_id == case["id"])
        )
    }
    assert "ORTHODONTIC_CASE_CREATED" in actions
    timeline = db_session.scalar(
        select(ClinicalTimelineEvent).where(
            ClinicalTimelineEvent.entity_id == case["id"],
            ClinicalTimelineEvent.event_type == "ORTHODONTIC_CASE_CREATED",
        )
    )
    assert timeline is not None


def test_one_open_case_and_concurrent_create_are_enforced(
    api_client, security_world
) -> None:
    tenant = _prepare(api_client, security_world)

    def create_case():
        return _create(api_client, tenant).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: create_case(), range(2)))
    assert sorted(statuses) == [201, 409]

    repeated = _create(api_client, tenant)
    assert repeated.status_code == 409
    assert repeated.json()["detail"]["code"] == "ORTHODONTICS_CASE_ALREADY_OPEN"


def test_lifecycle_closed_immutability_history_and_new_case(
    api_client, security_world
) -> None:
    tenant = _prepare(api_client, security_world)
    created = _create(api_client, tenant).json()["case"]
    invalid = api_client.post(
        f"/api/orthodontics/cases/{created['id']}/complete",
        token=tenant.dentist_admin.token,
        json={"row_version": created["row_version"]},
    )
    assert invalid.status_code == 409

    activated = api_client.post(
        f"/api/orthodontics/cases/{created['id']}/activate",
        token=tenant.dentist_admin.token,
        json={"row_version": created["row_version"]},
    )
    assert activated.status_code == 200, activated.text
    active = activated.json()["case"]
    assert active["status"] == "ACTIVE" and active["started_at"]

    suspended = api_client.post(
        f"/api/orthodontics/cases/{created['id']}/suspend",
        token=tenant.dentist_admin.token,
        json={"row_version": active["row_version"], "reason": "Pausa acordada"},
    )
    assert suspended.status_code == 200, suspended.text
    paused = suspended.json()["case"]
    assert paused["status"] == "SUSPENDED"
    resumed = api_client.post(
        f"/api/orthodontics/cases/{created['id']}/resume",
        token=tenant.dentist_admin.token,
        json={"row_version": paused["row_version"]},
    )
    assert resumed.status_code == 200, resumed.text
    active = resumed.json()["case"]
    assert active["status"] == "ACTIVE"

    completed = api_client.post(
        f"/api/orthodontics/cases/{created['id']}/complete",
        token=tenant.dentist_admin.token,
        json={"row_version": active["row_version"]},
    )
    assert completed.status_code == 200, completed.text
    closed = completed.json()["case"]
    assert closed["status"] == "COMPLETED" and closed["completed_at"]
    edit_closed = api_client.patch(
        f"/api/orthodontics/cases/{created['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": closed["row_version"], "treatment_plan": "No permitido"},
    )
    assert edit_closed.status_code == 409
    assert edit_closed.json()["detail"]["code"] == "ORTHODONTICS_CASE_CLOSED"

    second = _create(api_client, tenant)
    assert second.status_code == 201, second.text
    workspace = api_client.get(
        f"/api/patients/{tenant.patient.id}/orthodontics",
        token=tenant.dentist_admin.token,
    ).json()
    assert workspace["active_case"]["id"] == second.json()["case"]["id"]
    assert [item["id"] for item in workspace["historical_cases"]] == [created["id"]]


def test_discontinue_requires_reason_and_is_exposed_as_historical_status(
    api_client, db_session, security_world
) -> None:
    tenant = _prepare(api_client, security_world)
    draft = _create(api_client, tenant).json()["case"]
    active = api_client.post(
        f"/api/orthodontics/cases/{draft['id']}/activate",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"]},
    ).json()["case"]
    missing = api_client.post(
        f"/api/orthodontics/cases/{draft['id']}/discontinue",
        token=tenant.dentist_admin.token,
        json={"row_version": active["row_version"]},
    )
    assert missing.status_code == 422
    stopped = api_client.post(
        f"/api/orthodontics/cases/{draft['id']}/discontinue",
        token=tenant.dentist_admin.token,
        json={"row_version": active["row_version"], "reason": "Cambio de ciudad"},
    )
    assert stopped.status_code == 200, stopped.text
    assert stopped.json()["case"]["display_status"] == "DISCONTINUED"
    assert stopped.json()["case"]["closure_notes"] == "Cambio de ciudad"
    audit = db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == draft["id"],
            AuditEvent.action == "ORTHODONTIC_CASE_DISCONTINUED",
        )
    )
    assert audit is not None
    assert "Cambio de ciudad" not in str(audit.detail)


def test_responsible_must_be_active_assigned_same_tenant_and_change_is_audited(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    second = _second_dentist(db_session, tenant)
    _prepare(api_client, security_world, seats=2)
    unassigned = _create(
        api_client, tenant, responsible_dentist_id=str(second.id)
    )
    assert unassigned.status_code == 409
    assert unassigned.json()["detail"]["code"] == "ORTHODONTICS_RESPONSIBLE_NOT_ASSIGNED"
    foreign = _create(
        api_client,
        tenant,
        responsible_dentist_id=str(security_world.tenant_b.dentist_profile.id),
    )
    assert foreign.status_code == 409
    assert foreign.json()["detail"]["code"] == "ORTHODONTICS_RESPONSIBLE_NOT_ASSIGNED"

    assigned = _assign(api_client, tenant, second.id)
    assert assigned.status_code == 200, assigned.text
    created = _create(api_client, tenant).json()["case"]
    changed = api_client.post(
        f"/api/orthodontics/cases/{created['id']}/change-responsible",
        token=tenant.dentist_admin.token,
        json={
            "row_version": created["row_version"],
            "responsible_dentist_id": str(second.id),
        },
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["case"]["responsible_dentist_id"] == str(second.id)
    audit = db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == created["id"],
            AuditEvent.action == "ORTHODONTIC_CASE_RESPONSIBLE_CHANGED",
        )
    )
    assert audit is not None


def test_responsible_must_have_scope_in_case_site(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    other_site_dentist = _second_dentist(db_session, tenant, site=tenant.site_2)
    _prepare(api_client, security_world, seats=2)
    assert _assign(api_client, tenant, other_site_dentist.id).status_code == 200
    denied = _create(
        api_client,
        tenant,
        responsible_dentist_id=str(other_site_dentist.id),
    )
    assert denied.status_code == 409
    assert denied.json()["detail"]["code"] == "ORTHODONTICS_RESPONSIBLE_NOT_ASSIGNED"


def test_plan_appliance_updates_are_versioned_and_audited_without_clinical_text(
    api_client, db_session, security_world
) -> None:
    tenant = _prepare(api_client, security_world)
    created = _create(api_client, tenant).json()["case"]
    updated = api_client.patch(
        f"/api/orthodontics/cases/{created['id']}",
        token=tenant.dentist_admin.token,
        json={
            "row_version": created["row_version"],
            "treatment_plan": "Texto clínico reservado",
            "current_appliance_summary": "Aparatología reservada",
        },
    )
    assert updated.status_code == 200, updated.text
    current = updated.json()["case"]
    assert current["row_version"] == created["row_version"] + 1
    partial = api_client.patch(
        f"/api/orthodontics/cases/{created['id']}",
        token=tenant.dentist_admin.token,
        json={
            "row_version": current["row_version"],
            "treatment_plan": "Plan actualizado sin tocar aparatología",
        },
    )
    assert partial.status_code == 200, partial.text
    assert partial.json()["case"]["current_appliance_summary"] == "Aparatología reservada"
    stale = api_client.patch(
        f"/api/orthodontics/cases/{created['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": created["row_version"], "treatment_plan": "Stale"},
    )
    assert stale.status_code == 409
    events = list(
        db_session.scalars(
            select(AuditEvent).where(AuditEvent.entity_id == created["id"])
        )
    )
    actions = {event.action for event in events}
    assert "ORTHODONTIC_CASE_PLAN_UPDATED" in actions
    assert "ORTHODONTIC_CASE_APPLIANCE_UPDATED" in actions
    assert all("Texto clínico reservado" not in str(event.detail) for event in events)


def test_entitlement_or_assignment_revocation_blocks_writes_without_deleting_case(
    api_client, db_session, security_world
) -> None:
    tenant = _prepare(api_client, security_world)
    created = _create(api_client, tenant).json()["case"]
    assignment = api_client.get(
        "/api/orthodontics/assignments", token=tenant.admin.token
    ).json()["items"][0]
    revoked = api_client.post(
        f"/api/orthodontics/assignments/{assignment['id']}/revoke",
        token=tenant.admin.token,
        json={"reason": "Cambio de cobertura"},
    )
    assert revoked.status_code == 200, revoked.text
    blocked = api_client.patch(
        f"/api/orthodontics/cases/{created['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": created["row_version"], "treatment_plan": "No debe guardar"},
    )
    assert blocked.status_code == 403
    assert db_session.get(OrthodonticCase, created["id"]) is not None


def test_inactive_responsible_is_preserved_and_another_assigned_dentist_can_take_over(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    second = _second_dentist(db_session, tenant)
    _prepare(api_client, security_world, seats=2)
    assert _assign(api_client, tenant, second.id).status_code == 200
    created = _create(api_client, tenant).json()["case"]

    deactivated = api_client.post(
        f"/api/users/{tenant.dentist_admin.user.id}/deactivate",
        token=tenant.admin.token,
    )
    assert deactivated.status_code == 200, deactivated.text
    workspace = api_client.get(
        f"/api/patients/{tenant.patient.id}/orthodontics",
        token=tenant.dentist.token,
    )
    assert workspace.status_code == 200, workspace.text
    assert workspace.json()["active_case"]["responsible_dentist_id"] == str(
        tenant.dentist_profile.id
    )
    changed = api_client.post(
        f"/api/orthodontics/cases/{created['id']}/change-responsible",
        token=tenant.dentist.token,
        json={
            "row_version": created["row_version"],
            "responsible_dentist_id": str(second.id),
        },
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["case"]["responsible_dentist_id"] == str(second.id)
    assert db_session.get(OrthodonticCase, created["id"]) is not None


def test_country_label_comes_from_company_not_browser_locale(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    tenant.company.country = "CL"
    db_session.commit()
    _prepare(api_client, security_world)
    response = api_client.get(
        f"/api/patients/{tenant.patient.id}/orthodontics",
        token=tenant.dentist_admin.token,
        headers={"Accept-Language": "es-CO"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["record_label"] == "Ficha clínica de Ortodoncia"
