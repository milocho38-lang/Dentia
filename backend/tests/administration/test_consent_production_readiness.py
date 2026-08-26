from datetime import date, datetime, timezone
import hashlib
import json

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.audit_event import AuditEvent
from app.models.consent_template import (
    ConsentDeclarationVersion,
    ConsentProcedureApproval,
    ConsentTemplate,
    ConsentTemplateContentReview,
    ConsentTemplateVersion,
)
from app.services.consent_declaration_catalog import CO_DRAFT, ConsentDeclarationSetError, declaration_set_for
from app.services.consent_production_readiness import (
    PROCEDURE_VERSION,
    ConsentProductionReadinessError,
    assert_template_ready,
)


def _payload(code="READINESS-CUSTOM"):
    return {
        "code": code,
        "name": "Plantilla tenant de prueba",
        "description": "Contenido ficticio",
        "document_kind": "PROCEDURE_CONSENT",
        "country_code": "CO",
        "language_code": "es-CO",
        "initial_version": {
            "title": "Consentimiento tenant",
            "content": "# Consentimiento\n\nPaciente: {{ patient.full_name }}",
            "scope_type": "GENERAL",
            "priority": 0,
            "site_ids": [],
            "procedure_ids": [],
            "specialties": [],
        },
    }


def _create(api_client, actor, code="READINESS-CUSTOM"):
    response = api_client.post("/api/consent-templates", token=actor.token, json=_payload(code))
    assert response.status_code == 201, response.text
    body = response.json()
    return body, body["draft_versions"][0]


def _review(api_client, actor, template_id, version_id):
    return api_client.post(
        f"/api/consent-templates/{template_id}/versions/{version_id}/review-content",
        token=actor.token,
        json={"confirmed": True},
    )


