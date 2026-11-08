from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
import sys
from threading import Event
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.models.audit_event import AuditEvent
from app.models.associations import RolePermission, UserRole
from app.models.company import Company
from app.models.odontogram import OdontogramCatalogItem
from app.models.permission import Permission
from app.models.site import Site
from app.models.treatment import ProcedureCatalogDiagnosis, ProcedureCatalogItem
from app.models.user import User
from app.core.config import settings
from app.cli.seed_odontogram_resin_catalog import main as resin_catalog_cli_main
from app.services.bootstrap_service import BootstrapInput, bootstrap_installation
from app.services.procedure_catalog_odontogram_seed_service import preview_odontogram_resin_catalog, seed_odontogram_resin_catalog
from app.services import procedure_catalog_odontogram_seed_service as resin_service
from app.services import treatment_service
from app.services.procedure_catalog_seed_service import normalize_catalog_name
from tests.conftest import TestingSessionLocal


EXPECTED_NAMES = {
    290: "Restauración fotocurado pieza temporal: Compuesta Anterior o posterior",
    291: "Restauración fotocurado pieza temporal: Simple Anterior o posterior",
    329: "Restauración Cervical (Clase V)",
    330: "Restauración composite Compleja Posterior (Clase II - tres caras)",
    331: "Restauración composite Compuesta Anterior (Clase IV)",
    332: "Restauración composite Compuesta Posterior (Clase II - dos caras)",
    333: "Restauración composite Simple Anterior (Clase III o V)",
    334: "Restauración composite Simple Posterior (Clase I - una cara)",
}


def _clinical_items(session):
    definitions = []
    codes = {
        "FIND_CARIES", "FIND_FRACTURE", "FIND_ENDO_DEFECTIVE",
        "PLAN_CROWN", "DONE_CROWN", "PLAN_IMPLANT", "DONE_IMPLANT",
        "PLAN_ENDO", "DONE_ENDO", "PLAN_POST", "DONE_POST",
        "DONE_PULPOTOMY", "PLAN_EXTRACTION", "DONE_EXTRACTION",
        "PLAN_VENEER", "DONE_VENEER", "PLAN_RESIN", "DONE_RESIN",
    }
    for code in sorted(codes):
        item_type = (
            "FINDING" if code.startswith("FIND_")
            else "PLANNED_PROCEDURE" if code.startswith("PLAN_")
            else "PERFORMED_PROCEDURE"
        )
        color = "#dc2626" if code.startswith("FIND_") else "#2563eb"
        definitions.append((code, code, item_type, color))
    for code, name, item_type, color in definitions:
        session.add(OdontogramCatalogItem(
            company_id=None, code=code, name=name, type=item_type, color=color,
            pattern="solid", symbol=code, allowed_scopes=["TOOTH", "TOOTH_SURFACE"],
            allowed_surfaces=["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"],
            is_active=True,
        ))
    session.commit()


@pytest.mark.parametrize(("country", "currency", "row_290_value"), [
    ("Chile", "CLP", Decimal("66000")), ("Colombia", "COP", Decimal("217000")),
])
def test_literal_eight_rows_fixed_prices_and_collisions_are_preserved(db_session, security_world, country, currency, row_290_value):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = country
    db_session.commit()
    result = seed_odontogram_resin_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    assert (result.inserted, result.skipped_collisions, result.diagnosis_links) == (8, 0, 16)
    rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.odontogram_behavior == "REQUIRES_DIAGNOSIS",
    )).all()
    assert {row.price_provenance["source_row"]: row.name for row in rows} == EXPECTED_NAMES
    assert all(row.price_currency == currency and row.suggested_scope_type == "TOOTH_SURFACE" for row in rows)
    target = next(row for row in rows if row.price_provenance["source_row"] == 290)
    assert target.suggested_value == row_290_value
    target.suggested_value = Decimal("777")
    db_session.commit()
    replay = seed_odontogram_resin_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    assert (replay.inserted, replay.skipped_collisions, replay.diagnosis_links) == (0, 8, 0)
    db_session.refresh(target)
    assert target.suggested_value == Decimal("777")


