from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select

from app.core.security_catalog import (
    CLINIC_ADMIN_PERMISSION_CODES,
    DENTIST_ADMIN_PERMISSIONS,
    DENTIST_PERMISSIONS,
    PLATFORM_ADMIN_PERMISSIONS,
    SECRETARY_PERMISSIONS,
)
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalEvolution
from app.models.orthodontics import (
    OrthodonticCatalogOption,
    OrthodonticEvolutionMiniScrew,
)


def _prepare(api_client, world, tenant=None):
    tenant = tenant or world.tenant_a
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
        json={},
    )
    assert created.status_code == 201, created.text
    case = created.json()["case"]
    activated = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/activate",
        token=tenant.dentist_admin.token,
        json={"row_version": case["row_version"]},
    )
    assert activated.status_code == 200, activated.text
    return tenant, activated.json()["case"]


def _base_option(db_session, catalog_type, code, label, value=None, unit=None):
    item = OrthodonticCatalogOption(
        company_id=None,
        catalog_type=catalog_type,
        scope="DENTIA_BASE",
        code=code,
        label=label,
        status="ACTIVE",
        interval_value=value,
        interval_unit=unit,
    )
    db_session.add(item)
    db_session.commit()
    return item


def _create_evolution(api_client, tenant, case_id, **overrides):
    payload = {
        "performed_summary": "Cambio de arcos y control de alineación",
        "notes": "Paciente tolera adecuadamente el tratamiento.",
        **overrides,
    }
    return api_client.post(
        f"/api/orthodontics/cases/{case_id}/evolutions",
        token=tenant.dentist_admin.token,
        json=payload,
    )


def test_catalog_rbac_matches_authorized_matrix(api_client, security_world) -> None:
    administrator = {
        "orthodontics.catalog.view",
        "orthodontics.catalog.manage",
    }
    assert administrator <= CLINIC_ADMIN_PERMISSION_CODES
    assert "orthodontics.catalog.view" in DENTIST_PERMISSIONS
    assert "orthodontics.catalog.manage" not in DENTIST_PERMISSIONS
    assert administrator <= DENTIST_ADMIN_PERMISSIONS
    assert not administrator.intersection(SECRETARY_PERMISSIONS)
    assert not administrator.intersection(PLATFORM_ADMIN_PERMISSIONS)

    path = "/api/orthodontics/catalogs/ARCH_MATERIAL"
    tenant = security_world.tenant_a
    assert api_client.get(path, token=tenant.admin.token).status_code == 200
    assert api_client.get(path, token=tenant.dentist_admin.token).status_code == 200
    assert api_client.get(path, token=tenant.dentist.token).status_code == 200
    assert api_client.get(path, token=tenant.secretary.token).status_code == 403
    assert api_client.get(path, token=security_world.platform_admin.token).status_code == 403
    create_path = f"{path}/options"
    assert api_client.post(create_path, token=tenant.admin.token, json={"label": "Material propio"}).status_code == 201
    assert api_client.post(create_path, token=tenant.dentist_admin.token, json={"label": "Material clínico"}).status_code == 201
    assert api_client.post(create_path, token=tenant.dentist.token, json={"label": "No permitido"}).status_code == 403


