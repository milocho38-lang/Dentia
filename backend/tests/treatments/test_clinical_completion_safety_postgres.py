from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from time import sleep
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent, OdontogramEventDetail
from app.models.treatment import ProcedureCatalogDiagnosis, ProcedureCatalogItem, TreatmentProcedure


SURFACES = ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]


def _configured_resin(db_session, tenant):
    caries = OdontogramCatalogItem(
        company_id=None, code=f"FIND_CARIES_{uuid4().hex}", name="Caries", type="FINDING",
        color="#dc2626", pattern="solid", symbol="C", allowed_scopes=["TOOTH", "TOOTH_SURFACE"],
        allowed_surfaces=SURFACES, is_active=True,
    )
    fracture = OdontogramCatalogItem(
        company_id=None, code=f"FIND_FRACTURE_{uuid4().hex}", name="Fractura", type="FINDING",
        color="#ef4444", pattern="diagonal", symbol="F", allowed_scopes=["TOOTH", "TOOTH_SURFACE"],
        allowed_surfaces=SURFACES, is_active=True,
    )
    done = OdontogramCatalogItem(
        company_id=None, code=f"DONE_RESIN_{uuid4().hex}", name="Resina realizada", type="PERFORMED_PROCEDURE",
        color="#2563eb", pattern="solid", symbol="Re", allowed_scopes=["TOOTH", "TOOTH_SURFACE"],
        allowed_surfaces=SURFACES, is_active=True,
    )
    wrong_done = OdontogramCatalogItem(
        company_id=None, code=f"DONE_CROWN_{uuid4().hex}", name="Corona realizada", type="PERFORMED_PROCEDURE",
        color="#16a34a", pattern="solid", symbol="Co", allowed_scopes=["TOOTH", "TOOTH_SURFACE"],
        allowed_surfaces=SURFACES, is_active=True,
    )
    db_session.add_all([caries, fracture, done, wrong_done])
    db_session.flush()
    procedure = ProcedureCatalogItem(
        company_id=tenant.company.id, name=f"Resina segura {uuid4().hex}",
        normalized_name=f"resina segura {uuid4().hex}", suggested_value=Decimal("40000"),
        suggested_scope_type="TOOTH_SURFACE", odontogram_behavior="REQUIRES_DIAGNOSIS",
        odontogram_scope_type="TOOTH_SURFACE", default_performed_catalog_item_id=done.id,
        is_active=True, created_by=tenant.dentist_admin.user.id,
    )
    db_session.add(procedure)
    db_session.flush()
    db_session.add_all([
        ProcedureCatalogDiagnosis(
            company_id=tenant.company.id, procedure_catalog_id=procedure.id,
            odontogram_catalog_item_id=item.id, is_active=True,
        )
        for item in (caries, fracture)
    ])
    db_session.commit()
    return procedure, caries, fracture, done, wrong_done


def _create_treatment_and_procedure(api_client, tenant, catalog, diagnosis, tooth="36"):
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": f"Tratamiento seguro {uuid4().hex}",
        "main_site_id": str(tenant.site_1.id), "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    assert treatment.status_code == 201, treatment.text
    created = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": str(catalog.suggested_value), "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "TOOTH_SURFACE", "tooth": tooth, "surfaces": ["OCCLUSAL"],
            "idempotency_key": f"diagnosis-{uuid4().hex}", "diagnosis_mode": "CREATE_NEW",
            "diagnosis_catalog_item_id": str(diagnosis.id), "dentition": "PERMANENT",
        },
    )
    assert created.status_code == 201, created.text
    return treatment.json(), created.json()


