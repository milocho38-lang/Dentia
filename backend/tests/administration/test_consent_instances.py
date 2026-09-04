from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from dataclasses import replace
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4
import base64
import hashlib
import fitz
import json
from io import BytesIO
from PIL import Image, ImageDraw
import pytest
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from sqlalchemy import func, select, update

from app.models.audit_event import AuditEvent
from app.models.consent_template import (
    ConsentAccessSession,
    ConsentInstance,
    ConsentInstanceProcedure,
    ConsentLibraryDocument,
    ConsentLibraryVersion,
    ConsentOtpChallenge,
    ConsentResponsibleAdult,
    ConsentTemplateVersion,
)
from app.models.consent_acceptance import ConsentAcceptance, ConsentAcceptanceDeclaration, ConsentEvidenceManifest, ConsentFinalDocument, ConsentSignatureArtifact, ConsentPaperPacket, ConsentPaperPage
from app.models.treatment import ProcedureCatalogItem, TreatmentProcedure
from app.services.consent_template_service import find_applicable_published_templates
from app.services.email_service import get_test_email_outbox
from app.services.email_service import EmailDeliveryError, get_email_provider as configured_email_provider
import app.services.consent_access_service as consent_access_service
import app.services.consent_acceptance_service as consent_acceptance_service
import app.services.consent_declaration_catalog as consent_declaration_catalog
from app.services.consent_acceptance_context import (
    ACCEPTANCE_CONTEXT_SCHEMA_VERSION,
    LEGACY_ACCEPTANCE_CONTEXT_UNSUPPORTED,
    PUBLIC_LEGACY_MESSAGE,
)
from app.services.consent_instance_service import _sha
import app.services.consent_instance_service as consent_instance_service
from app.core.config import settings
from app.core.logging import RedactConsentTokenFilter
from app.utils.clinical_dates import local_clinical_date
import logging
import re
from zoneinfo import ZoneInfo


def _signature_data_url(width=420, height=140):
    image = Image.new("RGB", (width, height), "white")
    drawing = ImageDraw.Draw(image)
    drawing.line([(width*.07,height*.68),(width*.24,height*.25),(width*.42,height*.75),(width*.61,height*.32),(width*.9,height*.64)],fill="#0f172a",width=max(5,round(width/128)))
    buffer = BytesIO(); image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _install_test_logo(company, *, color="#16a34a"):
    directory=Path(settings.branding_storage_dir)/str(company.id);directory.mkdir(parents=True,exist_ok=True)
    path=directory/"logo-consent-test.png"
    image=Image.new("RGB",(640,220),"white");drawing=ImageDraw.Draw(image);drawing.rounded_rectangle((12,12,628,208),radius=35,fill=color);drawing.text((70,78),"DENTIA CLINICA",fill="white")
    image.save(path,format="PNG")
    company.logo_path=f"{company.id}/{path.name}";company.logo_filename="logo-institucional.png"
    return path


def _template(api_client, actor, code="INSTANCE-DEMO", content="# Consentimiento\n\nPaciente: {{ patient.full_name }}\n\nEdad clínica: {{ patient.age }}\n\nProfesional: {{ professional.full_name }}\n\nProcedimientos: {{ procedures.list }}\n\nFecha: {{ document.clinical_date }}", *, scope="GENERAL", site_ids=None, procedure_ids=None, country="CO", publish=True):
    created = api_client.post("/api/consent-templates", token=actor.token, json={
        "code": code, "name": "Plantilla ficticia de instancia", "description": "Solo pruebas", "document_kind": "PROCEDURE_CONSENT",
        "country_code": country, "language_code": f"es-{country}", "initial_version": {"title": "Consentimiento ficticio", "content": content, "scope_type": scope, "priority": 0, "site_ids": site_ids or [], "procedure_ids": procedure_ids or [], "specialties": []},
    })
    assert created.status_code == 201, created.text
    draft = created.json()["draft_versions"][0]
    if not publish:
        return created.json(), draft
    reviewed = api_client.post(f"/api/consent-templates/{created.json()['id']}/versions/{draft['id']}/review-content", token=actor.token, json={"confirmed": True})
    assert reviewed.status_code == 200, reviewed.text
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


def _set_template_signer_policy(db_session, version_id, policy):
    source_content = "# Consentimiento ficticio para pruebas del firmante"
    source_hash = _sha(source_content)
    document = ConsentLibraryDocument(
        code=f"TEST-SIGNER-{uuid4()}",
        title="Consentimiento ficticio de firmante",
        summary="Documento sintético exclusivo de pruebas.",
        document_type="INFORMED_CONSENT",
        category="Pruebas",
        specialty_code=None,
        specialty_name=None,
        signer_scope=policy,
        requires_patient_signature=True,
        supports_electronic_signature=True,
        source_package_version="TEST",
        source_document_hash=source_hash,
        source_page_start=1,
        source_page_end=1,
        source_title_exact="Consentimiento ficticio de firmante",
        source_origin_note="Fixture sintético sin contenido clínico real.",
        source_reference="pytest",
        is_active=True,
    )
    db_session.add(document)
    db_session.flush()
    library_version = ConsentLibraryVersion(
        library_document_id=document.id,
        country_code="CO",
        language_code="es-CO",
        version_number=1,
        publication_status="PUBLISHED",
        legal_review_status="APPROVED",
        clinical_review_status="APPROVED",
        reviewed_countries=["CO"],
        content_format="RESTRICTED_MARKDOWN_V1",
        content=source_content,
        source_text=source_content,
        source_text_sha256=source_hash,
        normalized_content_sha256=source_hash,
        variable_schema_snapshot=[],
        source_pages=[1],
        transformation_notes=[f"signer_compatibility={policy}"],
        review_notes="Fixture sintético.",
        imported_at=datetime.now(timezone.utc),
    )
    db_session.add(library_version)
    db_session.flush()
    template_version = db_session.get(ConsentTemplateVersion, UUID(str(version_id)))
    assert template_version is not None
    template_version.source_library_version_id = library_version.id
    db_session.commit()
    return template_version


def _prepare_acceptance(api_client, db_session, tenant, code, *, country="CO", content=None, before_requirements=None, expected_requirements_status=200, signer_policy=None, context_changes=None):
    get_test_email_outbox().clear()
    _,procedure=_procedure(db_session,tenant)
    version=_template(api_client,tenant.dentist_admin,code,country=country,content=content or "# Consentimiento de prueba\n\nPaciente: {{ patient.full_name }}\n\nFecha: {{ document.clinical_date }}")
    if signer_policy:
        _set_template_signer_policy(db_session, version["id"], signer_policy)
    created=api_client.post("/api/consent-instances/batch",token=tenant.dentist_admin.token,json={"context":_context(tenant,procedure,**(context_changes or {})),"template_version_ids":[version["id"]]}).json()[0]
    confirmed=api_client.post(f"/api/consent-instances/{created['id']}/professional-confirm",token=tenant.dentist_admin.token,json={"confirmed":True,"row_version":created["row_version"]}); assert confirmed.status_code==200,confirmed.text
    issued=api_client.post(f"/api/consent-instances/{created['id']}/access-sessions",token=tenant.dentist_admin.token,json={});token=issued.json()["public_url"].rsplit("/",1)[-1]
    assert api_client.post(f"/api/public/consents/{token}/otp").status_code==200
    otp=re.search(r"\b\d{6}\b",get_test_email_outbox()[-1].body).group(0);verified=api_client.post(f"/api/public/consents/{token}/otp/verify",json={"code":otp});cookie=verified.headers["set-cookie"].split(";",1)[0]
    if before_requirements: before_requirements()
    requirements=api_client.get(f"/api/public/consents/{token}/acceptance-requirements",headers={"Cookie":cookie}); assert requirements.status_code==expected_requirements_status,requirements.text
    if expected_requirements_status!=200: return created,token,cookie,requirements,None
    data=requirements.json();payload={"idempotency_key":f"review-{uuid4()}","acting_on_own_behalf":data["signer_actor_type"] == "PATIENT_SELF","declaration_set_code":data["declaration_set_code"],"declarations_version":data["declarations_version"],"declarations_set_sha256":data["declarations_set_sha256"],"declarations":[{"code":item["code"],"accepted":True} for item in data["declarations"]],"typed_full_name":data["signer_name"] or data["patient_name"],"signature_data_url":_signature_data_url()}
    return created,token,cookie,data,payload


def _prepare_paper(api_client, db_session, tenant, code="PAPER-FLOW", *, signer_policy=None, context_changes=None):
    _, procedure = _procedure(db_session, tenant)
    content = "# Consentimiento de prueba en papel\n\nPaciente: {{ patient.full_name }}\n\n" + "\n\n".join(f"Cláusula clínica ficticia {index}: información revisada para validar paginación y preservación documental." for index in range(1, 80))
    version = _template(api_client, tenant.dentist_admin, code, content=content)
    if signer_policy:
        _set_template_signer_policy(db_session, version["id"], signer_policy)
    created = api_client.post("/api/consent-instances/batch", token=tenant.dentist_admin.token, json={"context": _context(tenant, procedure, **(context_changes or {})), "template_version_ids": [version["id"]]})
    assert created.status_code == 201, created.text
    instance = created.json()[0]
    confirmed = api_client.post(f"/api/consent-instances/{instance['id']}/professional-confirm", token=tenant.dentist_admin.token, json={"confirmed": True, "row_version": instance["row_version"]})
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()