def test_structured_draft_miniscrews_control_and_catalog_snapshots(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare(api_client, security_world)
    material = _base_option(db_session, "ARCH_MATERIAL", "NO_CHANGE", "Sin cambios")
    size = _base_option(db_session, "ARCH_SIZE", "NO_ARCH", "Sin arco")
    control = _base_option(db_session, "CONTROL_INTERVAL", "WEEK_4", "4 semanas", 4, "WEEK")
    response = _create_evolution(
        api_client,
        tenant,
        case["id"],
        attended_at="2026-09-14T10:00:00-05:00",
        upper_material_option_id=str(material.id),
        lower_material_option_id=str(material.id),
        upper_size_option_id=str(size.id),
        lower_size_option_id=str(size.id),
        next_control_option_id=str(control.id),
        mini_screws=[
            {"screw_type": "SELF_TAPPING", "location": "INTERRADICULAR", "material": "TITANIUM", "measurement": "1.6 x 8", "notes": None},
            {"screw_type": "SELF_DRILLING", "location": "PALATAL", "material": "STEEL", "measurement": "Medida clínica B", "notes": "Controlar estabilidad"},
        ],
    )
    assert response.status_code == 201, response.text
    item = response.json()
    assert item["status"] == "DRAFT"
    assert item["upper_material"]["code"] == "NO_CHANGE"
    assert item["upper_size"]["code"] == "NO_ARCH"
    assert item["suggested_next_control_date"] == "2026-10-12"
    assert [screw["measurement"] for screw in item["mini_screws"]] == ["1.6 x 8", "Medida clínica B"]
    assert db_session.scalar(select(OrthodonticEvolutionMiniScrew).where(OrthodonticEvolutionMiniScrew.orthodontic_evolution_id == item["id"])) is not None


def test_draft_does_not_feed_summary_but_signed_evolution_does(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare(api_client, security_world)
    control = _base_option(db_session, "CONTROL_INTERVAL", "MONTH_2", "2 meses", 2, "MONTH")
    created = _create_evolution(
        api_client,
        tenant,
        case["id"],
        next_control_option_id=str(control.id),
        next_session_instructions="Revisar higiene y cooperación.",
        alert_text="Controlar resorte superior.",
        alert_active=True,
    )
    assert created.status_code == 201, created.text
    draft = created.json()
    summary_path = f"/api/orthodontics/cases/{case['id']}"
    assert api_client.get(summary_path, token=tenant.dentist_admin.token).json()["last_visit"] is None
    signed = api_client.post(
        f"/api/orthodontics/evolutions/{draft['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"], "clinical_evolution_version": draft["clinical_evolution_version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    signed_item = signed.json()
    assert signed_item["status"] == "SIGNED"
    assert signed_item["orthodontic_payload_hash"]
    parent = db_session.get(ClinicalEvolution, signed_item["clinical_evolution_id"])
    assert parent.content_hash and signed_item["orthodontic_payload_hash"] != parent.content_hash
    summary = api_client.get(summary_path, token=tenant.dentist_admin.token).json()
    assert summary["what_was_done"] == "Cambio de arcos y control de alineación"
    assert summary["next_session_instructions"] == "Revisar higiene y cooperación."
    assert summary["next_clinical_control"] == "2 meses"
    assert summary["active_alerts"] == ["Controlar resorte superior."]


def test_signed_is_immutable_and_double_sign_is_safe(api_client, security_world) -> None:
    tenant, case = _prepare(api_client, security_world)
    draft = _create_evolution(api_client, tenant, case["id"]).json()
    sign_payload = {"row_version": draft["row_version"], "clinical_evolution_version": draft["clinical_evolution_version"], "confirm_complete": True}
    def sign_once():
        return api_client.post(f"/api/orthodontics/evolutions/{draft['id']}/sign", token=tenant.dentist_admin.token, json=sign_payload).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: sign_once(), range(2)))
    assert sorted(statuses) == [200, 409]
    edit = api_client.patch(
        f"/api/orthodontics/evolutions/{draft['id']}/draft",
        token=tenant.dentist_admin.token,
        json={"row_version": draft["row_version"], "clinical_evolution_version": draft["clinical_evolution_version"], "performed_summary": "Mutación", "notes": None, "mini_screws": []},
    )
    assert edit.status_code == 409


def test_suspended_closed_unassigned_and_cross_tenant_are_denied(
    api_client, security_world
) -> None:
    tenant, case = _prepare(api_client, security_world)
    suspended = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/suspend",
        token=tenant.dentist_admin.token,
        json={"row_version": case["row_version"], "reason": "Pausa"},
    )
    assert suspended.status_code == 200
    denied = _create_evolution(api_client, tenant, case["id"])
    assert denied.status_code == 409
    assert denied.json()["detail"]["code"] == "ORTHODONTIC_EVOLUTION_CASE_SUSPENDED"
    other = security_world.tenant_b
    assert api_client.get(f"/api/orthodontics/cases/{case['id']}/evolutions", token=other.dentist_admin.token).status_code == 404
    assert api_client.post(f"/api/orthodontics/cases/{case['id']}/evolutions", token=tenant.admin.token, json={"notes": "No"}).status_code == 403
    assert api_client.post(f"/api/orthodontics/cases/{case['id']}/evolutions", token=tenant.secretary.token, json={"notes": "No"}).status_code == 403
    assert api_client.post(f"/api/orthodontics/cases/{case['id']}/evolutions", token=security_world.platform_admin.token, json={"notes": "No"}).status_code == 403