def test_concurrent_seed_creates_one_atomic_set(db_session, security_world):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    company_id, actor_id = tenant.company.id, tenant.admin.user.id
    db_session.commit()

    def run_once(_):
        with TestingSessionLocal() as session:
            result = seed_odontogram_resin_catalog(session, session.get(Company, company_id), actor_id)
            session.commit()
            return result.inserted, result.skipped_collisions

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run_once, range(2)))
    assert sorted(results) == [(0, 8), (8, 0)]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company_id,
        ProcedureCatalogItem.odontogram_behavior == "REQUIRES_DIAGNOSIS",
    )) == 8
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogDiagnosis).where(
        ProcedureCatalogDiagnosis.company_id == company_id,
    )) == 16


def test_preexisting_collision_is_untouched_and_receives_no_clinical_links(db_session, security_world):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    existing = ProcedureCatalogItem(
        company_id=tenant.company.id, name=EXPECTED_NAMES[290],
        normalized_name=normalize_catalog_name(EXPECTED_NAMES[290]),
        suggested_value=Decimal("999"), suggested_scope_type="GENERAL",
        odontogram_behavior="NO_CHANGE", is_active=True, created_by=tenant.admin.user.id,
    )
    db_session.add(existing)
    db_session.commit()
    before_count = db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
    ))
    audit_count_before = db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    ))
    preview = preview_odontogram_resin_catalog(db_session, tenant.company)
    assert preview.would_insert == 7
    assert len(preview.collisions) == 1
    assert preview.collisions[0]["existing_id"] == str(existing.id)
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
    )) == before_count
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    )) == audit_count_before
    result = seed_odontogram_resin_catalog(db_session, tenant.company, tenant.admin.user.id)
    db_session.commit()
    assert (result.inserted, result.skipped_collisions, result.diagnosis_links) == (7, 1, 14)
    db_session.refresh(existing)
    assert existing.suggested_value == Decimal("999")
    assert existing.suggested_scope_type == "GENERAL" and existing.odontogram_behavior == "NO_CHANGE"
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogDiagnosis).where(
        ProcedureCatalogDiagnosis.procedure_catalog_id == existing.id,
    )) == 0


def test_seed_is_isolated_between_two_companies(db_session, security_world):
    _clinical_items(db_session)
    tenant_a, tenant_b = security_world.tenant_a, security_world.tenant_b
    tenant_a.company.country, tenant_b.company.country = "Colombia", "Chile"
    db_session.commit()
    result_a = seed_odontogram_resin_catalog(db_session, tenant_a.company, tenant_a.admin.user.id)
    result_b = seed_odontogram_resin_catalog(db_session, tenant_b.company, tenant_b.admin.user.id)
    db_session.commit()
    assert result_a.inserted == result_b.inserted == 8
    rows_a = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant_a.company.id,
        ProcedureCatalogItem.odontogram_behavior == "REQUIRES_DIAGNOSIS",
    )).all()
    rows_b = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant_b.company.id,
        ProcedureCatalogItem.odontogram_behavior == "REQUIRES_DIAGNOSIS",
    )).all()
    assert len(rows_a) == len(rows_b) == 8
    assert all(row.price_currency == "COP" for row in rows_a)
    assert all(row.price_currency == "CLP" for row in rows_b)
    assert {row.id for row in rows_a}.isdisjoint({row.id for row in rows_b})
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogDiagnosis).where(
        ProcedureCatalogDiagnosis.company_id == tenant_a.company.id,
    )) == 16
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogDiagnosis).where(
        ProcedureCatalogDiagnosis.company_id == tenant_b.company.id,
    )) == 16


