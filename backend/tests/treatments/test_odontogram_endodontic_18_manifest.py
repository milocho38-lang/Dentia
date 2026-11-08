import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from time import sleep

from sqlalchemy import func, select

from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent, OdontogramEventDetail
from app.models.treatment import ProcedureCatalogDiagnosis, ProcedureCatalogItem, Treatment, TreatmentProcedure
from app.services.procedure_catalog_odontogram_endodontic_seed_service import _load_batch
from app.services.procedure_catalog_odontogram_endodontic_seed_service import (
    seed_odontogram_endodontic_catalog,
)


ROOT = Path(__file__).resolve().parents[3]
RECONCILIATION = Path(
    "/Users/camilo/Documents/Codex/2026-11-02/task/source-reconciliation-20261107/"
    "extracted/dentia-catalog-reconciliation-20261107/source-reconciliation-76.json"
)
EXPECTED_ROWS = set(range(179, 193)) | {282, 283, 292, 293}


def test_endodontic_18_matches_verified_reconciliation_and_fixed_prices():
    payload = _load_batch()
    source = json.loads(RECONCILIATION.read_text())["records"]
    source_by_row = {row["excel_row"]: row for row in source if row["excel_row"] in EXPECTED_ROWS}
    assert set(source_by_row) == EXPECTED_ROWS
    assert len(payload["items"]) == 18
    for item in payload["items"]:
        row = source_by_row[item["source_row"]]
        assert item["name"] == row["source_name"]
        assert item["source_note"] == row["source_note"]
        assert item["source_scope"] == row["source_scope"]
        assert Decimal(item["source_price_clp"]) == Decimal(row["source_price_clp"])
        expected_cop = (
            Decimal(row["source_price_clp"])
            * Decimal("3.291243")
            / Decimal("1000")
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("1000")
        assert Decimal(item["fixed_price_cop"]) == expected_cop
        assert item["suggested_scope_type"] == "TOOTH"
        assert item["planned_code"] == "PLAN_ENDO"
        assert item["default_performed_code"] == "DONE_ENDO"


def test_endodontic_18_stays_disconnected():
    execution = _load_batch()["execution"]
    assert execution == {
        "connected_to_runtime": False,
        "onboarding_enabled": False,
        "backfill_api_enabled": False,
        "cli_apply_enabled": False,
        "production_authorized": False,
    }


def _clinical_items(db_session):
    for code, name, item_type, scopes, surfaces in (
        ("PLAN_ENDO", "Endodoncia planificada", "PLANNED_PROCEDURE", ["TOOTH"], None),
        ("DONE_ENDO", "Endodoncia realizada", "PERFORMED_PROCEDURE", ["TOOTH"], None),
        ("FIND_CARIES", "Caries", "FINDING", ["TOOTH", "TOOTH_SURFACE"], ["OCCLUSAL", "MESIAL", "PALATAL"]),
        ("FIND_FRACTURE", "Fractura", "FINDING", ["TOOTH", "TOOTH_SURFACE"], ["OCCLUSAL", "MESIAL", "PALATAL"]),
        ("FIND_ENDO_DEFECTIVE", "Endodoncia previa defectuosa", "FINDING", ["TOOTH"], None),
    ):
        db_session.add(OdontogramCatalogItem(
            company_id=None, code=code, name=name, type=item_type,
            color="#dc2626" if code.startswith(("PLAN", "FIND")) else "#2563eb",
            pattern="solid", symbol=code, allowed_scopes=scopes,
            allowed_surfaces=surfaces, is_active=True,
        ))
    db_session.commit()


def test_endodontic_seed_links_all_rows_to_optional_surface_diagnoses(db_session, security_world):
    tenant = security_world.tenant_a
    tenant.company.country = "Chile"
    _clinical_items(db_session)
    result = seed_odontogram_endodontic_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    assert (result.inserted, result.skipped_collisions) == (18, 0)
    rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["catalog_version"].astext
        == "KIMBERLY-2026-11-08-ODONTOGRAM-ENDODONTIC-18-DRAFT",
    )).all()
    assert len(rows) == 18
    by_source = {row.price_provenance["source_row"]: row for row in rows}
    assert by_source[179].suggested_value == Decimal("160000")
    assert by_source[282].suggested_value == Decimal("28000")
    links = db_session.scalars(select(ProcedureCatalogDiagnosis).where(
        ProcedureCatalogDiagnosis.company_id == tenant.company.id,
    )).all()
    assert len(links) == 36
    assert {by_source[row].id for row in {282, 283, 292, 293}}.issubset(
        {link.procedure_catalog_id for link in links}
    )
    replay = seed_odontogram_endodontic_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    assert (replay.inserted, replay.skipped_collisions) == (0, 18)


