from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from time import sleep
from uuid import uuid4

from sqlalchemy import func, select

from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent
from app.models.treatment import ProcedureCatalogDiagnosis, ProcedureCatalogItem, TreatmentProcedure
from app.services.procedure_catalog_odontogram_clear_seed_service import (
    preview_odontogram_clear_catalog,
    seed_odontogram_clear_catalog,
)
from app.services.procedure_catalog_seed_service import normalize_catalog_name


def _clinical_items(db_session) -> None:
    definitions = (
        ("FIND_CARIES", "Caries", "FINDING", "solid", ["TOOTH", "TOOTH_SURFACE"]),
        ("FIND_FRACTURE", "Fractura", "FINDING", "diagonal", ["TOOTH", "TOOTH_SURFACE"]),
        ("FIND_ENDO_DEFECTIVE", "Endodoncia previa en mal estado", "FINDING", "zigzag", ["TOOTH"]),
        ("DONE_RESIN", "Resina realizada", "PERFORMED_PROCEDURE", "solid", ["TOOTH", "TOOTH_SURFACE"]),
        ("DONE_ENDO", "Endodoncia realizada", "PERFORMED_PROCEDURE", "solid", ["TOOTH"]),
    )
    for code, name, item_type, pattern, scopes in definitions:
        db_session.add(
            OdontogramCatalogItem(
                company_id=None,
                code=code,
                name=name,
                type=item_type,
                color="#2563eb",
                pattern=pattern,
                symbol=code,
                allowed_scopes=scopes,
                allowed_surfaces=None,
                is_active=True,
            )
        )
    db_session.commit()


def test_clear_twenty_seed_is_fixed_idempotent_and_preserves_collision(
    db_session, security_world
) -> None:
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    existing_name = "Retratamiento incisivos y caninos"
    existing = ProcedureCatalogItem(
        company_id=tenant.company.id,
        name=existing_name,
        normalized_name=normalize_catalog_name(existing_name),
        suggested_value=Decimal("777"),
        suggested_scope_type="GENERAL",
        odontogram_behavior="NO_CHANGE",
        is_active=True,
        created_by=tenant.admin.user.id,
    )
    db_session.add(existing)
    db_session.commit()

    preview = preview_odontogram_clear_catalog(db_session, tenant.company)
    assert preview.would_insert == 19
    assert len(preview.collisions) == 1
    result = seed_odontogram_clear_catalog(
        db_session, tenant.company, tenant.admin.user.id
    )
    db_session.commit()
    assert (result.inserted, result.skipped_collisions, result.diagnosis_links) == (
        19,
        1,
        19,
    )
    db_session.refresh(existing)
    assert existing.suggested_value == Decimal("777")
    assert existing.odontogram_behavior == "NO_CHANGE"
    assert db_session.scalar(
        select(func.count())
        .select_from(ProcedureCatalogDiagnosis)
        .where(ProcedureCatalogDiagnosis.procedure_catalog_id == existing.id)
    ) == 0

    replay = seed_odontogram_clear_catalog(
        db_session, tenant.company, tenant.admin.user.id
    )
    db_session.commit()
    assert (replay.inserted, replay.skipped_collisions, replay.diagnosis_links) == (
        0,
        20,
        0,
    )


def test_clear_twenty_isolated_clp_cop_and_no_runtime_conversion(
    db_session, security_world
) -> None:
    chile, colombia = security_world.tenant_a, security_world.tenant_b
    _clinical_items(db_session)
    chile.company.country = "Chile"
    colombia.company.country = "Colombia"
    db_session.commit()
    seed_odontogram_clear_catalog(db_session, chile.company, chile.admin.user.id)
    seed_odontogram_clear_catalog(db_session, colombia.company, colombia.admin.user.id)
    db_session.commit()

    rows_cl = db_session.scalars(
        select(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == chile.company.id,
            ProcedureCatalogItem.price_provenance["catalog_version"].astext
            == "KIMBERLY-2026-11-08-ODONTOGRAM-CLEAR-20-DRAFT",
        )
    ).all()
    rows_co = db_session.scalars(
        select(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == colombia.company.id,
            ProcedureCatalogItem.price_provenance["catalog_version"].astext
            == "KIMBERLY-2026-11-08-ODONTOGRAM-CLEAR-20-DRAFT",
        )
    ).all()
    assert len(rows_cl) == len(rows_co) == 20
    assert all(row.price_currency == "CLP" for row in rows_cl)
    assert all(row.price_currency == "COP" for row in rows_co)
    assert {row.id for row in rows_cl}.isdisjoint({row.id for row in rows_co})
    cl = next(row for row in rows_cl if row.price_provenance["source_row"] == 206)
    co = next(row for row in rows_co if row.price_provenance["source_row"] == 206)
    assert (cl.suggested_value, co.suggested_value) == (
        Decimal("180000"),
        Decimal("592000"),
    )
    assert cl.price_provenance["runtime_conversion"] is False
    assert co.price_provenance["runtime_conversion"] is False