@pytest.mark.parametrize(("country", "currency", "expected_value"), [
    ("Chile", "CLP", Decimal("66000")),
    ("Colombia", "COP", Decimal("217000")),
])
def test_enabled_bootstrap_adds_second_batch_by_country(
    db_session, country, currency, expected_value
):
    _clinical_items(db_session)
    previous = settings.procedure_catalog_odontogram_resin_seed_enabled
    settings.procedure_catalog_odontogram_resin_seed_enabled = True
    try:
        result = bootstrap_installation(db_session, BootstrapInput(
            company_name=f"Resinas {country}", company_slug=f"resinas-{uuid4().hex}",
            site_name="Sede Principal", admin_name="Admin Resinas",
            admin_username=f"resinas.{uuid4().hex[:10]}",
            admin_email=f"resinas-{uuid4().hex[:10]}@example.test",
            admin_password="BootstrapPassword!2026", company_country=country,
        ))
    finally:
        settings.procedure_catalog_odontogram_resin_seed_enabled = previous
    rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == result.company_id,
    )).all()
    assert len(rows) == 83
    assert all(row.price_currency == currency for row in rows)
    assert next(row for row in rows if row.price_provenance["source_row"] == 290).suggested_value == expected_value


def test_enabled_bootstrap_invalid_second_batch_rolls_back_everything(
    db_session, tmp_path, monkeypatch
):
    _clinical_items(db_session)
    payload = json.loads(resin_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload["items"][0]["name"] = "Nombre manipulado"
    invalid = tmp_path / "invalid-resin-batch.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(resin_service, "CATALOG_PATH", invalid)
    previous = settings.procedure_catalog_odontogram_resin_seed_enabled
    settings.procedure_catalog_odontogram_resin_seed_enabled = True
    try:
        with pytest.raises(Exception, match="manifiesto revisado"):
            bootstrap_installation(db_session, BootstrapInput(
                company_name="Resinas inválidas", company_slug=f"invalid-resin-{uuid4().hex}",
                site_name="Sede Principal", admin_name="Admin Inválido",
                admin_username=f"invalid.resin.{uuid4().hex[:8]}",
                admin_email=f"invalid-resin-{uuid4().hex[:8]}@example.test",
                admin_password="BootstrapPassword!2026", company_country="Chile",
            ))
        db_session.rollback()
    finally:
        settings.procedure_catalog_odontogram_resin_seed_enabled = previous
    assert db_session.scalar(select(func.count()).select_from(Company)) == 0
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent)) == 0


@pytest.mark.parametrize(("country", "currency"), [("Chile", "CLP"), ("Colombia", "COP")])
def test_enabled_platform_onboarding_adds_second_batch(
    api_client, db_session, security_world, country, currency
):
    _clinical_items(db_session)
    previous = settings.procedure_catalog_odontogram_resin_seed_enabled
    settings.procedure_catalog_odontogram_resin_seed_enabled = True
    unique = uuid4().hex[:10]
    try:
        response = api_client.post(
            "/api/platform/companies", token=security_world.platform_admin.token,
            json={
                "company_name": f"Resinas plataforma {unique}", "company_type": "Clínica",
                "address": "Calle sintética", "city": "Ciudad sintética", "country": country,
                "timezone": "America/Santiago" if country == "Chile" else "America/Bogota",
                "admin_name": "Admin Resinas", "admin_username": f"resinas{unique}",
                "admin_email": f"resinas-{unique}@example.test", "admin_password": "Temporal-12345!",
            },
        )
    finally:
        settings.procedure_catalog_odontogram_resin_seed_enabled = previous
    assert response.status_code == 201, response.text
    company_id = response.json()["company"]["id"]
    rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company_id,
    )).all()
    assert len(rows) == 83 and all(row.price_currency == currency for row in rows)


def test_enabled_bootstrap_unknown_country_keeps_onboarding_without_inference(db_session):
    previous = settings.procedure_catalog_odontogram_resin_seed_enabled
    settings.procedure_catalog_odontogram_resin_seed_enabled = True
    unique = uuid4().hex[:10]
    try:
        result = bootstrap_installation(db_session, BootstrapInput(
            company_name=f"Resinas país local {unique}", company_slug=f"local-{unique}",
            site_name="Sede Principal", admin_name="Admin Local",
            admin_username=f"local.{unique}", admin_email=f"local-{unique}@example.test",
            admin_password="BootstrapPassword!2026", company_country="Perú",
        ))
    finally:
        settings.procedure_catalog_odontogram_resin_seed_enabled = previous
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == result.company_id)) == 0


