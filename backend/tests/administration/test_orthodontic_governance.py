from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.agenda import Dentist, DentistSite
from app.models.clinical_record import ClinicalTimelineEvent
from app.models.orthodontics import (
    OrthodonticClinicalRecordVersion,
    OrthodonticEvolution,
)


def _prepare_active_case(api_client, world):
    tenant = world.tenant_a
    enabled = api_client.put(
        f"/api/platform/companies/{tenant.company.id}/orthodontics-entitlement",
        token=world.platform_admin.token,
        json={"enabled": True, "seat_limit": 1},
    )
    assert enabled.status_code == 200, enabled.text
    assigned = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(tenant.dentist_profile.id)},
    )
    assert assigned.status_code == 200, assigned.text
    created = api_client.post(
        f"/api/patients/{tenant.patient.id}/orthodontics/cases",
        token=tenant.dentist_admin.token,
        json={"treatment_plan": "Plan ORT-5"},
    )
    assert created.status_code == 201, created.text
    draft = created.json()["case"]
    activated = api_client.post(
        f"/api/orthodontics/cases/{draft['id']}/activate",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"]},
    )
    assert activated.status_code == 200, activated.text
    return tenant, activated.json()["case"]


def _signed_evolution(api_client, tenant, case):
    created = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/evolutions",
        token=tenant.dentist_admin.token,
        json={"performed_summary": "Control ortodóncico"},
    )
    assert created.status_code == 201, created.text
    draft = created.json()
    signed = api_client.post(
        f"/api/orthodontics/evolutions/{draft['id']}/sign",
        token=tenant.dentist_admin.token,
        json={
            "row_version": draft["row_version"],
            "clinical_evolution_version": draft["clinical_evolution_version"],
            "confirm_complete": True,
        },
    )
    assert signed.status_code == 200, signed.text
    return signed.json()


def _finalized_record(api_client, tenant, case):
    created = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert created.status_code == 201, created.text
    draft = created.json()["record"]["current_version"]
    updated = api_client.patch(
        f"/api/orthodontics/cases/{case['id']}/record/versions/{draft['id']}",
        token=tenant.dentist_admin.token,
        json={
            "row_version": draft["row_version"],
            "content": {"chief_complaint": "Seguimiento ORT-5"},
        },
    )
    assert updated.status_code == 200, updated.text
    version = updated.json()["record"]["current_version"]
    finalized = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/record/versions/{version['id']}/finalize",
        token=tenant.dentist_admin.token,
        json={"row_version": version["row_version"]},
    )
    assert finalized.status_code == 200, finalized.text
    return finalized.json()["record"]["current_version"]


def test_suspended_case_is_read_only_and_reactivation_is_audited(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    suspended = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/suspend",
        token=tenant.dentist_admin.token,
        json={"row_version": case["row_version"], "reason": "Pausa clínica"},
    )
    assert suspended.status_code == 200, suspended.text
    paused = suspended.json()["case"]

    blocked = api_client.patch(
        f"/api/orthodontics/cases/{case['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": paused["row_version"], "treatment_plan": "No permitido"},
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "ORTHODONTICS_CASE_SUSPENDED"

    resumed = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/resume",
        token=tenant.dentist_admin.token,
        json={"row_version": paused["row_version"]},
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["case"]["status"] == "ACTIVE"
    assert db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == case["id"],
            AuditEvent.action == "ORTHODONTIC_CASE_REACTIVATED",
        )
    ) is not None