def test_clinic_review_is_tenant_scoped_hash_bound_and_invalidated(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    created, draft = _create(api_client, tenant.dentist_admin)

    forced_payload = _payload("READINESS-CANNOT-FORCE")
    forced_payload["clinic_content_review_confirmed"] = True
    forced_payload["initial_version"]["clinic_content_review_confirmed"] = True
    forced = api_client.post("/api/consent-templates", token=tenant.dentist_admin.token, json=forced_payload)
    assert forced.status_code == 201, forced.text
    assert forced.json()["draft_versions"][0]["clinic_content_review_confirmed"] is False
    forced_draft = forced.json()["draft_versions"][0]
    assert _review(api_client, tenant.admin, forced.json()["id"], forced_draft["id"]).status_code == 200

    blocked = api_client.post(f"/api/consent-templates/{created['id']}/versions/{draft['id']}/publish", token=tenant.dentist_admin.token)
    assert blocked.status_code == 409
    assert "clínica debe revisar" in blocked.text
    assert _review(api_client, tenant.dentist, created["id"], draft["id"]).status_code == 403
    assert _review(api_client, security_world.tenant_b.dentist_admin, created["id"], draft["id"]).status_code == 404
    assert _review(api_client, security_world.platform_admin, created["id"], draft["id"]).status_code == 403

    reviewed = _review(api_client, tenant.dentist_admin, created["id"], draft["id"])
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["clinic_content_review_confirmed"] is True
    row = db_session.scalar(select(ConsentTemplateContentReview).where(ConsentTemplateContentReview.template_version_id == draft["id"], ConsentTemplateContentReview.invalidated_at.is_(None)))
    assert row is not None
    assert row.origin == "CLINIC_CUSTOM"
    assert row.company_id == tenant.company.id
    assert row.content_sha256 == reviewed.json()["content_sha256"]

    changed = api_client.patch(
        f"/api/consent-templates/{created['id']}/versions/{draft['id']}",
        token=tenant.dentist_admin.token,
        json={**_payload()["initial_version"], "content": "# Consentimiento actualizado\n\n{{ patient.full_name }}", "row_version": reviewed.json()["row_version"]},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["clinic_content_review_confirmed"] is False
    db_session.expire_all()
    assert db_session.get(ConsentTemplateContentReview, row.id).invalidation_reason == "VERSION_CONTENT_CHANGED"

    reviewed_again = _review(api_client, tenant.dentist_admin, created["id"], draft["id"])
    assert reviewed_again.status_code == 200
    published = api_client.post(f"/api/consent-templates/{created['id']}/versions/{draft['id']}/publish", token=tenant.dentist_admin.token)
    assert published.status_code == 200, published.text
    new_draft = api_client.post(
        f"/api/consent-templates/{created['id']}/versions/{draft['id']}/create-draft",
        token=tenant.dentist_admin.token,
        json={"change_summary": "Nueva versión tenant"},
    )
    assert new_draft.status_code == 201
    assert new_draft.json()["clinic_content_review_confirmed"] is False
    actions = set(db_session.scalars(select(AuditEvent.action).where(AuditEvent.entity_id == created["id"])))
    assert {"CONSENT_TEMPLATE_CONTENT_REVIEW_CONFIRMED", "CONSENT_TEMPLATE_CONTENT_REVIEW_INVALIDATED", "CONSENT_TEMPLATE_PUBLISHED_AFTER_REVIEW"}.issubset(actions)


def test_reviewed_hash_cannot_be_reused_after_out_of_band_change(api_client, db_session, security_world):
    actor = security_world.tenant_a.dentist_admin
    created, draft = _create(api_client, actor, "READINESS-HASH")
    assert _review(api_client, actor, created["id"], draft["id"]).status_code == 200
    version = db_session.get(ConsentTemplateVersion, draft["id"])
    version.content += "\nCambio no revisado"
    db_session.commit()
    publish = api_client.post(f"/api/consent-templates/{created['id']}/versions/{draft['id']}/publish", token=actor.token)
    assert publish.status_code == 409


def test_production_gate_and_approved_declaration_catalog(api_client, db_session, security_world, monkeypatch):
    actor = security_world.tenant_a.dentist_admin
    created, draft = _create(api_client, actor, "READINESS-PRODUCTION")
    assert _review(api_client, actor, created["id"], draft["id"]).status_code == 200
    assert api_client.post(f"/api/consent-templates/{created['id']}/versions/{draft['id']}/publish", token=actor.token).status_code == 200
    template = db_session.get(ConsentTemplate, created["id"])
    version = db_session.get(ConsentTemplateVersion, draft["id"])
    approval = ConsentProcedureApproval(
        procedure_version=PROCEDURE_VERSION,
        procedure_scope={"electronic": True, "paper": True},
        electronic_channel_reviewed=True,
        paper_channel_reviewed=True,
        responsible_adult_flow_reviewed=True,
        declaration_flow_reviewed=True,
        countries=["CO", "CL"],
        review_reference="Revisión integral anterior al 18 de agosto de 2026",
        review_recorded_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
        reviewer_roles=["LEGAL_REVIEWER", "CLINICAL_REVIEWER", "CLINIC_ADMIN_REVIEWER"],
        status="APPROVED",
    )
    db_session.add(approval)
    db_session.commit()

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "app_debug", False)
    monkeypatch.setattr(settings, "public_frontend_url", "https://dentiapro.com")
    monkeypatch.setattr(settings, "consent_acceptance_enabled", True)
    monkeypatch.setattr(settings, "consent_public_cookie_secure", True)
    monkeypatch.setattr(settings, "consent_storage_persistent", True)
    monkeypatch.setattr(settings, "consent_final_storage_dir", "/tmp/dentia-test-consents")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.test")
    monkeypatch.setattr(settings, "smtp_from_email", "consents@example.test")
    assert_template_ready(db_session, template=template, version=version, signer_policy="PATIENT_SELF", channel="ELECTRONIC")
    for origin in ("CLONED_FROM_DENTIA", "DENTIA_LIBRARY"):
        template.template_origin = origin
        db_session.commit()
        assert_template_ready(db_session, template=template, version=version, signer_policy="PATIENT_SELF", channel="ELECTRONIC")
    with pytest.raises(ConsentProductionReadinessError, match="flujo especial"):
        assert_template_ready(db_session, template=template, version=version, signer_policy="SPECIAL_WORKFLOW", channel="ELECTRONIC")
    monkeypatch.setattr(settings, "consent_storage_persistent", False)
    with pytest.raises(ConsentProductionReadinessError, match="Configuración productiva incompleta"):
        assert_template_ready(db_session, template=template, version=version, signer_policy="PATIENT_SELF", channel="ELECTRONIC")
    monkeypatch.setattr(settings, "consent_storage_persistent", True)

    rows = [{"code": code, "text": text, "order": order} for order, (code, text) in enumerate(CO_DRAFT.declarations, 1)]
    declaration_payload = {
        "code": CO_DRAFT.code,
        "country_code": "CO",
        "locale": "es-CO",
        "actor_type": "PATIENT_SELF",
        "version": "APPROVED_V1",
        "procedure_version": PROCEDURE_VERSION,
        "declarations": rows,
    }
    declaration = ConsentDeclarationVersion(
        code=CO_DRAFT.code,
        country_code="CO",
        locale="es-CO",
        actor_type="PATIENT_SELF",
        version="APPROVED_V1",
        declarations=rows,
        content_sha256=hashlib.sha256(json.dumps(declaration_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        procedure_version=PROCEDURE_VERSION,
        status="APPROVED",
        review_reference="Revisión integral anterior al 18 de agosto de 2026",
        approval_recorded_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
        effective_from=date(2026, 8, 18),
    )
    db_session.add(declaration)
    db_session.commit()
    selected = declaration_set_for("CO", "es-CO", actor_type="PATIENT_SELF", app_env="production", acceptance_enabled=True, on_date=date(2026, 8, 18), session=db_session)
    assert selected.version == "APPROVED_V1"
    assert selected.legal_status == "APPROVED"
    assert selected.is_test_document is False
    assert CO_DRAFT.version == "DRAFT_LEGAL_REVIEW_V1"

    declaration.declarations = [*rows, {"code": "UNREVIEWED", "text": "Cambio no aprobado", "order": 99}]
    db_session.commit()
    with pytest.raises(ConsentDeclarationSetError, match="integridad"):
        declaration_set_for("CO", "es-CO", actor_type="PATIENT_SELF", app_env="production", acceptance_enabled=True, on_date=date(2026, 8, 18), session=db_session)

    approval.status = "RETIRED"
    db_session.commit()
    with pytest.raises(ConsentProductionReadinessError):
        assert_template_ready(db_session, template=template, version=version, signer_policy="PATIENT_SELF", channel="ELECTRONIC")