def test_endodontic_create_new_keeps_surface_diagnosis_separate_from_tooth_plan(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_a
    tenant.company.country = "Chile"
    _clinical_items(db_session)
    seed_odontogram_endodontic_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    procedure_catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "179",
    ))
    caries = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "FIND_CARIES"
    ))
    done_endo = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "DONE_ENDO"
    ))
    defective = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "FIND_ENDO_DEFECTIVE"
    ))
    prior_endo = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={"event_type": "PROCEDURE_PERFORMED", "status": "CONFIRMED", "details": [{
            "catalog_item_id": str(done_endo.id), "scope_type": "TOOTH", "tooth_code": "36",
            "dentition": "PERMANENT", "layer": "PERFORMED",
        }]},
    )
    assert prior_endo.status_code == 201, prior_endo.text
    old_defect = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={"event_type": "FINDING_ADDED", "status": "CONFIRMED", "details": [{
            "catalog_item_id": str(defective.id), "scope_type": "TOOTH", "tooth_code": "36",
            "dentition": "PERMANENT", "layer": "FINDING",
            "metadata": {"prior_done_endo_event_id": prior_endo.json()["id"]},
        }]},
    )
    assert old_defect.status_code == 201, old_defect.text
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": "Endodoncia separada",
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    response = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            "catalog_procedure_id": str(procedure_catalog.id), "name": procedure_catalog.name,
            "unit_value": "160000", "quantity": "1", "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH",
            "tooth": "31", "surfaces": None, "dentition": "PERMANENT",
            "idempotency_key": "endo-create-new-179-0001", "diagnosis_mode": "CREATE_NEW",
            "diagnosis_catalog_item_id": str(caries.id), "diagnosis_scope_type": "TOOTH_SURFACE",
            "diagnosis_tooth": "31", "diagnosis_surfaces": ["MESIAL", "OCCLUSAL"],
        },
    )
    assert response.status_code == 201, response.text
    replay_payload = {
        "catalog_procedure_id": str(procedure_catalog.id), "name": procedure_catalog.name,
        "unit_value": "160000", "quantity": "1", "site_id": str(tenant.site_1.id),
        "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH",
        "tooth": "31", "surfaces": None, "dentition": "PERMANENT",
        "idempotency_key": "endo-create-new-179-0001", "diagnosis_mode": "CREATE_NEW",
        "diagnosis_catalog_item_id": str(caries.id), "diagnosis_scope_type": "TOOTH_SURFACE",
        "diagnosis_tooth": "31", "diagnosis_surfaces": ["OCCLUSAL", "MESIAL"],
    }
    replay = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json=replay_payload,
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["idempotent_replay"] is True
    changed = {**replay_payload, "diagnosis_surfaces": ["PALATAL"]}
    conflict = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json=changed,
    )
    assert conflict.status_code == 409
    procedure = response.json()["procedure"]
    plan_detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == procedure["planned_odontogram_event_id"]
    ))
    diagnosis_detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == response.json()["diagnosis_event_id"]
    ))
    assert (plan_detail.scope_type, plan_detail.tooth_code, plan_detail.surfaces) == ("TOOTH", "31", None)
    assert (diagnosis_detail.scope_type, diagnosis_detail.tooth_code) == ("TOOTH_SURFACE", "31")
    assert sorted(diagnosis_detail.surfaces) == ["MESIAL", "OCCLUSAL"]

    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={
            "treatment_id": treatment.json()["id"], "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Conducto realizado.",
        },
    )
    completion_payload = {
        "clinical_evolution_id": evolution.json()["id"],
        "odontogram_catalog_item_id": str(done_endo.id),
        "idempotency_key": "endo-complete-179-0001",
        "source_odontogram_event_id": response.json()["diagnosis_event_id"],
        "source_diagnosis_action": "KEEP_ACTIVE", "scope_type": "TOOTH",
        "tooth": "31", "surfaces": None, "dentition": "PERMANENT",
    }
    completion_endpoint = (
        f"/api/treatments/{treatment.json()['id']}/procedures/{procedure['id']}/clinical-completion"
    )
    completion = api_client.post(
        completion_endpoint,
        token=tenant.dentist_admin.token,
        json=completion_payload,
    )
    assert completion.status_code == 200, completion.text
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution.json()['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution.json()["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    replay_after_sign = api_client.post(
        completion_endpoint, token=tenant.dentist_admin.token, json=completion_payload
    )
    assert replay_after_sign.status_code == 200, replay_after_sign.text
    assert replay_after_sign.json()["idempotent_replay"] is True
    assert replay_after_sign.json()["odontogram_event_id"] == completion.json()["odontogram_event_id"]
    source = db_session.get(OdontogramEvent, response.json()["diagnosis_event_id"])
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    result = db_session.get(OdontogramEvent, completion.json()["odontogram_event_id"])
    assert source.status == "CONFIRMED"
    assert plan.status == "VOIDED_BY_COMPENSATING_EVENT"
    assert result.status == "CONFIRMED"
    preserved_defect = db_session.get(OdontogramEvent, old_defect.json()["id"])
    assert preserved_defect.status == "CONFIRMED"
    result_detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == result.id
    ))
    result_catalog = db_session.get(OdontogramCatalogItem, result_detail.catalog_item_id)
    assert result_catalog.code == "DONE_ENDO"
    assert db_session.scalar(select(func.count()).select_from(OdontogramEventDetail).join(
        OdontogramEvent, OdontogramEvent.id == OdontogramEventDetail.event_id
    ).join(
        OdontogramCatalogItem, OdontogramCatalogItem.id == OdontogramEventDetail.catalog_item_id
    ).where(
        OdontogramEvent.company_id == tenant.company.id,
        OdontogramEvent.patient_id == tenant.patient.id,
        OdontogramCatalogItem.code.like("DONE_RESIN%"),
    )) == 0

    reused = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            **replay_payload,
            "idempotency_key": "endo-use-existing-179-0002",
            "diagnosis_mode": "USE_EXISTING",
            "existing_odontogram_event_id": response.json()["diagnosis_event_id"],
        },
    )
    assert reused.status_code == 201, reused.text
    assert reused.json()["diagnosis_reused"] is True
    assert reused.json()["diagnosis_event_id"] == response.json()["diagnosis_event_id"]
    cancelled = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/{reused.json()['procedure']['id']}/cancel",
        token=tenant.dentist_admin.token,
        json={"reason": "Cancelación sintética del segundo conducto"},
    )
    assert cancelled.status_code == 200, cancelled.text
    db_session.refresh(source)
    reused_plan = db_session.get(
        OdontogramEvent, reused.json()["procedure"]["planned_odontogram_event_id"]
    )
    assert source.status == "CONFIRMED"
    assert reused_plan.status == "VOIDED_BY_COMPENSATING_EVENT"