def _paper_verification():
    return {"all_pages_present": True, "correct_order": True, "legible": True, "signature_page_included": True, "matches_printed_packet": True, "physical_original_retained": True}


def test_paper_consent_adult_packet_digitization_reorder_finalize_and_immutable(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    instance = _prepare_paper(api_client, db_session, tenant)
    prepared = api_client.post(f"/api/consent-instances/{instance['id']}/paper", token=tenant.dentist_admin.token)
    assert prepared.status_code == 200, prepared.text
    packet = prepared.json(); assert packet["status"] == "PRINTED" and packet["expected_page_count"] >= 2 and len(packet["print_sha256"]) == 64
    assert api_client.get(f"/api/consent-instances/{instance['id']}", token=tenant.dentist_admin.token).json()["paper_status"] == "PRINTED"
    printable = api_client.get(f"/api/consent-instances/{instance['id']}/paper/print-document", token=tenant.dentist_admin.token)
    assert printable.status_code == 200 and printable.content.startswith(b"%PDF")
    assert b"source_text" not in printable.content
    signed = api_client.post(f"/api/consent-instances/{instance['id']}/paper/record-signed", token=tenant.dentist_admin.token, json={"confirmed": True})
    assert signed.status_code == 200 and signed.json()["status"] == "SIGNED_PENDING_DIGITIZATION"
    assert api_client.get(f"/api/consent-instances/{instance['id']}", token=tenant.dentist_admin.token).json()["paper_status"] == "SIGNED_PENDING_DIGITIZATION"
    uploaded = api_client.post(f"/api/consent-instances/{instance['id']}/paper/pages", token=tenant.dentist_admin.token, files={"file": ("scan.pdf", printable.content, "application/pdf")})
    assert uploaded.status_code == 200, uploaded.text
    page_ids = [row["id"] for row in uploaded.json()["pages"]]
    assert len(page_ids) == packet["expected_page_count"]
    reordered = api_client.patch(f"/api/consent-instances/{instance['id']}/paper/pages/order", token=tenant.dentist_admin.token, json={"page_ids": list(reversed(page_ids))})
    assert reordered.status_code == 200 and reordered.json()["pages"][0]["id"] == page_ids[-1]
    finalized = api_client.post(f"/api/consent-instances/{instance['id']}/paper/finalize", token=tenant.dentist_admin.token, json=_paper_verification())
    assert finalized.status_code == 200, finalized.text
    result = finalized.json(); assert result["status"] == "FINALIZED" and result["final_page_count"] == packet["expected_page_count"] and len(result["final_pdf_sha256"]) == 64
    final_pdf = api_client.get(f"/api/consent-instances/{instance['id']}/paper/final-document?download=true", token=tenant.dentist_admin.token)
    assert final_pdf.status_code == 200 and hashlib.sha256(final_pdf.content).hexdigest() == result["final_pdf_sha256"]
    state = api_client.get(f"/api/consent-instances/{instance['id']}", token=tenant.dentist_admin.token).json()
    assert state["status"] == "SIGNED" and state["completion_channel"] == "PAPER" and state["paper_status"] == "FINALIZED"
    assert api_client.post(f"/api/consent-instances/{instance['id']}/paper/pages", token=tenant.dentist_admin.token, files={"file": ("overwrite.pdf", printable.content, "application/pdf")}).status_code == 409
    assert api_client.post(f"/api/consent-instances/{instance['id']}/access-sessions", token=tenant.dentist_admin.token, json={}).status_code == 409
    persisted = db_session.scalar(select(ConsentPaperPacket).where(ConsentPaperPacket.consent_instance_id == UUID(instance["id"])))
    assert persisted and persisted.verification_version == "PAPER_VERIFY_V1" and persisted.original_physical_retention_acknowledged_at


def test_paper_consent_minor_responsible_adult_and_human_relationship(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    responsible = {"full_name": "Tía Responsable Prueba", "document_type": "CC", "document_number": "900011", "relationship_type": "AUNT_UNCLE", "email": "tia@example.test", "phone": "3000000000", "identity_verified": True}
    instance = _prepare_paper(api_client, db_session, tenant, "PAPER-MINOR", signer_policy="RESPONSIBLE_ADULT_REQUIRED", context_changes={"signer_actor_type":"RESPONSIBLE_ADULT", "responsible_adult": responsible, "minor_participation_status":"INFORMED_AND_AGREED"})
    prepared = api_client.post(f"/api/consent-instances/{instance['id']}/paper", token=tenant.dentist_admin.token)
    assert prepared.status_code == 200, prepared.text
    printable = api_client.get(f"/api/consent-instances/{instance['id']}/paper/print-document", token=tenant.dentist_admin.token)
    with fitz.open(stream=printable.content, filetype="pdf") as document:
        text = "\n".join(page.get_text() for page in document)
    assert "Adulto responsable" in text and "Tía Responsable Prueba" in text and "Tío/a" in text and "tutor legal" not in text.casefold()


def test_paper_channel_revokes_electronic_qr_and_enforces_tenant_permissions(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    instance = _prepare_paper(api_client, db_session, tenant, "PAPER-REVOKE")
    issued = api_client.post(f"/api/consent-instances/{instance['id']}/access-sessions", token=tenant.dentist_admin.token, json={})
    assert issued.status_code == 201, issued.text
    public_token = issued.json()["public_url"].rsplit("/", 1)[-1]
    assert api_client.post(f"/api/consent-instances/{instance['id']}/paper", token=tenant.dentist_admin.token).status_code == 200
    assert api_client.get(f"/api/public/consents/{public_token}").status_code == 404
    access = db_session.scalar(select(ConsentAccessSession).where(ConsentAccessSession.consent_instance_id == UUID(instance["id"])))
    assert access and access.status == "REVOKED" and access.revoke_reason == "PAPER_CHANNEL_SELECTED"
    assert api_client.get(f"/api/consent-instances/{instance['id']}/paper", token=security_world.tenant_b.dentist_admin.token).status_code == 404
    assert api_client.get(f"/api/consent-instances/{instance['id']}/paper", token=security_world.platform_admin.token).status_code == 403


def test_paper_rejects_malformed_and_incomplete_digitization(api_client, db_session, security_world):
    tenant=security_world.tenant_a; instance=_prepare_paper(api_client,db_session,tenant,"PAPER-INVALID")
    prepared=api_client.post(f"/api/consent-instances/{instance['id']}/paper",token=tenant.dentist_admin.token).json()
    assert api_client.post(f"/api/consent-instances/{instance['id']}/paper/record-signed",token=tenant.dentist_admin.token,json={"confirmed":True}).status_code==200
    bad=api_client.post(f"/api/consent-instances/{instance['id']}/paper/pages",token=tenant.dentist_admin.token,files={"file":("attack.svg",b"<svg><script>alert(1)</script></svg>","image/svg+xml")})
    assert bad.status_code==422
    corrupt_pdf=api_client.post(f"/api/consent-instances/{instance['id']}/paper/pages",token=tenant.dentist_admin.token,files={"file":("scan.pdf",b"%PDF-corrupt","application/pdf")})
    assert corrupt_pdf.status_code==422
    invalid_image=api_client.post(f"/api/consent-instances/{instance['id']}/paper/pages",token=tenant.dentist_admin.token,files={"file":("scan.png",b"\x89PNG\r\n\x1a\ninvalid","image/png")})
    assert invalid_image.status_code==422
    oversized=api_client.post(f"/api/consent-instances/{instance['id']}/paper/pages",token=tenant.dentist_admin.token,files={"file":("scan.pdf",b"x"*(15*1024*1024+1),"application/pdf")})
    assert oversized.status_code==413
    image=Image.new("RGB",(800,1000),"white");buffer=BytesIO();image.save(buffer,format="JPEG")
    uploaded=api_client.post(f"/api/consent-instances/{instance['id']}/paper/pages",token=tenant.dentist_admin.token,files={"file":("../../patient-name.jpg",buffer.getvalue(),"image/jpeg")})
    assert uploaded.status_code==200 and uploaded.json()["uploaded_page_count"]==1
    stored_page=db_session.scalar(select(ConsentPaperPage).where(ConsentPaperPage.paper_packet_id==UUID(prepared["id"])))
    assert stored_page and "patient-name" not in stored_page.storage_key and ".." not in stored_page.storage_key
    incomplete=api_client.post(f"/api/consent-instances/{instance['id']}/paper/finalize",token=tenant.dentist_admin.token,json=_paper_verification())
    assert incomplete.status_code==422 and str(prepared["expected_page_count"]) in incomplete.text
    confirmations=api_client.post(f"/api/consent-instances/{instance['id']}/paper/finalize",token=tenant.dentist_admin.token,json={**_paper_verification(),"legible":False})
    assert confirmations.status_code==422




def test_legacy_template_is_quarantined_for_new_instances(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _, procedure = _procedure(db_session, tenant)
    legacy_content = "# Consentimiento legacy\n\nTexto del documento fuente\n\n[Página 1]\nPaciente: {{ patient.full_name }}\n\nPaciente o responsable: __________\nFirma: __________"
    version = _template(api_client, tenant.dentist_admin, "LEGACY-NORM4", content=legacy_content)
    context = _context(tenant, procedure)
    candidates = api_client.post("/api/consent-instances/applicable-templates", token=tenant.dentist_admin.token, json=context)
    assert candidates.status_code == 200, candidates.text
    assert version["id"] not in {item["version_id"] for item in candidates.json()["items"]}
    created = api_client.post("/api/consent-instances/batch", token=tenant.dentist_admin.token, json={"context": context, "template_version_ids": [version["id"]]})
    assert created.status_code == 422
    assert "no es aplicable" in created.text

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
    assert all(row["context_snapshot"]["schema_version"] == ACCEPTANCE_CONTEXT_SCHEMA_VERSION for row in rows)
    assert all(row["context_snapshot"]["document"] == {
        "schema_version": ACCEPTANCE_CONTEXT_SCHEMA_VERSION,
        "country": "CO", "country_code": "CO", "locale": "es-CO",
        "jurisdiction_code": "CO_ES_CO", "timezone": "America/Bogota",
    } for row in rows)
    assert all(row["context_snapshot"]["template"]["country_code"] == "CO" and row["context_snapshot"]["template"]["locale"] == "es-CO" for row in rows)
    assert all(row["context_snapshot"]["site"]["country_code"] == "CO" for row in rows)
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
    tenant_a.company.country = "Chile"
    db_session.commit()
    _template(api_client, tenant_a.dentist_admin, "GENERAL-CL", country="CL")
    tenant_a.company.country = "Colombia"
    db_session.commit()
    _template(api_client, tenant_b.dentist_admin, "GENERAL-OTHER-TENANT")
    _template(api_client, tenant_a.dentist_admin, "GENERAL-DRAFT", publish=False)

    retired = _template(api_client, tenant_a.dentist_admin, "GENERAL-RETIRED")
    assert api_client.post(f"/api/consent-templates/{retired['template_id']}/versions/{retired['id']}/retire", token=tenant_a.dentist_admin.token, json={"reason": "Retiro de prueba"}).status_code == 200

    void_template, void_draft = _template(api_client, tenant_a.dentist_admin, "GENERAL-VOIDED", publish=False)
    assert api_client.post(f"/api/consent-templates/{void_template['id']}/versions/{void_draft['id']}/void", token=tenant_a.dentist_admin.token, json={"reason": "Anulación de prueba"}).status_code == 200

    superseded = _template(api_client, tenant_a.dentist_admin, "GENERAL-SUPERSEDED")
    new_draft = api_client.post(f"/api/consent-templates/{superseded['template_id']}/versions/{superseded['id']}/create-draft", token=tenant_a.dentist_admin.token, json={"change_summary": "Versión vigente de prueba"})
    assert new_draft.status_code == 201, new_draft.text
    reviewed = api_client.post(f"/api/consent-templates/{superseded['template_id']}/versions/{new_draft.json()['id']}/review-content", token=tenant_a.dentist_admin.token, json={"confirmed": True})
    assert reviewed.status_code == 200, reviewed.text
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
    monkeypatch.setattr(settings, "public_frontend_url", "https://app.dentiapro.com")
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
    public_path = issued.json()["public_path"]
    assert public_path.startswith("/consentimiento/")
    assert public_url == f"https://app.dentiapro.com{public_path}"
    token = public_url.rsplit("/", 1)[-1]
    assert public_path.rsplit("/", 1)[-1] == token
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
    assert document.json()["is_test_document"] is True
    assert document.json()["test_notice"] == consent_declaration_catalog.TEST_DOCUMENT_NOTICE
    assert document.json()["declaration_set_code"] == "CONSENT_PATIENT_SELF_CO"
    assert document.json()["declaration_set_version"] == "DRAFT_LEGAL_REVIEW_V1"
    assert document.json()["legal_review_status"] == "DRAFT_LEGAL_REVIEW"
    assert "signature" not in document.json() and "accepted" not in document.json()
    clarification = api_client.post(f"/api/public/consents/{token}/clarification", headers={"Cookie": cookie}, json={"message": "Necesito una explicación breve."})
    assert clarification.status_code == 201
    reissued = api_client.post(f"/api/consent-instances/{created['id']}/access-sessions/reissue", token=tenant.dentist_admin.token, json={})
    assert reissued.status_code == 201 and reissued.json()["public_url"] != public_url
    assert api_client.get(f"/api/public/consents/{token}").status_code == 404
    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, f'GET /api/public/consents/{token}', (), None)
    RedactConsentTokenFilter().filter(record)
    assert token not in record.getMessage() and "[REDACTED]" in record.getMessage()


def test_adult_self_acceptance_is_atomic_idempotent_and_tenant_scoped(api_client, db_session, security_world, monkeypatch):
    tenant=security_world.tenant_a; get_test_email_outbox().clear(); _,procedure=_procedure(db_session,tenant); version=_template(api_client,tenant.dentist_admin,"ACCEPTANCE-FLOW"); context=_context(tenant,procedure)
    created=api_client.post("/api/consent-instances/batch",token=tenant.dentist_admin.token,json={"context":context,"template_version_ids":[version["id"]]}).json()[0]
    confirmed=api_client.post(f"/api/consent-instances/{created['id']}/professional-confirm",token=tenant.dentist_admin.token,json={"confirmed":True,"row_version":created["row_version"]}); assert confirmed.status_code==200
    issued=api_client.post(f"/api/consent-instances/{created['id']}/access-sessions",token=tenant.dentist_admin.token,json={}); token=issued.json()["public_url"].rsplit("/",1)[-1]
    assert api_client.post(f"/api/public/consents/{token}/otp").status_code==200
    otp=re.search(r"\b\d{6}\b",get_test_email_outbox()[-1].body).group(0); verified=api_client.post(f"/api/public/consents/{token}/otp/verify",json={"code":otp}); cookie=verified.headers["set-cookie"].split(";",1)[0]
    monkeypatch.setattr(settings,"app_env","production"); assert api_client.get(f"/api/public/consents/{token}/acceptance-requirements",headers={"Cookie":cookie}).status_code==409; monkeypatch.setattr(settings,"app_env","test")
    requirements=api_client.get(f"/api/public/consents/{token}/acceptance-requirements",headers={"Cookie":cookie}); assert requirements.status_code==200
    declarations=requirements.json()["declarations"]; assert declarations and all("accepted" not in item for item in declarations)
    requirements_data=requirements.json(); assert requirements_data["declarations_country_code"]=="CO" and requirements_data["declarations_locale"]=="es-CO" and requirements_data["test_document"] is True
    payload={"idempotency_key":"acceptance-test-key-001","acting_on_own_behalf":True,"declaration_set_code":requirements_data["declaration_set_code"],"declarations_version":requirements_data["declarations_version"],"declarations_set_sha256":requirements_data["declarations_set_sha256"],"declarations":[{"code":item["code"],"accepted":True} for item in declarations],"typed_full_name":requirements_data["patient_name"],"signature_data_url":_signature_data_url()}
    assert api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json={**payload,"acting_on_own_behalf":False}).status_code==422
    assert api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json={**payload,"typed_full_name":"Persona Diferente"}).status_code==422
    assert api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json={**payload,"declarations":payload["declarations"][:-1]}).status_code==422
    assert api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json={**payload,"signature_data_url":"data:image/svg+xml;base64,PHN2Zz48c2NyaXB0Lz48L3N2Zz4="}).status_code==422
    class FailingCopyProvider:
        def send(self,_delivery): raise EmailDeliveryError("simulated copy failure")
    monkeypatch.setattr(consent_acceptance_service,"get_email_provider",lambda:FailingCopyProvider())
    signed=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload); assert signed.status_code==200,signed.text
    result=signed.json(); assert result["status"]=="COMPLETED" and result["copy_delivery_status"]=="FAILED" and len(result["final_document_sha256"])==64 and result["test_document"] is True
    repeated=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload); assert repeated.status_code==200 and repeated.json()["acceptance_id"]==result["acceptance_id"]
    download=api_client.get(repeated.json()["download_url"]); assert download.status_code==200 and download.content.startswith(b"%PDF")
    assert api_client.get(f"/api/public/consents/{token}").status_code==404
    assert api_client.post(f"/api/consent-instances/{created['id']}/access-sessions/reissue",token=tenant.dentist_admin.token,json={}).status_code==409
    instance=db_session.get(ConsentInstance,created["id"]); assert instance.status=="SIGNED" and instance.signed_at
    assert api_client.post(f"/api/consent-instances/{created['id']}/void",token=tenant.dentist_admin.token,json={"reason":"No debe proceder"}).status_code==409
    summary=api_client.get(f"/api/consent-instances/{created['id']}/acceptance",token=tenant.dentist_admin.token); assert summary.status_code==200
    assert api_client.get(f"/api/consent-instances/{created['id']}/acceptance",token=security_world.tenant_b.dentist_admin.token).status_code==404
    assert api_client.get(f"/api/consent-instances/{created['id']}/acceptance/evidence",token=tenant.secretary.token).status_code==403
    final=api_client.get(f"/api/consent-instances/{created['id']}/final-document",token=tenant.secretary.token); assert final.status_code==200 and final.content.startswith(b"%PDF")
    monkeypatch.setattr(consent_acceptance_service,"get_email_provider",configured_email_provider)
    resent=api_client.post(f"/api/consent-instances/{created['id']}/copy-deliveries/resend",token=tenant.secretary.token); assert resent.status_code==200 and resent.json()["status"]=="SENT"


