import json
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from sqlalchemy import func, select

from app.models.odontogram import OdontogramCatalogItem, OdontogramEvent, OdontogramEventDetail
from app.models.treatment import ProcedureCatalogItem, TreatmentProcedure
from app.services.procedure_catalog_odontogram_extraction_seed_service import (
    CATALOG_PATH,
    EXPECTED_ROWS,
    _load_batch,
    preview_odontogram_extraction_catalog,
    seed_odontogram_extraction_catalog,
)
from app.services.procedure_catalog_seed_service import normalize_catalog_name


EXPECTED = {
    66: ("Exodoncia a colgajo (Compleja)", "50000", "165000"),
    67: ("Exodoncia Comlpeja", "80000", "263000"),
    68: ("Exodoncia de piezas incluidas o de implantes previamente instalados", "95000", "313000"),
    69: ("Exodoncia de Terceros molares incluidos", "20000", "66000"),
    70: ("Exodoncia pieza semi incluida", "120000", "395000"),
    71: ("Exodoncia simple", "40000", "132000"),
    72: ("Exodoncia Tercer Molar inferior Erupcionado", "100000", "329000"),
    73: ("Exodoncia Tercer Molar Semi erupcionado", "120000", "395000"),
    74: ("Exodoncia Terceros Molares Superiores Erupcionados", "60000", "197000"),
    267: ("Exodoncia piezas temporales", "30000", "99000"),
    268: ("Exodoncia supernumerario incluido", "90000", "296000"),
}


def _install_symbols_and_seed(session, tenant):
    for code, name, item_type, color in (
        ("PLAN_EXTRACTION", "Exodoncia planificada", "PLANNED_PROCEDURE", "#dc2626"),
        ("DONE_EXTRACTION", "Exodoncia realizada", "PERFORMED_PROCEDURE", "#2563eb"),
    ):
        if session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == code)) is None:
            session.add(OdontogramCatalogItem(
                company_id=None, code=code, name=name, type=item_type,
                color=color, pattern="symbol", symbol="X",
                allowed_scopes=["TOOTH"], is_active=True,
            ))
    tenant.company.country = "Chile"
    session.flush()
    seed_odontogram_extraction_catalog(session, tenant.company, tenant.admin.user.id)
    session.commit()