def _create_evolution(api_client, tenant, treatment_id):
    response = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={
            "treatment_id": treatment_id, "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Realización clínica de prueba.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _completion_payload(evolution_id, result_id, source_id, *, tooth="36", key=None):
    return {
        "clinical_evolution_id": evolution_id, "odontogram_catalog_item_id": str(result_id),
        "idempotency_key": key or f"completion-{uuid4().hex}",
        "source_odontogram_event_id": str(source_id), "source_diagnosis_action": "RESOLVE_ON_SIGN",
        "scope_type": "TOOTH_SURFACE", "tooth": tooth, "surfaces": ["OCCLUSAL"],
    }


def test_completion_rejects_unrelated_scope_source_and_result_then_signs_exact_link(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, fracture, done, wrong_done = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    other_treatment, other_procedure = _create_treatment_and_procedure(api_client, tenant, catalog, fracture, tooth="37")
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    endpoint = f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion"

    wrong_scope = api_client.post(endpoint, token=tenant.dentist_admin.token, json=_completion_payload(
        evolution["id"], done.id, procedure["diagnosis_event_id"], tooth="37"
    ))
    assert wrong_scope.status_code == 409
    wrong_source = api_client.post(endpoint, token=tenant.dentist_admin.token, json=_completion_payload(
        evolution["id"], done.id, other_procedure["diagnosis_event_id"]
    ))
    assert wrong_source.status_code == 409
    wrong_result = api_client.post(endpoint, token=tenant.dentist_admin.token, json=_completion_payload(
        evolution["id"], wrong_done.id, procedure["diagnosis_event_id"]
    ))
    assert wrong_result.status_code == 409

    key = f"completion-{uuid4().hex}"
    completed = api_client.post(endpoint, token=tenant.dentist_admin.token, json=_completion_payload(
        evolution["id"], done.id, procedure["diagnosis_event_id"], key=key
    ))
    assert completed.status_code == 200, completed.text
    replay = api_client.post(endpoint, token=tenant.dentist_admin.token, json=_completion_payload(
        evolution["id"], done.id, procedure["diagnosis_event_id"], key=key
    ))
    assert replay.status_code == 200 and replay.json()["idempotent_replay"] is True
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    replay_after_sign = api_client.post(
        endpoint,
        token=tenant.dentist_admin.token,
        json=_completion_payload(
            evolution["id"], done.id, procedure["diagnosis_event_id"], key=key
        ),
    )
    assert replay_after_sign.status_code == 200, replay_after_sign.text
    assert replay_after_sign.json()["idempotent_replay"] is True
    assert replay_after_sign.json()["odontogram_event_id"] == completed.json()["odontogram_event_id"]
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    unrelated = db_session.get(OdontogramEvent, other_procedure["diagnosis_event_id"])
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    db_session.refresh(source); db_session.refresh(unrelated); db_session.refresh(performed)
    assert source.status == "VOIDED_BY_COMPENSATING_EVENT"
    assert unrelated.status == "CONFIRMED"
    assert performed.status == "CONFIRMED"


def test_completion_idempotency_key_cannot_cross_route_evolution_or_tenant(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, fracture, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    other_treatment, other_procedure = _create_treatment_and_procedure(
        api_client, tenant, catalog, fracture, tooth="37"
    )
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    other_evolution = _create_evolution(api_client, tenant, other_treatment["id"])
    key = f"completion-{uuid4().hex}"
    endpoint = f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion"
    payload = _completion_payload(
        evolution["id"], done.id, procedure["diagnosis_event_id"], key=key
    )
    created = api_client.post(endpoint, token=tenant.dentist_admin.token, json=payload)
    assert created.status_code == 200, created.text

    wrong_route = api_client.post(
        f"/api/treatments/{other_treatment['id']}/procedures/{other_procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=_completion_payload(
            other_evolution["id"], done.id, other_procedure["diagnosis_event_id"],
            tooth="37", key=key,
        ),
    )
    assert wrong_route.status_code == 409
    assert "otra realización" in wrong_route.json()["detail"]

    wrong_evolution = api_client.post(
        endpoint,
        token=tenant.dentist_admin.token,
        json={**payload, "clinical_evolution_id": other_evolution["id"]},
    )
    assert wrong_evolution.status_code in {404, 409}

    missing = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{uuid4()}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=payload,
    )
    assert missing.status_code == 404

    tenant_a = security_world.tenant_a
    other_company = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant_a.dentist_admin.token,
        json=payload,
    )
    assert other_company.status_code == 404