def test_concurrent_acceptance_with_same_key_creates_one_immutable_result(api_client, db_session, security_world):
    created,token,cookie,_,payload=_prepare_acceptance(api_client,db_session,security_world.tenant_a,"REVIEW-CONCURRENT-IDEMPOTENCY")
    payload={**payload,"idempotency_key":"same-browser-submission-act"}
    db_session.expire_all(); version_before_submit=db_session.get(ConsentInstance,created["id"]).row_version
    barrier=Barrier(2)

    def submit_once():
        barrier.wait(timeout=10)
        return api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses=[future.result(timeout=30) for future in [executor.submit(submit_once),executor.submit(submit_once)]]

    assert [response.status_code for response in responses]==[200,200],[response.text for response in responses]
    acceptance_ids={response.json()["acceptance_id"] for response in responses}; assert len(acceptance_ids)==1
    db_session.expire_all()
    acceptance_id=next(iter(acceptance_ids))
    assert db_session.scalar(select(func.count()).select_from(ConsentAcceptance).where(ConsentAcceptance.consent_instance_id==created["id"]))==1
    assert db_session.scalar(select(func.count()).select_from(ConsentSignatureArtifact).where(ConsentSignatureArtifact.acceptance_id==acceptance_id))==1
    assert db_session.scalar(select(func.count()).select_from(ConsentEvidenceManifest).where(ConsentEvidenceManifest.acceptance_id==acceptance_id))==1
    assert db_session.scalar(select(func.count()).select_from(ConsentFinalDocument).where(ConsentFinalDocument.acceptance_id==acceptance_id))==1
    declaration_count=db_session.scalar(select(func.count()).select_from(ConsentAcceptanceDeclaration).where(ConsentAcceptanceDeclaration.acceptance_id==acceptance_id))
    assert declaration_count==len(payload["declarations"])
    instance=db_session.get(ConsentInstance,created["id"]); assert instance.status=="SIGNED" and instance.row_version==version_before_submit+1
    completed_transitions=db_session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.company_id==security_world.tenant_a.company.id,AuditEvent.action=="CONSENT_ACCEPTANCE_COMPLETED"))
    assert completed_transitions==1