def test_enabled_platform_invalid_second_batch_rolls_back_company(
    api_client, db_session, security_world, tmp_path, monkeypatch
):
    payload = json.loads(resin_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload["catalog_version"] = "INVALID"
    invalid = tmp_path / "invalid-platform-resin-batch.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(resin_service, "CATALOG_PATH", invalid)
    previous = settings.procedure_catalog_odontogram_resin_seed_enabled
    settings.procedure_catalog_odontogram_resin_seed_enabled = True
    unique = uuid4().hex[:10]
    company_name = f"Resinas rollback {unique}"
    before = {
        "companies": db_session.scalar(select(func.count()).select_from(Company)),
        "users": db_session.scalar(select(func.count()).select_from(User)),
        "sites": db_session.scalar(select(func.count()).select_from(Site)),
        "procedures": db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem)),
        "audits": db_session.scalar(select(func.count()).select_from(AuditEvent)),
    }
    try:
        response = api_client.post(
            "/api/platform/companies", token=security_world.platform_admin.token,
            json={
                "company_name": company_name, "company_type": "Clínica",
                "address": "Calle sintética", "city": "Santiago", "country": "Chile",
                "timezone": "America/Santiago", "admin_name": "Admin Rollback",
                "admin_username": f"rollback{unique}",
                "admin_email": f"rollback-{unique}@example.test", "admin_password": "Temporal-12345!",
            },
        )
    finally:
        settings.procedure_catalog_odontogram_resin_seed_enabled = previous
    assert response.status_code == 422, response.text
    assert db_session.scalar(select(func.count()).select_from(Company).where(
        Company.name == company_name)) == 0
    assert db_session.scalar(select(func.count()).select_from(Company)) == before["companies"]
    assert db_session.scalar(select(func.count()).select_from(User)) == before["users"]
    assert db_session.scalar(select(func.count()).select_from(Site)) == before["sites"]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem)) == before["procedures"]
    assert db_session.scalar(select(func.count()).select_from(AuditEvent)) == before["audits"]


def test_disabled_flag_leaves_bootstrap_catalog_untouched(db_session):
    settings.procedure_catalog_odontogram_resin_seed_enabled = False
    result = bootstrap_installation(db_session, BootstrapInput(
        company_name="Resinas flag apagado", company_slug=f"flag-off-{uuid4().hex}",
        site_name="Sede Principal", admin_name="Admin Flag Off",
        admin_username=f"flag.off.{uuid4().hex[:8]}",
        admin_email=f"flag-off-{uuid4().hex[:8]}@example.test",
        admin_password="BootstrapPassword!2026", company_country="Chile",
    ))
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == result.company_id)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.company_id == result.company_id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    )) == 0


def test_disabled_flag_leaves_platform_onboarding_catalog_untouched(
    api_client, db_session, security_world
):
    settings.procedure_catalog_odontogram_resin_seed_enabled = False
    unique = uuid4().hex[:10]
    response = api_client.post(
        "/api/platform/companies", token=security_world.platform_admin.token,
        json={
            "company_name": f"Resinas plataforma off {unique}", "company_type": "Clínica",
            "address": "Calle sintética", "city": "Santiago", "country": "Chile",
            "timezone": "America/Santiago", "admin_name": "Admin Flag Off",
            "admin_username": f"off{unique}", "admin_email": f"off-{unique}@example.test",
            "admin_password": "Temporal-12345!",
        },
    )
    assert response.status_code == 201, response.text
    company_id = response.json()["company"]["id"]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == company_id)) == 0


