import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, ROUND_HALF_UP
from time import sleep
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.models.agenda import Patient
from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent, OdontogramEventDetail
from app.models.treatment import ProcedureCatalogItem, TreatmentProcedure
from app.services.procedure_catalog_odontogram_prosthetic_seed_service import (
    preview_odontogram_planned_catalog,
    seed_odontogram_planned_catalog,
)
from app.services.procedure_catalog_seed_service import normalize_catalog_name

from app.services.procedure_catalog_odontogram_prosthetic_seed_service import (
    CATALOG_PATH,
    EXPECTED_ROWS,
    _load_batch,
)


EXPECTED = {
    197: ("Pulpotomía en pieza permanente joven (parcial o total)", "55000", "181000"),
    228: ("Corona Sobre Implante", "350000", "1152000"),
    229: ("Corona Sobre Implante (Otra marca)", "400000", "1316000"),
    303: ("Cementación y colocación de perno técnica adhesiva", "55000", "181000"),
    482: ("Corona provisoria sobre implante", "57000", "188000"),
    487: ("Espiga muñón colado bipartito o pasante", "87000", "286000"),
    488: ("Espiga muñón colado simple", "76000", "250000"),
    489: ("Espiga muñón preformado o postes de fibra de vidrio", "99000", "326000"),
    519: ("Protesis fija sobre implante atornillada o cementada", "271000", "892000"),
}


def test_prosthetic_nine_source_identity_prices_and_gates():
    payload = _load_batch()
    items = {item["source_row"]: item for item in payload["items"]}
    assert set(items) == EXPECTED_ROWS == set(EXPECTED)
    assert payload["source_sha256"] == "1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df"
    assert payload["reconciliation_sha256"] == "10f0e7cbe0fedd2666ee4dba730b991a080c7ce5e2322f8397f3253de32f02a4"
    assert all(value is False for value in payload["execution"].values())
    rate = Decimal("3.291243")
    for source_row, (name, clp, cop) in EXPECTED.items():
        item = items[source_row]
        assert (item["name"], item["source_price_clp"], item["fixed_price_cop"]) == (name, clp, cop)
        calculated = (Decimal(clp) * rate / Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 1000
        assert calculated == Decimal(cop)
    assert json.loads(CATALOG_PATH.read_text())["items"] == payload["items"]


def test_family_contracts_are_explicit_and_not_inferred_from_similar_names():
    items = {item["source_row"]: item for item in _load_batch()["items"]}
    assert items[197]["odontogram_behavior"] == "OPTIONAL_DIAGNOSIS"
    assert items[197]["default_performed_code"] == "DONE_PULPOTOMY"
    assert "planned_code" not in items[197]
    for row in {228, 229, 482, 519}:
        assert items[row]["requires_prior_code"] == "DONE_IMPLANT"
        assert (items[row]["planned_code"], items[row]["default_performed_code"]) == ("PLAN_CROWN", "DONE_CROWN")
    for row in {303, 487, 488, 489}:
        assert (items[row]["planned_code"], items[row]["default_performed_code"]) == ("PLAN_POST", "DONE_POST")


def test_seed_is_idempotent_country_specific_and_preserves_collision(db_session, security_world):
    for code, name, item_type in (
        ("PLAN_CROWN", "Corona planificada", "PLANNED_PROCEDURE"),
        ("DONE_CROWN", "Corona realizada", "PERFORMED_PROCEDURE"),
        ("DONE_IMPLANT", "Implante realizado", "PERFORMED_PROCEDURE"),
        ("PLAN_POST", "Perno planificado", "PLANNED_PROCEDURE"),
        ("DONE_POST", "Perno realizado", "PERFORMED_PROCEDURE"),
        ("DONE_PULPOTOMY", "Pulpotomía realizada", "PERFORMED_PROCEDURE"),
    ):
        db_session.add(OdontogramCatalogItem(
            company_id=None, code=code, name=name, type=item_type,
            color="#2563eb", pattern="symbol", symbol=code,
            allowed_scopes=["TOOTH"], allowed_surfaces=["OCCLUSAL"] if code == "DONE_PULPOTOMY" else None,
            is_active=True,
        ))
    chile, colombia = security_world.tenant_a, security_world.tenant_b
    chile.company.country = "Chile"
    colombia.company.country = "Colombia"
    existing = ProcedureCatalogItem(
        company_id=chile.company.id,
        name="Corona Sobre Implante",
        normalized_name=normalize_catalog_name("Corona Sobre Implante"),
        suggested_value=Decimal("777"),
        odontogram_behavior="NO_CHANGE",
        is_active=True,
    )
    db_session.add(existing)
    db_session.commit()

    preview = preview_odontogram_planned_catalog(db_session, chile.company)
    assert (preview.would_insert, len(preview.collisions)) == (8, 1)
    cl = seed_odontogram_planned_catalog(db_session, chile.company, chile.admin.user.id)
    co = seed_odontogram_planned_catalog(db_session, colombia.company, colombia.admin.user.id)
    db_session.commit()
    assert (cl.inserted, cl.skipped_collisions) == (8, 1)
    assert (co.inserted, co.skipped_collisions) == (9, 0)
    db_session.refresh(existing)
    assert (existing.suggested_value, existing.odontogram_behavior) == (Decimal("777"), "NO_CHANGE")
    co_rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == colombia.company.id,
        ProcedureCatalogItem.price_provenance["catalog_version"].astext
        == "KIMBERLY-2026-11-08-ODONTOGRAM-PROSTHETIC-9-DRAFT",
    )).all()
    assert len(co_rows) == 9
    assert {row.price_provenance["source_row"] for row in co_rows} == EXPECTED_ROWS
    assert next(row for row in co_rows if row.price_provenance["source_row"] == 519).suggested_value == Decimal("892000")
    assert all(row.price_provenance["runtime_conversion"] is False for row in co_rows)
    replay = seed_odontogram_planned_catalog(db_session, colombia.company, colombia.admin.user.id)
    db_session.commit()
    assert (replay.inserted, replay.skipped_collisions) == (0, 9)


