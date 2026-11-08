import json
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from sqlalchemy import func, select

from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent, OdontogramEventDetail
from app.models.treatment import ProcedureCatalogItem, TreatmentProcedure
from app.services.procedure_catalog_odontogram_esthetic_seed_service import (
    CATALOG_PATH, EXPECTED_ROWS, _load_batch,
    preview_odontogram_esthetic_catalog, seed_odontogram_esthetic_catalog,
)
from app.services.procedure_catalog_seed_service import normalize_catalog_name


EXPECTED = {
    9: ("Diseño de Sonrisa 6 dientes RC", "540000", "1777000"),
    302: ("Carillas directas", "119000", "392000"),
    304: ("Cierre de diastema (por sesión)", "60000", "197000"),
    478: ("Carillas indirectas (cualquier tipo o material)", "237000", "780000"),
}


def _install_symbols_and_seed(session, tenant):
    for code, kind in (
        ("PLAN_VENEER", "PLANNED_PROCEDURE"), ("DONE_VENEER", "PERFORMED_PROCEDURE"),
        ("PLAN_RESIN", "PLANNED_PROCEDURE"), ("DONE_RESIN", "PERFORMED_PROCEDURE"),
    ):
        if session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == code)) is None:
            session.add(OdontogramCatalogItem(
                company_id=None, code=code, name=code, type=kind,
                color="#dc2626" if code.startswith("PLAN_") else "#2563eb",
                pattern="veneer" if "VENEER" in code else "solid",
                symbol="V" if "VENEER" in code else "R",
                allowed_scopes=["TOOTH"] if "VENEER" in code else ["TOOTH_SURFACE"],
                is_active=True,
            ))
    tenant.company.country = "Chile"
    session.flush(); seed_odontogram_esthetic_catalog(session, tenant.company, tenant.admin.user.id); session.commit()


def _new_treatment(api_client, tenant, name):
    response = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": name,
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    assert response.status_code == 201
    return response.json()


def test_esthetic_four_source_identity_prices_targets_and_gates():
    payload = _load_batch(); items = {item["source_row"]: item for item in payload["items"]}
    assert set(items) == EXPECTED_ROWS == set(EXPECTED)
    assert all(value is False for value in payload["execution"].values())
    rate = Decimal("3.291243")
    for row, (name, clp, cop) in EXPECTED.items():
        item = items[row]
        assert (item["name"], item["source_price_clp"], item["fixed_price_cop"]) == (name, clp, cop)
        assert (Decimal(clp) * rate / 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 1000 == Decimal(cop)
    assert items[9]["graphical_targets"] == {"dentition": "PERMANENT", "teeth": ["11", "12", "13", "21", "22", "23"]}
    assert items[9]["billing_multiplier"] == 1
    assert items[304]["diagnosis_mode"] == "NONE"
    assert json.loads(CATALOG_PATH.read_text())["items"] == payload["items"]


def test_esthetic_seed_country_prices_idempotency_and_collision(db_session, security_world):
    for code, kind in (("PLAN_VENEER", "PLANNED_PROCEDURE"), ("DONE_VENEER", "PERFORMED_PROCEDURE"), ("PLAN_RESIN", "PLANNED_PROCEDURE"), ("DONE_RESIN", "PERFORMED_PROCEDURE")):
        db_session.add(OdontogramCatalogItem(company_id=None, code=code, name=code, type=kind, color="#2563eb", pattern="symbol", symbol=code, allowed_scopes=["TOOTH", "TOOTH_SURFACE"], is_active=True))
    chile, colombia = security_world.tenant_a, security_world.tenant_b
    chile.company.country = "Chile"; colombia.company.country = "Colombia"
    existing = ProcedureCatalogItem(company_id=chile.company.id, name=EXPECTED[302][0], normalized_name=normalize_catalog_name(EXPECTED[302][0]), suggested_value=Decimal("777"), odontogram_behavior="NO_CHANGE", is_active=True)
    db_session.add(existing); db_session.commit()
    assert preview_odontogram_esthetic_catalog(db_session, chile.company).would_insert == 3
    cl = seed_odontogram_esthetic_catalog(db_session, chile.company, chile.admin.user.id)
    co = seed_odontogram_esthetic_catalog(db_session, colombia.company, colombia.admin.user.id)
    db_session.commit()
    assert (cl.inserted, cl.skipped_collisions, co.inserted) == (3, 1, 4)
    design = db_session.scalar(select(ProcedureCatalogItem).where(ProcedureCatalogItem.company_id == colombia.company.id, ProcedureCatalogItem.price_provenance["source_row"].astext == "9"))
    assert (design.suggested_value, design.price_provenance["billing_multiplier"]) == (Decimal("1777000"), 1)
    assert design.price_provenance["graphical_targets"]["teeth"] == ["11", "12", "13", "21", "22", "23"]
    replay = seed_odontogram_esthetic_catalog(db_session, colombia.company, colombia.admin.user.id)
    assert (replay.inserted, replay.skipped_collisions) == (0, 4)


def test_single_veneer_and_diastema_use_plans_without_inventing_diagnosis(api_client, db_session, security_world):
    tenant = security_world.tenant_a; _install_symbols_and_seed(db_session, tenant)
    before_diagnoses = db_session.scalar(select(func.count()).select_from(OdontogramEvent).where(OdontogramEvent.event_type.in_(["DIAGNOSIS_ADDED", "FINDING_ADDED"])))
    for row, scope, surfaces, expected_plan in ((302, "TOOTH", None, "PLAN_VENEER"), (304, "TOOTH_SURFACE", ["MESIAL"], "PLAN_RESIN")):
        catalog = db_session.scalar(select(ProcedureCatalogItem).where(ProcedureCatalogItem.company_id == tenant.company.id, ProcedureCatalogItem.price_provenance["source_row"].astext == str(row)))
        treatment = _new_treatment(api_client, tenant, f"Estético {row}")
        response = api_client.post(f"/api/treatments/{treatment['id']}/procedures/with-diagnosis", token=tenant.dentist_admin.token, json={
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": str(catalog.suggested_value), "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": scope, "tooth": "11", "surfaces": surfaces,
            "dentition": "PERMANENT", "diagnosis_mode": "NONE",
            "idempotency_key": f"esthetic-{row}-{uuid4().hex}",
        })
        assert response.status_code == 201, response.text
        procedure = response.json()["procedure"]
        assert procedure["source_odontogram_event_id"] is None
        plan_detail = db_session.scalar(select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == procedure["planned_odontogram_event_id"]))
        assert db_session.get(OdontogramCatalogItem, plan_detail.catalog_item_id).code == expected_plan
        assert sorted(plan_detail.surfaces or []) == sorted(surfaces or [])
    after_diagnoses = db_session.scalar(select(func.count()).select_from(OdontogramEvent).where(OdontogramEvent.event_type.in_(["DIAGNOSIS_ADDED", "FINDING_ADDED"])))
    assert after_diagnoses == before_diagnoses


