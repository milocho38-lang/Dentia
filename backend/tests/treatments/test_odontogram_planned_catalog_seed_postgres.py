from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from time import sleep
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent, OdontogramEventDetail
from app.models.treatment import ProcedureCatalogItem, Treatment, TreatmentProcedure
from app.services.procedure_catalog_odontogram_planned_seed_service import (
    preview_odontogram_planned_catalog,
    seed_odontogram_planned_catalog,
)
from app.services.procedure_catalog_seed_service import normalize_catalog_name


def _clinical_items(db_session):
    for code, name, item_type, color in (
        ("PLAN_CROWN", "Corona planificada", "PLANNED_PROCEDURE", "#dc2626"),
        ("DONE_CROWN", "Corona realizada", "PERFORMED_PROCEDURE", "#2563eb"),
        ("PLAN_IMPLANT", "Implante planificado", "PLANNED_PROCEDURE", "#dc2626"),
        ("DONE_IMPLANT", "Implante realizado", "PERFORMED_PROCEDURE", "#2563eb"),
    ):
        db_session.add(OdontogramCatalogItem(
            company_id=None, code=code, name=name, type=item_type,
            color=color, pattern="solid", symbol=code,
            allowed_scopes=["TOOTH"], allowed_surfaces=None, is_active=True,
        ))
    db_session.commit()


def _create_planned(api_client, db_session, tenant, *, source_row=6, tooth="36", dentition="PERMANENT", key=None):
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == str(source_row),
    ))
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": f"Plan seguro {uuid4().hex[:6]}",
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    payload = {
        "catalog_procedure_id": str(catalog.id), "name": catalog.name,
        "unit_value": str(catalog.suggested_value), "quantity": "1",
        "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
        "scope_type": "TOOTH", "tooth": tooth, "dentition": dentition,
        "idempotency_key": key or f"planned-create-{uuid4().hex}", "diagnosis_mode": "NONE",
    }
    endpoint = f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis"
    created = api_client.post(endpoint, token=tenant.dentist_admin.token, json=payload)
    assert created.status_code == 201, created.text
    return treatment.json(), created.json()["procedure"], payload, endpoint


def test_planned_thirteen_fixed_prices_collisions_and_idempotency(db_session, security_world):
    chile, colombia = security_world.tenant_a, security_world.tenant_b
    _clinical_items(db_session)
    chile.company.country = "Chile"
    colombia.company.country = "Colombia"
    existing = ProcedureCatalogItem(
        company_id=chile.company.id,
        name="Corona Ceromero",
        normalized_name=normalize_catalog_name("Corona Ceromero"),
        suggested_value=Decimal("777"),
        odontogram_behavior="NO_CHANGE",
        is_active=True,
    )
    db_session.add(existing)
    db_session.commit()
    preview = preview_odontogram_planned_catalog(db_session, chile.company)
    assert preview.would_insert == 12
    assert len(preview.collisions) == 1
    cl = seed_odontogram_planned_catalog(db_session, chile.company, chile.admin.user.id)
    co = seed_odontogram_planned_catalog(db_session, colombia.company, colombia.admin.user.id)
    db_session.commit()
    assert (cl.inserted, cl.skipped_collisions) == (12, 1)
    assert (co.inserted, co.skipped_collisions) == (13, 0)
    db_session.refresh(existing)
    assert existing.suggested_value == Decimal("777")
    assert existing.odontogram_behavior == "NO_CHANGE"
    rows_co = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == colombia.company.id,
        ProcedureCatalogItem.price_provenance["catalog_version"].astext
        == "KIMBERLY-2026-11-08-ODONTOGRAM-PLANNED-13-DRAFT",
    )).all()
    assert len(rows_co) == 13
    assert {row.price_provenance["source_row"] for row in rows_co} == {
        6, 231, 260, 261, 305, 308, 309, 310, 480, 481, 493, 517, 518
    }
    assert next(row for row in rows_co if row.price_provenance["source_row"] == 231).suggested_value == Decimal("987000")
    assert all(row.price_provenance["runtime_conversion"] is False for row in rows_co)
    replay = seed_odontogram_planned_catalog(db_session, colombia.company, colombia.admin.user.id)
    db_session.commit()
    assert (replay.inserted, replay.skipped_collisions) == (0, 13)