def test_primary_pulpectomy_uses_tooth_plan_without_inferred_surface_diagnosis(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_a
    tenant.company.country = "Chile"
    _clinical_items(db_session)
    seed_odontogram_endodontic_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "282",
    ))
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": "Pulpectomía temporal",
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    endpoint = f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis"
    created = api_client.post(endpoint, token=tenant.dentist_admin.token, json={
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": "28000", "quantity": "1", "site_id": str(tenant.site_1.id),
        "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH",
        "tooth": "53", "dentition": "PRIMARY", "idempotency_key": "primary-endo-282-0001",
        "diagnosis_mode": "NONE",
    })
    assert created.status_code == 201, created.text
    assert created.json()["diagnosis_event_id"] is None
    procedure = created.json()["procedure"]
    detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == procedure["planned_odontogram_event_id"]
    ))
    assert (detail.scope_type, detail.tooth_code, detail.dentition, detail.surfaces) == (
        "TOOTH", "53", "PRIMARY", None
    )
    caries = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "FIND_CARIES"
    ))
    second_treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": "Pulpectomía temporal con diagnóstico",
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    with_diagnosis = api_client.post(
        f"/api/treatments/{second_treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": "28000", "quantity": "1", "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH",
            "tooth": "53", "dentition": "PRIMARY", "idempotency_key": "primary-endo-282-palatal",
            "diagnosis_mode": "CREATE_NEW", "diagnosis_catalog_item_id": str(caries.id),
            "diagnosis_scope_type": "TOOTH_SURFACE", "diagnosis_tooth": "53",
            "diagnosis_surfaces": ["PALATAL"],
        },
    )
    assert with_diagnosis.status_code == 201, with_diagnosis.text
    diagnosis_detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == with_diagnosis.json()["diagnosis_event_id"]
    ))
    assert (diagnosis_detail.dentition, diagnosis_detail.tooth_code, diagnosis_detail.surfaces) == (
        "PRIMARY", "53", ["PALATAL"]
    )
    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={
            "treatment_id": treatment.json()["id"], "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Pulpectomía temporal.",
        },
    )
    done_endo = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "DONE_ENDO"
    ))
    completion = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json={
            "clinical_evolution_id": evolution.json()["id"],
            "odontogram_catalog_item_id": str(done_endo.id),
            "idempotency_key": "primary-endo-complete-282-0001",
            "source_diagnosis_action": "KEEP_ACTIVE", "scope_type": "TOOTH",
            "tooth": "53", "dentition": "PRIMARY",
        },
    )
    assert completion.status_code == 200, completion.text
    catalog.is_active = False
    db_session.commit()
    rejected = api_client.post(
        f"/api/clinical-evolutions/{evolution.json()['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution.json()["version"], "confirm_complete": True},
    )
    assert rejected.status_code == 409
    db_session.expire_all()
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    result = db_session.get(OdontogramEvent, completion.json()["odontogram_event_id"])
    assert plan.status == "CONFIRMED"
    assert result.status == "DRAFT"