def test_retreatment_requires_existing_defect_then_resolves_only_it_on_sign(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    seed_odontogram_clear_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    defect = db_session.scalar(
        select(OdontogramCatalogItem).where(
            OdontogramCatalogItem.company_id.is_(None),
            OdontogramCatalogItem.code == "FIND_ENDO_DEFECTIVE",
        )
    )
    done_endo = db_session.scalar(
        select(OdontogramCatalogItem).where(
            OdontogramCatalogItem.company_id.is_(None),
            OdontogramCatalogItem.code == "DONE_ENDO",
        )
    )
    retreatment = db_session.scalar(
        select(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == tenant.company.id,
            ProcedureCatalogItem.price_provenance["source_row"].astext == "206",
        )
    )
    assert defect is not None and done_endo is not None and retreatment is not None

    treatment = api_client.post(
        "/api/treatments",
        token=tenant.dentist_admin.token,
        json={
            "patient_id": str(tenant.patient.id),
            "name": "Retratamiento sintético",
            "main_site_id": str(tenant.site_1.id),
            "responsible_dentist_id": str(tenant.dentist_profile.id),
        },
    )
    assert treatment.status_code == 201, treatment.text
    endpoint = f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis"
    base_payload = {
        "catalog_procedure_id": str(retreatment.id),
        "name": retreatment.name,
        "unit_value": str(retreatment.suggested_value),
        "quantity": "1",
        "site_id": str(tenant.site_1.id),
        "dentist_id": str(tenant.dentist_profile.id),
        "scope_type": "TOOTH",
        "tooth": "36",
        "idempotency_key": f"retreatment-{uuid4().hex}",
        "diagnosis_mode": "CREATE_NEW",
        "diagnosis_catalog_item_id": str(defect.id),
        "dentition": "PERMANENT",
    }
    missing_prior = api_client.post(
        endpoint, token=tenant.dentist_admin.token, json=base_payload
    )
    assert missing_prior.status_code == 422
    assert "no se crea ese antecedente" in missing_prior.json()["detail"].lower()

    prior_endo = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={
            "event_type": "PROCEDURE_PERFORMED",
            "status": "CONFIRMED",
            "details": [
                {
                    "catalog_item_id": str(done_endo.id),
                    "scope_type": "TOOTH",
                    "tooth_code": "36",
                    "dentition": "PERMANENT",
                    "layer": "PERFORMED",
                }
            ],
        },
    )
    assert prior_endo.status_code == 201, prior_endo.text
    prior = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={
            "event_type": "FINDING_ADDED",
            "status": "CONFIRMED",
            "details": [
                {
                    "catalog_item_id": str(defect.id),
                    "scope_type": "TOOTH",
                    "tooth_code": "36",
                    "dentition": "PERMANENT",
                    "layer": "FINDING",
                    "metadata": {
                        "prior_done_endo_event_id": prior_endo.json()["id"]
                    },
                }
            ],
        },
    )
    assert prior.status_code == 201, prior.text
    reuse_prompt = api_client.post(
        endpoint, token=tenant.dentist_admin.token, json=base_payload
    )
    assert reuse_prompt.status_code == 201, reuse_prompt.text
    assert reuse_prompt.json()["procedure"] is None
    assert reuse_prompt.json()["compatible_existing_event_id"] == prior.json()["id"]

    linked_payload = {
        **base_payload,
        "idempotency_key": f"retreatment-linked-{uuid4().hex}",
        "diagnosis_mode": "USE_EXISTING",
        "existing_odontogram_event_id": prior.json()["id"],
    }
    linked = api_client.post(
        endpoint, token=tenant.dentist_admin.token, json=linked_payload
    )
    assert linked.status_code == 201, linked.text
    procedure = linked.json()["procedure"]

    second_treatment = api_client.post(
        "/api/treatments",
        token=tenant.dentist_admin.token,
        json={"patient_id": str(tenant.patient.id), "name": "Segundo retratamiento"},
    )
    duplicate_link = api_client.post(
        f"/api/treatments/{second_treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            **linked_payload,
            "idempotency_key": f"retreatment-duplicate-{uuid4().hex}",
        },
    )
    assert duplicate_link.status_code == 409

    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={
            "treatment_id": treatment.json()["id"],
            "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id),
            "evolution_text": "Retratamiento endodóntico sintético.",
        },
    )
    assert evolution.status_code == 201, evolution.text
    completion_key = f"retreatment-completion-{uuid4().hex}"
    completion_endpoint = (
        f"/api/treatments/{treatment.json()['id']}/procedures/"
        f"{procedure['id']}/clinical-completion"
    )
    completion_payload = {
        "clinical_evolution_id": evolution.json()["id"],
        "odontogram_catalog_item_id": str(done_endo.id),
        "idempotency_key": completion_key,
        "source_odontogram_event_id": prior.json()["id"],
        "source_diagnosis_action": "RESOLVE_ON_SIGN",
        "scope_type": "TOOTH",
        "tooth": "36",
    }
    keep_active = api_client.post(
        completion_endpoint,
        token=tenant.dentist_admin.token,
        json={**completion_payload, "source_diagnosis_action": "KEEP_ACTIVE"},
    )
    assert keep_active.status_code == 409
    completed = api_client.post(
        completion_endpoint,
        token=tenant.dentist_admin.token,
        json=completion_payload,
    )
    assert completed.status_code == 200, completed.text
    replay = api_client.post(
        completion_endpoint,
        token=tenant.dentist_admin.token,
        json=completion_payload,
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    source = db_session.get(OdontogramEvent, prior.json()["id"])
    performed = db_session.get(
        OdontogramEvent, completed.json()["odontogram_event_id"]
    )
    db_session.refresh(source)
    db_session.refresh(performed)
    assert source.status == "CONFIRMED"
    assert performed.status == "DRAFT"

    preserved_prior_endo = db_session.get(OdontogramEvent, prior_endo.json()["id"])
    preserved_prior_endo.status = "VOIDED_BY_COMPENSATING_EVENT"
    db_session.commit()
    rejected_sign = api_client.post(
        f"/api/clinical-evolutions/{evolution.json()['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution.json()["version"], "confirm_complete": True},
    )
    assert rejected_sign.status_code == 409
    db_session.refresh(source)
    db_session.refresh(performed)
    assert source.status == "CONFIRMED"
    assert performed.status == "DRAFT"
    preserved_prior_endo.status = "CONFIRMED"
    db_session.commit()

    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution.json()['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution.json()["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    db_session.refresh(source)
    db_session.refresh(performed)
    db_session.refresh(preserved_prior_endo)
    assert source.status == "VOIDED_BY_COMPENSATING_EVENT"
    assert performed.status == "CONFIRMED"
    assert preserved_prior_endo.status == "CONFIRMED"
    assert db_session.scalar(
        select(func.count())
        .select_from(OdontogramEvent)
        .where(
            OdontogramEvent.procedure_id == procedure["id"],
            OdontogramEvent.event_type == "PROCEDURE_PERFORMED",
        )
    ) == 1


def test_defective_marker_rejects_semantically_invalid_prior_endo_events(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    defect = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "FIND_ENDO_DEFECTIVE"
    ))
    done = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "DONE_ENDO"
    ))
    cases = [
        ("FINDING_ADDED", "PERFORMED", "TOOTH", 1),
        ("PROCEDURE_PERFORMED", "FINDING", "TOOTH", 1),
        ("PROCEDURE_PERFORMED", "PERFORMED", "TOOTH_SURFACE", 1),
        ("PROCEDURE_PERFORMED", "PERFORMED", "TOOTH", 2),
    ]
    for index, (event_type, layer, scope, count) in enumerate(cases):
        details = [{
            "catalog_item_id": str(done.id), "scope_type": scope,
            "tooth_code": "36", "dentition": "PERMANENT", "layer": layer,
            **({"surfaces": ["OCCLUSAL"]} if scope == "TOOTH_SURFACE" else {}),
        } for _ in range(count)]
        prior = api_client.post(
            f"/api/patients/{tenant.patient.id}/odontogram/events",
            token=tenant.dentist_admin.token,
            json={"event_type": event_type, "status": "CONFIRMED", "details": details},
        )
        if scope == "TOOTH_SURFACE":
            assert prior.status_code == 422
            continue
        assert prior.status_code == 201, prior.text
        marker = api_client.post(
            f"/api/patients/{tenant.patient.id}/odontogram/events",
            token=tenant.dentist_admin.token,
            json={
                "event_type": "FINDING_ADDED", "status": "CONFIRMED",
                "details": [{
                    "catalog_item_id": str(defect.id), "scope_type": "TOOTH",
                    "tooth_code": "36", "dentition": "PERMANENT", "layer": "FINDING",
                    "metadata": {"prior_done_endo_event_id": prior.json()["id"]},
                }],
                "observation": f"invalid-prior-{index}",
            },
        )
        assert marker.status_code == 409