def test_safari_canvas_dpr_is_bounded_and_rejected_attempts_are_safe_and_retryable(api_client, db_session, security_world):
    tenant=security_world.tenant_a;tenant.patient.first_names="María José";tenant.patient.last_names="Álvarez";db_session.commit()
    created,token,cookie,requirements,payload=_prepare_acceptance(api_client,db_session,tenant,"REVIEW-SAFARI-CANVAS")
    assert len(requirements["declarations"])==10 and payload["typed_full_name"]=="María José Álvarez"
    payload={**payload,"idempotency_key":"00112233-4455-4677-8899-aabbccddeeff","signature_data_url":_signature_data_url(1920,660)}

    missing_signature=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json={key:value for key,value in payload.items() if key!="signature_data_url"})
    assert missing_signature.status_code==422 and missing_signature.json()=={"detail":{"code":"REQUEST_INVALID","message":"La solicitud de aceptación está incompleta o no es válida."}}

    rejected=[api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload) for _ in range(2)]
    assert all(response.status_code==422 and response.json()["detail"]["code"]=="SIGNATURE_INVALID" for response in rejected)
    db_session.expire_all();instance=db_session.get(ConsentInstance,created["id"]);assert instance.status=="PENDING_SIGNATURE"
    assert db_session.scalar(select(func.count()).select_from(ConsentAcceptance).where(ConsentAcceptance.consent_instance_id==instance.id))==0
    instance_root=Path(settings.consent_final_storage_dir)/str(instance.company_id)/str(instance.id)
    assert not (instance_root/"final").exists() and not list(instance_root.glob(".staging-*"))
    rejection_audits=list(db_session.scalars(select(AuditEvent).where(AuditEvent.entity_id==instance.id,AuditEvent.action=="CONSENT_ACCEPTANCE_REJECTED").order_by(AuditEvent.occurred_at)))
    assert len(rejection_audits)==2
    assert len({row.detail["idempotency_key_sha256"] for row in rejection_audits})==1
    assert all(row.detail["category"]=="SIGNATURE_INVALID" and row.detail["width"]==1920 and row.detail["height"]==660 and row.detail["declared_mime"]=="image/png" for row in rejection_audits)
    assert all("signature_data_url" not in row.detail and "typed_full_name" not in row.detail for row in rejection_audits)

    valid_retry=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json={**payload,"signature_data_url":_signature_data_url(1280,440)})
    assert valid_retry.status_code==200,valid_retry.text
    db_session.expire_all();instance=db_session.get(ConsentInstance,created["id"]);assert instance.status=="SIGNED"
    acceptance=db_session.scalar(select(ConsentAcceptance).where(ConsentAcceptance.consent_instance_id==instance.id));assert acceptance and acceptance.idempotency_key==payload["idempotency_key"]
    assert db_session.scalar(select(func.count()).select_from(ConsentSignatureArtifact).where(ConsentSignatureArtifact.acceptance_id==acceptance.id))==1
    assert db_session.scalar(select(func.count()).select_from(ConsentEvidenceManifest).where(ConsentEvidenceManifest.acceptance_id==acceptance.id))==1
    assert db_session.scalar(select(func.count()).select_from(ConsentFinalDocument).where(ConsentFinalDocument.acceptance_id==acceptance.id))==1


def test_signature_contract_requires_png_data_url_and_derives_real_dimensions():
    valid_data_url=_signature_data_url(1280,440);raw,width,height=consent_acceptance_service._decode_signature(valid_data_url)
    assert raw.startswith(b"\x89PNG\r\n\x1a\n") and (width,height)==(1280,440)
    with pytest.raises(consent_acceptance_service.ConsentAcceptanceError) as raw_base64:
        consent_acceptance_service._decode_signature(valid_data_url.split(",",1)[1])
    assert raw_base64.value.code=="SIGNATURE_INVALID"


def test_declaration_sets_are_exactly_bound_to_country_locale_and_legal_status(api_client, db_session, security_world, monkeypatch):
    co=_prepare_acceptance(api_client,db_session,security_world.tenant_a,"REVIEW-CO")[3]
    tenant_cl=security_world.tenant_b;tenant_cl.company.country="Chile";tenant_cl.site_1.timezone="America/Santiago";db_session.commit()
    cl=_prepare_acceptance(api_client,db_session,tenant_cl,"REVIEW-CL",country="CL")[3]
    assert (co["declarations_country_code"],co["declarations_locale"],co["declaration_set_code"])==("CO","es-CO","CONSENT_PATIENT_SELF_CO")
    assert (cl["declarations_country_code"],cl["declarations_locale"],cl["declaration_set_code"])==("CL","es-CL","CONSENT_PATIENT_SELF_CL")
    assert co["declarations_set_sha256"]!=cl["declarations_set_sha256"] and co["declarations"]!=cl["declarations"]
    with pytest.raises(consent_declaration_catalog.ConsentDeclarationSetError): consent_declaration_catalog.declaration_set_for("CO","es-CL",app_env="test",acceptance_enabled=True,on_date=date.today())
    with pytest.raises(consent_declaration_catalog.ConsentDeclarationSetError): consent_declaration_catalog.declaration_set_for("ZZ","es-ZZ",app_env="test",acceptance_enabled=True,on_date=date.today())
    retired=replace(consent_declaration_catalog.CO_DRAFT,legal_status="RETIRED")
    monkeypatch.setitem(consent_declaration_catalog.DECLARATION_SETS,("CO","es-CO"),retired)
    with pytest.raises(consent_declaration_catalog.ConsentDeclarationSetError): consent_declaration_catalog.declaration_set_for("CO","es-CO",app_env="test",acceptance_enabled=True,on_date=date.today())
    approved=replace(consent_declaration_catalog.CO_DRAFT,code="CONSENT_PATIENT_SELF_CO_APPROVED_TEST",version="APPROVED_TEST_V1",legal_status="APPROVED",effective_from=date.today())
    monkeypatch.setitem(consent_declaration_catalog.DECLARATION_SETS,("CO","es-CO"),approved)
    assert consent_declaration_catalog.declaration_set_for("CO","es-CO",app_env="test",acceptance_enabled=True,on_date=date.today()).is_test_document is True


