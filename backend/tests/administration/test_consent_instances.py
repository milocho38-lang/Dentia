from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, update

from app.models.audit_event import AuditEvent
from app.models.consent_template import ConsentAccessSession, ConsentInstance, ConsentOtpChallenge
from app.models.treatment import ProcedureCatalogItem, TreatmentProcedure
from app.services.consent_template_service import find_applicable_published_templates
from app.services.email_service import get_test_email_outbox
from app.services.email_service import EmailDeliveryError, get_email_provider as configured_email_provider
import app.services.consent_access_service as consent_access_service
from app.core.config import settings
from app.core.logging import RedactConsentTokenFilter
import logging
import re


def _template(api_client, actor, code="INSTANCE-DEMO", content="# Consentimiento\n\nPaciente: {{ patient.full_name }}\n\nEdad clínica: {{ patient.age }}\n\nProfesional: {{ professional.full_name }}\n\nProcedimientos: {{ procedures.list }}\n\nFecha: {{ document.clinical_date }}", *, scope="GENERAL", site_ids=None, procedure_ids=None, country="CO", publish=True):
    created = api_client.post("/api/consent-templates", token=actor.token, json={
        "code": code, "name": "Plantilla ficticia de instancia", "description": "Solo pruebas", "document_kind": "PROCEDURE_CONSENT",
        "country_code": country, "language_code": f"es-{country}", "initial_version": {"title": "Consentimiento ficticio", "content": content, "scope_type": scope, "priority": 0, "site_ids": site_ids or [], "procedure_ids": procedure_ids or [], "specialties": []},
    })
    assert created.status_code == 201, created.text
    draft = created.json()["draft_versions"][0]
    if not publish:
        return created.json(), draft
    published = api_client.post(f"/api/consent-templates/{created.json()['id']}/versions/{draft['id']}/publish", token=actor.token)
    assert published.status_code == 200, published.text
    return published.json()


def _procedure(db_session, tenant):
    catalog = ProcedureCatalogItem(company_id=tenant.company.id, name="Procedimiento clínico ficticio", normalized_name=f"procedimiento-{uuid4()}", description="Descripción ficticia", is_active=True, created_by=tenant.dentist_admin.user.id)
    db_session.add(catalog); db_session.flush()
    procedure = TreatmentProcedure(company_id=tenant.company.id, treatment_id=tenant.treatment.id, patient_id=tenant.patient.id, catalog_procedure_id=catalog.id, name=catalog.name, status="Pendiente", unit_value=0, quantity=1, total_value=0, scope_type="GENERAL", created_by=tenant.dentist_admin.user.id)
    db_session.add(procedure); db_session.commit()
    return catalog, procedure


def _context(tenant, procedure, **changes):
    data = {"patient_id": str(tenant.patient.id), "site_id": str(tenant.site_1.id), "appointment_id": str(tenant.appointment.id), "treatment_id": str(tenant.treatment.id), "treatment_procedure_ids": [str(procedure.id)], "procedure_catalog_ids": [], "dentist_profile_id": str(tenant.dentist_profile.id), "clinical_date": "2026-08-01"}
    data.update(changes)
    return data