def test_concurrent_retreatments_cannot_link_same_defective_marker(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    seed_odontogram_clear_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    defect = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "FIND_ENDO_DEFECTIVE"
    ))
    done = db_session.scalar(select(OdontogramCatalogItem).where(
        OdontogramCatalogItem.code == "DONE_ENDO"
    ))
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "206",
    ))
    prior = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={"event_type": "PROCEDURE_PERFORMED", "status": "CONFIRMED", "details": [{
            "catalog_item_id": str(done.id), "scope_type": "TOOTH", "tooth_code": "36",
            "dentition": "PERMANENT", "layer": "PERFORMED",
        }]},
    )
    marker = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={"event_type": "FINDING_ADDED", "status": "CONFIRMED", "details": [{
            "catalog_item_id": str(defect.id), "scope_type": "TOOTH", "tooth_code": "36",
            "dentition": "PERMANENT", "layer": "FINDING",
            "metadata": {"prior_done_endo_event_id": prior.json()["id"]},
        }]},
    )
    treatments = [api_client.post(
        "/api/treatments", token=tenant.dentist_admin.token,
        json={"patient_id": str(tenant.patient.id), "name": f"Concurrente {index}"},
    ).json() for index in range(2)]
    def link(index):
        return api_client.post(
            f"/api/treatments/{treatments[index]['id']}/procedures/with-diagnosis",
            token=tenant.dentist_admin.token,
            json={
                "catalog_procedure_id": str(catalog.id), "name": catalog.name,
                "unit_value": str(catalog.suggested_value), "quantity": "1",
                "scope_type": "TOOTH", "tooth": "36",
                "idempotency_key": f"concurrent-retreatment-{index}-{uuid4().hex}",
                "diagnosis_mode": "USE_EXISTING", "diagnosis_catalog_item_id": str(defect.id),
                "existing_odontogram_event_id": marker.json()["id"], "dentition": "PERMANENT",
            },
        )
    db_session.scalar(select(OdontogramEvent).where(
        OdontogramEvent.id == marker.json()["id"]
    ).with_for_update())
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(link, index) for index in range(2)]
        sleep(0.2)
        assert not any(future.done() for future in futures)
        db_session.commit()
        responses = [future.result() for future in futures]
    assert sorted(response.status_code for response in responses) == [201, 409]
    links = db_session.scalars(select(TreatmentProcedure).where(
        TreatmentProcedure.source_odontogram_event_id == marker.json()["id"]
    )).all()
    assert len(links) == 1
