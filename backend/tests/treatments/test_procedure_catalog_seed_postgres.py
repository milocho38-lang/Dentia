from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
import sys
from uuid import uuid4

import fitz
import pytest
from sqlalchemy import func, select

from app.cli.seed_procedure_catalog import main as catalog_cli_main
from app.models.company import Company
from app.models.audit_event import AuditEvent
from app.core.config import settings
from app.models.odontogram import OdontogramEvent
from app.models.treatment import ProcedureCatalogItem
from app.services.bootstrap_service import BootstrapInput, bootstrap_installation
from app.services.procedure_catalog_seed_service import CatalogConversion, seed_initial_procedure_catalog
from tests.conftest import TestingSessionLocal


def test_real_bootstrap_with_missing_country_skips_only_catalog_and_cli_refuses_inference(
    db_session, monkeypatch
):
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
    try:
        result = bootstrap_installation(
            db_session,
            BootstrapInput(
                company_name="Bootstrap sin país", company_slug=f"bootstrap-{uuid4().hex}",
                site_name="Sede Principal", admin_name="Admin Bootstrap",
                admin_username=f"admin.{uuid4().hex[:10]}",
                admin_email=f"bootstrap-{uuid4().hex[:10]}@example.test",
                admin_password="BootstrapPassword!2026",
            ),
        )
        db_session.commit()
    finally:
        settings.procedure_catalog_seed_enabled = previous
    company = db_session.get(Company, result.company_id)
    assert company.country is None
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company.id)) == 0
    skipped = db_session.scalar(select(AuditEvent).where(
        AuditEvent.company_id == company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_SEED_SKIPPED",
    ))
    assert skipped is not None
    assert skipped.detail["reason"] == "UNSUPPORTED_OR_MISSING_COUNTRY"

    argv = ["seed_procedure_catalog", "--company-id", str(company.id),
            "--actor-id", result.admin_user_id, "--dry-run"]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit, match="no se infiere moneda"):
        catalog_cli_main()

    company.country = "Perú"
    db_session.commit()
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit, match="no se infiere moneda"):
        catalog_cli_main()


def test_real_postgres_backfill_is_concurrent_idempotent_and_preserves_existing(db_session):
    company = Company(name="Catálogo existente", slug=f"catalog-{uuid4().hex}", country="Chile")
    db_session.add(company)
    db_session.flush()
    existing = ProcedureCatalogItem(
        company_id=company.id,
        name="Aplicación Flúor Gel total niños y adultos",
        normalized_name="aplicación flúor gel total niños y adultos",
        suggested_value=Decimal("777"),
        price_currency="CLP",
        odontogram_behavior="NO_CHANGE",
    )
    db_session.add(existing)
    db_session.commit()
    company_id = company.id
    existing_id = existing.id

    def seed():
        with TestingSessionLocal() as session:
            target = session.get(Company, company_id)
            result = seed_initial_procedure_catalog(session, target, None, CatalogConversion())
            session.commit()
            return result.inserted, result.skipped_collisions

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = sorted(executor.map(lambda _: seed(), range(2)))
    assert results == [(0, 173), (172, 1)]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company_id)) == 173
    preserved = db_session.get(ProcedureCatalogItem, existing_id)
    assert preserved.suggested_value == Decimal("777")


def test_new_chile_company_onboarding_receives_catalog(api_client, db_session, security_world):
    previous = (settings.procedure_catalog_seed_enabled, settings.procedure_catalog_clp_to_cop_rate)
    settings.procedure_catalog_seed_enabled = True
    settings.procedure_catalog_clp_to_cop_rate = "TASA-COP-INVALIDA-IGNORADA-POR-CHILE"
    unique = uuid4().hex[:10]
    try:
        response = api_client.post(
            "/api/platform/companies",
            token=security_world.platform_admin.token,
            json={
                "company_name": f"Clínica onboarding {unique}",
                "company_type": "Clínica",
                "address": "Calle de prueba 123",
                "city": "Santiago",
                "country": "Chile",
                "timezone": "America/Santiago",
                "admin_name": "Administrador Prueba",
                "admin_username": f"admin{unique}",
                "admin_email": f"admin-{unique}@example.test",
                "admin_password": "Temporal-12345!",
            },
        )
    finally:
        settings.procedure_catalog_seed_enabled, settings.procedure_catalog_clp_to_cop_rate = previous
    assert response.status_code == 201, response.text
    company_id = response.json()["company"]["id"]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company_id)) == 173