def test_endodontic_invalid_diagnosis_target_rolls_back_plan_and_procedure(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_a
    tenant.company.country = "Chile"
    _clinical_items(db_session)
    seed_odontogram_endodontic_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "179",
    ))
    caries = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "FIND_CARIES"
    ))
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": "Endodoncia rollback",
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    before_procedures = list(db_session.scalars(select(TreatmentProcedure).where(
        TreatmentProcedure.company_id == tenant.company.id
    )).all())
    before_events = list(db_session.scalars(select(OdontogramEvent).where(
        OdontogramEvent.company_id == tenant.company.id,
        OdontogramEvent.patient_id == tenant.patient.id,
    )).all())
    endpoint = f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis"
    invalid = api_client.post(endpoint, token=tenant.dentist_admin.token, json={
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": "160000", "quantity": "1", "site_id": str(tenant.site_1.id),
        "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH",
        "tooth": "31", "dentition": "PERMANENT", "idempotency_key": "endo-invalid-target-1",
        "diagnosis_mode": "CREATE_NEW", "diagnosis_catalog_item_id": str(caries.id),
        "diagnosis_scope_type": "TOOTH_SURFACE", "diagnosis_tooth": "32",
        "diagnosis_surfaces": ["OCCLUSAL"],
    })
    assert invalid.status_code == 422
    assert "misma pieza" in invalid.json()["detail"]
    db_session.expire_all()
    assert len(list(db_session.scalars(select(TreatmentProcedure).where(
        TreatmentProcedure.company_id == tenant.company.id
    )).all())) == len(before_procedures)
    assert len(list(db_session.scalars(select(OdontogramEvent).where(
        OdontogramEvent.company_id == tenant.company.id,
        OdontogramEvent.patient_id == tenant.patient.id,
    )).all())) == len(before_events)

    wrong_dentition = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={
            "event_type": "FINDING_ADDED", "status": "CONFIRMED",
            "details": [{
                "catalog_item_id": str(caries.id), "scope_type": "TOOTH_SURFACE",
                "tooth_code": "31", "surfaces": ["OCCLUSAL"],
                "dentition": "PRIMARY", "layer": "FINDING",
            }],
        },
    )
    assert wrong_dentition.status_code == 201, wrong_dentition.text
    reuse_wrong_dentition = api_client.post(endpoint, token=tenant.dentist_admin.token, json={
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": "160000", "quantity": "1", "site_id": str(tenant.site_1.id),
        "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH",
        "tooth": "31", "dentition": "PERMANENT", "idempotency_key": "endo-wrong-dentition-2",
        "diagnosis_mode": "USE_EXISTING", "diagnosis_catalog_item_id": str(caries.id),
        "existing_odontogram_event_id": wrong_dentition.json()["id"],
        "diagnosis_scope_type": "TOOTH_SURFACE", "diagnosis_tooth": "31",
        "diagnosis_surfaces": ["OCCLUSAL"],
    })
    assert reuse_wrong_dentition.status_code in {404, 409}
    db_session.expire_all()
    assert len(list(db_session.scalars(select(TreatmentProcedure).where(
        TreatmentProcedure.company_id == tenant.company.id
    )).all())) == len(before_procedures)