def test_entitlement_loss_preserves_all_history_and_blocks_new_work(
    api_client, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    evolution = _signed_evolution(api_client, tenant, case)
    record_version = _finalized_record(api_client, tenant, case)
    disabled = api_client.put(
        f"/api/platform/companies/{tenant.company.id}/orthodontics-entitlement",
        token=security_world.platform_admin.token,
        json={"enabled": False, "seat_limit": 1},
    )
    assert disabled.status_code == 200, disabled.text

    assert api_client.get(
        f"/api/orthodontics/cases/{case['id']}",
        token=tenant.dentist_admin.token,
    ).status_code == 200
    history = api_client.get(
        f"/api/orthodontics/cases/{case['id']}/evolutions",
        token=tenant.dentist_admin.token,
    )
    assert history.status_code == 200, history.text
    assert history.json()["items"][0]["id"] == evolution["id"]
    record = api_client.get(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert record.status_code == 200, record.text
    assert record.json()["current_version"]["id"] == record_version["id"]
    assert record.json()["can_edit"] is False

    assert api_client.patch(
        f"/api/orthodontics/cases/{case['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": case["row_version"], "treatment_plan": "No permitido"},
    ).status_code == 403
    assert api_client.post(
        f"/api/orthodontics/cases/{case['id']}/evolutions",
        token=tenant.dentist_admin.token,
        json={"performed_summary": "No permitido"},
    ).status_code == 403


def test_signed_evolution_and_finalized_record_report_integrity_and_detect_tamper(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    evolution = _signed_evolution(api_client, tenant, case)
    version = _finalized_record(api_client, tenant, case)
    assert evolution["integrity_status"] == "PASS"
    assert version["integrity_status"] == "PASS"

    extension = db_session.get(OrthodonticEvolution, evolution["id"])
    extension.alert_text = "Alteración controlada"
    record_version = db_session.get(OrthodonticClinicalRecordVersion, version["id"])
    record_version.content = {"chief_complaint": "Alteración controlada"}
    db_session.commit()

    evolution_read = api_client.get(
        f"/api/orthodontics/evolutions/{evolution['id']}",
        token=tenant.dentist_admin.token,
    )
    assert evolution_read.status_code == 200, evolution_read.text
    assert evolution_read.json()["integrity_status"] == "FAIL"
    record_read = api_client.get(
        f"/api/orthodontics/cases/{case['id']}/record?version_id={version['id']}",
        token=tenant.dentist_admin.token,
    )
    assert record_read.status_code == 200, record_read.text
    assert record_read.json()["current_version"]["integrity_status"] == "FAIL"


def test_retired_catalog_option_blocks_sign_but_keeps_draft_snapshot(
    api_client, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    option = api_client.post(
        "/api/orthodontics/catalogs/ARCH_MATERIAL/options",
        token=tenant.admin.token,
        json={"label": "Material temporal ORT-5"},
    )
    assert option.status_code == 201, option.text
    selected = option.json()
    created = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/evolutions",
        token=tenant.dentist_admin.token,
        json={
            "performed_summary": "Control con opción temporal",
            "upper_material_option_id": selected["id"],
        },
    )
    assert created.status_code == 201, created.text
    draft = created.json()
    retired = api_client.post(
        f"/api/orthodontics/catalog-options/{selected['id']}/retire",
        token=tenant.admin.token,
    )
    assert retired.status_code == 200, retired.text

    signed = api_client.post(
        f"/api/orthodontics/evolutions/{draft['id']}/sign",
        token=tenant.dentist_admin.token,
        json={
            "row_version": draft["row_version"],
            "clinical_evolution_version": draft["clinical_evolution_version"],
            "confirm_complete": True,
        },
    )
    assert signed.status_code == 409
    assert signed.json()["detail"]["code"] == "ORTHODONTIC_CATALOG_OPTION_INACTIVE"
    preserved = api_client.get(
        f"/api/orthodontics/evolutions/{draft['id']}",
        token=tenant.dentist_admin.token,
    )
    assert preserved.status_code == 200
    assert preserved.json()["upper_material"]["label"] == selected["label"]


def test_responsible_availability_and_change_timeline_are_explicit(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    assignment = api_client.get(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
    ).json()["items"][0]
    revoked = api_client.post(
        f"/api/orthodontics/assignments/{assignment['id']}/revoke",
        token=tenant.admin.token,
        json={"reason": "Cambio de responsable"},
    )
    assert revoked.status_code == 200, revoked.text
    workspace = api_client.get(
        f"/api/patients/{tenant.patient.id}/orthodontics",
        token=tenant.dentist_admin.token,
    )
    assert workspace.status_code == 200, workspace.text
    assert workspace.json()["active_case"]["responsible_dentist_available"] is False

    # The original responsible identity and case remain intact after revocation.
    assert workspace.json()["active_case"]["responsible_dentist_id"] == str(
        tenant.dentist_profile.id
    )
    replacement = Dentist(
        company_id=tenant.company.id,
        user_id=tenant.dentist.user.id,
        name=tenant.dentist.user.name,
        status="Activo",
        is_active=True,
        created_by=tenant.admin.user.id,
    )
    db_session.add(replacement)
    db_session.flush()
    db_session.add(
        DentistSite(
            company_id=tenant.company.id,
            dentist_id=replacement.id,
            site_id=tenant.site_1.id,
            is_active=True,
            created_by=tenant.admin.user.id,
        )
    )
    db_session.commit()
    assigned = api_client.post(
        "/api/orthodontics/assignments",
        token=tenant.admin.token,
        json={"dentist_id": str(replacement.id)},
    )
    assert assigned.status_code == 200, assigned.text
    changed = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/change-responsible",
        token=tenant.dentist.token,
        json={
            "row_version": case["row_version"],
            "responsible_dentist_id": str(replacement.id),
        },
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["case"]["responsible_dentist_available"] is True
    assert db_session.scalar(
        select(ClinicalTimelineEvent.id).where(
            ClinicalTimelineEvent.entity_id == case["id"],
            ClinicalTimelineEvent.event_type == "ORTHODONTIC_CASE_RESPONSIBLE_CHANGED",
        )
    ) is not None


def test_case_read_and_write_require_dentist_scope_in_case_site(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare_active_case(api_client, security_world)
    dentist_site = db_session.scalar(
        select(DentistSite).where(
            DentistSite.company_id == tenant.company.id,
            DentistSite.dentist_id == tenant.dentist_profile.id,
            DentistSite.site_id == tenant.site_1.id,
        )
    )
    assert dentist_site is not None
    dentist_site.is_active = False
    db_session.commit()

    denied_read = api_client.get(
        f"/api/orthodontics/cases/{case['id']}",
        token=tenant.dentist_admin.token,
    )
    assert denied_read.status_code == 403

    denied_write = api_client.patch(
        f"/api/orthodontics/cases/{case['id']}",
        token=tenant.dentist_admin.token,
        json={"row_version": case["row_version"], "treatment_plan": "No permitido"},
    )
    assert denied_write.status_code == 403

    denied_evolution = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/evolutions",
        token=tenant.dentist_admin.token,
        json={"performed_summary": "No permitido"},
    )
    assert denied_evolution.status_code == 403

    denied_record = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/record",
        token=tenant.dentist_admin.token,
    )
    assert denied_record.status_code == 403