@pytest.mark.parametrize(
    "source_row,tooth,dentition,plan_code,done_code",
    [
        (6, "36", "PERMANENT", "PLAN_CROWN", "DONE_CROWN"),
        (260, "51", "PRIMARY", "PLAN_CROWN", "DONE_CROWN"),
        (231, "46", "PERMANENT", "PLAN_IMPLANT", "DONE_IMPLANT"),
    ],
)
def test_planned_mark_survives_draft_and_is_resolved_only_on_signature(
    api_client, db_session, security_world, source_row, tooth, dentition, plan_code, done_code
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    seed_odontogram_planned_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == str(source_row),
    ))
    result_item = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == done_code
    ))
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": f"Plan {source_row}",
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    created = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": str(catalog.suggested_value), "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "TOOTH", "tooth": tooth, "dentition": dentition,
            "idempotency_key": f"planned-create-{source_row}-{uuid4().hex}",
            "diagnosis_mode": "NONE",
        },
    )
    assert created.status_code == 201, created.text
    procedure = created.json()["procedure"]
    assert procedure["planned_odontogram_event_id"]
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    plan_detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == plan.id
    ))
    plan_item = db_session.get(OdontogramCatalogItem, plan_detail.catalog_item_id)
    assert (plan.status, plan.event_type, plan_item.code, plan_detail.layer) == (
        "CONFIRMED", "PLANNED_PROCEDURE_ADDED", plan_code, "PLANNED"
    )
    assert (plan_detail.tooth_code, plan_detail.dentition, plan_detail.surfaces) == (tooth, dentition, None)
    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={
            "treatment_id": treatment.json()["id"], "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Realización sintética.",
        },
    )
    completion_payload = {
        "clinical_evolution_id": evolution.json()["id"],
        "odontogram_catalog_item_id": str(result_item.id),
        "idempotency_key": f"planned-complete-{source_row}-{uuid4().hex}",
        "source_diagnosis_action": "KEEP_ACTIVE", "scope_type": "TOOTH",
        "tooth": tooth, "dentition": dentition,
    }
    completion = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token, json=completion_payload,
    )
    assert completion.status_code == 200, completion.text
    db_session.refresh(plan)
    assert plan.status == "CONFIRMED"
    replay = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token, json=completion_payload,
    )
    assert replay.status_code == 200 and replay.json()["idempotent_replay"] is True
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution.json()['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution.json()["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    db_session.refresh(plan)
    assert plan.status == "VOIDED_BY_COMPENSATING_EVENT"
    assert db_session.scalar(select(func.count()).select_from(OdontogramEvent).where(
        OdontogramEvent.procedure_id == procedure["id"],
        OdontogramEvent.event_type == "PROCEDURE_PERFORMED",
        OdontogramEvent.status == "CONFIRMED",
    )) == 1


def test_planned_procedure_rejects_incompatible_edit_and_shortcut_then_cancels_only_its_plan(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    seed_odontogram_planned_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    treatment, procedure, _, _ = _create_planned(api_client, db_session, tenant)
    plan_id = procedure["planned_odontogram_event_id"]
    update = api_client.patch(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}",
        token=tenant.dentist_admin.token,
        json={"tooth": "37", "scope_type": "TOOTH"},
    )
    assert update.status_code == 409
    shortcut = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/mark-done",
        token=tenant.dentist_admin.token,
    )
    assert shortcut.status_code == 409
    cancelled = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/cancel",
        token=tenant.dentist_admin.token,
        json={"reason": "Cambio de plan sintético"},
    )
    assert cancelled.status_code == 200, cancelled.text
    plan = db_session.get(OdontogramEvent, plan_id)
    db_session.refresh(plan)
    assert plan.status == "VOIDED_BY_COMPENSATING_EVENT"


def test_delete_planned_procedure_preserves_voided_plan_history(api_client, db_session, security_world):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    seed_odontogram_planned_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    treatment, procedure, _, _ = _create_planned(api_client, db_session, tenant, source_row=231, tooth="46")
    plan_id = procedure["planned_odontogram_event_id"]
    deleted = api_client.delete(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}",
        token=tenant.dentist_admin.token,
    )
    assert deleted.status_code == 204, deleted.text
    db_session.expire_all()
    plan = db_session.get(OdontogramEvent, plan_id)
    assert plan is not None and plan.status == "VOIDED_BY_COMPENSATING_EVENT"
    assert plan.procedure_id is None