def _install_symbols_and_seed(db_session, tenant):
    for code, name, item_type, surfaces in (
        ("PLAN_CROWN", "Corona planificada", "PLANNED_PROCEDURE", None),
        ("DONE_CROWN", "Corona realizada", "PERFORMED_PROCEDURE", None),
        ("DONE_IMPLANT", "Implante realizado", "PERFORMED_PROCEDURE", None),
        ("PLAN_POST", "Perno planificado", "PLANNED_PROCEDURE", None),
        ("DONE_POST", "Perno realizado", "PERFORMED_PROCEDURE", None),
        ("DONE_PULPOTOMY", "Pulpotomía realizada", "PERFORMED_PROCEDURE", ["OCCLUSAL"]),
    ):
        db_session.add(OdontogramCatalogItem(
            company_id=None, code=code, name=name, type=item_type,
            color="#2563eb", pattern="symbol", symbol=code,
            allowed_scopes=["TOOTH"], allowed_surfaces=surfaces, is_active=True,
        ))
    tenant.company.country = "Chile"
    db_session.flush()
    seed_odontogram_planned_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()


def _new_treatment(api_client, tenant, name):
    response = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": name,
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_post_has_own_plan_and_completion_without_creating_endodontics(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "303",
    ))
    treatment = _new_treatment(api_client, tenant, "Perno sintético")
    created = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": str(catalog.suggested_value), "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "TOOTH", "tooth": "36", "dentition": "PERMANENT",
            "idempotency_key": f"post-create-{uuid4().hex}", "diagnosis_mode": "NONE",
        },
    )
    assert created.status_code == 201, created.text
    procedure = created.json()["procedure"]
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    detail = db_session.scalar(select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == plan.id))
    assert db_session.get(OdontogramCatalogItem, detail.catalog_item_id).code == "PLAN_POST"
    assert db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_ENDO")) is None

    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={"treatment_id": treatment["id"], "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Perno realizado."},
    ).json()
    done_post = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_POST"))
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json={"clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(done_post.id), "idempotency_key": f"post-done-{uuid4().hex}", "scope_type": "TOOTH", "tooth": "36", "dentition": "PERMANENT", "source_diagnosis_action": "KEEP_ACTIVE"},
    )
    assert completed.status_code == 200, completed.text
    signed = api_client.post(f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token, json={"version": evolution["version"], "confirm_complete": True})
    assert signed.status_code == 200, signed.text
    db_session.refresh(plan)
    assert plan.status == "VOIDED_BY_COMPENSATING_EVENT"


