from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
import sys
from uuid import uuid4

import fitz
import pytest
from sqlalchemy import func, select

from app.cli.seed_procedure_catalog import main as catalog_cli_main
from app.cli import bootstrap as bootstrap_cli
from app.models.company import Company
from app.models.audit_event import AuditEvent
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.core.config import settings
from app.models.odontogram import OdontogramEvent
from app.models.treatment import ProcedureCatalogItem
from app.services.bootstrap_service import BootstrapInput, bootstrap_installation
from app.services.procedure_catalog_seed_service import seed_initial_procedure_catalog
from app.services import procedure_catalog_seed_service as catalog_service
from tests.conftest import TestingSessionLocal


def _bootstrap_cli_argv(unique: str, *country_args: str) -> list[str]:
    return [
        "bootstrap", "--company-name", f"CLI {unique}",
        "--company-slug", f"cli-{unique}", *country_args,
        "--site-name", "Sede Principal", "--admin-name", "Admin CLI",
        "--admin-username", f"admin.{unique}",
        "--admin-email", f"admin-{unique}@example.test",
    ]


def _run_bootstrap_cli(monkeypatch, argv: list[str]) -> int:
    passwords = iter(["BootstrapPassword!2026", "BootstrapPassword!2026"])
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(bootstrap_cli.getpass, "getpass", lambda _prompt: next(passwords))
    return bootstrap_cli.main()


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


@pytest.mark.parametrize(("country", "currency"), [("Chile", "CLP"), ("Colombia", "COP")])
def test_real_bootstrap_chile_and_colombia_receive_fixed_catalog_without_rate_config(
    db_session, country, currency
):
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
    try:
        result = bootstrap_installation(
            db_session,
            BootstrapInput(
                company_name=f"Bootstrap {country}",
                company_slug=f"bootstrap-{country.casefold()}-{uuid4().hex}",
                site_name="Sede Principal", admin_name="Admin Bootstrap",
                admin_username=f"admin.{uuid4().hex[:10]}",
                admin_email=f"bootstrap-{uuid4().hex[:10]}@example.test",
                admin_password="BootstrapPassword!2026",
                company_country=country,
            ),
        )
        db_session.commit()
    finally:
        settings.procedure_catalog_seed_enabled = previous

    company = db_session.get(Company, result.company_id)
    rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company.id
    )).all()
    assert company.country == country
    assert len(rows) == 173
    assert all(row.price_currency == currency for row in rows)
    assert all(row.price_provenance["catalog_version"].endswith("173-V2") for row in rows)
    assert all(
        row.price_provenance["approved_payload_sha256"] == catalog_service.APPROVED_PAYLOAD_SHA256
        for row in rows
    )


def test_real_bootstrap_cli_interactive_prompts_country_and_seeds_chile(
    db_session, monkeypatch
):
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
    unique = uuid4().hex[:10]
    monkeypatch.setattr(bootstrap_cli.sys, "stdin", type("InteractiveInput", (), {"isatty": lambda self: True})())
    monkeypatch.setattr("builtins.input", lambda _prompt: "Chile")
    try:
        status = _run_bootstrap_cli(monkeypatch, _bootstrap_cli_argv(unique))
    finally:
        settings.procedure_catalog_seed_enabled = previous
    assert status == 0
    company = db_session.scalar(select(Company).where(Company.slug == f"cli-{unique}"))
    assert company.country == "Chile"
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company.id,
        ProcedureCatalogItem.price_currency == "CLP",
    )) == 173


def test_real_bootstrap_cli_noninteractive_colombia_seeds_without_prompt(db_session, monkeypatch):
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
    unique = uuid4().hex[:10]
    monkeypatch.setattr(bootstrap_cli.sys, "stdin", type("NonInteractiveInput", (), {"isatty": lambda self: False})())
    try:
        status = _run_bootstrap_cli(
            monkeypatch, _bootstrap_cli_argv(unique, "--company-country", "Colombia")
        )
    finally:
        settings.procedure_catalog_seed_enabled = previous
    assert status == 0
    company = db_session.scalar(select(Company).where(Company.slug == f"cli-{unique}"))
    assert company.country == "Colombia"
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company.id,
        ProcedureCatalogItem.price_currency == "COP",
    )) == 173