def test_signature_fails_closed_if_link_is_corrupted_and_preserves_events(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, fracture, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    _, other_procedure = _create_treatment_and_procedure(api_client, tenant, catalog, fracture, tooth="37")
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    endpoint = f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion"
    completed = api_client.post(endpoint, token=tenant.dentist_admin.token, json=_completion_payload(
        evolution["id"], done.id, procedure["diagnosis_event_id"]
    ))
    assert completed.status_code == 200, completed.text
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    source.procedure_id = other_procedure["procedure"]["id"]
    db_session.commit()

    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 409
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    db_session.refresh(source); db_session.refresh(performed)
    assert source.status == "CONFIRMED"
    assert performed.status == "DRAFT"


def test_completion_cannot_use_other_company_diagnosis(api_client, db_session, security_world):
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    catalog_a, caries_a, _, _, _ = _configured_resin(db_session, tenant_a)
    catalog_b, caries_b, _, done_b, _ = _configured_resin(db_session, tenant_b)
    _, procedure_a = _create_treatment_and_procedure(api_client, tenant_a, catalog_a, caries_a)
    treatment_b, procedure_b = _create_treatment_and_procedure(api_client, tenant_b, catalog_b, caries_b)
    evolution_b = _create_evolution(api_client, tenant_b, treatment_b["id"])
    response = api_client.post(
        f"/api/treatments/{treatment_b['id']}/procedures/{procedure_b['procedure']['id']}/clinical-completion",
        token=tenant_b.dentist_admin.token,
        json=_completion_payload(evolution_b["id"], done_b.id, procedure_a["diagnosis_event_id"]),
    )
    assert response.status_code == 404


def test_ordinary_diagnosis_can_support_two_keep_active_catalog_treatments(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, _, done, _ = _configured_resin(db_session, tenant)
    treatment_one, procedure_one = _create_treatment_and_procedure(
        api_client, tenant, catalog, caries
    )
    treatment_two = api_client.post(
        "/api/treatments",
        token=tenant.dentist_admin.token,
        json={
            "patient_id": str(tenant.patient.id),
            "name": "Segundo tratamiento sobre diagnóstico ordinario",
            "main_site_id": str(tenant.site_1.id),
            "responsible_dentist_id": str(tenant.dentist_profile.id),
        },
    )
    second = api_client.post(
        f"/api/treatments/{treatment_two.json()['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            "catalog_procedure_id": str(catalog.id),
            "name": catalog.name,
            "unit_value": str(catalog.suggested_value),
            "quantity": "1",
            "site_id": str(tenant.site_1.id),
            "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "TOOTH_SURFACE",
            "tooth": "36",
            "surfaces": ["OCCLUSAL"],
            "idempotency_key": f"shared-{uuid4().hex}",
            "diagnosis_mode": "USE_EXISTING",
            "diagnosis_catalog_item_id": str(caries.id),
            "existing_odontogram_event_id": procedure_one["diagnosis_event_id"],
            "dentition": "PERMANENT",
        },
    )
    assert second.status_code == 201, second.text
    owner_evolution = _create_evolution(api_client, tenant, treatment_one["id"])
    rejected_resolve = api_client.post(
        f"/api/treatments/{treatment_one['id']}/procedures/"
        f"{procedure_one['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=_completion_payload(
            owner_evolution["id"], done.id, procedure_one["diagnosis_event_id"]
        ),
    )
    assert rejected_resolve.status_code == 409
    source_before_keep = db_session.get(
        OdontogramEvent, procedure_one["diagnosis_event_id"]
    )
    db_session.refresh(source_before_keep)
    assert source_before_keep.status == "CONFIRMED"
    evolution = _create_evolution(api_client, tenant, treatment_two.json()["id"])
    payload = _completion_payload(
        evolution["id"], done.id, procedure_one["diagnosis_event_id"]
    )
    payload["source_diagnosis_action"] = "KEEP_ACTIVE"
    completed = api_client.post(
        f"/api/treatments/{treatment_two.json()['id']}/procedures/"
        f"{second.json()['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=payload,
    )
    assert completed.status_code == 200, completed.text
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    source = db_session.get(OdontogramEvent, procedure_one["diagnosis_event_id"])
    db_session.refresh(source)
    assert source.status == "CONFIRMED"