def test_pulpotomy_has_only_occlusal_result_and_no_planned_root_mark(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "197",
    ))
    treatment = _new_treatment(api_client, tenant, "Pulpotomía sintética")
    created = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={"catalog_procedure_id": str(catalog.id), "name": catalog.name, "unit_value": "55000", "quantity": "1", "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH", "tooth": "16", "dentition": "PERMANENT", "idempotency_key": f"pulpotomy-{uuid4().hex}", "diagnosis_mode": "NONE"},
    )
    assert created.status_code == 201, created.text
    procedure = created.json()["procedure"]
    assert procedure["planned_odontogram_event_id"] is None
    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={"treatment_id": treatment["id"], "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Pulpotomía realizada."},
    ).json()
    result = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_PULPOTOMY"))
    wrong = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json={"clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(result.id), "idempotency_key": f"pulp-wrong-{uuid4().hex}", "scope_type": "TOOTH_SURFACE", "tooth": "16", "surfaces": ["OCCLUSAL", "MESIAL"], "dentition": "PERMANENT"},
    )
    assert wrong.status_code in {409, 422}
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json={"clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(result.id), "idempotency_key": f"pulp-done-{uuid4().hex}", "scope_type": "TOOTH", "tooth": "16", "dentition": "PERMANENT"},
    )
    assert completed.status_code == 200, completed.text
    event = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    detail = db_session.scalar(select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == event.id))
    assert detail.surfaces in (None, [])


def test_implant_crown_requires_explicit_valid_antecedent_and_revalidates_at_signature(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "228",
    ))
    implant_item = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_IMPLANT"))
    implant = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={"event_type": "PROCEDURE_PERFORMED", "status": "CONFIRMED", "details": [{"catalog_item_id": str(implant_item.id), "scope_type": "TOOTH", "tooth_code": "36", "dentition": "PERMANENT", "layer": "PERFORMED"}]},
    )
    assert implant.status_code == 201, implant.text
    treatment = _new_treatment(api_client, tenant, "Corona sobre implante sintética")
    payload = {
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": str(catalog.suggested_value), "quantity": "1",
        "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
        "scope_type": "TOOTH", "tooth": "36", "dentition": "PERMANENT",
        "idempotency_key": f"implant-crown-{uuid4().hex}", "diagnosis_mode": "NONE",
    }
    missing = api_client.post(f"/api/treatments/{treatment['id']}/procedures/with-diagnosis", token=tenant.dentist_admin.token, json=payload)
    assert missing.status_code == 422
    created = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={**payload, "idempotency_key": f"implant-crown-valid-{uuid4().hex}", "prior_implant_event_id": implant.json()["id"]},
    )
    assert created.status_code == 201, created.text
    procedure = created.json()["procedure"]
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    plan_detail = db_session.scalar(select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == plan.id))
    assert plan_detail.detail_metadata["prior_implant_event_id"] == implant.json()["id"]

    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={"treatment_id": treatment["id"], "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Corona realizada."},
    ).json()
    done = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_CROWN"))
    completion_payload = {
        "clinical_evolution_id": evolution["id"],
        "odontogram_catalog_item_id": str(done.id),
        "idempotency_key": f"implant-crown-done-{uuid4().hex}",
        "scope_type": "TOOTH", "tooth": "36", "dentition": "PERMANENT",
    }
    before_events = db_session.scalar(select(func.count()).select_from(OdontogramEvent))
    original_metadata = dict(plan_detail.detail_metadata)
    plan_detail.detail_metadata = {**original_metadata, "prior_implant_event_id": None}
    db_session.commit()
    missing_before_completion = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=completion_payload,
    )
    assert missing_before_completion.status_code == 409
    db_session.refresh(plan)
    assert plan.status == "CONFIRMED"
    assert db_session.scalar(select(func.count()).select_from(OdontogramEvent)) == before_events

    plan_detail.detail_metadata = original_metadata
    original_provenance = dict(catalog.price_provenance)
    catalog.price_provenance = {**original_provenance, "requires_prior_code": None}
    db_session.commit()
    changed_requirement = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json={**completion_payload, "idempotency_key": f"changed-requirement-{uuid4().hex}"},
    )
    assert changed_requirement.status_code == 409
    db_session.refresh(plan)
    assert plan.status == "CONFIRMED"
    assert db_session.scalar(select(func.count()).select_from(OdontogramEvent)) == before_events

    catalog.price_provenance = original_provenance
    db_session.commit()
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json={**completion_payload, "idempotency_key": f"implant-crown-valid-done-{uuid4().hex}"},
    )
    assert completed.status_code == 200, completed.text
    draft = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])

    plan_detail.detail_metadata = {**original_metadata, "prior_implant_event_id": ""}
    db_session.commit()
    missing_before_sign = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert missing_before_sign.status_code == 409
    db_session.refresh(plan)
    db_session.refresh(draft)
    assert (plan.status, draft.status) == ("CONFIRMED", "DRAFT")

    plan_detail.detail_metadata = original_metadata
    implant_event = db_session.get(OdontogramEvent, implant.json()["id"])
    implant_event.status = "VOIDED_BY_COMPENSATING_EVENT"
    db_session.commit()
    signed = api_client.post(f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token, json={"version": evolution["version"], "confirm_complete": True})
    assert signed.status_code == 409
    db_session.refresh(plan)
    db_session.refresh(draft)
    assert (plan.status, draft.status) == ("CONFIRMED", "DRAFT")


