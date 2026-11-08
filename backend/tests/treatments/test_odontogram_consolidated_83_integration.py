import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.models.audit_event import AuditEvent
from app.models.odontogram import OdontogramCatalogItem
from app.models.treatment import ProcedureCatalogItem
from app.services import procedure_catalog_odontogram_esthetic_seed_service as esthetic_service
from app.services.procedure_catalog_seed_service import normalize_catalog_name


ALL_CODES = {
    "FIND_CARIES",
    "FIND_FRACTURE",
    "FIND_ENDO_DEFECTIVE",
    "PLAN_CROWN",
    "DONE_CROWN",
    "PLAN_IMPLANT",
    "DONE_IMPLANT",
    "PLAN_ENDO",
    "DONE_ENDO",
    "PLAN_POST",
    "DONE_POST",
    "DONE_PULPOTOMY",
    "PLAN_EXTRACTION",
    "DONE_EXTRACTION",
    "PLAN_VENEER",
    "DONE_VENEER",
    "PLAN_RESIN",
    "DONE_RESIN",
}


def _install_global_codes(session) -> None:
    existing = set(
        session.scalars(
            select(OdontogramCatalogItem.code).where(
                OdontogramCatalogItem.company_id.is_(None),
                OdontogramCatalogItem.code.in_(ALL_CODES),
            )
        )
    )
    for code in sorted(ALL_CODES - existing):
        if code.startswith("FIND_"):
            item_type = "FINDING"
        elif code.startswith("PLAN_"):
            item_type = "PLANNED_PROCEDURE"
        else:
            item_type = "PERFORMED_PROCEDURE"
        session.add(
            OdontogramCatalogItem(
                company_id=None,
                code=code,
                name=code,
                type=item_type,
                color="#2563eb",
                pattern="solid",
                symbol=code,
                allowed_scopes=["GENERAL", "ZONE", "TOOTH", "TOOTH_SURFACE"],
                allowed_surfaces=[
                    "VESTIBULAR",
                    "LINGUAL",
                    "PALATAL",
                    "MESIAL",
                    "DISTAL",
                    "OCCLUSAL",
                    "INCISAL",
                ],
                is_active=True,
            )
        )
    session.commit()


def _preview(api_client, tenant):
    return api_client.get(
        "/api/procedure-catalog/odontogram-clinical-batch/preview",
        token=tenant.admin.token,
    )


def _apply(api_client, tenant, preview):
    return api_client.post(
        "/api/procedure-catalog/odontogram-clinical-batch/apply",
        token=tenant.admin.token,
        json={
            "expected_catalog_version": preview["catalog_version"],
            "expected_manifest_sha256": preview["manifest_sha256"],
            "confirmation": "APPLY_ODONTOGRAM_CLINICAL_83",
        },
    )


def test_consolidated_gate_off_rejects_without_writes(
    api_client, db_session, security_world, monkeypatch
):
    tenant = security_world.tenant_b
    tenant.company.country = "Chile"
    db_session.commit()
    monkeypatch.setattr(settings, "procedure_catalog_odontogram_resin_backfill_enabled", False)

    preview = _preview(api_client, tenant)
    applied = api_client.post(
        "/api/procedure-catalog/odontogram-clinical-batch/apply",
        token=tenant.admin.token,
        json={
            "expected_catalog_version": "disabled",
            "expected_manifest_sha256": "0" * 64,
            "confirmation": "APPLY_ODONTOGRAM_CLINICAL_83",
        },
    )
    assert preview.status_code == applied.status_code == 404
    assert db_session.scalar(
        select(func.count()).select_from(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == tenant.company.id
        )
    ) == 0


def test_consolidated_preview_apply_collision_and_retry_are_safe(
    api_client, db_session, security_world, monkeypatch
):
    tenant = security_world.tenant_b
    _install_global_codes(db_session)
    tenant.company.country = "Chile"
    collision = ProcedureCatalogItem(
        company_id=tenant.company.id,
        name="Restauración Cervical (Clase V)",
        normalized_name=normalize_catalog_name("Restauración Cervical (Clase V)"),
        suggested_value=Decimal("777"),
        suggested_scope_type="GENERAL",
        odontogram_behavior="NO_CHANGE",
        is_active=True,
        created_by=tenant.admin.user.id,
    )
    db_session.add(collision)
    db_session.commit()
    monkeypatch.setattr(settings, "procedure_catalog_odontogram_resin_backfill_enabled", True)

    audits_before = db_session.scalar(select(func.count()).select_from(AuditEvent))
    preview_response = _preview(api_client, tenant)
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    assert preview["would_insert"] == 82
    assert len(preview["collisions"]) == 1
    assert db_session.scalar(
        select(func.count()).select_from(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == tenant.company.id
        )
    ) == 1
    assert db_session.scalar(select(func.count()).select_from(AuditEvent)) == audits_before

    applied = _apply(api_client, tenant, preview)
    assert applied.status_code == 200, applied.text
    assert (applied.json()["inserted"], applied.json()["skipped_collisions"]) == (82, 1)
    db_session.refresh(collision)
    assert collision.suggested_value == Decimal("777")
    assert db_session.scalar(
        select(func.count()).select_from(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == tenant.company.id
        )
    ) == 83

    retry = _apply(api_client, tenant, preview)
    assert retry.status_code == 200, retry.text
    assert (retry.json()["inserted"], retry.json()["skipped_collisions"]) == (0, 83)
    consolidated_audits = db_session.scalars(
        select(AuditEvent).where(
            AuditEvent.company_id == tenant.company.id,
            AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_CONSOLIDATED_SEEDED",
        )
    ).all()
    assert len(consolidated_audits) == 2
    assert all(item.user_id == tenant.admin.user.id and item.session_id for item in consolidated_audits)


def test_consolidated_apply_rolls_back_all_components_on_invalid_manifest(
    api_client, db_session, security_world, monkeypatch, tmp_path
):
    tenant = security_world.tenant_b
    _install_global_codes(db_session)
    tenant.company.country = "Colombia"
    db_session.commit()
    monkeypatch.setattr(settings, "procedure_catalog_odontogram_resin_backfill_enabled", True)
    preview_response = _preview(api_client, tenant)
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()

    payload = json.loads(esthetic_service.CATALOG_PATH.read_text())
    payload["items"][0]["source_price_clp"] = "-1"
    invalid = tmp_path / "invalid-esthetic.json"
    invalid.write_text(json.dumps(payload))
    monkeypatch.setattr(esthetic_service, "CATALOG_PATH", invalid)

    applied = _apply(api_client, tenant, preview)
    assert applied.status_code == 422
    assert db_session.scalar(
        select(func.count()).select_from(ProcedureCatalogItem).where(
            ProcedureCatalogItem.company_id == tenant.company.id
        )
    ) == 0
    assert db_session.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.company_id == tenant.company.id,
            AuditEvent.entity == "procedure_catalog_seed",
        )
    ) == 0