def test_concurrent_new_link_and_resolving_signature_serialize_safely(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, _, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=_completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"]),
    )
    assert completed.status_code == 200, completed.text
    second_treatment = api_client.post(
        "/api/treatments", token=tenant.dentist_admin.token,
        json={"patient_id": str(tenant.patient.id), "name": "Alta paralela a firma"},
    ).json()
    def sign():
        return api_client.post(
            f"/api/clinical-evolutions/{evolution['id']}/sign",
            token=tenant.dentist_admin.token,
            json={"version": evolution["version"], "confirm_complete": True},
        )
    def link():
        return api_client.post(
            f"/api/treatments/{second_treatment['id']}/procedures/with-diagnosis",
            token=tenant.dentist_admin.token,
            json={
                "catalog_procedure_id": str(catalog.id), "name": catalog.name,
                "unit_value": str(catalog.suggested_value), "quantity": "1",
                "scope_type": "TOOTH_SURFACE", "tooth": "36", "surfaces": ["OCCLUSAL"],
                "idempotency_key": f"parallel-link-{uuid4().hex}",
                "diagnosis_mode": "USE_EXISTING", "diagnosis_catalog_item_id": str(caries.id),
                "existing_odontogram_event_id": procedure["diagnosis_event_id"],
                "dentition": "PERMANENT",
            },
        )
    db_session.scalar(select(OdontogramEvent).where(
        OdontogramEvent.id == procedure["diagnosis_event_id"]
    ).with_for_update())
    with ThreadPoolExecutor(max_workers=2) as executor:
        signed_future = executor.submit(sign)
        linked_future = executor.submit(link)
        sleep(0.2)
        assert not signed_future.done() and not linked_future.done()
        db_session.commit()
        signed, linked = signed_future.result(), linked_future.result()
    assert (signed.status_code, linked.status_code) in {(200, 404), (200, 409), (409, 201)}
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    db_session.refresh(source)
    linked_rows = db_session.scalars(select(TreatmentProcedure).where(
        TreatmentProcedure.source_odontogram_event_id == source.id
    )).all()
    if source.status == "VOIDED_BY_COMPENSATING_EVENT":
        assert len(linked_rows) == 1
    else:
        assert source.status == "CONFIRMED"
        assert len(linked_rows) == 2


def test_concurrent_completion_serializes_to_one_draft(api_client, db_session, security_world):
    tenant = security_world.tenant_b
    catalog, caries, _, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    endpoint = f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion"

    def complete_once(_index):
        return api_client.post(
            endpoint, token=tenant.dentist_admin.token,
            json=_completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"]),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(complete_once, range(2)))
    assert [response.status_code for response in responses] == [200, 200]
    event_ids = {response.json()["odontogram_event_id"] for response in responses}
    assert len(event_ids) == 1
    assert any(response.json()["idempotent_replay"] for response in responses)
    events = db_session.scalars(select(OdontogramEvent).where(
        OdontogramEvent.procedure_id == procedure["procedure"]["id"],
        OdontogramEvent.event_type == "PROCEDURE_PERFORMED",
    )).all()
    assert len(events) == 1 and events[0].status == "DRAFT"


def test_completion_fails_closed_for_source_event_with_additional_detail(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, fracture, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    db_session.add(OdontogramEventDetail(
        company_id=tenant.company.id, event_id=source.id, catalog_item_id=fracture.id,
        scope_type="TOOTH_SURFACE", tooth_code="37", dentition="PERMANENT",
        surfaces=["OCCLUSAL"], layer="FINDING",
    ))
    db_session.commit()
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    response = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=_completion_payload(evolution["id"], done.id, source.id),
    )
    assert response.status_code == 409
    treatment_procedure = db_session.get(
        TreatmentProcedure, procedure["procedure"]["id"]
    )
    db_session.refresh(source)
    assert source.status == "CONFIRMED"
    assert treatment_procedure.status == "Pendiente"
    assert len(db_session.scalars(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == source.id
    )).all()) == 2


def test_signature_fails_closed_if_source_becomes_multidetail_without_mutation(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, fracture, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=_completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"]),
    )
    assert completed.status_code == 200, completed.text
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    treatment_procedure = db_session.get(TreatmentProcedure, procedure["procedure"]["id"])
    before = (source.status, performed.status, treatment_procedure.status)
    db_session.add(OdontogramEventDetail(
        company_id=tenant.company.id, event_id=source.id, catalog_item_id=fracture.id,
        scope_type="TOOTH_SURFACE", tooth_code="37", dentition="PERMANENT",
        surfaces=["OCCLUSAL"], layer="FINDING",
    ))
    db_session.commit()
    detail_ids_before = [row.id for row in db_session.scalars(
        select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == source.id)
    ).all()]
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 409
    db_session.refresh(source); db_session.refresh(performed); db_session.refresh(treatment_procedure)
    assert (source.status, performed.status, treatment_procedure.status) == before
    assert [row.id for row in db_session.scalars(
        select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == source.id)
    ).all()] == detail_ids_before