@pytest.mark.parametrize("country_args", [(), ("--without-company-country",),
                                           ("--company-country", "Perú")])
def test_real_bootstrap_cli_missing_or_unsupported_country_installs_and_skips_catalog(
    db_session, monkeypatch, capsys, country_args
):
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
    unique = uuid4().hex[:10]
    monkeypatch.setattr(bootstrap_cli.sys, "stdin", type("NonInteractiveInput", (), {"isatty": lambda self: False})())
    try:
        status = _run_bootstrap_cli(monkeypatch, _bootstrap_cli_argv(unique, *country_args))
    finally:
        settings.procedure_catalog_seed_enabled = previous
    assert status == 0
    company = db_session.scalar(select(Company).where(Company.slug == f"cli-{unique}"))
    assert company is not None
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company.id
    )) == 0
    skipped = db_session.scalar(select(AuditEvent).where(
        AuditEvent.company_id == company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_SEED_SKIPPED",
    ))
    assert skipped is not None
    if not country_args:
        assert "País no indicado en ejecución no interactiva" in capsys.readouterr().err


def test_real_bootstrap_cli_invalid_manifest_fails_safely(db_session, monkeypatch, tmp_path):
    payload = json.loads(catalog_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload["catalog_version"] = "INVALID-CLI"
    invalid = tmp_path / "invalid-cli-catalog.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(catalog_service, "CATALOG_PATH", invalid)
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
    unique = uuid4().hex[:10]
    try:
        with pytest.raises(catalog_service.ProcedureCatalogSeedError, match="manifiesto aprobado"):
            _run_bootstrap_cli(
                monkeypatch, _bootstrap_cli_argv(unique, "--company-country", "Colombia")
            )
    finally:
        settings.procedure_catalog_seed_enabled = previous
    assert db_session.scalar(select(func.count()).select_from(Company)) == 0
    assert db_session.scalar(select(func.count()).select_from(User)) == 0


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
            result = seed_initial_procedure_catalog(session, target, None)
            session.commit()
            return result.inserted, result.skipped_collisions

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = sorted(executor.map(lambda _: seed(), range(2)))
    assert results == [(0, 173), (172, 1)]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company_id)) == 173
    preserved = db_session.get(ProcedureCatalogItem, existing_id)
    assert preserved.suggested_value == Decimal("777")


def test_invalid_manifest_rolls_back_without_partial_rows_or_audit(db_session, tmp_path, monkeypatch):
    company = Company(name="Catálogo inválido", slug=f"invalid-{uuid4().hex}", country="Colombia")
    db_session.add(company)
    db_session.commit()
    payload = json.loads(catalog_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload["items"][86]["suggested_price_cop"] = "123000"
    invalid = tmp_path / "invalid-catalog.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(catalog_service, "CATALOG_PATH", invalid)

    with pytest.raises(catalog_service.ProcedureCatalogSeedError, match="manifiesto aprobado"):
        seed_initial_procedure_catalog(db_session, company, None)
    db_session.rollback()

    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company.id
    )) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.company_id == company.id,
        AuditEvent.entity == "procedure_catalog_seed",
    )) == 0