def _new_treatment(api_client, tenant, name):
    response = api_client.post("/api/treatments", token=tenant.dentist_admin.token, json={
        "patient_id": str(tenant.patient.id), "name": name,
        "main_site_id": str(tenant.site_1.id),
        "responsible_dentist_id": str(tenant.dentist_profile.id),
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_extraction_eleven_source_identity_prices_and_gates():
    payload = _load_batch()
    items = {item["source_row"]: item for item in payload["items"]}
    assert set(items) == EXPECTED_ROWS == set(EXPECTED)
    assert payload["source_sha256"] == "1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df"
    assert payload["reconciliation_sha256"] == "10f0e7cbe0fedd2666ee4dba730b991a080c7ce5e2322f8397f3253de32f02a4"
    assert all(value is False for value in payload["execution"].values())
    rate = Decimal("3.291243")
    for row, (name, clp, cop) in EXPECTED.items():
        item = items[row]
        assert (item["name"], item["source_price_clp"], item["fixed_price_cop"]) == (name, clp, cop)
        expected_cop = (Decimal(clp) * rate / 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 1000
        assert expected_cop == Decimal(cop)
        assert (item["planned_code"], item["default_performed_code"]) == ("PLAN_EXTRACTION", "DONE_EXTRACTION")
    assert json.loads(CATALOG_PATH.read_text())["items"] == payload["items"]
    assert items[267]["required_dentition"] == "PRIMARY"
    assert items[268]["required_dentition"] == "SUPERNUMERARY"


def test_extraction_seed_is_idempotent_country_specific_and_preserves_collision(db_session, security_world):
    for code, item_type in (("PLAN_EXTRACTION", "PLANNED_PROCEDURE"), ("DONE_EXTRACTION", "PERFORMED_PROCEDURE")):
        db_session.add(OdontogramCatalogItem(
            company_id=None, code=code, name=code, type=item_type, color="#2563eb",
            pattern="symbol", symbol="X", allowed_scopes=["TOOTH"], is_active=True,
        ))
    chile, colombia = security_world.tenant_a, security_world.tenant_b
    chile.company.country = "Chile"; colombia.company.country = "Colombia"
    existing = ProcedureCatalogItem(
        company_id=chile.company.id, name=EXPECTED[66][0],
        normalized_name=normalize_catalog_name(EXPECTED[66][0]),
        suggested_value=Decimal("777"), odontogram_behavior="NO_CHANGE", is_active=True,
    )
    db_session.add(existing); db_session.commit()
    assert preview_odontogram_extraction_catalog(db_session, chile.company).would_insert == 10
    cl = seed_odontogram_extraction_catalog(db_session, chile.company, chile.admin.user.id)
    co = seed_odontogram_extraction_catalog(db_session, colombia.company, colombia.admin.user.id)
    db_session.commit()
    assert (cl.inserted, cl.skipped_collisions) == (10, 1)
    assert (co.inserted, co.skipped_collisions) == (11, 0)
    db_session.refresh(existing)
    assert (existing.suggested_value, existing.odontogram_behavior) == (Decimal("777"), "NO_CHANGE")
    replay = seed_odontogram_extraction_catalog(db_session, colombia.company, colombia.admin.user.id)
    assert (replay.inserted, replay.skipped_collisions) == (0, 11)


def test_extraction_lifecycle_uses_red_plan_blue_result_and_preserves_history(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _install_symbols_and_seed(db_session, tenant)
    catalog = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "267",
    ))
    treatment = _new_treatment(api_client, tenant, "Exodoncia temporal sintética")
    created = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/with-diagnosis",
        token=tenant.dentist_admin.token,
        json={
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": str(catalog.suggested_value), "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "TOOTH", "tooth": "53", "dentition": "PRIMARY",
            "diagnosis_mode": "NONE", "idempotency_key": f"extraction-{uuid4().hex}",
        },
    )
    assert created.status_code == 201, created.text
    procedure = created.json()["procedure"]
    plan = db_session.get(OdontogramEvent, procedure["planned_odontogram_event_id"])
    plan_detail = db_session.scalar(select(OdontogramEventDetail).where(OdontogramEventDetail.event_id == plan.id))
    assert db_session.get(OdontogramCatalogItem, plan_detail.catalog_item_id).code == "PLAN_EXTRACTION"
    assert (plan_detail.tooth_code, plan_detail.dentition, plan_detail.layer) == ("53", "PRIMARY", "PLANNED")

    evolution = api_client.post(
        f"/api/patients/{tenant.patient.id}/clinical-evolutions",
        token=tenant.dentist_admin.token,
        json={"treatment_id": treatment["id"], "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id), "evolution_text": "Exodoncia realizada."},
    ).json()
    done = db_session.scalar(select(OdontogramCatalogItem).where(OdontogramCatalogItem.code == "DONE_EXTRACTION"))
    completed = api_client.post(
        f"/api/treatments/{treatment['id']}/procedures/{procedure['id']}/clinical-completion",
        token=tenant.dentist_admin.token,
        json={"clinical_evolution_id": evolution["id"], "odontogram_catalog_item_id": str(done.id), "idempotency_key": f"done-{uuid4().hex}", "scope_type": "TOOTH", "tooth": "53", "dentition": "PRIMARY"},
    )
    assert completed.status_code == 200, completed.text
    signed = api_client.post(
        f"/api/clinical-evolutions/{evolution['id']}/sign",
        token=tenant.dentist_admin.token,
        json={"version": evolution["version"], "confirm_complete": True},
    )
    assert signed.status_code == 200, signed.text
    db_session.refresh(plan)
    done_event = db_session.get(OdontogramEvent, completed.json()["odontogram_event_id"])
    db_session.refresh(done_event)
    assert (plan.status, done_event.status) == ("VOIDED_BY_COMPENSATING_EVENT", "CONFIRMED")
    assert db_session.scalar(select(func.count()).select_from(TreatmentProcedure).where(TreatmentProcedure.id == procedure["id"])) == 1


def test_extraction_catalog_enforces_authoritative_dentition_without_partial_writes(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _install_symbols_and_seed(db_session, tenant)
    treatment = _new_treatment(api_client, tenant, "Dentición autoritativa sintética")
    before_procedures = db_session.scalar(select(func.count()).select_from(TreatmentProcedure))
    before_events = db_session.scalar(select(func.count()).select_from(OdontogramEvent))
    for row, invalid, tooth in ((267, "PERMANENT", "53"), (268, "PERMANENT", "16")):
        catalog = db_session.scalar(select(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == tenant.company.id,
            ProcedureCatalogItem.price_provenance["source_row"].astext == str(row),
        ))
        response = api_client.post(f"/api/treatments/{treatment['id']}/procedures/with-diagnosis", token=tenant.dentist_admin.token, json={
            "catalog_procedure_id": str(catalog.id), "name": catalog.name,
            "unit_value": str(catalog.suggested_value), "quantity": "1",
            "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
            "scope_type": "TOOTH", "tooth": tooth, "dentition": invalid,
            "diagnosis_mode": "NONE", "idempotency_key": f"invalid-dentition-{uuid4().hex}",
        })
        assert response.status_code == 422, response.text
        assert db_session.scalar(select(func.count()).select_from(TreatmentProcedure)) == before_procedures
        assert db_session.scalar(select(func.count()).select_from(OdontogramEvent)) == before_events

    supernumerary = db_session.scalar(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.price_provenance["source_row"].astext == "268",
    ))
    valid = api_client.post(f"/api/treatments/{treatment['id']}/procedures/with-diagnosis", token=tenant.dentist_admin.token, json={
        "catalog_procedure_id": str(supernumerary.id), "name": supernumerary.name,
        "unit_value": str(supernumerary.suggested_value), "quantity": "1",
        "site_id": str(tenant.site_1.id), "dentist_id": str(tenant.dentist_profile.id),
        "scope_type": "TOOTH", "tooth": "16", "dentition": "SUPERNUMERARY",
        "diagnosis_mode": "NONE", "idempotency_key": f"valid-supernumerary-{uuid4().hex}",
    })
    assert valid.status_code == 201, valid.text
