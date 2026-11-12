from uuid import uuid4

from sqlalchemy import func, select

from app.models.odontogram import OdontogramEvent
from app.models.treatment import Budget, ProcedureCatalogItem, TreatmentProcedure


def _treatment_payload(tenant, *, site_id=None):
    return {
        "patient_id": str(tenant.patient.id),
        "name": "Presupuesto administrativo de prueba",
        "main_site_id": str(site_id or tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    }


def test_secretary_prepares_budget_without_clinical_capabilities(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    token = tenant.secretary.token
    treatment = api_client.post("/api/treatments", token=token, json=_treatment_payload(tenant))
    assert treatment.status_code == 201, treatment.text
    treatment_id = treatment.json()["id"]

    catalog = ProcedureCatalogItem(
        company_id=tenant.company.id,
        name="Procedimiento con efecto para presupuesto",
        normalized_name=f"administrativo-{uuid4()}",
        is_active=True,
        odontogram_behavior="PLANNED_RESULT",
        odontogram_scope_type="TOOTH",
        created_by=tenant.dentist_admin.user.id,
    )
    db_session.add(catalog)
    db_session.commit()

    event_count = db_session.scalar(select(func.count(OdontogramEvent.id)))
    rejected_integrated = api_client.post(
        f"/api/treatments/{treatment_id}/procedures",
        token=token,
        json={
            "catalog_procedure_id": str(catalog.id),
            "name": catalog.name,
            "unit_value": "45000",
            "scope_type": "TOOTH",
            "tooth": "36",
            "status": "Pendiente",
        },
    )
    assert rejected_integrated.status_code == 422

    created = api_client.post(
        f"/api/treatments/{treatment_id}/procedures",
        token=token,
        json={
            "catalog_procedure_id": str(catalog.id),
            "name": catalog.name,
            "unit_value": "45000",
            "scope_type": "TOOTH",
            "tooth": "36",
            "status": "Pendiente",
            "odontogram_integration_opt_out": True,
            "idempotency_key": "secretary-budget-effect-1",
        },
    )
    assert created.status_code == 201, created.text
    procedure = created.json()
    assert procedure["odontogram_integration_opt_out"] is True
    assert db_session.scalar(select(func.count(OdontogramEvent.id))) == event_count

    budget = api_client.post(
        f"/api/treatments/{treatment_id}/budget",
        token=token,
        json={"procedure_ids": [procedure["id"]], "discount_value": "0"},
    )
    assert budget.status_code == 201, budget.text
    assert budget.json()["final_value"] == "45000.00"
    assert api_client.get(f"/api/budgets/{budget.json()['id']}/pdf", token=token).status_code == 200

    edited = api_client.patch(
        f"/api/treatments/{treatment_id}/procedures/{procedure['id']}",
        token=token,
        json={"unit_value": "47000", "observations": "Preparado por secretaría"},
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["unit_value"] == "47000.00"

    forbidden = [
        api_client.post(
            f"/api/treatments/{treatment_id}/procedures/{procedure['id']}/mark-done",
            token=token,
        ),
        api_client.post(
            f"/api/treatments/{treatment_id}/procedures/{procedure['id']}/cancel",
            token=token,
            json={"reason": "No autorizado"},
        ),
        api_client.post(
            f"/api/treatments/{treatment_id}/procedures/with-diagnosis",
            token=token,
            json={
                "catalog_procedure_id": str(catalog.id),
                "name": catalog.name,
                "unit_value": "45000",
                "scope_type": "TOOTH",
                "tooth": "36",
                "idempotency_key": "secretary-clinical-denied",
                "diagnosis_mode": "NONE",
            },
        ),
    ]
    assert [response.status_code for response in forbidden] == [403, 403, 403]


def test_secretary_budget_preparation_respects_tenant_and_site(
    api_client, db_session, security_world
) -> None:
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    token = tenant_a.restricted_site_1.token

    wrong_site = api_client.post(
        "/api/treatments", token=token, json=_treatment_payload(tenant_a, site_id=tenant_a.site_2.id)
    )
    assert wrong_site.status_code == 403
    cross_tenant = api_client.post(
        "/api/treatments", token=token, json=_treatment_payload(tenant_b)
    )
    assert cross_tenant.status_code in {403, 404}

    before_b = db_session.scalar(
        select(func.count(TreatmentProcedure.id)).where(
            TreatmentProcedure.company_id == tenant_b.company.id
        )
    )
    own = api_client.post("/api/treatments", token=token, json=_treatment_payload(tenant_a))
    assert own.status_code == 201, own.text
    assert db_session.scalar(
        select(func.count(TreatmentProcedure.id)).where(
            TreatmentProcedure.company_id == tenant_b.company.id
        )
    ) == before_b


def test_restricted_secretary_cannot_edit_or_delete_procedure_from_other_site(
    api_client, db_session, security_world
) -> None:
    tenant = security_world.tenant_a
    treatment = api_client.post(
        "/api/treatments",
        token=tenant.admin.token,
        json=_treatment_payload(tenant, site_id=tenant.site_1.id),
    )
    assert treatment.status_code == 201, treatment.text
    treatment_id = treatment.json()["id"]
    created = api_client.post(
        f"/api/treatments/{treatment_id}/procedures",
        token=tenant.admin.token,
        json={
            "name": "Procedimiento administrativo sede dos",
            "unit_value": "91000",
            "quantity": "1",
            "scope_type": "GENERAL",
            "site_id": str(tenant.site_2.id),
            "status": "Pendiente",
            "idempotency_key": "admin-site-two-procedure",
        },
    )
    assert created.status_code == 201, created.text
    procedure_id = created.json()["id"]

    patch = api_client.patch(
        f"/api/treatments/{treatment_id}/procedures/{procedure_id}",
        token=tenant.restricted_site_1.token,
        json={"unit_value": "92000"},
    )
    delete = api_client.delete(
        f"/api/treatments/{treatment_id}/procedures/{procedure_id}",
        token=tenant.restricted_site_1.token,
    )
    assert patch.status_code == 403, patch.text
    assert delete.status_code == 403, delete.text
    db_session.expire_all()
    persisted = db_session.get(TreatmentProcedure, procedure_id)
    assert persisted is not None
    assert str(persisted.unit_value) == "91000.00"
    assert persisted.site_id == tenant.site_2.id