def test_cli_defaults_to_no_write_and_apply_is_disabled_preserving_collision(
    db_session, security_world, monkeypatch, capsys
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    existing = ProcedureCatalogItem(
        company_id=tenant.company.id, name=EXPECTED_NAMES[290],
        normalized_name=normalize_catalog_name(EXPECTED_NAMES[290]), suggested_value=Decimal("888"),
        suggested_scope_type="GENERAL", odontogram_behavior="NO_CHANGE", is_active=True,
        created_by=tenant.admin.user.id,
    )
    db_session.add(existing); db_session.commit()
    base = ["seed_odontogram_resin_catalog", "--company-id", str(tenant.company.id),
            "--actor-id", str(tenant.admin.user.id)]
    monkeypatch.setattr(sys, "argv", base)
    resin_catalog_cli_main()
    assert "dry-run: sin escrituras ni auditoría" in capsys.readouterr().out
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id)) == 1
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED")) == 0

    monkeypatch.setattr(sys, "argv", [*base, "--apply"])
    with pytest.raises(SystemExit, match="identidad real"):
        resin_catalog_cli_main()
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id)) == 1
    db_session.refresh(existing)
    assert existing.suggested_value == Decimal("888")
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED")) == 0


def test_cli_rejects_cross_company_or_inactive_actor_without_writes(
    db_session, security_world, monkeypatch
):
    tenant_a, tenant_b = security_world.tenant_a, security_world.tenant_b
    tenant_b.company.country = "Colombia"
    db_session.commit()
    monkeypatch.setattr(sys, "argv", [
        "seed_odontogram_resin_catalog", "--company-id", str(tenant_b.company.id),
        "--actor-id", str(tenant_a.admin.user.id), "--apply",
    ])
    with pytest.raises(SystemExit, match="actor empresarial activo"):
        resin_catalog_cli_main()
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant_b.company.id)) == 0


@pytest.mark.parametrize("actor_name", ["secretary", "admin"])
def test_cli_apply_is_disabled_even_for_uuid_of_authorized_user(
    db_session, security_world, monkeypatch, actor_name
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    db_session.commit()
    actor = getattr(tenant, actor_name)
    monkeypatch.setattr(sys, "argv", [
        "seed_odontogram_resin_catalog", "--company-id", str(tenant.company.id),
        "--actor-id", str(actor.user.id), "--apply",
    ])
    with pytest.raises(SystemExit, match="identidad real"):
        resin_catalog_cli_main()
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    )) == 0


@pytest.fixture
def authenticated_backfill_enabled():
    previous = settings.procedure_catalog_odontogram_resin_backfill_enabled
    settings.procedure_catalog_odontogram_resin_backfill_enabled = True
    try:
        yield
    finally:
        settings.procedure_catalog_odontogram_resin_backfill_enabled = previous


def _authenticated_batch_preview(api_client, tenant):
    response = api_client.get(
        "/api/procedure-catalog/odontogram-resin-batch/preview",
        token=tenant.admin.token,
    )
    assert response.status_code == 200, response.text
    return response.json()


def _authenticated_batch_apply(api_client, tenant, version):
    preview_digest = resin_service.APPROVED_FILE_SHA256
    return api_client.post(
        "/api/procedure-catalog/odontogram-resin-batch/apply",
        token=tenant.admin.token,
        json={
            "expected_catalog_version": version,
            "expected_manifest_sha256": preview_digest,
            "confirmation": "APPLY_ODONTOGRAM_RESIN_BATCH",
        },
    )


def test_authenticated_backfill_gate_off_rejects_preview_and_apply_without_effects(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    settings.procedure_catalog_odontogram_resin_backfill_enabled = False
    db_session.commit()
    preview = api_client.get(
        "/api/procedure-catalog/odontogram-resin-batch/preview",
        token=tenant.admin.token,
    )
    applied = _authenticated_batch_apply(api_client, tenant, "any-version")
    assert preview.status_code == applied.status_code == 404
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    )) == 0