def test_smile_design_keeps_one_charge_and_six_graphical_targets_through_signature(api_client, db_session, security_world):
    tenant = security_world.tenant_a; _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "9",
    ))
    treatment = _new_treatment(api_client, tenant, "Diseño de sonrisa sintético")
    create_payload = {
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": str(catalog.suggested_value), "quantity": "1",
        "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
        "scope_type": "ZONE", "zone": "ANTERIOR", "dentition": "PERMANENT",
        "diagnosis_mode": "NONE", "idempotency_key": f"smile-{uuid4().hex}",
    }
    created = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token, json=create_payload,
    )
    assert created.status_code == 201, created.text
    procedure = created.json()["procedure"]
    assert (Decimal(procedure["unit_value"]), Decimal(procedure["quantity"])) == (Decimal("540000"), Decimal("1"))
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    plan_details = db_session.scalars(select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == plan.id)).all()
    expected_teeth = {"11", "12", "13", "21", "22", "23"}
    assert len(plan_details) == 6
    assert {detail.tooth_code for detail in plan_details} == expected_teeth
    assert all(detail.scope_type == "TOOTH" and detail.dentition == "PERMANENT" for detail in plan_details)

    replay_create = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token, json=create_payload,
    )
    assert replay_create.status_code == 201
    assert replay_create.json()["idempotent_replay"] is True
    assert db_session.scalar(select(func.count()).select_from(TreatmentProcedure).where(TreatmentProcedure.treatment_id == treatment["id"])) == 1

    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={"treatment_id": treatment["id"], "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Diseño de sonrisa realizado."},
    ).json()
    done = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_VENEER"))
    completion_payload = {
        "clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(done.id),
        "idempotency_key": f"smile-done-{uuid4().hex}", "scope_type": "ZONE",
        "zone": "ANTERIOR", "dentition": "PERMANENT",
    }
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token, json=completion_payload,
    )
    assert completed.status_code == 200, completed.text
    done_event = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    done_details = db_session.scalars(select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == done_event.id)).all()
    assert len(done_details) == 6 and {detail.tooth_code for detail in done_details} == expected_teeth
    changed = next(detail for detail in done_details if detail.tooth_code == "23")
    changed.tooth_code = "24"; db_session.commit()
    rejected = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert rejected.status_code == 409, rejected.text
    db_session.refresh(plan); db_session.refresh(done_event)
    assert (plan.status, done_event.status) == ("CONFIRMED", "DRAFT")
    changed.tooth_code = "23"; db_session.commit()
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    db_session.refresh(plan); db_session.refresh(done_event)
    assert (plan.status, done_event.status) == ("VOIDED_BY_COMPENSATING_EVENT", "CONFIRMED")