def test_planned_creation_replay_is_scoped_to_route_catalog_and_payload(api_client, db_session, security_world):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    seed_odontogram_planned_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    key = f"planned-replay-{uuid4().hex}"
    treatment, procedure, payload, endpoint = _create_planned(
        api_client, db_session, tenant, key=key
    )
    replay = api_client.post(endpoint, token=tenant.dentist_admin.token, json=payload)
    assert replay.status_code == 201
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["procedure"]["id"] == procedure["id"]
    crossed_payload = {**payload, "tooth": "37"}
    crossed = api_client.post(endpoint, token=tenant.dentist_admin.token, json=crossed_payload)
    assert crossed.status_code == 409
    for changed in (
        {"category": "Categoría distinta"},
        {"estimated_date": "2026-12-31"},
        {"observations": "Observación distinta"},
        {"requires_tooth": True},
        {"diagnosis_mode": "CREATE_NEW", "allow_existing_duplicate": True},
    ):
        response = api_client.post(
            endpoint, token=tenant.dentist_admin.token, json={**payload, **changed}
        )
        assert response.status_code == 409, (changed, response.text)
    invalid_dentition = api_client.post(
        endpoint, token=tenant.dentist_admin.token, json={**payload, "dentition": "PRIMARY"}
    )
    assert invalid_dentition.status_code == 422
    other = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": "Otra ruta",
    })
    crossed_route = api_client.post(
        f"/api/treatments/{other.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token, json=payload,
    )
    assert crossed_route.status_code == 409


def test_concurrent_planned_creation_waits_then_replays_once(api_client, db_session, security_world):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    seed_odontogram_planned_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    treatment, _, payload, endpoint = _create_planned(api_client, db_session, tenant)
    # Use a fresh key: the helper's initial creation is unrelated to this deterministic race.
    payload = {**payload, "idempotency_key": f"planned-race-{uuid4().hex}", "tooth": "37"}
    db_session.scalar(select(Treatment).where(Treatment.id == treatment["id"]).with_for_update())

    def create_once():
        return api_client.post(endpoint, token=tenant.dentist_admin.token, json=payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(create_once) for _ in range(2)]
        sleep(0.2)
        assert not any(future.done() for future in futures)
        db_session.commit()
        responses = [future.result(timeout=20) for future in futures]
    assert [response.status_code for response in responses] == [201, 201]
    assert sorted(response.json()["idempotent_replay"] for response in responses) == [False, True]
    ids = {response.json()["procedure"]["id"] for response in responses}
    assert len(ids) == 1
    procedure = db_session.get(TreatmentProcedure, next(iter(ids)))
    assert procedure.planned_odontogram_event_id is not None
    assert db_session.scalar(select(func.count()).select_from(OdontogramEvent).where(
        OdontogramEvent.procedure_id == procedure.id,
        OdontogramEvent.event_type == "PLANNED_PROCEDURE_ADDED",
    )) == 1


def test_concurrent_completion_and_cancellation_serialize_without_orphan_plan(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    seed_odontogram_planned_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    treatment, procedure, _, _ = _create_planned(api_client, db_session, tenant)
    done = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_CROWN"))
    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={
            "treatment_id": treatment["id"], "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Carrera sintética.",
        },
    ).json()
    completion_payload = {
        "clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(done.id),
        "idempotency_key": f"planned-complete-race-{uuid4().hex}",
        "source_diagnosis_action": "KEEP_ACTIVE", "scope_type": "TOOTH",
        "tooth": "36", "dentition": "PERMANENT",
    }

    def complete():
        return api_client.post(
            f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
            token=tenant.dentist_admin.token, json=completion_payload,
        )

    def cancel():
        return api_client.post(
            f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/cancel",
            token=tenant.dentist_admin.token, json={"reason": "Carrera sintética"},
        )

    db_session.scalar(select(TreatmentProcedure).where(
        TreatmentProcedure.id == procedure["id"]
    ).with_for_update())
    with ThreadPoolExecutor(max_workers=2) as executor:
        complete_future, cancel_future = executor.submit(complete), executor.submit(cancel)
        sleep(0.2)
        assert not complete_future.done() and not cancel_future.done()
        db_session.commit()
        completed, cancelled = complete_future.result(timeout=20), cancel_future.result(timeout=20)
    assert sum(response.status_code == 200 for response in (completed, cancelled)) == 1
    db_session.expire_all()
    stored = db_session.get(TreatmentProcedure, procedure["id"])
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    performed = db_session.scalar(select(func.count()).select_from(OdontogramEvent).where(
        OdontogramEvent.procedure_id == stored.id,
        OdontogramEvent.event_type == "PROCEDURE_PERFORMED",
    ))
    if stored.status == "Cancelado":
        assert plan.status == "VOIDED_BY_COMPENSATING_EVENT" and performed == 0
    else:
        assert stored.status == "Realizado" and plan.status == "CONFIRMED" and performed == 1