def test_custom_catalog_is_tenant_scoped_retired_and_snapshot_survives(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare(api_client, security_world)
    created = api_client.post(
        "/api/orthodontics/catalogs/ARCH_MATERIAL/options",
        token=tenant.admin.token,
        json={"label": "Arco Aurora"},
    )
    assert created.status_code == 201, created.text
    option = created.json()
    evolution = _create_evolution(api_client, tenant, case["id"], upper_material_option_id=option["id"])
    assert evolution.status_code == 201, evolution.text
    retired = api_client.post(
        f"/api/orthodontics/catalog-options/{option['id']}/retire",
        token=tenant.admin.token,
    )
    assert retired.status_code == 200
    listing = api_client.get("/api/orthodontics/catalogs/ARCH_MATERIAL", token=tenant.dentist_admin.token).json()
    assert option["id"] not in {item["id"] for item in listing["items"]}
    stored = api_client.get(f"/api/orthodontics/evolutions/{evolution.json()['id']}", token=tenant.dentist_admin.token).json()
    assert stored["upper_material"]["label"] == "Arco Aurora"
    inactive = _create_evolution(
        api_client,
        tenant,
        case["id"],
        upper_material_option_id=option["id"],
    )
    assert inactive.status_code == 409
    base = _base_option(db_session, "ARCH_MATERIAL", "STEEL_BASE", "Acero base")
    assert api_client.post(
        f"/api/orthodontics/catalog-options/{base.id}/retire",
        token=tenant.admin.token,
    ).status_code == 404
    other = security_world.tenant_b
    cross = api_client.post(
        "/api/orthodontics/catalog-options/{}/retire".format(option["id"]),
        token=other.admin.token,
    )
    assert cross.status_code == 404
    audit_actions = {item.action for item in db_session.scalars(select(AuditEvent).where(AuditEvent.entity_id == option["id"]))}
    assert {"ORTHODONTIC_CATALOG_OPTION_CREATED", "ORTHODONTIC_CATALOG_OPTION_RETIRED"} <= audit_actions


def test_structured_only_is_valid_and_generic_draft_route_cannot_bypass_extension(
    api_client, db_session, security_world
) -> None:
    tenant, case = _prepare(api_client, security_world)
    material = _base_option(db_session, "ARCH_MATERIAL", "STEEL", "Acero")
    empty = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/evolutions",
        token=tenant.dentist_admin.token,
        json={},
    )
    assert empty.status_code == 422
    structured = api_client.post(
        f"/api/orthodontics/cases/{case['id']}/evolutions",
        token=tenant.dentist_admin.token,
        json={"upper_material_option_id": str(material.id)},
    )
    assert structured.status_code == 201, structured.text
    item = structured.json()
    assert item["notes"] is None
    bypass = api_client.patch(
        f"/api/clinical-evolutions/{item['clinical_evolution_id']}/draft",
        token=tenant.dentist_admin.token,
        json={
            "version": item["clinical_evolution_version"],
            "evolution_text": "Intento fuera del módulo",
        },
    )
    assert bypass.status_code == 409
    generic_sign = api_client.post(
        f"/api/clinical-evolutions/{item['clinical_evolution_id']}/sign",
        token=tenant.dentist_admin.token,
        json={
            "version": item["clinical_evolution_version"],
            "confirm_complete": True,
        },
    )
    assert generic_sign.status_code == 409


def test_addendum_reuses_clinical_flow_and_requires_active_orthodontic_assignment(
    api_client, security_world
) -> None:
    tenant, case = _prepare(api_client, security_world)
    draft = _create_evolution(api_client, tenant, case["id"]).json()
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
    parent_id = signed.json()["clinical_evolution_id"]
    addendum = api_client.post(
        f"/api/clinical-evolutions/{parent_id}/addendum",
        token=tenant.dentist_admin.token,
        json={"reason": "Aclaración clínica", "content": "Se precisa el control realizado."},
    )
    assert addendum.status_code == 201, addendum.text

    assignment = api_client.get(
        "/api/orthodontics/assignments", token=tenant.admin.token
    ).json()["items"][0]
    revoked = api_client.post(
        f"/api/orthodontics/assignments/{assignment['id']}/revoke",
        token=tenant.admin.token,
        json={"reason": "Cambio de cobertura"},
    )
    assert revoked.status_code == 200, revoked.text
    denied = api_client.post(
        f"/api/clinical-evolutions/{parent_id}/addendum",
        token=tenant.dentist_admin.token,
        json={"reason": "Intento posterior", "content": "No debe registrarse."},
    )
    assert denied.status_code == 403


def test_custom_option_from_other_tenant_cannot_be_used(
    api_client, security_world
) -> None:
    tenant_a, _ = _prepare(api_client, security_world)
    option = api_client.post(
        "/api/orthodontics/catalogs/ARCH_SIZE/options",
        token=tenant_a.admin.token,
        json={"label": "Tamaño privado A"},
    ).json()
    tenant_b, case_b = _prepare(api_client, security_world, security_world.tenant_b)
    denied = _create_evolution(
        api_client,
        tenant_b,
        case_b["id"],
        upper_size_option_id=option["id"],
    )
    assert denied.status_code == 422
    assert denied.json()["detail"]["code"] == "ORTHODONTIC_INVALID_CATALOG_OPTION"