@pytest.mark.parametrize("legacy_mutation", ["missing_country", "missing_locale", "previous_schema"])
def test_legacy_acceptance_context_is_blocked_without_mutating_sealed_snapshot(api_client, db_session, security_world, legacy_mutation):
    tenant=security_world.tenant_a;get_test_email_outbox().clear();_,procedure=_procedure(db_session,tenant)
    version=_template(api_client,tenant.dentist_admin,f"LEGACY-{legacy_mutation}")
    created=api_client.post("/api/consent-instances/batch",token=tenant.dentist_admin.token,json={"context":_context(tenant,procedure),"template_version_ids":[version["id"]]}).json()[0]
    instance=db_session.get(ConsentInstance,created["id"]);snapshot=deepcopy(instance.context_snapshot)
    if legacy_mutation=="missing_country": snapshot["document"].pop("country")
    elif legacy_mutation=="missing_locale": snapshot["document"].pop("locale")
    else: snapshot["schema_version"]="C019A3_V1"
    instance.context_snapshot=snapshot;db_session.commit()
    confirmed=api_client.post(f"/api/consent-instances/{created['id']}/professional-confirm",token=tenant.dentist_admin.token,json={"confirmed":True,"row_version":created["row_version"]});assert confirmed.status_code==200,confirmed.text
    private=confirmed.json();assert private["acceptance_compatible"] is False and private["acceptance_block_code"]==LEGACY_ACCEPTANCE_CONTEXT_UNSUPPORTED
    assert "Debe crearse una nueva instancia" in private["acceptance_block_message"] and "documento histórico no será modificado" in private["acceptance_block_message"]
    db_session.expire_all();sealed=db_session.get(ConsentInstance,created["id"]);before_snapshot=deepcopy(sealed.context_snapshot);before_hashes=(sealed.context_sha256,sealed.integrity_hash)
    issued=api_client.post(f"/api/consent-instances/{created['id']}/access-sessions",token=tenant.dentist_admin.token,json={});token=issued.json()["public_url"].rsplit("/",1)[-1]
    assert api_client.post(f"/api/public/consents/{token}/otp").status_code==200
    otp=re.search(r"\b\d{6}\b",get_test_email_outbox()[-1].body).group(0);verified=api_client.post(f"/api/public/consents/{token}/otp/verify",json={"code":otp});cookie=verified.headers["set-cookie"].split(";",1)[0]
    document=api_client.get(f"/api/public/consents/{token}/document",headers={"Cookie":cookie});assert document.status_code==200
    public=document.json();assert public["acceptance_compatible"] is False and public["acceptance_block_message"]==PUBLIC_LEGACY_MESSAGE
    assert public["is_test_document"] is True and public["test_notice"]==consent_declaration_catalog.TEST_DOCUMENT_NOTICE
    assert all(term not in public["acceptance_block_message"].casefold() for term in ["jurisdicción sellada","schema","hash","context_snapshot"])
    blocked=api_client.get(f"/api/public/consents/{token}/acceptance-requirements",headers={"Cookie":cookie});assert blocked.status_code==409 and blocked.json()["detail"]==PUBLIC_LEGACY_MESSAGE
    db_session.expire_all();unchanged=db_session.get(ConsentInstance,created["id"])
    assert unchanged.context_snapshot==before_snapshot and (unchanged.context_sha256,unchanged.integrity_hash)==before_hashes and unchanged.status=="PENDING_SIGNATURE"


def test_incompatible_country_locale_and_live_master_changes_cannot_repair_sealed_context(api_client, db_session, security_world):
    tenant=security_world.tenant_a;get_test_email_outbox().clear();_,procedure=_procedure(db_session,tenant)
    version=_template(api_client,tenant.dentist_admin,"SEALED-CO-ESCL")
    created=api_client.post("/api/consent-instances/batch",token=tenant.dentist_admin.token,json={"context":_context(tenant,procedure),"template_version_ids":[version["id"]]}).json()[0]
    instance=db_session.get(ConsentInstance,created["id"]);snapshot=deepcopy(instance.context_snapshot);snapshot["document"]["locale"]="es-CL";snapshot["template"]["locale"]="es-CL";instance.context_snapshot=snapshot;instance.language_code="es-CL";db_session.commit()
    confirmed=api_client.post(f"/api/consent-instances/{created['id']}/professional-confirm",token=tenant.dentist_admin.token,json={"confirmed":True,"row_version":created["row_version"]});assert confirmed.status_code==200
    db_session.expire_all();sealed=db_session.get(ConsentInstance,created["id"]);snapshot_before=deepcopy(sealed.context_snapshot);hashes_before=(sealed.context_sha256,sealed.integrity_hash)
    tenant.company.country="Chile";tenant.site_1.timezone="America/Santiago";tenant.patient.first_names="Paciente maestro cambiado";db_session.commit()
    issued=api_client.post(f"/api/consent-instances/{created['id']}/access-sessions",token=tenant.dentist_admin.token,json={})
    assert issued.status_code==409
    assert "declaraciones" in issued.json()["detail"]
    db_session.expire_all();unchanged=db_session.get(ConsentInstance,created["id"]);assert unchanged.context_snapshot==snapshot_before and (unchanged.context_sha256,unchanged.integrity_hash)==hashes_before


def test_age_and_identity_use_sealed_snapshot_with_site_timezone(api_client, db_session, security_world):
    tenant=security_world.tenant_a;today=datetime.now(ZoneInfo("America/Bogota")).date();tenant.patient.birth_date=today.replace(year=today.year-18);original_name=f"{tenant.patient.first_names} {tenant.patient.last_names}";db_session.commit()
    def mutate_master():
        tenant.patient.birth_date=today.replace(year=today.year-17);tenant.patient.first_names="Nombre Maestro Cambiado";db_session.commit()
    created,token,cookie,requirements,payload=_prepare_acceptance(api_client,db_session,tenant,"REVIEW-AGE-SNAPSHOT",before_requirements=mutate_master)
    assert requirements["patient_name"]==original_name
    payload["typed_full_name"]="  paciente   á seguridad  "
    signed=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload);assert signed.status_code==200,signed.text
    acceptance=db_session.scalar(select(ConsentAcceptance).where(ConsentAcceptance.consent_instance_id==created["id"]));assert acceptance.patient_birth_date_snapshot==today.replace(year=today.year-18) and acceptance.patient_name_snapshot==original_name


def test_changed_email_after_otp_is_not_used_for_acceptance_or_delivery(api_client, db_session, security_world):
    tenant=security_world.tenant_a
    def change_email(): tenant.patient.email="otro-destinatario@example.test";tenant.patient.normalized_email=tenant.patient.email;db_session.commit()
    _,token,cookie,_,payload=_prepare_acceptance(api_client,db_session,tenant,"REVIEW-FROZEN-EMAIL",before_requirements=change_email)
    accepted=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload);assert accepted.status_code==200, accepted.text
    assert get_test_email_outbox()[-1].recipient != "otro-destinatario@example.test"


@pytest.mark.parametrize("birth_mode",["seventeen","missing","future"])
def test_invalid_or_missing_sealed_birth_date_blocks_acceptance(api_client, db_session, security_world, birth_mode):
    tenant=security_world.tenant_a;today=datetime.now(ZoneInfo("America/Bogota")).date()
    tenant.patient.birth_date={"seventeen":today.replace(year=today.year-17),"missing":None,"future":today+timedelta(days=30)}[birth_mode];db_session.commit()
    if birth_mode == "seventeen":
        _,procedure=_procedure(db_session,tenant)
        version=_template(api_client,tenant.dentist_admin,f"REVIEW-AGE-{birth_mode}",content="# Documento\n\nPaciente: {{ patient.full_name }}")
        response=api_client.post("/api/consent-instances/batch",token=tenant.dentist_admin.token,json={"context":_context(tenant,procedure),"template_version_ids":[version["id"]]})
        assert response.status_code == 422
    else:
        _prepare_acceptance(api_client,db_session,tenant,f"REVIEW-AGE-{birth_mode}",content="# Documento\n\nPaciente: {{ patient.full_name }}",expected_requirements_status=422)