@pytest.mark.parametrize("mutation", [
    "diagnosis_disabled", "scope_changed", "result_changed", "catalog_unlinked", "catalog_inactive",
])
def test_signature_revalidates_complete_configuration_and_rolls_back(
    api_client, db_session, security_world, mutation
):
    tenant = security_world.tenant_b
    catalog, caries, _, done, wrong_done = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=_completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"]),
    )
    assert completed.status_code == 200, completed.text
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    performed_detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == performed.id
    ))
    treatment_procedure = db_session.get(TreatmentProcedure, procedure["procedure"]["id"])
    if mutation == "diagnosis_disabled":
        link = db_session.scalar(select(ProcedureCatalogDiagnosis).where(
            ProcedureCatalogDiagnosis.procedure_catalog_id == catalog.id,
            ProcedureCatalogDiagnosis.odontogram_catalog_item_id == caries.id,
        ))
        link.is_active = False
    elif mutation == "scope_changed":
        performed_detail.tooth_code = "37"
    elif mutation == "result_changed":
        performed_detail.catalog_item_id = wrong_done.id
    elif mutation == "catalog_unlinked":
        treatment_procedure.catalog_procedure_id = None
    else:
        catalog.is_active = False
    db_session.commit()

    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 409
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    db_session.refresh(source); db_session.refresh(performed)
    assert source.status == "CONFIRMED"
    assert performed.status == "DRAFT"


def test_keep_active_confirms_result_and_preserves_source_diagnosis(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, _, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    payload = _completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"])
    payload["source_diagnosis_action"] = "KEEP_ACTIVE"
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token, json=payload,
    )
    assert completed.status_code == 200, completed.text
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    db_session.refresh(source); db_session.refresh(performed)
    assert source.status == "CONFIRMED"
    assert performed.status == "CONFIRMED"
    assert db_session.scalars(select(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "SOURCE_ODONTOGRAM_DIAGNOSIS_RESOLVED",
        AuditEvent.entity_id == source.id,
    )).all() == []


def test_manual_procedure_without_catalog_or_source_keeps_previous_completion_flow(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    _, _, _, done, _ = _configured_resin(db_session, tenant)
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": "Tratamiento manual",
        "main_site_id": str(tenant.site_1.id), "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    assert treatment.status_code == 201, treatment.text
    procedure = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures", token=tenant.dentist_admin.token,
        json={
            "name": "Procedimiento manual", "unit_value": "1000", "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "TOOTH_SURFACE", "tooth": "36", "surfaces": ["OCCLUSAL"],
        },
    )
    assert procedure.status_code == 201, procedure.text
    evolution = _create_evolution(api_client, tenant, treatment.json()["id"])
    endpoint = f"/api/treatments/{treatment.json()['id']}/procedures/{procedure.json()['id']}/clinical-completion"
    base_payload = {
        "clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(done.id),
        "source_diagnosis_action": "KEEP_ACTIVE", "scope_type": "TOOTH_SURFACE",
        "tooth": "36", "surfaces": ["OCCLUSAL"], "dentition": "PERMANENT",
    }
    for mismatch in (
        {"tooth": "37"},
        {"surfaces": ["MESIAL"]},
        {"dentition": "PRIMARY"},
    ):
        rejected = api_client.post(
            endpoint,
            token=tenant.dentist_admin.token,
            json={**base_payload, **mismatch, "idempotency_key": f"manual-bad-{uuid4().hex}"},
        )
        assert rejected.status_code in {409, 422}, rejected.text
    stored = db_session.get(TreatmentProcedure, procedure.json()["id"])
    db_session.refresh(stored)
    assert stored.status == "Pendiente"
    completed = api_client.post(
        endpoint,
        token=tenant.dentist_admin.token,
        json={**base_payload, "idempotency_key": f"manual-{uuid4().hex}"},
    )
    assert completed.status_code == 200, completed.text
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    db_session.refresh(performed)
    assert performed.status == "CONFIRMED" and performed.source_odontogram_event_id is None