def test_smile_design_rejects_non_authoritative_targets_without_partial_writes(api_client, db_session, security_world):
    tenant = security_world.tenant_a; _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "9",
    ))
    treatment = _new_treatment(api_client, tenant, "Diseño inválido sintético")
    before_procedures = db_session.scalar(select(func.count()).select_from(TreatmentProcedure))
    before_events = db_session.scalar(select(func.count()).select_from(OdontogramEvent))
    for payload_override in (
        {"scope_type": "TOOTH", "tooth": "11", "zone": None},
        {"scope_type": "ZONE", "zone": "POSTERIOR"},
        {"scope_type": "ZONE", "zone": "ANTERIOR", "dentition": "PRIMARY"},
        {"scope_type": "ZONE", "zone": "ANTERIOR", "quantity": "6"},
    ):
        payload = {
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": str(catalog.suggested_value), "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "ZONE", "zone": "ANTERIOR", "dentition": "PERMANENT",
            "diagnosis_mode": "NONE", "idempotency_key": f"invalid-smile-{uuid4().hex}",
            **payload_override,
        }
        response = api_client.post(
            f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
            token=tenant.dentist_admin.token, json=payload,
        )
        assert response.status_code in (409, 422), response.text
        assert db_session.scalar(select(func.count()).select_from(TreatmentProcedure)) == before_procedures
        assert db_session.scalar(select(func.count()).select_from(OdontogramEvent)) == before_events


def test_smile_design_revalidates_all_plan_targets_before_completion(api_client, db_session, security_world):
    tenant = security_world.tenant_a; _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "9",
    ))
    treatment = _new_treatment(api_client, tenant, "Diseño alterado sintético")
    created = api_client.post(f"/api/treatments/{treatment['id']}/procedures/with-diagnosis", token=tenant.dentist_admin.token, json={
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": str(catalog.suggested_value), "quantity": "1",
        "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
        "scope_type": "ZONE", "zone": "ANTERIOR", "dentition": "PERMANENT",
        "diagnosis_mode": "NONE", "idempotency_key": f"tampered-smile-{uuid4().hex}",
    }).json()
    procedure = created["procedure"]
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    plan_detail = db_session.scalar(select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == plan.id, OdontogramEventDetail.tooth_code == "13"))
    plan_detail.tooth_code = "14"; db_session.commit()
    evolution = api_client.post(f"/api/patients/{tenant.patient.id}/clinical-evolutions", token=tenant.dentist_admin.token, json={
        "treatment_id": treatment["id"], "site_id": str(tenant.site_1.id),
        "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "No debe completar.",
    }).json()
    done = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_VENEER"))
    before_events = db_session.scalar(select(func.count()).select_from(OdontogramEvent))
    response = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json={"clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(done.id),
              "idempotency_key": f"tampered-done-{uuid4().hex}", "scope_type": "ZONE",
              "zone": "ANTERIOR", "dentition": "PERMANENT"},
    )
    assert response.status_code == 409, response.text
    db_session.refresh(plan)
    assert plan.status == "CONFIRMED"
    assert db_session.scalar(select(func.count()).select_from(OdontogramEvent)) == before_events


def test_smile_design_cancellation_compensates_one_multidetail_plan_and_preserves_history(api_client, db_session, security_world):
    tenant = security_world.tenant_a; _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "9",
    ))
    treatment = _new_treatment(api_client, tenant, "Cancelación diseño sintético")
    created = api_client.post(f"/api/treatments/{treatment['id']}/procedures/with-diagnosis", token=tenant.dentist_admin.token, json={
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": str(catalog.suggested_value), "quantity": "1",
        "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
        "scope_type": "ZONE", "zone": "ANTERIOR", "dentition": "PERMANENT",
        "diagnosis_mode": "NONE", "idempotency_key": f"cancel-smile-{uuid4().hex}",
    }).json()["procedure"]
    plan = db_session.get(OdontogramEvent, created["planned_odontogram_event_id"])
    detail_ids = set(db_session.scalars(select(OdontogramEventDetail.id).where(OdontogramEventDetail.event_id == plan.id)).all())
    assert len(detail_ids) == 6
    cancelled = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{created['id']}/cancel",
        token=tenant.dentist_admin.token, json={"reason": "Cancelación sintética"},
    )
    assert cancelled.status_code == 200, cancelled.text
    db_session.refresh(plan)
    assert plan.status == "VOIDED_BY_COMPENSATING_EVENT"
    assert set(db_session.scalars(select(OdontogramEventDetail.id).where(OdontogramEventDetail.event_id == plan.id)).all()) == detail_ids