def test_colombia_onboarding_rejects_malformed_cop_rate_clearly(api_client, security_world):
    previous = (settings.procedure_catalog_seed_enabled, settings.procedure_catalog_clp_to_cop_rate)
    settings.procedure_catalog_seed_enabled = True
    settings.procedure_catalog_clp_to_cop_rate = "NO-ES-DECIMAL"
    unique = uuid4().hex[:10]
    try:
        response = api_client.post(
            "/api/platform/companies", token=security_world.platform_admin.token,
            json={"company_name": f"Clínica CO inválida {unique}", "company_type": "Clínica",
                  "address": "Calle de prueba 789", "city": "Bogotá", "country": "Colombia",
                  "timezone": "America/Bogota", "admin_name": "Admin Colombia Inválida",
                  "admin_username": f"bad{unique}", "admin_email": f"bad-{unique}@example.test",
                  "admin_password": "Temporal-12345!"},
        )
    finally:
        settings.procedure_catalog_seed_enabled, settings.procedure_catalog_clp_to_cop_rate = previous
    assert response.status_code == 422, response.text
    assert "tasa CLP/COP configurada no es decimal válida" in response.text


def test_new_colombia_company_onboarding_converts_once_and_existing_backfill_preserves(api_client, db_session, security_world):
    previous = (
        settings.procedure_catalog_seed_enabled,
        settings.procedure_catalog_clp_to_cop_rate,
        settings.procedure_catalog_rate_source,
        settings.procedure_catalog_rate_observed_at_utc,
        settings.procedure_catalog_rate_is_reference,
    )
    observed = datetime.now(timezone.utc).isoformat()
    settings.procedure_catalog_seed_enabled = True
    settings.procedure_catalog_clp_to_cop_rate = "3.2"
    settings.procedure_catalog_rate_source = "TEST-CURRENT-RATE"
    settings.procedure_catalog_rate_observed_at_utc = observed
    settings.procedure_catalog_rate_is_reference = False
    unique = uuid4().hex[:10]
    try:
        response = api_client.post(
            "/api/platform/companies", token=security_world.platform_admin.token,
            json={"company_name": f"Clínica CO {unique}", "company_type": "Clínica",
                  "address": "Calle de prueba 456", "city": "Bogotá", "country": "Colombia",
                  "timezone": "America/Bogota", "admin_name": "Administrador Colombia",
                  "admin_username": f"co{unique}", "admin_email": f"co-{unique}@example.test",
                  "admin_password": "Temporal-12345!"},
        )
    finally:
        (settings.procedure_catalog_seed_enabled,
         settings.procedure_catalog_clp_to_cop_rate,
         settings.procedure_catalog_rate_source,
         settings.procedure_catalog_rate_observed_at_utc,
         settings.procedure_catalog_rate_is_reference) = previous
    assert response.status_code == 201, response.text
    company_id = response.json()["company"]["id"]
    rows = db_session.scalars(select(ProcedureCatalogItem).where(ProcedureCatalogItem.company_id == company_id)).all()
    assert len(rows) == 173
    assert all(row.price_currency == "COP" and row.suggested_value % 1000 == 0 for row in rows)
    preserved = rows[0]
    preserved.suggested_value = Decimal("999")
    db_session.commit()
    result = seed_initial_procedure_catalog(
        db_session, db_session.get(Company, company_id), None,
        CatalogConversion(Decimal("3.2"), "TEST-CURRENT-RATE", observed),
    )
    db_session.commit()
    assert result.inserted == 0 and result.skipped_collisions == 173
    db_session.refresh(preserved)
    assert preserved.suggested_value == Decimal("999")