def test_concurrent_endodontic_creation_waits_then_replays_single_plan(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    tenant.company.country = "Chile"
    _clinical_items(db_session)
    seed_odontogram_endodontic_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "179",
    ))
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": "Carrera endodóntica",
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    }).json()
    endpoint = f"/api/treatments/{treatment['id']}/procedures/with-diagnosis"
    payload = {
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": "160000", "quantity": "1", "site_id": str(tenant.site_1.id),
        "dentist_id": str(tenant.dentist_profile.id), "scope_type": "TOOTH",
        "tooth": "31", "dentition": "PERMANENT", "idempotency_key": "endo-race-179-1",
        "diagnosis_mode": "NONE",
    }
    db_session.scalar(select(Treatment).where(
        Treatment.id == treatment["id"]
    ).with_for_update())

    def create_once():
        return api_client.post(endpoint, token=tenant.dentist_admin.token, json=payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(create_once)
        second = executor.submit(create_once)
        sleep(0.2)
        assert not first.done() and not second.done()
        db_session.commit()
        responses = [first.result(timeout=20), second.result(timeout=20)]
    assert [response.status_code for response in responses] == [201, 201]
    assert sorted(response.json()["idempotent_replay"] for response in responses) == [False, True]
    procedure_ids = {response.json()["procedure"]["id"] for response in responses}
    assert len(procedure_ids) == 1
    procedure_id = next(iter(procedure_ids))
    assert db_session.scalar(select(func.count()).select_from(OdontogramEvent).where(
        OdontogramEvent.procedure_id == procedure_id,
        OdontogramEvent.event_type == "PLANNED_PROCEDURE_ADDED",
    )) == 1