@pytest.mark.parametrize("failure_point",["PDF_GENERATED","SIGNATURE_STORED","PDF_STORED","MANIFEST_STORED","HASH_VERIFIED","DB_PERSISTED","BEFORE_DB_COMMIT"])
def test_storage_and_db_failures_compensate_and_allow_idempotent_retry(api_client, db_session, security_world, monkeypatch, failure_point):
    created,token,cookie,_,payload=_prepare_acceptance(api_client,db_session,security_world.tenant_a,f"REVIEW-FAIL-{failure_point}")
    original_hook=consent_acceptance_service._failure_point
    def fail_here(name):
        if name==failure_point: raise OSError(f"injected {name}")
    monkeypatch.setattr(consent_acceptance_service,"_failure_point",fail_here)
    failed=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload);assert failed.status_code==500
    db_session.rollback();db_session.expire_all();instance=db_session.get(ConsentInstance,created["id"]);assert instance.status=="PENDING_SIGNATURE"
    assert db_session.scalar(select(ConsentAcceptance).where(ConsentAcceptance.consent_instance_id==instance.id)) is None
    instance_root=Path(settings.consent_final_storage_dir)/str(instance.company_id)/str(instance.id);assert not (instance_root/"final").exists() and not list(instance_root.glob(".staging-*"))
    if failure_point=="BEFORE_DB_COMMIT":
        (instance_root/"final").mkdir(parents=True);(instance_root/"final"/"orphan.tmp").write_text("orphan",encoding="utf-8")
    monkeypatch.setattr(consent_acceptance_service,"_failure_point",original_hook)
    retried=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload);assert retried.status_code==200,retried.text
    assert not (instance_root/"final"/"orphan.tmp").exists()
    assert len(list(db_session.scalars(select(ConsentAcceptance).where(ConsentAcceptance.consent_instance_id==instance.id))))==1


def test_test_pdf_manifest_email_and_professional_semantics(api_client, db_session, security_world):
    long_content="# Documento de prueba\n\n## Riesgos\n\n- Riesgo ficticio\n\n---\n\n"+("Contenido clínico ficticio para validación técnica.\n\n"*180)
    created,token,cookie,_,payload=_prepare_acceptance(api_client,db_session,security_world.tenant_a,"REVIEW-PDF-MARK",content=long_content)
    signed=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload);assert signed.status_code==200,signed.text
    final=api_client.get(signed.json()["download_url"]);assert final.status_code==200
    page_count=final.content.count(b"/Type /Page")-final.content.count(b"/Type /Pages");assert page_count>=2 and final.content.count(b"DOCUMENTO DE PRUEBA")>=page_count
    with fitz.open(stream=final.content,filetype="pdf") as pdf_document:
        final_text="\n".join(page.get_text() for page in pdf_document)
    assert consent_acceptance_service.ELECTRONIC_TRACEABILITY_NOTICE in final_text
    assert "pendiente de revisión jurídica" not in final_text
    assert "no constituye una afirmación de validez legal" not in final_text
    assert b"# Documento de prueba" not in final.content and b"## Riesgos" not in final.content
    assert b"Profesional que confirm" in final.content and b"Firmado por el odont" not in final.content and b"Firma electr" not in final.content
    evidence=api_client.get(f"/api/consent-instances/{created['id']}/acceptance/evidence",token=security_world.tenant_a.dentist_admin.token).json()["manifest"]
    assert evidence["test_document"] is True and evidence["test_notice"]==consent_declaration_catalog.TEST_DOCUMENT_NOTICE
    assert evidence["branding_snapshot"]["company"]["name"]==security_world.tenant_a.company.name
    assert evidence["branding_snapshot"]["sha256"]
    assert evidence["professional_role"]=="REVIEWED_CONTENT" and evidence["declaration_set"]["country_code"]=="CO"
    delivery=get_test_email_outbox()[-1];assert delivery.subject.startswith("[PRUEBA]") and consent_declaration_catalog.TEST_DOCUMENT_NOTICE in delivery.body


def test_final_pdf_freezes_tenant_branding_logo_and_does_not_regenerate(api_client, db_session, security_world):
    tenant=security_world.tenant_a
    logo_path=_install_test_logo(tenant.company)
    tenant.company.legal_name="Dentia Servicios Odontológicos S.A.S."
    tenant.company.website="https://dentia.example.test"
    tenant.company.footer_text="Atención odontológica con cita previa"
    db_session.commit()
    created,token,cookie,_,payload=_prepare_acceptance(api_client,db_session,tenant,"REVIEW-FROZEN-BRANDING")
    signed=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload);assert signed.status_code==200,signed.text
    first=api_client.get(signed.json()["download_url"]);assert first.status_code==200
    evidence_before=api_client.get(f"/api/consent-instances/{created['id']}/acceptance/evidence",token=tenant.dentist_admin.token).json()
    branding=evidence_before["manifest"]["branding_snapshot"]
    assert evidence_before["schema_version"]=="1.2"
    assert branding["company"]["name"]==tenant.company.name
    assert branding["company"]["legal_name"]=="Dentia Servicios Odontológicos S.A.S."
    assert branding["logo"]["validation"]=="VALID" and branding["logo"]["rendered"] is True
    assert branding["logo"]["mime_type"]=="image/png" and branding["logo"]["width"]==640 and branding["logo"]["height"]==220
    assert branding["logo"]["sha256"]==consent_acceptance_service._sha_bytes(logo_path.read_bytes())
    assert b"/Subtype /Image" in first.content
    frozen_pdf=first.content;frozen_manifest=evidence_before["manifest"]
    tenant.company.name="Identidad institucional posterior"
    tenant.company.footer_text="Pie posterior"
    replacement=Image.new("RGB",(320,120),"#991b1b");replacement.save(logo_path,format="PNG")
    db_session.commit()
    second=api_client.get(signed.json()["download_url"]);assert second.status_code==200 and second.content==frozen_pdf
    evidence_after=api_client.get(f"/api/consent-instances/{created['id']}/acceptance/evidence",token=tenant.dentist_admin.token).json()["manifest"]
    assert evidence_after==frozen_manifest


def test_cross_tenant_logo_path_is_rejected_and_pdf_uses_typographic_fallback(api_client, db_session, security_world):
    tenant_a=security_world.tenant_a;tenant_b=security_world.tenant_b
    other_logo=_install_test_logo(tenant_b.company,color="#1d4ed8")
    tenant_a.company.logo_path=f"{tenant_b.company.id}/{other_logo.name}";tenant_a.company.logo_filename="otro-tenant.png";db_session.commit()
    created,token,cookie,_,payload=_prepare_acceptance(api_client,db_session,tenant_a,"REVIEW-TENANT-BRANDING")
    signed=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload);assert signed.status_code==200,signed.text
    evidence=api_client.get(f"/api/consent-instances/{created['id']}/acceptance/evidence",token=tenant_a.dentist_admin.token).json()["manifest"]
    assert evidence["branding_snapshot"]["logo"]["validation"]=="TENANT_PATH_MISMATCH"
    assert evidence["branding_snapshot"]["logo"]["rendered"] is False


def test_branding_snapshot_handles_missing_and_invalid_logo_without_failing(db_session, security_world):
    tenant=security_world.tenant_a
    tenant.company.logo_path=f"{tenant.company.id}/missing.png";tenant.company.logo_filename="missing.png"
    missing,_=consent_acceptance_service._branding_snapshot(tenant.company,tenant.site_1)
    assert missing["logo"]["validation"]=="FILE_NOT_FOUND" and missing["logo"]["rendered"] is False
    directory=Path(settings.branding_storage_dir)/str(tenant.company.id);directory.mkdir(parents=True,exist_ok=True)
    invalid=directory/"invalid.png";invalid.write_bytes(b"not-an-image")
    tenant.company.logo_path=f"{tenant.company.id}/{invalid.name}";tenant.company.logo_filename="invalid.png"
    snapshot,raw=consent_acceptance_service._branding_snapshot(tenant.company,tenant.site_1)
    assert raw is None and snapshot["logo"]["validation"]=="INVALID_IMAGE"
    assert snapshot["logo"]["sha256"]==consent_acceptance_service._sha_bytes(invalid.read_bytes())


def test_pdf_markdown_skips_empty_headings_and_first_duplicated_title():
    base=getSampleStyleSheet();body=ParagraphStyle("ConsentTestBody",parent=base["BodyText"]);heading=ParagraphStyle("ConsentTestHeading",parent=base["Heading2"])
    story=consent_acceptance_service._pdf_markdown_story("# Consentimiento ficticio\n\n#\n##   \n###\n\n## Riesgos\n\n- **Elemento seguro**\n\n---\n\n<script>alert('x')</script>",body,heading,skip_first_heading="Consentimiento ficticio")
    texts=[item.getPlainText() for item in story if hasattr(item,"getPlainText")]
    assert texts==["Riesgos","• Elemento seguro","<script>alert('x')</script>"]
    assert sum(item.__class__.__name__=="HRFlowable" for item in story)==1