@pytest.mark.parametrize("mutation", ["version", "digest", "confirmation"])
def test_authenticated_backfill_rejects_invalid_confirmations_without_effects(
    api_client, db_session, security_world, authenticated_backfill_enabled, mutation
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Colombia"
    db_session.commit()
    preview = _authenticated_batch_preview(api_client, tenant)
    body = {
        "expected_catalog_version": preview["catalog_version"],
        "expected_manifest_sha256": preview["manifest_sha256"],
        "confirmation": "APPLY_ODONTOGRAM_RESIN_BATCH",
    }
    if mutation == "version":
        body["expected_catalog_version"] = "WRONG"
    elif mutation == "digest":
        body["expected_manifest_sha256"] = "0" * 64
    else:
        body["confirmation"] = "WRONG"
    response = api_client.post(
        "/api/procedure-catalog/odontogram-resin-batch/apply",
        token=tenant.admin.token,
        json=body,
    )
    assert response.status_code in {409, 422}
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    )) == 0


def test_authenticated_backfill_dry_run_and_apply_audit_real_session(
    api_client, db_session, security_world, authenticated_backfill_enabled
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    db_session.commit()
    preview = _authenticated_batch_preview(api_client, tenant)
    assert preview["would_insert"] == 8 and preview["collisions"] == []
    assert preview["manifest_sha256"] == resin_service.APPROVED_FILE_SHA256
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED")) == 0

    applied = _authenticated_batch_apply(api_client, tenant, preview["catalog_version"])
    assert applied.status_code == 200, applied.text
    assert (applied.json()["inserted"], applied.json()["diagnosis_links"]) == (8, 16)
    audit = db_session.scalar(select(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    ))
    assert audit is not None
    assert audit.user_id == tenant.admin.user.id
    assert audit.session_id is not None
    assert audit.ip_address is not None
    assert audit.user_agent is not None and "httpx" in audit.user_agent.casefold()
    assert audit.detail["authenticated_operator"] is True


def test_authenticated_backfill_requires_permission_and_observes_revocation(
    api_client, db_session, security_world, authenticated_backfill_enabled
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Colombia"
    db_session.commit()
    denied = api_client.get(
        "/api/procedure-catalog/odontogram-resin-batch/preview",
        token=tenant.secretary.token,
    )
    assert denied.status_code == 403

    permission = db_session.scalar(select(Permission).where(
        Permission.code == "procedure_catalog.manage"
    ))
    role_ids = select(UserRole.role_id).where(
        UserRole.company_id == tenant.company.id,
        UserRole.user_id == tenant.admin.user.id,
        UserRole.is_active.is_(True),
    )
    grants = db_session.scalars(select(RolePermission).where(
        RolePermission.company_id == tenant.company.id,
        RolePermission.role_id.in_(role_ids),
        RolePermission.permission_id == permission.id,
    )).all()
    assert grants
    for grant in grants:
        grant.is_active = False
    db_session.commit()
    revoked = api_client.get(
        "/api/procedure-catalog/odontogram-resin-batch/preview",
        token=tenant.admin.token,
    )
    assert revoked.status_code == 403
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id)) == 0