def test_implant_crown_rejects_cross_tenant_and_obsolete_selection_without_mutation(api_client, db_session, security_world):
    tenant, other = security_world.tenant_a, security_world.tenant_b
    _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "228",
    ))
    implant_item = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_IMPLANT"))
    foreign = api_client.post(
        f"/api/patients/{other.patient.id}/odontogram/events", token=other.dentist_admin.token,
        json={"event_type": "PROCEDURE_PERFORMED", "status": "CONFIRMED", "details": [{"catalog_item_id": str(implant_item.id), "scope_type": "TOOTH", "tooth_code": "36", "dentition": "PERMANENT", "layer": "PERFORMED"}]},
    )
    local = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events", token=tenant.dentist_admin.token,
        json={"event_type": "PROCEDURE_PERFORMED", "status": "CONFIRMED", "details": [{"catalog_item_id": str(implant_item.id), "scope_type": "TOOTH", "tooth_code": "36", "dentition": "PERMANENT", "layer": "PERFORMED"}]},
    )
    assert foreign.status_code == local.status_code == 201
    treatment = _new_treatment(api_client, tenant, "Antecedentes inválidos")
    base = {"catalog_procedure_id": str(catalog.id), "name": catalog.name, "unit_value": str(catalog.suggested_value), "quantity": "1", "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH", "tooth": "36", "dentition": "PERMANENT", "diagnosis_mode": "NONE"}
    before = db_session.scalar(select(func.count()).select_from(TreatmentProcedure))
    crossed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis", token=tenant.dentist_admin.token,
        json={**base, "idempotency_key": f"crossed-{uuid4().hex}", "prior_implant_event_id": foreign.json()["id"]},
    )
    assert crossed.status_code == 409
    obsolete_event = db_session.get(OdontogramEvent, local.json()["id"])
    obsolete_event.status = "VOIDED_BY_COMPENSATING_EVENT"
    db_session.commit()
    obsolete = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis", token=tenant.dentist_admin.token,
        json={**base, "idempotency_key": f"obsolete-{uuid4().hex}", "prior_implant_event_id": local.json()["id"]},
    )
    assert obsolete.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(TreatmentProcedure)) == before


