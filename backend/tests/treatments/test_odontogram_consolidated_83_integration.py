import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.models.audit_event import AuditEvent
from app.models.associations import RolePermission, UserRole
from app.models.company import Company
from app.models.odontogram import OdontogramCatalogItem
from app.models.permission import Permission
from app.models.role import Role
from app.models.treatment import ProcedureCatalogItem
from app.services import platform_service
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
    assert db_session.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.company_id == tenant.company.id,
            AuditEvent.entity == "procedure_catalog_seed",
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


def _platform_preview(api_client, security_world):
    return api_client.get(
        "/api/platform/procedure-catalog/odontogram-clinical-batch/preview",
        token=security_world.platform_admin.token,
    )


def _platform_apply(api_client, security_world, preview):
    return api_client.post(
        "/api/platform/procedure-catalog/odontogram-clinical-batch/apply",
        token=security_world.platform_admin.token,
        json={
            "expected_catalog_version": preview["catalog_version"],
            "expected_manifest_sha256": preview["manifest_sha256"],
            "confirmation": "APPLY_PLATFORM_ODONTOGRAM_CLINICAL_83",
        },
    )


def test_platform_global_catalog_apply_is_authenticated_audited_and_idempotent(
    api_client, db_session, security_world, monkeypatch
):
    _install_global_codes(db_session)
    security_world.tenant_a.company.country = "Colombia"
    security_world.tenant_b.company.country = "Chile"
    platform_company = db_session.get(
        Company, security_world.platform_admin.user.company_id
    )
    assert platform_company is not None
    platform_company.country = "Colombia"
    collision = ProcedureCatalogItem(
        company_id=security_world.tenant_a.company.id,
        name="Restauración Cervical (Clase V)",
        normalized_name=normalize_catalog_name("Restauración Cervical (Clase V)"),
        suggested_value=Decimal("777"),
        suggested_scope_type="GENERAL",
        odontogram_behavior="NO_CHANGE",
        is_active=True,
        created_by=security_world.tenant_a.admin.user.id,
    )
    db_session.add(collision)
    db_session.commit()
    monkeypatch.setattr(
        settings, "procedure_catalog_odontogram_resin_backfill_enabled", True
    )

    preview_response = _platform_preview(api_client, security_world)
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    assert preview["active_companies"] == 3
    assert preview["eligible_companies"] == 3
    assert preview["complete_companies"] == 0
    assert preview["would_insert"] == 248
    assert preview["collisions"] == 1
    assert preview["currencies"] == {"COP": 2, "CLP": 1}

    applied = _platform_apply(api_client, security_world, preview)
    assert applied.status_code == 200, applied.text
    assert applied.json() == {
        "eligible_companies": 3,
        "applied_companies": 3,
        "already_complete_companies": 0,
        "skipped_companies": 0,
        "inserted": 248,
        "skipped_collisions": 1,
        # The preserved collision is a resin item with two diagnosis links;
        # global backfill must not mutate it to add those links.
        "diagnosis_links": 106,
        "catalog_version": preview["catalog_version"],
        "manifest_sha256": preview["manifest_sha256"],
    }
    db_session.refresh(collision)
    assert collision.suggested_value == Decimal("777")

    audits = list(
        db_session.scalars(
            select(AuditEvent).where(
                AuditEvent.action
                == "PROCEDURE_CATALOG_ODONTOGRAM_CONSOLIDATED_SEEDED"
            )
        )
    )
    assert len(audits) == 3
    assert {audit.company_id for audit in audits} == {
        security_world.tenant_a.company.id,
        security_world.tenant_b.company.id,
        security_world.platform_admin.user.company_id,
    }
    assert all(
        audit.user_id == security_world.platform_admin.user.id
        and audit.session_id is not None
        and audit.ip_address is not None
        and audit.user_agent is not None
        and audit.detail["authenticated_operator"] is True
        for audit in audits
    )

    retry_preview_response = _platform_preview(api_client, security_world)
    assert retry_preview_response.status_code == 200
    retry_preview = retry_preview_response.json()
    assert retry_preview["would_insert"] == 0
    assert retry_preview["collisions"] == 249
    assert retry_preview["complete_companies"] == 3
    retry = _platform_apply(api_client, security_world, retry_preview)
    assert retry.status_code == 200, retry.text
    assert retry.json()["applied_companies"] == 0
    assert retry.json()["already_complete_companies"] == 3
    assert retry.json()["inserted"] == 0
    assert db_session.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.action == "PROCEDURE_CATALOG_ODONTOGRAM_CONSOLIDATED_SEEDED"
        )
    ) == 3


def test_platform_global_catalog_rolls_back_every_company_on_later_failure(
    api_client, db_session, security_world, monkeypatch
):
    _install_global_codes(db_session)
    security_world.tenant_a.company.country = "Colombia"
    security_world.tenant_b.company.country = "Chile"
    platform_company = db_session.get(
        Company, security_world.platform_admin.user.company_id
    )
    assert platform_company is not None
    platform_company.country = "Colombia"
    db_session.commit()
    monkeypatch.setattr(
        settings, "procedure_catalog_odontogram_resin_backfill_enabled", True
    )

    preview_response = _platform_preview(api_client, security_world)
    assert preview_response.status_code == 200
    preview = preview_response.json()
    before_items = db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem))
    before_audits = db_session.scalar(select(func.count()).select_from(AuditEvent))
    real_seed = platform_service.seed_odontogram_consolidated_catalog
    calls = 0

    def fail_on_second_company(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("synthetic later-company failure")
        return real_seed(*args, **kwargs)

    monkeypatch.setattr(
        platform_service,
        "seed_odontogram_consolidated_catalog",
        fail_on_second_company,
    )
    response = _platform_apply(api_client, security_world, preview)
    assert response.status_code == 422
    assert "synthetic later-company failure" in response.json()["detail"]
    assert db_session.scalar(select(func.count()).select_from(ProcedureCatalogItem)) == before_items
    assert db_session.scalar(select(func.count()).select_from(AuditEvent)) == before_audits


def test_platform_global_catalog_rejects_non_platform_admin_even_with_permission(
    api_client, db_session, security_world, monkeypatch
):
    monkeypatch.setattr(
        settings, "procedure_catalog_odontogram_resin_backfill_enabled", True
    )
    actor = security_world.tenant_a.admin
    membership = db_session.scalar(
        select(UserRole).where(
            UserRole.user_id == actor.user.id,
            UserRole.company_id == actor.user.company_id,
            UserRole.is_active.is_(True),
        )
    )
    permission = db_session.scalar(
        select(Permission).where(Permission.code == "platform.companies.manage")
    )
    role = db_session.get(Role, membership.role_id)
    assert membership is not None and permission is not None and role is not None
    assert role.code != "PLATFORM_ADMIN"
    db_session.add(
        RolePermission(
            company_id=actor.user.company_id,
            role_id=role.id,
            permission_id=permission.id,
            created_by=actor.user.id,
        )
    )
    db_session.commit()

    response = api_client.get(
        "/api/platform/procedure-catalog/odontogram-clinical-batch/preview",
        token=actor.token,
    )
    assert response.status_code == 403
    assert "Administrador de plataforma real" in response.text