def test_authenticated_backfill_serializes_with_concurrent_permission_revocation(
    api_client, db_session, security_world, monkeypatch, authenticated_backfill_enabled
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    db_session.commit()
    preview = _authenticated_batch_preview(api_client, tenant)
    entered_seed = Event()
    release_seed = Event()
    revocation_ready = Event()
    original_seed = treatment_service.seed_odontogram_resin_catalog

    def controlled_seed(*args, **kwargs):
        entered_seed.set()
        assert release_seed.wait(timeout=10)
        return original_seed(*args, **kwargs)

    monkeypatch.setattr(treatment_service, "seed_odontogram_resin_catalog", controlled_seed)

    def revoke_permission():
        with TestingSessionLocal() as session:
            permission = session.scalar(select(Permission).where(
                Permission.code == "procedure_catalog.manage"
            ))
            role_ids = select(UserRole.role_id).where(
                UserRole.company_id == tenant.company.id,
                UserRole.user_id == tenant.admin.user.id,
                UserRole.is_active.is_(True),
            )
            grants = session.scalars(select(RolePermission).where(
                RolePermission.company_id == tenant.company.id,
                RolePermission.role_id.in_(role_ids),
                RolePermission.permission_id == permission.id,
            )).all()
            for grant in grants:
                grant.is_active = False
            revocation_ready.set()
            session.commit()

    with ThreadPoolExecutor(max_workers=2) as executor:
        apply_future = executor.submit(
            _authenticated_batch_apply, api_client, tenant, preview["catalog_version"]
        )
        assert entered_seed.wait(timeout=10)
        revoke_future = executor.submit(revoke_permission)
        assert revocation_ready.wait(timeout=10)
        release_seed.set()
        applied = apply_future.result(timeout=20)
        revoke_future.result(timeout=20)
    assert applied.status_code == 200, applied.text
    revoked_retry = api_client.get(
        "/api/procedure-catalog/odontogram-resin-batch/preview",
        token=tenant.admin.token,
    )
    assert revoked_retry.status_code == 403
    audits = db_session.scalars(select(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    )).all()
    assert len(audits) == 1 and audits[0].session_id is not None


def test_authenticated_backfill_is_tenant_isolated_and_preserves_collision(
    api_client, db_session, security_world, authenticated_backfill_enabled
):
    tenant_a, tenant_b = security_world.tenant_a, security_world.tenant_b
    _clinical_items(db_session)
    tenant_a.company.country, tenant_b.company.country = "Chile", "Colombia"
    existing = ProcedureCatalogItem(
        company_id=tenant_a.company.id, name=EXPECTED_NAMES[290],
        normalized_name=normalize_catalog_name(EXPECTED_NAMES[290]), suggested_value=Decimal("654321"),
        suggested_scope_type="GENERAL", odontogram_behavior="NO_CHANGE", is_active=True,
        created_by=tenant_a.admin.user.id,
    )
    db_session.add(existing); db_session.commit()
    preview = _authenticated_batch_preview(api_client, tenant_a)
    assert preview["would_insert"] == 7 and len(preview["collisions"]) == 1
    applied = _authenticated_batch_apply(api_client, tenant_a, preview["catalog_version"])
    assert applied.status_code == 200, applied.text
    assert applied.json()["inserted"] == 7 and applied.json()["skipped_collisions"] == 1
    db_session.refresh(existing)
    assert existing.suggested_value == Decimal("654321")
    assert existing.odontogram_behavior == "NO_CHANGE"
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant_b.company.id)) == 0


def test_authenticated_backfill_invalid_manifest_rolls_back_without_audit(
    api_client, db_session, security_world, tmp_path, monkeypatch, authenticated_backfill_enabled
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Chile"
    payload = json.loads(resin_service.CATALOG_PATH.read_text(encoding="utf-8"))
    payload["items"][0]["source_price_clp"] = "-1"
    invalid = tmp_path / "invalid-authenticated-resin.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(resin_service, "CATALOG_PATH", invalid)
    db_session.commit()
    response = api_client.post(
        "/api/procedure-catalog/odontogram-resin-batch/apply",
        token=tenant.admin.token,
        json={
            "expected_catalog_version": payload["catalog_version"],
            "expected_manifest_sha256": resin_service.APPROVED_FILE_SHA256,
            "confirmation": "APPLY_ODONTOGRAM_RESIN_BATCH",
        },
    )
    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    )) == 0