def test_primary_tooth_completion_requires_primary_dentition(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    _, _, _, done, _ = _configured_resin(db_session, tenant)
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": "Tratamiento temporal",
        "main_site_id": str(tenant.site_1.id), "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    procedure = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures",
        token=tenant.dentist_admin.token,
        json={"name": "Restauración temporal", "unit_value": "1000", "quantity": "1",
              "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
              "scope_type": "TOOTH_SURFACE", "tooth": "51", "surfaces": ["OCCLUSAL"]},
    )
    assert procedure.status_code == 201, procedure.text
    evolution = _create_evolution(api_client, tenant, treatment.json()["id"])
    endpoint = f"/api/treatments/{treatment.json()['id']}/procedures/{procedure.json()['id']}/clinical-completion"
    payload = {"clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(done.id),
               "source_diagnosis_action": "KEEP_ACTIVE", "scope_type": "TOOTH_SURFACE",
               "tooth": "51", "surfaces": ["OCCLUSAL"]}
    wrong = api_client.post(endpoint, token=tenant.dentist_admin.token,
                            json={**payload, "dentition": "PERMANENT", "idempotency_key": f"primary-bad-{uuid4().hex}"})
    assert wrong.status_code == 422
    completed = api_client.post(endpoint, token=tenant.dentist_admin.token,
                                json={**payload, "dentition": "PRIMARY", "idempotency_key": f"primary-ok-{uuid4().hex}"})
    assert completed.status_code == 200, completed.text
    detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == completed.json()["odontogram_event_id"]
    ))
    assert detail.tooth_code == "51" and detail.dentition == "PRIMARY"


@pytest.mark.parametrize("source_action", ["KEEP_ACTIVE", "RESOLVE_ON_SIGN"])
def test_legacy_catalog_draft_without_configuration_snapshot_can_be_revalidated(
    api_client, db_session, security_world, source_action
):
    tenant = security_world.tenant_b
    catalog, caries, _, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    payload = _completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"])
    payload["source_diagnosis_action"] = source_action
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token, json=payload,
    )
    assert completed.status_code == 200, completed.text
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == performed.id
    ))
    legacy_metadata = dict(detail.detail_metadata or {})
    legacy_metadata.pop("completion_configuration_mode", None)
    legacy_metadata.pop("configured_catalog_procedure_id", None)
    detail.detail_metadata = legacy_metadata
    db_session.commit()

    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    db_session.refresh(source); db_session.refresh(performed)
    assert performed.status == "CONFIRMED"
    assert source.status == (
        "CONFIRMED" if source_action == "KEEP_ACTIVE" else "VOIDED_BY_COMPENSATING_EVENT"
    )


@pytest.mark.parametrize("source_action", ["KEEP_ACTIVE", "RESOLVE_ON_SIGN"])
def test_manual_procedure_with_unique_diagnosis_origin_signs_safely(
    api_client, db_session, security_world, source_action
):
    tenant = security_world.tenant_b
    _, caries, _, done, _ = _configured_resin(db_session, tenant)
    source = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=tenant.dentist_admin.token,
        json={
            "event_type": "FINDING_ADDED", "status": "CONFIRMED",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "details": [{
                "catalog_item_id": str(caries.id), "scope_type": "TOOTH_SURFACE",
                "tooth_code": "36", "dentition": "PERMANENT", "surfaces": ["OCCLUSAL"],
                "layer": "FINDING",
            }],
        },
    )
    assert source.status_code == 201, source.text
    treatment = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": f"Manual origen {uuid4().hex}",
        "main_site_id": str(tenant.site_1.id), "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    assert treatment.status_code == 201, treatment.text
    planned = api_client.post(
        f"/api/odontogram/events/{source.json()['id']}/planned-procedures",
        token=tenant.dentist_admin.token,
        json={
            "idempotency_key": f"manual-origin-{uuid4().hex}",
            "treatment_id": treatment.json()["id"], "name": "Procedimiento manual con origen",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "unit_value": "1000", "scope_type": "TOOTH_SURFACE", "tooth": "36",
            "surfaces": ["OCCLUSAL"],
        },
    )
    assert planned.status_code == 200, planned.text
    procedure_id = planned.json()["procedure"]["id"]
    evolution = _create_evolution(api_client, tenant, treatment.json()["id"])
    payload = _completion_payload(evolution["id"], done.id, source.json()["id"])
    payload["source_diagnosis_action"] = source_action
    completed = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/{procedure_id}/clinical-completion",
        token=tenant.dentist_admin.token, json=payload,
    )
    assert completed.status_code == 200, completed.text
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    source_event = db_session.get(OdontogramEvent, source.json()["id"])
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    db_session.refresh(source_event); db_session.refresh(performed)
    assert performed.status == "CONFIRMED"
    assert source_event.status == (
        "CONFIRMED" if source_action == "KEEP_ACTIVE" else "VOIDED_BY_COMPENSATING_EVENT"
    )