def test_pdf_human_dates_use_sealed_timezone_and_spanish_locale():
    value=datetime(2026,8,1,19,5,tzinfo=timezone.utc)
    assert consent_acceptance_service._human_datetime(value,"America/Bogota","es-CO")=="1 de agosto de 2026, 2:05 p. m."
    assert consent_acceptance_service._human_datetime(value,"America/Santiago","es-CL")=="1 de agosto de 2026, 3:05 p. m."


def test_local_approved_set_still_generates_test_mark(api_client, db_session, security_world, monkeypatch):
    tenant=security_world.tenant_a
    clinical_today=local_clinical_date(tenant.company,tenant.site_1)
    approved=replace(consent_declaration_catalog.CO_DRAFT,code="CONSENT_PATIENT_SELF_CO_APPROVED_TEST",version="APPROVED_TEST_V1",legal_status="APPROVED",effective_from=clinical_today)
    monkeypatch.setitem(consent_declaration_catalog.DECLARATION_SETS,("CO","es-CO"),approved)
    created,token,cookie,requirements,payload=_prepare_acceptance(api_client,db_session,tenant,"REVIEW-APPROVED-NO-MARK")
    document=api_client.get(f"/api/public/consents/{token}/document",headers={"Cookie":cookie}).json();assert document["is_test_document"] is True and document["test_notice"]==consent_declaration_catalog.TEST_DOCUMENT_NOTICE and document["legal_review_status"]=="APPROVED"
    assert requirements["test_document"] is True and requirements["declarations_legal_status"]=="APPROVED"
    signed=api_client.post(f"/api/public/consents/{token}/acceptance",headers={"Cookie":cookie},json=payload);assert signed.status_code==200,signed.text
    final=api_client.get(signed.json()["download_url"])
    final_text="\n".join(page.get_text() for page in fitz.open(stream=final.content,filetype="pdf"))
    assert "DOCUMENTO DE PRUEBA" in final_text
    summary=api_client.get(f"/api/consent-instances/{created['id']}/acceptance",token=security_world.tenant_a.dentist_admin.token).json();assert summary["test_document"] is True


def test_signer1_responsible_adult_relationships_and_minor_policy():
    from datetime import date
    from types import SimpleNamespace
    from uuid import uuid4

    from app.models.agenda import Patient
    from app.services.consent_signer import (
        MINOR_PARTICIPATION_LABELS,
        RELATIONSHIP_LABELS,
        RESPONSIBLE_ADULT,
        minor_participation_label,
        resolve_signer_snapshot,
        responsible_relationship_label,
    )

    assert RELATIONSHIP_LABELS == {
        "MOTHER": "Madre", "FATHER": "Padre", "SIBLING": "Hermano/a", "GRANDPARENT": "Abuelo/a",
        "AUNT_UNCLE": "Tío/a", "COUSIN": "Primo/a", "CAREGIVER": "Cuidador/a", "NEIGHBOR": "Vecino/a",
        "LEGAL_REPRESENTATIVE": "Representante legal", "OTHER": "Otro",
    }
    assert MINOR_PARTICIPATION_LABELS == {
        "INFORMED_AND_AGREED": "Informado y de acuerdo",
        "INFORMED_NO_OBJECTION": "Informado, sin manifestar oposición",
        "COULD_NOT_EXPRESS_DUE_TO_AGE_OR_CONDITION": "No fue posible obtener manifestación por edad o condición",
        "NOT_APPLICABLE": "No aplica",
        "OTHER": "Otro",
    }
    assert responsible_relationship_label("AUNT_UNCLE") == "Tío/a"
    assert minor_participation_label("OTHER", "  Explicación saneada  ") == "Otro: Explicación saneada"

    patient = Patient(
        id=uuid4(),
        company_id=uuid4(),
        first_names="Niña",
        last_names="Paciente",
        document_type="TI",
        document="1001",
        mobile="3000000000",
        birth_date=date(date.today().year - 8, 1, 1),
        email="menor@example.com",
    )
    base = dict(
        patient_responsible_id=None,
        full_name="Adulto Responsable",
        document_type="CC",
        document_number="9001",
        email="adulto@example.com",
        phone="3001112233",
        identity_verified=True,
        relationship_other=None,
    )
    for relationship in ["MOTHER", "FATHER", "SIBLING", "GRANDPARENT", "AUNT_UNCLE", "COUSIN", "CAREGIVER", "NEIGHBOR", "LEGAL_REPRESENTATIVE"]:
        payload = SimpleNamespace(**base, relationship_type=relationship)
        context = SimpleNamespace(responsible_adult=payload, minor_participation_status="INFORMED_NO_OBJECTION", minor_participation_observation=None)
        signer = resolve_signer_snapshot(None, company_id=patient.company_id, patient=patient, payload_context=context, policy="RESPONSIBLE_ADULT_REQUIRED", actor_type=RESPONSIBLE_ADULT, verified_by_user_id=uuid4())
        assert signer.actor_type == RESPONSIBLE_ADULT
        assert signer.relationship_type == relationship
        assert signer.relationship_label == RELATIONSHIP_LABELS[relationship]
    other_base = {**base, "relationship_other": "Acudiente autorizado por la familia"}
    payload = SimpleNamespace(**other_base, relationship_type="OTHER")
    context = SimpleNamespace(responsible_adult=payload, minor_participation_status="OTHER", minor_participation_observation="La menor escuchó la explicación con apoyo del adulto.")
    signer = resolve_signer_snapshot(None, company_id=patient.company_id, patient=patient, payload_context=context, policy="PATIENT_OR_RESPONSIBLE_ADULT", actor_type=RESPONSIBLE_ADULT, verified_by_user_id=uuid4())
    assert signer.relationship_other == "Acudiente autorizado por la familia"
    assert signer.minor_participation_status == "OTHER"