def test_authenticated_backfill_concurrent_retries_are_idempotent(
    api_client, db_session, security_world, authenticated_backfill_enabled
):
    tenant = security_world.tenant_b
    _clinical_items(db_session)
    tenant.company.country = "Colombia"
    db_session.commit()
    version = _authenticated_batch_preview(api_client, tenant)["catalog_version"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(
            lambda _index: _authenticated_batch_apply(api_client, tenant, version),
            range(2),
        ))
    assert [response.status_code for response in responses] == [200, 200]
    assert sorted(response.json()["inserted"] for response in responses) == [0, 8]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant.company.id,
        ProcedureCatalogItem.odontogram_behavior == "REQUIRES_DIAGNOSIS",
    )) == 8
    audits = db_session.scalars(select(AuditEvent).where(
        AuditEvent.company_id == tenant.company.id,
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED",
    )).all()
    assert len(audits) == 2
    assert sorted(audit.detail["inserted"] for audit in audits) == [0, 8]
    assert all(audit.user_id == tenant.admin.user.id and audit.session_id is not None for audit in audits)


def test_isolated_staging_sequence_health_flags_cl_co_collision_retry_and_audit(
    api_client, db_session, security_world, monkeypatch
):
    tenant_cl, tenant_co = security_world.tenant_a, security_world.tenant_b
    _clinical_items(db_session)
    tenant_cl.company.country, tenant_co.company.country = "Chile", "Colombia"
    existing = ProcedureCatalogItem(
        company_id=tenant_cl.company.id, name=EXPECTED_NAMES[290],
        normalized_name=normalize_catalog_name(EXPECTED_NAMES[290]), suggested_value=Decimal("909090"),
        suggested_scope_type="GENERAL", odontogram_behavior="NO_CHANGE", is_active=True,
        created_by=tenant_cl.admin.user.id,
    )
    db_session.add(existing); db_session.commit()
    monkeypatch.setattr(settings, "procedure_catalog_odontogram_resin_seed_enabled", False)
    monkeypatch.setattr(settings, "procedure_catalog_odontogram_resin_backfill_enabled", False)

    health = api_client.get("/health")
    assert health.status_code == 200
    gated = api_client.get(
        "/api/procedure-catalog/odontogram-resin-batch/preview", token=tenant_cl.admin.token
    )
    assert gated.status_code == 404
    assert db_session.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED")) == 0

    monkeypatch.setattr(settings, "procedure_catalog_odontogram_resin_backfill_enabled", True)
    preview_cl = _authenticated_batch_preview(api_client, tenant_cl)
    preview_co = _authenticated_batch_preview(api_client, tenant_co)
    assert (preview_cl["currency"], preview_cl["would_insert"], len(preview_cl["collisions"])) == (
        "CLP", 7, 1
    )
    assert (preview_co["currency"], preview_co["would_insert"], preview_co["collisions"]) == (
        "COP", 8, []
    )
    applied_cl = _authenticated_batch_apply(api_client, tenant_cl, preview_cl["catalog_version"])
    applied_co = _authenticated_batch_apply(api_client, tenant_co, preview_co["catalog_version"])
    retry_cl = _authenticated_batch_apply(api_client, tenant_cl, preview_cl["catalog_version"])
    assert applied_cl.status_code == applied_co.status_code == retry_cl.status_code == 200
    assert (applied_cl.json()["inserted"], applied_cl.json()["skipped_collisions"]) == (7, 1)
    assert (applied_co.json()["inserted"], applied_co.json()["skipped_collisions"]) == (8, 0)
    assert (retry_cl.json()["inserted"], retry_cl.json()["skipped_collisions"]) == (0, 8)
    db_session.refresh(existing)
    assert existing.suggested_value == Decimal("909090")
    cl_rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant_cl.company.id,
    )).all()
    co_rows = db_session.scalars(select(ProcedureCatalogItem).where(
        ProcedureCatalogItem.company_id == tenant_co.company.id,
    )).all()
    assert len(cl_rows) == len(co_rows) == 8
    assert all(row.price_currency == "COP" for row in co_rows)
    audits = db_session.scalars(select(AuditEvent).where(
        AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEEDED"
    )).all()
    assert len(audits) == 3
    assert sorted((audit.company_id, audit.detail["inserted"]) for audit in audits) == sorted([
        (tenant_cl.company.id, 7), (tenant_cl.company.id, 0), (tenant_co.company.id, 8),
    ])
    assert all(audit.user_id is not None and audit.session_id is not None for audit in audits)