def test_platform_onboarding_invalid_manifest_rolls_back_entire_company(
    api_client, db_session, security_world, tmp_path, monkeypatch
):
    payload = json.loads(catalog_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload["items"][0]["name"] = "Lote manipulado"
    invalid = tmp_path / "invalid-platform-catalog.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(catalog_service, "CATALOG_PATH", invalid)
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
    unique = uuid4().hex[:10]
    company_name = f"Clínica inválida {unique}"
    try:
        response = api_client.post(
            "/api/platform/companies", token=security_world.platform_admin.token,
            json={"company_name": company_name, "company_type": "Clínica",
                  "address": "Calle de prueba", "city": "Bogotá", "country": "Colombia",
                  "timezone": "America/Bogota", "admin_name": "Admin Inválido",
                  "admin_username": f"invalid{unique}",
                  "admin_email": f"invalid-{unique}@example.test",
                  "admin_password": "Temporal-12345!"},
        )
    finally:
        settings.procedure_catalog_seed_enabled = previous
    assert response.status_code == 422, response.text
    assert "manifiesto aprobado" in response.text
    assert db_session.scalar(select(func.count()).select_from(Company).where(Company.name == company_name)) == 0


def test_bootstrap_invalid_manifest_rolls_back_entire_installation(db_session, tmp_path, monkeypatch):
    payload = json.loads(catalog_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload["source_sha256"] = "f" * 64
    invalid = tmp_path / "invalid-bootstrap-catalog.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(catalog_service, "CATALOG_PATH", invalid)
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
    try:
        with pytest.raises(catalog_service.ProcedureCatalogSeedError, match="manifiesto aprobado"):
            bootstrap_installation(
                db_session,
                BootstrapInput(
                    company_name="Bootstrap inválido", company_slug=f"invalid-{uuid4().hex}",
                    site_name="Sede Principal", admin_name="Admin Inválido",
                    admin_username=f"invalid.{uuid4().hex[:10]}",
                    admin_email=f"invalid-{uuid4().hex[:10]}@example.test",
                    admin_password="BootstrapPassword!2026", company_country="Colombia",
                ),
            )
        db_session.rollback()
    finally:
        settings.procedure_catalog_seed_enabled = previous

    assert db_session.scalar(select(func.count()).select_from(Company)) == 0
    assert db_session.scalar(select(func.count()).select_from(User)) == 0
    assert db_session.scalar(select(func.count()).select_from(Role)) == 0
    assert db_session.scalar(select(func.count()).select_from(Permission)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent)) == 0


def test_new_chile_company_onboarding_receives_catalog_without_rate_config(api_client, db_session, security_world):
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
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
        settings.procedure_catalog_seed_enabled = previous
    assert response.status_code == 201, response.text
    company_id = response.json()["company"]["id"]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company_id)) == 173


def test_colombia_onboarding_succeeds_without_rate_config(api_client, db_session, security_world):
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
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
        settings.procedure_catalog_seed_enabled = previous
    assert response.status_code == 201, response.text
    company_id = response.json()["company"]["id"]
    rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company_id
    )).all()
    assert len(rows) == 173
    assert all(row.price_currency == "COP" and row.suggested_value % 1000 == 0 for row in rows)


def test_new_colombia_company_onboarding_uses_fixed_prices_and_existing_backfill_preserves(
    api_client, db_session, security_world, monkeypatch, capsys
):
    previous = settings.procedure_catalog_seed_enabled
    settings.procedure_catalog_seed_enabled = True
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
        settings.procedure_catalog_seed_enabled = previous
    assert response.status_code == 201, response.text
    company_id = response.json()["company"]["id"]
    rows = db_session.scalars(select(ProcedureCatalogItem).where(ProcedureCatalogItem.company_id == company_id)).all()
    assert len(rows) == 173
    assert all(row.price_currency == "COP" and row.suggested_value % 1000 == 0 for row in rows)
    preserved = rows[0]
    preserved.suggested_value = Decimal("999")
    db_session.commit()
    result = seed_initial_procedure_catalog(db_session, db_session.get(Company, company_id), None)
    db_session.commit()
    assert result.inserted == 0 and result.skipped_collisions == 173
    db_session.refresh(preserved)
    assert preserved.suggested_value == Decimal("999")

    monkeypatch.setattr(sys, "argv", [
        "seed_procedure_catalog", "--company-id", str(company_id),
        "--actor-id", str(rows[0].created_by), "--dry-run",
    ])
    catalog_cli_main()
    output = capsys.readouterr().out
    assert "insertados=0 colisiones=173 moneda=COP" in output
    assert "dry-run: transacción revertida" in output


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
        db_session, tenant.company, tenant.admin.user.id
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