def test_country_changes_only_labels_and_never_changes_financial_sums(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    tenant.company.country = "Colombia"
    db_session.commit()
    before = api_client.get("/api/finance/dashboard", token=tenant.admin.token)
    assert before.status_code == 200, before.text
    before_payload = before.json()
    assert before_payload["currency_code"] == "COP"
    catalog = api_client.post("/api/procedure-catalog", token=tenant.admin.token, json={
        "name": "Etiqueta por país", "suggested_value": "12345",
        "suggested_scope_type": "GENERAL", "odontogram_behavior": "NO_CHANGE",
    })
    assert catalog.status_code == 201, catalog.text
    assert catalog.json()["price_currency"] == "COP"

    budget_before = api_client.get(f"/api/budgets/{tenant.budget.id}", token=tenant.admin.token)
    payment_before = api_client.get(f"/api/payments/{tenant.payment.id}", token=tenant.admin.token)
    assert budget_before.json()["currency_code"] == "COP"
    assert payment_before.json()["currency_code"] == "COP"

    tenant.company.country = "Chile"
    db_session.commit()
    after = api_client.get("/api/finance/dashboard", token=tenant.admin.token)
    assert after.status_code == 200, after.text
    after_payload = after.json()
    assert after_payload["currency_code"] == "CLP"
    catalog_after = api_client.get("/api/procedure-catalog", token=tenant.admin.token)
    changed_item = next(item for item in catalog_after.json()["items"] if item["id"] == catalog.json()["id"])
    assert changed_item["price_currency"] == "CLP"
    for field in ("income_today", "income_month", "income_year", "receivables_total", "average_ticket"):
        assert after_payload[field] == before_payload[field]
    assert api_client.get(f"/api/budgets/{tenant.budget.id}", token=tenant.admin.token).json()["currency_code"] == "CLP"
    assert api_client.get(f"/api/payments/{tenant.payment.id}", token=tenant.admin.token).json()["currency_code"] == "CLP"

    tenant.company.country = "Perú"
    db_session.commit()
    local = api_client.get("/api/finance/dashboard", token=tenant.admin.token)
    assert local.status_code == 200
    assert local.json()["currency_code"] is None
    for field in ("income_today", "income_month", "income_year", "receivables_total", "average_ticket"):
        assert local.json()[field] == before_payload[field]


def test_budget_and_payment_pdfs_use_company_country_label(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    tenant.company.country = "Chile"
    db_session.commit()
    budget_pdf = api_client.get(f"/api/budgets/{tenant.budget.id}/pdf", token=tenant.admin.token)
    receipt_pdf = api_client.get(f"/api/payments/{tenant.payment.id}/receipt", token=tenant.admin.token)
    assert budget_pdf.status_code == 200, budget_pdf.text
    assert receipt_pdf.status_code == 200, receipt_pdf.text
    for payload in (budget_pdf.content, receipt_pdf.content):
        document = fitz.open(stream=payload, filetype="pdf")
        text = "\n".join(page.get_text() for page in document)
        document.close()
        assert "CLP" in text


def test_procedure_create_list_and_update_return_country_label(api_client, db_session, security_world):
    tenant = security_world.tenant_b
    tenant.company.country = "Chile"
    db_session.commit()
    treatment = api_client.post(
        "/api/treatments", token=tenant.admin.token,
        json={"patient_id": str(tenant.patient.id), "name": "Tratamiento API editable"},
    )
    assert treatment.status_code == 201, treatment.text
    treatment_id = treatment.json()["id"]
    created = api_client.post(
        f"/api/treatments/{treatment_id}/procedures",
        token=tenant.admin.token,
        json={"name": "Procedimiento API real", "unit_value": "1234", "quantity": "2", "scope_type": "GENERAL"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["currency_code"] == "CLP"
    assert created.json()["total_value"] == "2468.00"
    procedure_id = created.json()["id"]

    listed = api_client.get(
        f"/api/treatments/{treatment_id}/procedures", token=tenant.admin.token,
    )
    assert listed.status_code == 200, listed.text
    listed_item = next(item for item in listed.json() if item["id"] == procedure_id)
    assert listed_item["currency_code"] == "CLP"

    updated = api_client.patch(
        f"/api/treatments/{treatment_id}/procedures/{procedure_id}",
        token=tenant.admin.token,
        json={"name": "Procedimiento API editado", "unit_value": "2000"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Procedimiento API editado"
    assert updated.json()["currency_code"] == "CLP"
    assert updated.json()["total_value"] == "4000.00"


def test_seeded_no_change_procedure_creates_no_odontogram_event(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    tenant.company.country = "Chile"
    seeded = seed_initial_procedure_catalog(
        db_session, tenant.company, tenant.admin.user.id, CatalogConversion()
    )
    db_session.commit()
    assert seeded.inserted == 173
    catalog_item = db_session.scalar(
        select(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == tenant.company.id,
            ProcedureCatalogItem.odontogram_behavior == "NO_CHANGE",
        )
    )
    assert catalog_item is not None

    treatment = api_client.post(
        "/api/treatments", token=tenant.admin.token,
        json={"patient_id": str(tenant.patient.id), "name": "NO_CHANGE sin odontograma"},
    )
    assert treatment.status_code == 201, treatment.text
    event_count_before = db_session.scalar(
        select(func.count()).select_from(OdontogramEvent).where(
            OdontogramEvent.company_id == tenant.company.id,
            OdontogramEvent.patient_id == tenant.patient.id,
        )
    )
    created = api_client.post(
        f"/api/treatments/{treatment.json()['id']}/procedures/with-diagnosis",
        token=tenant.admin.token,
        json={
            "catalog_procedure_id": str(catalog_item.id),
            "name": catalog_item.name,
            "unit_value": str(catalog_item.suggested_value),
            "quantity": "1",
            "scope_type": catalog_item.suggested_scope_type,
            "idempotency_key": f"no-change-{uuid4().hex}",
            "diagnosis_mode": "CREATE_NEW",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["diagnosis_event_id"] is None
    assert created.json()["diagnosis_created"] is False
    event_count_after = db_session.scalar(
        select(func.count()).select_from(OdontogramEvent).where(
            OdontogramEvent.company_id == tenant.company.id,
            OdontogramEvent.patient_id == tenant.patient.id,
        )
    )
    assert event_count_after == event_count_before


def test_reports_keep_tenant_isolation_and_add_only_presentation_currency(api_client, db_session, security_world):
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    tenant_a.company.country = "Colombia"
    tenant_b.company.country = "Chile"
    db_session.commit()
    report_a = api_client.get("/api/reports/finance", token=tenant_a.admin.token)
    report_b = api_client.get("/api/reports/finance", token=tenant_b.admin.token)
    assert report_a.status_code == report_b.status_code == 200
    assert report_a.json()["currency_code"] == "COP"
    assert report_b.json()["currency_code"] == "CLP"
    assert str(tenant_b.payment.id) not in report_a.text
    assert str(tenant_a.payment.id) not in report_b.text