def test_candidates_batch_snapshots_hashes_and_audit(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _, procedure = _procedure(db_session, tenant)
    version_1 = _template(api_client, tenant.dentist_admin, "INSTANCE-ONE")
    version_2 = _template(api_client, tenant.dentist_admin, "INSTANCE-TWO")
    context = _context(tenant, procedure)
    candidates = api_client.post("/api/consent-instances/applicable-templates", token=tenant.dentist_admin.token, json=context)
    assert candidates.status_code == 200, candidates.text
    assert candidates.json()["total"] == 2
    assert all("Paciente A Seguridad" in item["rendered_preview"] for item in candidates.json()["items"])
    assert all("Edad clínica: 36" in item["rendered_preview"] for item in candidates.json()["items"])
    assert all("Fecha: 2026-08-01" in item["rendered_preview"] for item in candidates.json()["items"])
    created = api_client.post("/api/consent-instances/batch", token=tenant.dentist_admin.token, json={"context": context, "template_version_ids": [version_1["id"], version_2["id"]]})
    assert created.status_code == 201, created.text
    rows = created.json()
    assert [row["visible_number"] for row in rows] == ["CNS-000001", "CNS-000002"]
    assert all(row["status"] == "DRAFT" and row["missing_variables"] == [] for row in rows)
    assert all(row["timezone"] == "America/Bogota" for row in rows)
    assert all(row["procedures"][0]["name"] == "Procedimiento clínico ficticio" for row in rows)
    preview = api_client.post(f"/api/consent-instances/{rows[0]['id']}/preview", token=tenant.dentist_admin.token)
    assert preview.status_code == 200 and "Todavía no ha sido enviado ni firmado" in preview.json()["warning"]
    confirmed = api_client.post(f"/api/consent-instances/{rows[0]['id']}/professional-confirm", token=tenant.dentist_admin.token, json={"confirmed": True, "row_version": rows[0]["row_version"]})
    assert confirmed.status_code == 200, confirmed.text
    sealed = confirmed.json()
    assert sealed["status"] == "READY_FOR_REVIEW"
    assert all(len(sealed[key]) == 64 for key in ["template_content_sha256", "instance_content_sha256", "context_sha256", "integrity_hash"])
    assert api_client.patch(f"/api/consent-instances/{rows[0]['id']}", token=tenant.dentist_admin.token, json={**context, "row_version": sealed["row_version"]}).status_code == 409
    assert api_client.post(f"/api/consent-instances/{rows[0]['id']}/mark-pending-signature", token=tenant.dentist_admin.token).status_code == 409
    actions = set(db_session.scalars(select(AuditEvent.action).where(AuditEvent.entity_id == rows[0]["id"])))
    assert {"CONSENT_INSTANCE_CREATED", "CONSENT_INSTANCE_PREVIEWED", "CONSENT_INSTANCE_PROFESSIONAL_CONFIRMED", "CONSENT_INSTANCE_READY_FOR_REVIEW"}.issubset(actions)
    db_session.execute(update(ConsentInstance).where(ConsentInstance.id == rows[0]["id"]).values(rendered_content_snapshot="Contenido alterado"))
    db_session.commit()
    assert api_client.get(f"/api/consent-instances/{rows[0]['id']}", token=tenant.dentist_admin.token).status_code == 409


def test_tenant_site_role_and_professional_boundaries(api_client, db_session, security_world):
    tenant_a, tenant_b = security_world.tenant_a, security_world.tenant_b
    _, procedure = _procedure(db_session, tenant_a)
    version = _template(api_client, tenant_a.dentist_admin, "BOUNDARIES")
    context = _context(tenant_a, procedure)
    secretary_created = api_client.post("/api/consent-instances/batch", token=tenant_a.secretary.token, json={"context": context, "template_version_ids": [version["id"]]})
    assert secretary_created.status_code == 201, secretary_created.text
    instance = secretary_created.json()[0]
    assert api_client.post(f"/api/consent-instances/{instance['id']}/professional-confirm", token=tenant_a.secretary.token, json={"confirmed": True, "row_version": instance["row_version"]}).status_code == 403
    assert api_client.post(f"/api/consent-instances/{instance['id']}/professional-confirm", token=tenant_a.admin.token, json={"confirmed": True, "row_version": instance["row_version"]}).status_code == 403
    assert api_client.get(f"/api/consent-instances/{instance['id']}", token=tenant_b.dentist_admin.token).status_code == 404
    assert api_client.get(f"/api/consent-instances/{instance['id']}", token=security_world.platform_admin.token).status_code == 403
    denied = db_session.scalar(select(AuditEvent).where(AuditEvent.user_id == security_world.platform_admin.user.id, AuditEvent.action == "CONSENT_INSTANCE_ACCESS_DENIED"))
    assert denied and denied.result == "FAILURE" and denied.detail["permission"] == "consent.instance.read"
    crossed = api_client.post("/api/consent-instances/applicable-templates", token=tenant_a.dentist_admin.token, json={**context, "patient_id": str(tenant_b.patient.id)})
    assert crossed.status_code == 404
    wrong_site = api_client.post("/api/consent-instances/applicable-templates", token=tenant_a.restricted_site_1.token, json={**context, "site_id": str(tenant_a.site_2.id)})
    assert wrong_site.status_code == 403


def test_missing_variables_block_confirmation_and_void_preserves_history(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _, procedure = _procedure(db_session, tenant)
    version = _template(api_client, tenant.dentist_admin, "MISSING", "# Consentimiento\n\nPlan: {{ treatment.plan_number }}")
    context = _context(tenant, procedure)
    created = api_client.post("/api/consent-instances/batch", token=tenant.dentist_admin.token, json={"context": context, "template_version_ids": [version["id"]]})
    assert created.status_code == 201, created.text
    instance = created.json()[0]
    assert instance["missing_variable_labels"] == ["Número del plan"]
    blocked = api_client.post(f"/api/consent-instances/{instance['id']}/professional-confirm", token=tenant.dentist_admin.token, json={"confirmed": True, "row_version": instance["row_version"]})
    assert blocked.status_code == 422
    voided = api_client.post(f"/api/consent-instances/{instance['id']}/void", token=tenant.dentist_admin.token, json={"reason": "Cambio clínico de prueba"})
    assert voided.status_code == 200 and voided.json()["status"] == "VOIDED"
    persisted = db_session.get(ConsentInstance, instance["id"])
    assert persisted and persisted.template_content_snapshot and persisted.void_reason == "Cambio clínico de prueba"


def test_general_and_specific_templates_are_combined_without_duplicates(api_client, db_session, security_world):
    tenant_a, tenant_b = security_world.tenant_a, security_world.tenant_b
    catalog, procedure = _procedure(db_session, tenant_a)
    other_catalog = ProcedureCatalogItem(company_id=tenant_a.company.id, name="Otro procedimiento ficticio", normalized_name=f"otro-{uuid4()}", description="No aplicable", is_active=True, created_by=tenant_a.dentist_admin.user.id)
    db_session.add(other_catalog)
    db_session.commit()

    general = _template(api_client, tenant_a.dentist_admin, "GENERAL-ALL")
    general_site = _template(api_client, tenant_a.dentist_admin, "GENERAL-SITE-A", site_ids=[str(tenant_a.site_1.id)])
    specific = _template(api_client, tenant_a.dentist_admin, "SPECIFIC-MATCH", scope="SPECIFIC", procedure_ids=[str(catalog.id)])
    _template(api_client, tenant_a.dentist_admin, "SPECIFIC-OTHER", scope="SPECIFIC", procedure_ids=[str(other_catalog.id)])
    _template(api_client, tenant_a.dentist_admin, "GENERAL-CL", country="CL")
    _template(api_client, tenant_b.dentist_admin, "GENERAL-OTHER-TENANT")
    _template(api_client, tenant_a.dentist_admin, "GENERAL-DRAFT", publish=False)

    retired = _template(api_client, tenant_a.dentist_admin, "GENERAL-RETIRED")
    assert api_client.post(f"/api/consent-templates/{retired['template_id']}/versions/{retired['id']}/retire", token=tenant_a.dentist_admin.token, json={"reason": "Retiro de prueba"}).status_code == 200

    void_template, void_draft = _template(api_client, tenant_a.dentist_admin, "GENERAL-VOIDED", publish=False)
    assert api_client.post(f"/api/consent-templates/{void_template['id']}/versions/{void_draft['id']}/void", token=tenant_a.dentist_admin.token, json={"reason": "Anulación de prueba"}).status_code == 200

    superseded = _template(api_client, tenant_a.dentist_admin, "GENERAL-SUPERSEDED")
    new_draft = api_client.post(f"/api/consent-templates/{superseded['template_id']}/versions/{superseded['id']}/create-draft", token=tenant_a.dentist_admin.token, json={"change_summary": "Versión vigente de prueba"})
    assert new_draft.status_code == 201, new_draft.text
    current = api_client.post(f"/api/consent-templates/{superseded['template_id']}/versions/{new_draft.json()['id']}/publish", token=tenant_a.dentist_admin.token)
    assert current.status_code == 200, current.text

    context = _context(tenant_a, procedure)
    response = api_client.post("/api/consent-instances/applicable-templates", token=tenant_a.dentist_admin.token, json=context)
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    version_ids = [item["version_id"] for item in items]
    assert len(version_ids) == len(set(version_ids))
    assert general["id"] in version_ids
    assert general_site["id"] in version_ids
    assert specific["id"] in version_ids
    assert superseded["id"] not in version_ids
    assert current.json()["id"] in version_ids
    general_item = next(item for item in items if item["version_id"] == general["id"])
    assert general_item["applicability_reason_codes"] == ["GENERAL_TEMPLATE"]
    assert general_item["applicability_reasons"] == ["Plantilla general"]

    direct_candidates = find_applicable_published_templates(
        db_session,
        company_id=tenant_a.company.id,
        country_code="CO",
        language_code="es-CO",
        site_id=tenant_a.site_1.id,
        procedure_ids={catalog.id},
    )
    direct_codes = [item.template_code for item in direct_candidates]
    assert "GENERAL-ALL" in direct_codes
    assert "GENERAL-SITE-A" in direct_codes
    assert "SPECIFIC-MATCH" in direct_codes
    assert "SPECIFIC-OTHER" not in direct_codes
    assert "GENERAL-CL" not in direct_codes
    assert "GENERAL-OTHER-TENANT" not in direct_codes
    assert "GENERAL-DRAFT" not in direct_codes
    assert "GENERAL-RETIRED" not in direct_codes
    assert "GENERAL-VOIDED" not in direct_codes
    assert direct_codes.count("GENERAL-SUPERSEDED") == 1

    site_2_candidates = find_applicable_published_templates(
        db_session,
        company_id=tenant_a.company.id,
        country_code="CO",
        language_code="es-CO",
        site_id=tenant_a.site_2.id,
        procedure_ids={catalog.id},
    )
    site_2_ids = {str(item.version_id) for item in site_2_candidates}
    assert general["id"] in site_2_ids
    assert general_site["id"] not in site_2_ids

    selected = [general["id"], specific["id"]]
    created = api_client.post("/api/consent-instances/batch", token=tenant_a.dentist_admin.token, json={"context": context, "template_version_ids": selected})
    assert created.status_code == 201, created.text
    assert len(created.json()) == 2
    assert {item["template_version_id"] for item in created.json()} == set(selected)


def test_secure_access_otp_document_clarification_reissue_and_tenant_boundaries(api_client, db_session, security_world, monkeypatch):
    tenant = security_world.tenant_a
    get_test_email_outbox().clear()
    _, procedure = _procedure(db_session, tenant)
    version = _template(api_client, tenant.dentist_admin, "ACCESS-PORTAL")
    context = _context(tenant, procedure)
    created = api_client.post("/api/consent-instances/batch", token=tenant.dentist_admin.token, json={"context": context, "template_version_ids": [version["id"]]}).json()[0]
    confirmed = api_client.post(f"/api/consent-instances/{created['id']}/professional-confirm", token=tenant.dentist_admin.token, json={"confirmed": True, "row_version": created["row_version"]})
    assert confirmed.status_code == 200
    issued = api_client.post(f"/api/consent-instances/{created['id']}/access-sessions", token=tenant.dentist_admin.token, json={})
    assert issued.status_code == 201, issued.text
    public_url = issued.json()["public_url"]
    token = public_url.rsplit("/", 1)[-1]
    assert len(token) >= 32
    stored = db_session.scalar(select(ConsentAccessSession).where(ConsentAccessSession.consent_instance_id == created["id"]))
    assert stored and token not in stored.public_token_hash and len(stored.public_token_hash) == 64
    assert api_client.get(f"/api/consent-instances/{created['id']}/access-sessions", token=security_world.platform_admin.token).status_code == 403
    assert api_client.get(f"/api/consent-instances/{created['id']}/access-sessions", token=security_world.tenant_b.dentist_admin.token).status_code == 404
    access_audit = api_client.get(f"/api/consent-instances/{created['id']}/access-sessions/audit", token=tenant.dentist_admin.token)
    assert access_audit.status_code == 200
    assert "CONSENT_ACCESS_SESSION_ISSUED" in {event["action"] for event in access_audit.json()}
    assert api_client.get(f"/api/consent-instances/{created['id']}/access-sessions/audit", token=security_world.platform_admin.token).status_code == 403
    assert api_client.get(f"/api/consent-instances/{created['id']}/access-sessions/audit", token=security_world.tenant_b.dentist_admin.token).status_code == 404
    pre = api_client.get(f"/api/public/consents/{token}")
    assert pre.status_code == 200 and "patient_name" not in pre.json() and pre.headers["cache-control"].startswith("no-store")
    stored.open_count = settings.consent_link_open_max_requests
    db_session.commit()
    assert api_client.get(f"/api/public/consents/{token}").status_code == 429
    stored.open_window_started_at = datetime.now(timezone.utc) - timedelta(seconds=settings.consent_link_open_window_seconds + 1)
    db_session.commit()
    assert api_client.get(f"/api/public/consents/{token}").status_code == 200

    class FailingProvider:
        def send(self, _delivery):
            raise EmailDeliveryError("simulated local SMTP failure")

    monkeypatch.setattr(consent_access_service, "get_email_provider", lambda: FailingProvider())
    failed_delivery = api_client.post(f"/api/public/consents/{token}/otp")
    assert failed_delivery.status_code == 503
    failed_challenge = db_session.scalar(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id == stored.id, ConsentOtpChallenge.status == "DELIVERY_FAILED"))
    assert failed_challenge is not None
    monkeypatch.setattr(consent_access_service, "get_email_provider", configured_email_provider)
    sent = api_client.post(f"/api/public/consents/{token}/otp")
    assert sent.status_code == 200 and "***@" in sent.json()["recipient_masked"]
    delivery = get_test_email_outbox()[-1]
    otp = re.search(r"\b\d{6}\b", delivery.body).group(0)
    challenge = db_session.scalar(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id == stored.id, ConsentOtpChallenge.status == "PENDING"))
    assert challenge and otp not in challenge.otp_hash and len(challenge.otp_hash) == 64
    challenge.last_sent_at = datetime.now(timezone.utc) - timedelta(seconds=settings.consent_otp_resend_seconds + 1)
    db_session.commit()
    resent = api_client.post(f"/api/public/consents/{token}/otp")
    assert resent.status_code == 200
    db_session.expire_all()
    pending = list(db_session.scalars(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id == stored.id, ConsentOtpChallenge.status == "PENDING")))
    assert len(pending) == 1 and challenge.status == "INVALIDATED"
    assert len(get_test_email_outbox()) == 2
    otp = re.search(r"\b\d{6}\b", get_test_email_outbox()[-1].body).group(0)
    assert api_client.post(f"/api/public/consents/{token}/otp/verify", json={"code": "000000"}).status_code == 400
    verified = api_client.post(f"/api/public/consents/{token}/otp/verify", json={"code": otp})
    assert verified.status_code == 200, verified.text
    cookie = verified.headers["set-cookie"].split(";", 1)[0]
    document = api_client.get(f"/api/public/consents/{token}/document", headers={"Cookie": cookie})
    assert document.status_code == 200 and document.json()["status_label"] == "Revisado, aún no firmado"
    assert "signature" not in document.json() and "accepted" not in document.json()
    clarification = api_client.post(f"/api/public/consents/{token}/clarification", headers={"Cookie": cookie}, json={"message": "Necesito una explicación breve."})
    assert clarification.status_code == 201
    reissued = api_client.post(f"/api/consent-instances/{created['id']}/access-sessions/reissue", token=tenant.dentist_admin.token, json={})
    assert reissued.status_code == 201 and reissued.json()["public_url"] != public_url
    assert api_client.get(f"/api/public/consents/{token}").status_code == 404
    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, f'GET /api/public/consents/{token}', (), None)
    RedactConsentTokenFilter().filter(record)
    assert token not in record.getMessage() and "[REDACTED]" in record.getMessage()