def test_ambiguous_legacy_manual_origin_fails_closed_without_changing_events(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, _, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=_completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"]),
    )
    assert completed.status_code == 200, completed.text
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == performed.id
    ))
    detail.detail_metadata = {
        key: value for key, value in (detail.detail_metadata or {}).items()
        if key not in {"completion_configuration_mode", "configured_catalog_procedure_id"}
    }
    db_session.get(TreatmentProcedure, procedure["procedure"]["id"]).catalog_procedure_id = None
    db_session.commit()

    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 409
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    db_session.refresh(source); db_session.refresh(performed)
    assert source.status == "CONFIRMED" and performed.status == "DRAFT"


def test_catalog_without_default_result_fails_before_draft_creation(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    catalog, caries, _, done, _ = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    catalog.default_performed_catalog_item_id = None
    db_session.commit()
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    response = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json=_completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"]),
    )
    assert response.status_code == 409
    assert db_session.scalars(select(OdontogramEvent).where(
        OdontogramEvent.procedure_id == procedure["procedure"]["id"],
        OdontogramEvent.event_type == "PROCEDURE_PERFORMED",
    )).all() == []
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    db_session.refresh(source)
    assert source.status == "CONFIRMED"


@pytest.mark.parametrize("mutation", [
    "diagnosis_disabled", "scope_changed", "result_changed", "catalog_unlinked", "catalog_inactive",
])
def test_keep_active_revalidates_mutations_and_rolls_back(
    api_client, db_session, security_world, mutation
):
    tenant = security_world.tenant_b
    catalog, caries, _, done, wrong_done = _configured_resin(db_session, tenant)
    treatment, procedure = _create_treatment_and_procedure(api_client, tenant, catalog, caries)
    evolution = _create_evolution(api_client, tenant, treatment["id"])
    payload = _completion_payload(evolution["id"], done.id, procedure["diagnosis_event_id"])
    payload["source_diagnosis_action"] = "KEEP_ACTIVE"
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['procedure']['id']}/clinical-completion",
        token=tenant.dentist_admin.token, json=payload,
    )
    assert completed.status_code == 200, completed.text
    performed = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    performed_detail = db_session.scalar(select(OdontogramEventDetail).where(
        OdontogramEventDetail.event_id == performed.id
    ))
    treatment_procedure = db_session.get(TreatmentProcedure, procedure["procedure"]["id"])
    if mutation == "diagnosis_disabled":
        link = db_session.scalar(select(ProcedureCatalogDiagnosis).where(
            ProcedureCatalogDiagnosis.procedure_catalog_id == catalog.id,
            ProcedureCatalogDiagnosis.odontogram_catalog_item_id == caries.id,
        ))
        link.is_active = False
    elif mutation == "scope_changed":
        performed_detail.tooth_code = "37"
    elif mutation == "result_changed":
        performed_detail.catalog_item_id = wrong_done.id
    elif mutation == "catalog_unlinked":
        treatment_procedure.catalog_procedure_id = None
    else:
        catalog.is_active = False
    db_session.commit()

    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign", token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 409
    source = db_session.get(OdontogramEvent, procedure["diagnosis_event_id"])
    db_session.refresh(source); db_session.refresh(performed)
    assert source.status == "CONFIRMED"
    assert performed.status == "DRAFT"