@pytest.mark.parametrize(
    "invalid_field",
    ["patient", "catalog_code", "event_type", "layer", "scope", "tooth", "dentition"],
)
def test_implant_crown_rejects_semantically_invalid_antecedent_atomically(
    invalid_field, api_client, db_session, security_world
):
    tenant = security_world.tenant_a
    _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "228",
    ))
    implant_item = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "DONE_IMPLANT"
    ))
    implant_response = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={
            "event_type": "PROCEDURE_PERFORMED", "status": "CONFIRMED",
            "details": [{
                "catalog_item_id": str(implant_item.id), "scope_type": "TOOTH",
                "tooth_code": "36", "dentition": "PERMANENT", "layer": "PERFORMED",
            }],
        },
    )
    assert implant_response.status_code == 201
    implant = db_session.get(OdontogramEvent, implant_response.json()["id"])
    detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == implant.id
    ))
    if invalid_field == "patient":
        another_patient = Patient(
            company_id=tenant.company.id,
            first_names="Paciente", last_names="Sintético distinto",
            mobile="+56900000099", normalized_mobile="56900000099",
            document_type="Sin documento", search_text="paciente sintetico distinto",
            created_by=tenant.admin.user.id,
        )
        db_session.add(another_patient)
        db_session.flush()
        implant.patient_id = another_patient.id
    elif invalid_field == "catalog_code":
        detail.catalog_item_id = db_session.scalar(select(OdontogramCatalogItem.id).where(
            OdontogramCatalogItem.code == "DONE_CROWN"
        ))
    elif invalid_field == "event_type":
        implant.event_type = "FINDING_ADDED"
    elif invalid_field == "layer":
        detail.layer = "FINDING"
    elif invalid_field == "scope":
        detail.scope_type = "GENERAL"
    elif invalid_field == "tooth":
        detail.tooth_code = "37"
    elif invalid_field == "dentition":
        detail.dentition = "PRIMARY"
    db_session.commit()

    treatment = _new_treatment(api_client, tenant, f"Antecedente inválido {invalid_field}")
    procedure_count = db_session.scalar(select(func.count()).select_from(TreatmentProcedure))
    event_count = db_session.scalar(select(func.count()).select_from(OdontogramEvent))
    response = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": str(catalog.suggested_value), "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "TOOTH", "tooth": "36", "dentition": "PERMANENT",
            "diagnosis_mode": "NONE", "idempotency_key": f"invalid-{invalid_field}-{uuid4().hex}",
            "prior_implant_event_id": str(implant.id),
        },
    )
    assert response.status_code in {404, 409}
    assert db_session.scalar(select(func.count()).select_from(TreatmentProcedure)) == procedure_count
    assert db_session.scalar(select(func.count()).select_from(OdontogramEvent)) == event_count


def test_implant_antecedent_lock_serializes_obsolescence_against_creation(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "228",
    ))
    implant_item = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_IMPLANT"))
    implant = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events", token=tenant.dentist_admin.token,
        json={"event_type": "PROCEDURE_PERFORMED", "status": "CONFIRMED", "details": [{"catalog_item_id": str(implant_item.id), "scope_type": "TOOTH", "tooth_code": "36", "dentition": "PERMANENT", "layer": "PERFORMED"}]},
    )
    treatment = _new_treatment(api_client, tenant, "Carrera antecedente")
    payload = {"catalog_procedure_id": str(catalog.id), "name": catalog.name, "unit_value": str(catalog.suggested_value), "quantity": "1", "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH", "tooth": "36", "dentition": "PERMANENT", "diagnosis_mode": "NONE", "idempotency_key": f"race-{uuid4().hex}", "prior_implant_event_id": implant.json()["id"]}
    locked = db_session.scalar(select(OdontogramEvent).where(OdontogramEvent.id == implant.json()["id"]).with_for_update())

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            api_client.post,
            f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
            token=tenant.dentist_admin.token,
            json=payload,
        )
        sleep(0.2)
        assert not future.done()
        locked.status = "VOIDED_BY_COMPENSATING_EVENT"
        db_session.commit()
        response = future.result(timeout=20)
    assert response.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(TreatmentProcedure).where(
        TreatmentProcedure.treatment_id == treatment["id"]
    )) == 0