def test_signer1_responsible_adult_acceptance_uses_human_labels_and_pdf_participation(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    tenant.patient.birth_date = date(2016, 8, 2)
    tenant.patient.document_type = "TI"
    db_session.commit()
    context_changes = {
        "signer_actor_type": "RESPONSIBLE_ADULT",
        "responsible_adult": {
            "patient_responsible_id": None,
            "full_name": "Tía Ficticia",
            "document_type": "CC",
            "document_number": "900000099",
            "relationship_type": "AUNT_UNCLE",
            "relationship_other": None,
            "email": "tia-ficticia@example.com",
            "phone": "3009998877",
            "identity_verified": True,
        },
        "minor_participation_status": "INFORMED_AND_AGREED",
        "minor_participation_observation": None,
    }
    created, token, cookie, requirements, payload = _prepare_acceptance(
        api_client,
        db_session,
        tenant,
        "SIGNER1-HUMAN-PDF-LABELS",
        signer_policy="RESPONSIBLE_ADULT_REQUIRED",
        context_changes=context_changes,
    )

    assert requirements["signer_relationship"] == "Tío/a"
    signed = api_client.post(f"/api/public/consents/{token}/acceptance", headers={"Cookie": cookie}, json=payload)
    assert signed.status_code == 200, signed.text
    summary = api_client.get(f"/api/consent-instances/{created['id']}/acceptance", token=tenant.dentist_admin.token)
    assert summary.status_code == 200
    assert summary.json()["signer_relationship"] == "Tío/a"
    acceptance = db_session.scalar(select(ConsentAcceptance).where(ConsentAcceptance.consent_instance_id == UUID(created["id"])))
    assert consent_acceptance_service._acceptance_human_labels(acceptance) == ("Tío/a", "Informado y de acuerdo")
    final = api_client.get(signed.json()["download_url"])
    assert final.status_code == 200 and final.content.startswith(b"%PDF")
    with fitz.open(stream=final.content, filetype="pdf") as pdf_document:
        pdf_text = "\n".join(page.get_text() for page in pdf_document)
    assert "Relación con el paciente" in pdf_text
    assert "Tío/a" in pdf_text
    assert "AUNT_UNCLE" not in pdf_text
    assert "Participación del menor" in pdf_text
    assert "Informado y de acuerdo" in pdf_text
    assert consent_acceptance_service.ELECTRONIC_TRACEABILITY_NOTICE in pdf_text
    assert "pendiente de revisión jurídica" not in pdf_text
    assert "no constituye una afirmación de validez legal" not in pdf_text
    assert acceptance.signer_relationship_type_snapshot == "AUNT_UNCLE"


def test_signer1_minor_cannot_use_patient_self_and_other_requires_description():
    from datetime import date
    from types import SimpleNamespace
    from uuid import uuid4

    import pytest

    from app.models.agenda import Patient
    from app.services.consent_signer import resolve_signer_snapshot

    patient = Patient(
        id=uuid4(),
        company_id=uuid4(),
        first_names="Niño",
        last_names="Paciente",
        document_type="TI",
        document="1002",
        mobile="3000000000",
        birth_date=date(date.today().year - 7, 1, 1),
        email="menor2@example.com",
    )
    context = SimpleNamespace(responsible_adult=None, minor_participation_status=None, minor_participation_observation=None)
    with pytest.raises(ValueError, match="menores de edad"):
        resolve_signer_snapshot(None, company_id=patient.company_id, patient=patient, payload_context=context, policy="PATIENT_OR_RESPONSIBLE_ADULT", actor_type="PATIENT_SELF", verified_by_user_id=uuid4())
    payload = SimpleNamespace(patient_responsible_id=None, full_name="Adulto", document_type="CC", document_number="1", relationship_type="OTHER", relationship_other=None, email="adulto@example.com", phone="300", identity_verified=True)
    context = SimpleNamespace(responsible_adult=payload, minor_participation_status="INFORMED_NO_OBJECTION", minor_participation_observation=None)
    with pytest.raises(ValueError, match="describirla"):
        resolve_signer_snapshot(None, company_id=patient.company_id, patient=patient, payload_context=context, policy="RESPONSIBLE_ADULT_REQUIRED", actor_type="RESPONSIBLE_ADULT", verified_by_user_id=uuid4())


def test_signer1_minor_aunt_uncle_creates_canonical_snapshots_and_minimal_audits(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    tenant.patient.birth_date = date(2016, 8, 2)
    tenant.patient.document_type = "TI"
    db_session.commit()
    _, procedure = _procedure(db_session, tenant)
    published = _template(api_client, tenant.dentist_admin, "SIGNER1-AUNT-UNCLE")
    _set_template_signer_policy(db_session, published["id"], "RESPONSIBLE_ADULT_REQUIRED")
    context = _context(
        tenant,
        procedure,
        signer_actor_type="RESPONSIBLE_ADULT",
        responsible_adult={
            "patient_responsible_id": None,
            "full_name": "Adulta Ficticia",
            "document_type": "CC",
            "document_number": "900000001",
            "relationship_type": "AUNT_UNCLE",
            "relationship_other": None,
            "email": "adulta-ficticia@example.com",
            "phone": "3001112233",
            "identity_verified": True,
        },
        minor_participation_status="INFORMED_AND_AGREED",
        minor_participation_observation="La paciente menor comprendió la explicación.",
    )

    response = api_client.post(
        "/api/consent-instances/batch",
        token=tenant.dentist_admin.token,
        json={"context": context, "template_version_ids": [published["id"]]},
    )

    assert response.status_code == 201, response.text
    body = response.json()[0]
    assert body["signer_policy"] == "RESPONSIBLE_ADULT_REQUIRED"
    assert body["signer_actor_type"] == "RESPONSIBLE_ADULT"
    assert body["responsible_adult"]["relationship_type"] == "AUNT_UNCLE"
    assert body["minor_participation_status"] == "INFORMED_AND_AGREED"
    instance = db_session.get(ConsentInstance, UUID(body["id"]))
    assert instance is not None
    assert instance.signer_relationship_type_snapshot == "AUNT_UNCLE"
    assert instance.signer_relationship_other_snapshot is None
    assert instance.minor_participation_status == "INFORMED_AND_AGREED"
    responsible = db_session.scalar(
        select(ConsentResponsibleAdult).where(
            ConsentResponsibleAdult.consent_instance_id == instance.id
        )
    )
    assert responsible is not None
    assert responsible.relationship_type == "AUNT_UNCLE"
    assert responsible.patient_responsible_id is None
    assert db_session.scalar(
        select(func.count()).select_from(ConsentInstanceProcedure).where(
            ConsentInstanceProcedure.instance_id == instance.id
        )
    ) == 1
    audits = list(
        db_session.scalars(
            select(AuditEvent).where(AuditEvent.entity_id == instance.id)
        )
    )
    actions = {item.action for item in audits}
    assert {
        "CONSENT_SIGNER_MODE_SELECTED",
        "RESPONSIBLE_ADULT_SELECTED",
        "RESPONSIBLE_ADULT_CREATED",
        "RESPONSIBLE_ADULT_IDENTITY_CONFIRMED",
        "MINOR_PARTICIPATION_RECORDED",
    }.issubset(actions)
    created_audit = next(
        item for item in audits if item.action == "RESPONSIBLE_ADULT_CREATED"
    )
    assert created_audit.detail["relationship_type"] == "AUNT_UNCLE"
    serialized_audits = json.dumps(
        [item.detail for item in audits], ensure_ascii=False, default=str
    )
    for sensitive_value in [
        "Adulta Ficticia",
        "900000001",
        "adulta-ficticia@example.com",
        "3001112233",
    ]:
        assert sensitive_value not in serialized_audits


def test_signer1_batch_failure_rolls_back_instances_responsible_adults_procedures_and_audits(api_client, db_session, security_world, monkeypatch, caplog):
    tenant = security_world.tenant_a
    tenant.patient.birth_date = date(2016, 8, 2)
    db_session.commit()
    _, procedure = _procedure(db_session, tenant)
    first = _template(api_client, tenant.dentist_admin, "SIGNER1-ATOMIC-FIRST")
    second = _template(api_client, tenant.dentist_admin, "SIGNER1-ATOMIC-SECOND")
    _set_template_signer_policy(db_session, first["id"], "RESPONSIBLE_ADULT_REQUIRED")
    _set_template_signer_policy(db_session, second["id"], "RESPONSIBLE_ADULT_REQUIRED")
    context = _context(
        tenant,
        procedure,
        signer_actor_type="RESPONSIBLE_ADULT",
        responsible_adult={
            "patient_responsible_id": None,
            "full_name": "Responsable Atómica",
            "document_type": "CC",
            "document_number": "900000002",
            "relationship_type": "MOTHER",
            "relationship_other": None,
            "email": "responsable-atomica@example.com",
            "phone": "3002223344",
            "identity_verified": True,
        },
        minor_participation_status="INFORMED_AND_AGREED",
    )
    company_filter = (ConsentInstance.company_id == tenant.company.id,)
    before = {
        "instances": db_session.scalar(select(func.count()).select_from(ConsentInstance).where(*company_filter)),
        "responsible": db_session.scalar(select(func.count()).select_from(ConsentResponsibleAdult).where(ConsentResponsibleAdult.company_id == tenant.company.id)),
        "procedures": db_session.scalar(select(func.count()).select_from(ConsentInstanceProcedure).where(ConsentInstanceProcedure.company_id == tenant.company.id)),
        "audits": db_session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.company_id == tenant.company.id, AuditEvent.entity == "consent_instance")),
    }
    original_create_one = consent_instance_service._create_one
    calls = 0

    def fail_on_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected atomic batch failure")
        return original_create_one(*args, **kwargs)

    monkeypatch.setattr(consent_instance_service, "_create_one", fail_on_second)
    with caplog.at_level(logging.ERROR, logger=consent_instance_service.__name__):
        response = api_client.post(
            "/api/consent-instances/batch",
            token=tenant.dentist_admin.token,
            json={
                "context": context,
                "template_version_ids": [first["id"], second["id"]],
            },
        )

    assert response.status_code == 500
    assert "Traceback" not in response.text
    assert "injected atomic batch failure" not in response.text
    assert any(
        "Consent instance batch creation failed correlation_id=" in record.getMessage()
        and record.exc_info is not None
        for record in caplog.records
    )
    db_session.expire_all()
    after = {
        "instances": db_session.scalar(select(func.count()).select_from(ConsentInstance).where(*company_filter)),
        "responsible": db_session.scalar(select(func.count()).select_from(ConsentResponsibleAdult).where(ConsentResponsibleAdult.company_id == tenant.company.id)),
        "procedures": db_session.scalar(select(func.count()).select_from(ConsentInstanceProcedure).where(ConsentInstanceProcedure.company_id == tenant.company.id)),
        "audits": db_session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.company_id == tenant.company.id, AuditEvent.entity == "consent_instance")),
    }
    assert calls == 2
    assert after == before


def test_signer1_adult_patient_self_remains_supported(api_client, db_session, security_world):
    tenant = security_world.tenant_a
    _, procedure = _procedure(db_session, tenant)
    published = _template(api_client, tenant.dentist_admin, "SIGNER1-ADULT-SELF")
    context = _context(
        tenant,
        procedure,
        signer_actor_type="PATIENT_SELF",
        responsible_adult=None,
        minor_participation_status="NOT_APPLICABLE",
    )

    response = api_client.post(
        "/api/consent-instances/batch",
        token=tenant.dentist_admin.token,
        json={"context": context, "template_version_ids": [published["id"]]},
    )

    assert response.status_code == 201, response.text
    body = response.json()[0]
    assert body["signer_policy"] == "PATIENT_SELF"
    assert body["signer_actor_type"] == "PATIENT_SELF"
    assert body["responsible_adult"] is None
    assert db_session.scalar(
        select(func.count()).select_from(ConsentResponsibleAdult).where(
            ConsentResponsibleAdult.consent_instance_id == UUID(body["id"])
        )
    ) == 0
