import hashlib
import hmac
import json
import logging
import re
from datetime import datetime, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Appointment, Dentist, DentistSite, Patient
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.consent_acceptance import ConsentPaperPacket
from app.models.consent_template import (
    ConsentAccessSession,
    ConsentOtpChallenge,
    ConsentPublicSession,
    ConsentInstance,
    ConsentInstanceProcedure,
    ConsentInstanceSequence,
    ConsentResponsibleAdult,
    ConsentTemplate,
    ConsentTemplateVersion,
)
from app.models.site import Site
from app.models.treatment import ProcedureCatalogItem, Treatment, TreatmentProcedure
from app.models.user import User
from app.schemas.consent_instance_schema import (
    ApplicableConsentTemplateResponse,
    ApplicableTemplatesResponse,
    ConsentContextInput,
    ConsentInstanceAuditResponse,
    ConsentInstanceBatchCreateRequest,
    ConsentInstanceConfirmRequest,
    ConsentInstanceListResponse,
    ConsentInstancePreviewResponse,
    ConsentInstanceProcedureResponse,
    ConsentInstanceResponse,
    ConsentResponsibleAdultResponse,
    ConsentInstanceUpdateRequest,
    ConsentInstanceVoidRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.consent_library_normalization import validate_patient_facing_content
from app.services.consent_production_readiness import ConsentProductionReadinessError, assert_template_ready
from app.services.consent_template_service import VARIABLE_CATALOG, find_applicable_published_templates, validate_content
from app.services.patient_service import calculate_age
from app.services.document_style import resolve_professional_document_identity
from app.services.consent_acceptance_context import (
    ACCEPTANCE_CONTEXT_SCHEMA_VERSION,
    JURISDICTION_CODES,
    inspect_acceptance_context,
)
from app.services.consent_declaration_catalog import DECLARATION_SETS, TEST_DOCUMENT_NOTICE, declaration_set_for
from app.services.consent_signer import (
    RESPONSIBLE_ADULT,
    apply_signer_snapshot,
    canonical_signer_policy,
    resolve_signer_snapshot,
    responsible_relationship_label,
    signer_policy_from_library_version,
)
from app.services.site_access_service import authorized_site_ids
from app.utils.clinical_dates import clinical_date_or_local_default, effective_timezone


PREVIEW_WARNING = "Documento preparado para revisión profesional. Todavía no ha sido enviado ni firmado."
VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)\s*\}\}")
logger = logging.getLogger(__name__)


class ConsentInstanceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sha(value) -> str:
    raw = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _label(code: str) -> str:
    return VARIABLE_CATALOG.get(code, (code, "", "", ""))[0]


def _ensure_patient_facing_snapshot(content: str | None, document_kind: str, signer_policy: str = "PATIENT_SELF") -> None:
    validation = validate_patient_facing_content(
        content or "",
        allowed_variables=None,
        document_type=document_kind,
        signer_compatibility=canonical_signer_policy(signer_policy),
        normalized_hash=_sha(content or ""),
        enforce_electronic_readiness=True,
    )
    if validation.status == "BLOCKED":
        raise ConsentInstanceError(
            "El contenido del consentimiento contiene artefactos internos de biblioteca o no es compatible con el flujo electrónico actual.",
            422,
        )


def _mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def _signer_context_dict(signer) -> dict:
    return {
        "policy": signer.policy,
        "actor_type": signer.actor_type,
        "full_name": signer.full_name,
        "document_type": signer.document_type,
        "document_number": signer.document_number,
        "email_masked": signer.recipient_masked,
        "phone": signer.phone,
        "relationship_type": signer.relationship_type,
        "relationship_other": signer.relationship_other,
        "relationship_label": signer.relationship_label,
        "minor_participation_status": signer.minor_participation_status,
        "minor_participation_observation": signer.minor_participation_observation,
    }


def _responsible_response(session: Session, instance: ConsentInstance) -> ConsentResponsibleAdultResponse | None:
    row = session.scalar(select(ConsentResponsibleAdult).where(ConsentResponsibleAdult.consent_instance_id == instance.id))
    if not row:
        return None
    relationship_label = responsible_relationship_label(row.relationship_type, row.relationship_other)
    return ConsentResponsibleAdultResponse(
        id=row.id,
        patient_responsible_id=row.patient_responsible_id,
        full_name=row.full_name,
        document_type=row.document_type,
        document_number=row.document_number,
        relationship_type=row.relationship_type,
        relationship_other=row.relationship_other,
        relationship_label=relationship_label,
        email_masked=_mask_email(row.email),
        phone=row.phone,
        identity_verified_at=row.identity_verified_at,
        identity_verified_by=row.identity_verified_by,
    )


def _save_responsible_snapshot(session: Session, context: AuthContext, instance: ConsentInstance, signer) -> None:
    existing = session.scalar(select(ConsentResponsibleAdult).where(ConsentResponsibleAdult.consent_instance_id == instance.id).with_for_update())
    if signer.actor_type != RESPONSIBLE_ADULT:
        if existing:
            session.delete(existing)
        return
    statement = "La clínica verificó presencialmente la identidad del adulto responsable y registró sus datos antes de emitir el consentimiento."
    if existing is None:
        existing = ConsentResponsibleAdult(
            company_id=instance.company_id,
            patient_id=instance.patient_id,
            consent_instance_id=instance.id,
            patient_responsible_id=signer.responsible_adult_id,
            full_name=signer.full_name,
            document_type=signer.document_type or "No informado",
            document_number=signer.document_number or "No informado",
            relationship_type=signer.relationship_type or "OTHER",
            relationship_other=signer.relationship_other,
            email=signer.email,
            phone=signer.phone or "No informado",
            identity_verified_by=context.user.id,
            identity_verified_at=_now(),
            verification_statement=statement,
        )
        session.add(existing)
    else:
        existing.patient_responsible_id=signer.responsible_adult_id
        existing.full_name=signer.full_name
        existing.document_type=signer.document_type or "No informado"
        existing.document_number=signer.document_number or "No informado"
        existing.relationship_type=signer.relationship_type or "OTHER"
        existing.relationship_other=signer.relationship_other
        existing.email=signer.email
        existing.phone=signer.phone or "No informado"
        existing.identity_verified_by=context.user.id
        existing.identity_verified_at=_now()
        existing.verification_statement=statement
        existing.row_version += 1


def _audit(session: Session, context: AuthContext, metadata: RequestMetadata, instance: ConsentInstance, action: str, *, before: str | None = None, detail: dict | None = None, result: str = "SUCCESS") -> None:
    session.add(AuditEvent(company_id=context.user.company_id, user_id=context.user.id, session_id=context.auth_session.id, entity="consent_instance", entity_id=instance.id, action=action, result=result, detail={"site_id": str(instance.site_id), "patient_id": str(instance.patient_id), "previous_status": before, "new_status": instance.status, **(detail or {})}, ip_address=metadata.ip_address, user_agent=metadata.user_agent))


def _allowed_sites(session: Session, context: AuthContext) -> set[UUID]:
    return authorized_site_ids(session, company_id=context.user.company_id, user_id=context.user.id, roles=context.roles)


def _clinical_context(session: Session, context: AuthContext, payload: ConsentContextInput):
    company_id = context.user.company_id
    if payload.site_id not in _allowed_sites(session, context):
        raise ConsentInstanceError("La sede no está disponible para este usuario.", 403)
    company = session.scalar(select(Company).where(Company.id == company_id, Company.is_active.is_(True)))
    site = session.scalar(select(Site).where(Site.id == payload.site_id, Site.company_id == company_id, Site.is_active.is_(True)))
    patient = session.scalar(select(Patient).where(Patient.id == payload.patient_id, Patient.company_id == company_id, Patient.is_active.is_(True)))
    dentist = session.scalar(select(Dentist).where(Dentist.id == payload.dentist_profile_id, Dentist.company_id == company_id, Dentist.is_active.is_(True)))
    user = session.scalar(select(User).where(User.id == dentist.user_id, User.company_id == company_id, User.is_active.is_(True))) if dentist and dentist.user_id else None
    if not company or not site or not patient or not user or not dentist:
        raise ConsentInstanceError("El contexto clínico contiene una relación no válida.", 404)
    linked = session.scalar(select(DentistSite.id).where(DentistSite.company_id == company_id, DentistSite.dentist_id == dentist.id, DentistSite.site_id == site.id, DentistSite.is_active.is_(True)))
    if linked is None:
        raise ConsentInstanceError("El profesional no está vinculado a la sede seleccionada.", 422)
    appointment = None
    if payload.appointment_id:
        appointment = session.scalar(select(Appointment).where(Appointment.id == payload.appointment_id, Appointment.company_id == company_id, Appointment.patient_id == patient.id, Appointment.site_id == site.id))
        if appointment is None:
            raise ConsentInstanceError("La cita no corresponde al paciente y sede seleccionados.", 422)
    treatment = None
    if payload.treatment_id:
        treatment = session.scalar(select(Treatment).where(Treatment.id == payload.treatment_id, Treatment.company_id == company_id, Treatment.patient_id == patient.id))
        if treatment is None:
            raise ConsentInstanceError("El tratamiento no corresponde al paciente.", 422)
    treatment_procedures = list(session.scalars(select(TreatmentProcedure).where(TreatmentProcedure.id.in_(payload.treatment_procedure_ids), TreatmentProcedure.company_id == company_id, TreatmentProcedure.patient_id == patient.id))) if payload.treatment_procedure_ids else []
    if len(treatment_procedures) != len(payload.treatment_procedure_ids) or (treatment and any(item.treatment_id != treatment.id for item in treatment_procedures)):
        raise ConsentInstanceError("Uno o más procedimientos no corresponden al contexto seleccionado.", 422)
    catalog_items = list(session.scalars(select(ProcedureCatalogItem).where(ProcedureCatalogItem.id.in_(payload.procedure_catalog_ids), ProcedureCatalogItem.company_id == company_id, ProcedureCatalogItem.is_active.is_(True)))) if payload.procedure_catalog_ids else []
    if len(catalog_items) != len(payload.procedure_catalog_ids):
        raise ConsentInstanceError("Uno o más procedimientos de catálogo no son válidos.", 422)
    return company, site, patient, user, dentist, appointment, treatment, treatment_procedures, catalog_items


def _procedure_rows(treatment_procedures: list[TreatmentProcedure], catalog_items: list[ProcedureCatalogItem]):
    rows: list[dict] = []
    for item in sorted(treatment_procedures, key=lambda row: str(row.id)):
        rows.append({"catalog_id": item.catalog_procedure_id, "treatment_id": item.id, "code": None, "name": item.name, "description": item.observations})
    existing_catalog = {item["catalog_id"] for item in rows if item["catalog_id"]}
    for item in sorted(catalog_items, key=lambda row: row.name):
        if item.id not in existing_catalog:
            rows.append({"catalog_id": item.id, "treatment_id": None, "code": None, "name": item.name, "description": item.description})
    return rows


def _values(session, company, site, patient, user, dentist, treatment, procedures: list[dict], clinical_date, timezone_name, version_number: int, country_code: str, language_code: str) -> tuple[dict, dict]:
    local_now = _now().astimezone(ZoneInfo(timezone_name))
    age = calculate_age(patient.birth_date, clinical_date)
    one = procedures[0] if len(procedures) == 1 else None
    identity = resolve_professional_document_identity(session, company, dentist)
    values = {
        "patient.full_name": f"{patient.first_names} {patient.last_names}".strip(), "patient.document_type": patient.document_type,
        "patient.document_number": patient.document, "patient.birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "patient.age": str(age) if age is not None else None, "company.name": company.name, "company.tax_id": company.tax_id,
        "company.contact": company.email or company.phone, "site.name": site.name, "site.address": site.address, "site.city": site.city,
        "site.country": company.country, "professional.name": identity.full_name, "professional.full_name": identity.full_name,
        "professional.specialty": identity.specialty, "professional.registration": identity.professional_license,
        "professional.license_number": identity.professional_license, "treatment.name": treatment.name if treatment else None,
        "treatment.diagnosis": None, "treatment.description": treatment.description if treatment else None, "treatment.plan_number": None,
        "procedure.name": one["name"] if one else None, "procedure.code": one["code"] if one else None,
        "procedure.description": one["description"] if one else None, "procedures.list": "; ".join(item["name"] for item in procedures) or None,
        "document.clinical_date": clinical_date.isoformat(), "document.generated_date": local_now.date().isoformat(),
        "document.local_time": local_now.strftime("%H:%M"), "document.country": country_code,
        "document.language": language_code, "document.version": str(version_number),
    }
    procedure_snapshot = json.loads(json.dumps(procedures, default=str))
    jurisdiction_code = JURISDICTION_CODES.get((country_code, language_code))
    context_snapshot = {
        "schema_version": ACCEPTANCE_CONTEXT_SCHEMA_VERSION,
        "patient": {"id": str(patient.id), "full_name": values["patient.full_name"], "document_type": patient.document_type, "document_number": patient.document, "birth_date": values["patient.birth_date"], "age": age},
        "company": {"id": str(company.id), "name": company.name, "tax_id": company.tax_id},
        "site": {"id": str(site.id), "name": site.name, "address": site.address, "city": site.city, "country_code": country_code, "timezone": timezone_name},
        "professional": {
            "user_id": str(user.id),
            "dentist_profile_id": str(dentist.id),
            "full_name": identity.full_name,
            "specialty": identity.specialty,
            "document_type": identity.document_type,
            "document_number": identity.document_number,
            "license_number": identity.professional_license,
            "email": identity.email,
        },
        "treatment": {"id": str(treatment.id), "name": treatment.name, "description": treatment.description} if treatment else None,
        "procedures": procedure_snapshot,
        "template": {"country_code": country_code, "locale": language_code, "version_number": version_number},
        "document": {
            "schema_version": ACCEPTANCE_CONTEXT_SCHEMA_VERSION,
            "country": country_code,
            "country_code": country_code,
            "locale": language_code,
            "jurisdiction_code": jurisdiction_code,
            "timezone": timezone_name,
        },
        "clinical_date": clinical_date.isoformat(), "generated_at_utc": _now().isoformat(),
    }
    return values, context_snapshot


def _resolve_content(content: str, values: dict) -> tuple[str, list[str]]:
    used = validate_content(content, require_registered=True)
    if not used.valid:
        raise ConsentInstanceError("La plantilla publicada contiene variables o sintaxis no registradas.", 409)
    missing = sorted(code for code in used.used_variables if values.get(code) in (None, ""))
    rendered = content
    for code in used.used_variables:
        if code not in missing:
            rendered = re.sub(r"\{\{\s*" + re.escape(code) + r"\s*\}\}", str(values[code]), rendered)
    return rendered, missing


def _next_number(session: Session, company_id: UUID) -> tuple[int, str]:
    session.execute(text("INSERT INTO consentimiento_instancia_consecutivos (id, empresa_id, next_number, created_at, updated_at) VALUES (gen_random_uuid(), :company, 1, now(), now()) ON CONFLICT (empresa_id) DO NOTHING"), {"company": company_id})
    sequence = session.scalar(select(ConsentInstanceSequence).where(ConsentInstanceSequence.company_id == company_id).with_for_update())
    number = sequence.next_number
    sequence.next_number += 1
    return number, f"CNS-{number:06d}"


def _require_instance(session: Session, context: AuthContext, instance_id: UUID, *, lock=False) -> ConsentInstance:
    statement = select(ConsentInstance).where(ConsentInstance.id == instance_id, ConsentInstance.company_id == context.user.company_id, ConsentInstance.site_id.in_(_allowed_sites(session, context)))
    if lock:
        statement = statement.with_for_update()
    instance = session.scalar(statement)
    if instance is None:
        raise ConsentInstanceError("Instancia de consentimiento no encontrada.", 404)
    return instance


def _procedures(session: Session, instance_id: UUID) -> list[ConsentInstanceProcedure]:
    return list(session.scalars(select(ConsentInstanceProcedure).where(ConsentInstanceProcedure.instance_id == instance_id).order_by(ConsentInstanceProcedure.order_number)))


def _verify_seal(instance: ConsentInstance) -> None:
    if not instance.instance_content_sha256:
        return
    expected_content = _sha(instance.rendered_content_snapshot or "")
    expected_context = _sha(instance.context_snapshot)
    expected_integrity = _sha({
        "instance_id": str(instance.id),
        "template_hash": instance.template_content_sha256,
        "template_snapshot_hash": _sha(instance.template_content_snapshot),
        "content_hash": expected_content,
        "context_hash": expected_context,
        "version": instance.template_version_number,
    })
    checks = (
        (instance.instance_content_sha256, expected_content),
        (instance.context_sha256 or "", expected_context),
        (instance.integrity_hash or "", expected_integrity),
    )
    if not all(hmac.compare_digest(stored, expected) for stored, expected in checks):
        raise ConsentInstanceError("La integridad del consentimiento no pudo verificarse.", 409)


def _response(session: Session, instance: ConsentInstance) -> ConsentInstanceResponse:
    _verify_seal(instance)
    rows = _procedures(session, instance.id)
    compatibility = inspect_acceptance_context(instance)
    declaration_set = None
    if compatibility.compatible:
        try:
            declaration_set = declaration_set_for(compatibility.country_code, compatibility.locale, actor_type=getattr(instance, "signer_actor_type", "PATIENT_SELF"), app_env=settings.app_env, acceptance_enabled=settings.consent_acceptance_enabled, on_date=_now().date(), session=session)
        except Exception:
            declaration_set = None
    is_test_document = declaration_set.is_test_document if declaration_set else True
    paper_status = session.scalar(select(ConsentPaperPacket.status).where(ConsentPaperPacket.consent_instance_id == instance.id)) if instance.completion_channel == "PAPER" else None
    return ConsentInstanceResponse(id=instance.id, visible_number=instance.visible_number, patient_id=instance.patient_id, site_id=instance.site_id, template_id=instance.template_id, template_version_id=instance.template_version_id, appointment_id=instance.appointment_id, treatment_id=instance.treatment_id, professional_user_id=instance.professional_user_id, dentist_profile_id=instance.dentist_profile_id, status=instance.status, completion_channel=instance.completion_channel, paper_status=paper_status, document_kind=instance.document_kind, country_code=instance.country_code, language_code=instance.language_code, clinical_date=instance.clinical_date, timezone=instance.timezone_name, display_title=instance.display_title, signer_policy=getattr(instance, "signer_policy", "PATIENT_SELF"), signer_actor_type=getattr(instance, "signer_actor_type", "PATIENT_SELF"), signer_name=getattr(instance, "signer_full_name_snapshot", None), signer_email_masked=_mask_email(getattr(instance, "signer_email_snapshot", None)), responsible_adult=_responsible_response(session, instance), minor_participation_status=getattr(instance, "minor_participation_status", None), minor_participation_observation=getattr(instance, "minor_participation_observation", None), rendered_content=instance.rendered_content_snapshot, template_version_number=instance.template_version_number, template_content_sha256=instance.template_content_sha256, instance_content_sha256=instance.instance_content_sha256, context_sha256=instance.context_sha256, integrity_hash=instance.integrity_hash, variable_values=instance.variable_values_snapshot, missing_variables=instance.missing_variables, missing_variable_labels=[_label(code) for code in instance.missing_variables], context_snapshot=instance.context_snapshot, acceptance_compatible=compatibility.compatible, acceptance_block_code=compatibility.code, acceptance_block_message=compatibility.private_message, is_test_document=is_test_document, test_notice=TEST_DOCUMENT_NOTICE if is_test_document else None, legal_review_status=declaration_set.legal_status if declaration_set else None, declaration_set_code=declaration_set.code if declaration_set else None, declaration_set_version=declaration_set.version if declaration_set else None, procedures=[ConsentInstanceProcedureResponse(id=row.id, procedure_catalog_id=row.procedure_catalog_id, treatment_procedure_id=row.treatment_procedure_id, code=row.code_snapshot, name=row.name_snapshot, description=row.description_snapshot, order=row.order_number) for row in rows], professional_confirmed_at=instance.professional_confirmed_at, professional_confirmed_by=instance.professional_confirmed_by, ready_at=instance.ready_at, voided_at=instance.voided_at, voided_by=instance.voided_by, void_reason=instance.void_reason, row_version=instance.row_version, created_by=instance.created_by, updated_by=instance.updated_by, created_at=instance.created_at, updated_at=instance.updated_at)


def applicable_templates(session: Session, context: AuthContext, payload: ConsentContextInput) -> ApplicableTemplatesResponse:
    company, site, patient, user, dentist, appointment, treatment, treatment_procedures, catalog_items = _clinical_context(session, context, payload)
    procedures = _procedure_rows(treatment_procedures, catalog_items)
    catalog_ids = {item["catalog_id"] for item in procedures if item["catalog_id"]}
    specialty = {treatment.specialty} if treatment and treatment.specialty else set()
    country = "CL" if (company.country or "").strip().casefold() in {"chile", "cl"} else "CO"
    candidates = find_applicable_published_templates(session, company_id=company.id, country_code=country, language_code=f"es-{country}", site_id=site.id, procedure_ids=catalog_ids, specialty_codes=specialty)
    result = []
    for candidate in candidates:
        version = session.get(ConsentTemplateVersion, candidate.version_id)
        values, _ = _values(session, company, site, patient, user, dentist, treatment, procedures, clinical_date_or_local_default(payload.clinical_date, company, site), effective_timezone(company, site), version.version_number, candidate.country_code, candidate.language_code)
        used = validate_content(version.content, require_registered=True).used_variables
        rendered, missing = _resolve_content(version.content, values)
        candidate_template = session.get(ConsentTemplate, candidate.template_id)
        signer_policy = signer_policy_from_library_version(session, version)
        _ensure_patient_facing_snapshot(rendered, candidate_template.document_kind, signer_policy)
        reason_codes = ["GENERAL_TEMPLATE"] if candidate.scope_type == "GENERAL" else []
        reasons = ["Plantilla general"] if candidate.scope_type == "GENERAL" else []
        if candidate.site_ids:
            reason_codes.append("SITE_MATCH")
            reasons.append("Aplica a esta sede")
        if candidate.scope_type == "SPECIFIC" and candidate.procedure_ids:
            reason_codes.append("PROCEDURE_MATCH")
            reasons.append("Aplica por procedimiento")
        if candidate.scope_type == "SPECIFIC" and candidate.specialties:
            reason_codes.append("SPECIALTY_MATCH")
            reasons.append("Aplica por especialidad")
        result.append(ApplicableConsentTemplateResponse(template_id=candidate.template_id, version_id=candidate.version_id, template_name=candidate.template_name, title=version.title, document_kind=candidate_template.document_kind, country_code=candidate.country_code, language_code=candidate.language_code, version_number=candidate.version_number, applicability_reason_codes=reason_codes, applicability_reasons=reasons, covered_procedure_ids=sorted(catalog_ids.intersection(set(candidate.procedure_ids)), key=str), required_variables=used, required_variable_labels=[_label(code) for code in used], missing_variables=missing, missing_variable_labels=[_label(code) for code in missing], rendered_preview=rendered, signer_policy=signer_policy))
    return ApplicableTemplatesResponse(items=result, total=len(result))


def _create_one(session: Session, context: AuthContext, payload: ConsentContextInput, version_id: UUID, metadata: RequestMetadata) -> ConsentInstance:
    company, site, patient, user, dentist, appointment, treatment, treatment_procedures, catalog_items = _clinical_context(session, context, payload)
    version = session.scalar(select(ConsentTemplateVersion).where(ConsentTemplateVersion.id == version_id, ConsentTemplateVersion.company_id == company.id, ConsentTemplateVersion.status == "PUBLISHED"))
    if version is None:
        raise ConsentInstanceError("La versión seleccionada no está publicada y vigente.", 409)
    template = session.scalar(select(ConsentTemplate).where(ConsentTemplate.id == version.template_id, ConsentTemplate.company_id == company.id, ConsentTemplate.is_active.is_(True)))
    if template is None:
        raise ConsentInstanceError("La plantilla seleccionada no está activa.", 409)
    available = applicable_templates(session, context, payload)
    if version.id not in {item.version_id for item in available.items}:
        raise ConsentInstanceError("La plantilla no es aplicable al contexto clínico seleccionado.", 422)
    procedure_data = _procedure_rows(treatment_procedures, catalog_items)
    clinical_date = clinical_date_or_local_default(payload.clinical_date, company, site)
    timezone_name = effective_timezone(company, site)
    signer_policy = signer_policy_from_library_version(session, version)
    try:
        assert_template_ready(
            session,
            template=template,
            version=version,
            signer_policy=signer_policy,
            channel="COMMON",
        )
    except ConsentProductionReadinessError as exc:
        raise ConsentInstanceError(str(exc), 409) from exc
    try:
        signer = resolve_signer_snapshot(session, company_id=company.id, patient=patient, payload_context=payload, policy=signer_policy, actor_type=payload.signer_actor_type, verified_by_user_id=context.user.id)
    except ValueError as exc:
        raise ConsentInstanceError(str(exc), 422) from exc
    values, context_snapshot = _values(session, company, site, patient, user, dentist, treatment, procedure_data, clinical_date, timezone_name, version.version_number, template.country_code, template.language_code)
    context_snapshot["signer"] = _signer_context_dict(signer)
    rendered, missing = _resolve_content(version.content, values)
    _ensure_patient_facing_snapshot(rendered, template.document_kind, signer_policy)
    sequence, visible = _next_number(session, company.id)
    instance = ConsentInstance(company_id=company.id, site_id=site.id, patient_id=patient.id, template_id=template.id, template_version_id=version.id, appointment_id=appointment.id if appointment else None, treatment_id=treatment.id if treatment else None, professional_user_id=user.id, dentist_profile_id=dentist.id, sequence_number=sequence, visible_number=visible, status="DRAFT", document_kind=template.document_kind, country_code=template.country_code, language_code=template.language_code, clinical_date=clinical_date, timezone_name=timezone_name, display_title=version.title, rendered_content_snapshot=rendered, template_content_snapshot=version.content, variable_values_snapshot=values, missing_variables=missing, context_snapshot=context_snapshot, template_version_number=version.version_number, template_content_sha256=version.content_sha256 or _sha(version.content), created_by=context.user.id, updated_by=context.user.id)
    apply_signer_snapshot(instance, signer); instance.signer_selected_by = context.user.id
    session.add(instance); session.flush(); _save_responsible_snapshot(session, context, instance, signer)
    for order, item in enumerate(procedure_data, 1):
        session.add(ConsentInstanceProcedure(company_id=company.id, instance_id=instance.id, procedure_catalog_id=item["catalog_id"], treatment_procedure_id=item["treatment_id"], code_snapshot=item["code"], name_snapshot=item["name"], description_snapshot=item["description"], order_number=order))
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_CREATED", detail={"template_version_id": str(version.id), "visible_number": visible, "procedure_count": len(procedure_data)})
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_TEMPLATE_SELECTED", detail={"template_id": str(template.id), "template_version_id": str(version.id)})
    _audit(session, context, metadata, instance, "CONSENT_SIGNER_MODE_SELECTED", detail={"signer_policy": instance.signer_policy, "signer_actor_type": instance.signer_actor_type})
    if instance.signer_actor_type == RESPONSIBLE_ADULT:
        _audit(session, context, metadata, instance, "RESPONSIBLE_ADULT_SELECTED", detail={"relationship_type": instance.signer_relationship_type_snapshot})
        if signer.responsible_adult_id is None:
            _audit(session, context, metadata, instance, "RESPONSIBLE_ADULT_CREATED", detail={"relationship_type": instance.signer_relationship_type_snapshot})
        _audit(session, context, metadata, instance, "RESPONSIBLE_ADULT_IDENTITY_CONFIRMED")
        if instance.minor_participation_status:
            _audit(session, context, metadata, instance, "MINOR_PARTICIPATION_RECORDED", detail={"status": instance.minor_participation_status})
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_VARIABLES_RESOLVED", detail={"missing_variable_count": len(missing)})
    return instance


def create_batch(session: Session, context: AuthContext, payload: ConsentInstanceBatchCreateRequest, metadata: RequestMetadata) -> list[ConsentInstanceResponse]:
    correlation_id = uuid4().hex
    try:
        instances = [_create_one(session, context, payload.context, version_id, metadata) for version_id in payload.template_version_ids]
        session.commit()
    except Exception:
        session.rollback()
        logger.exception(
            "Consent instance batch creation failed correlation_id=%s company_id=%s actor_id=%s template_count=%s",
            correlation_id,
            context.user.company_id,
            context.user.id,
            len(payload.template_version_ids),
        )
        raise
    return [_response(session, item) for item in instances]


def list_instances(session: Session, context: AuthContext, patient_id: UUID | None = None) -> ConsentInstanceListResponse:
    statement = select(ConsentInstance).where(ConsentInstance.company_id == context.user.company_id, ConsentInstance.site_id.in_(_allowed_sites(session, context)))
    if patient_id: statement = statement.where(ConsentInstance.patient_id == patient_id)
    rows = list(session.scalars(statement.order_by(ConsentInstance.created_at.desc()).limit(250)))
    return ConsentInstanceListResponse(items=[_response(session, item) for item in rows], total=len(rows))


def get_instance(session: Session, context: AuthContext, instance_id: UUID) -> ConsentInstanceResponse:
    return _response(session, _require_instance(session, context, instance_id))


def update_instance(session: Session, context: AuthContext, instance_id: UUID, payload: ConsentInstanceUpdateRequest, metadata: RequestMetadata) -> ConsentInstanceResponse:
    instance = _require_instance(session, context, instance_id, lock=True)
    if instance.status != "DRAFT": raise ConsentInstanceError("Solo un borrador puede modificarse.", 409)
    if payload.row_version != instance.row_version: raise ConsentInstanceError("La instancia fue modificada por otro usuario.", 409)
    company, site, patient, user, dentist, appointment, treatment, treatment_procedures, catalog_items = _clinical_context(session, context, payload)
    if patient.id != instance.patient_id: raise ConsentInstanceError("No se puede cambiar el paciente de una instancia.", 409)
    version = session.get(ConsentTemplateVersion, instance.template_version_id)
    procedure_data = _procedure_rows(treatment_procedures, catalog_items)
    clinical_date = clinical_date_or_local_default(payload.clinical_date, company, site)
    timezone_name = effective_timezone(company, site)
    signer_policy = signer_policy_from_library_version(session, version)
    try:
        signer = resolve_signer_snapshot(session, company_id=company.id, patient=patient, payload_context=payload, policy=signer_policy, actor_type=payload.signer_actor_type or instance.signer_actor_type, verified_by_user_id=context.user.id)
    except ValueError as exc:
        raise ConsentInstanceError(str(exc), 422) from exc
    values, snapshot = _values(session, company, site, patient, user, dentist, treatment, procedure_data, clinical_date, timezone_name, version.version_number, instance.country_code, instance.language_code)
    snapshot["signer"] = _signer_context_dict(signer)
    rendered, missing = _resolve_content(instance.template_content_snapshot, values)
    _ensure_patient_facing_snapshot(rendered, instance.document_kind, signer_policy)
    instance.site_id=site.id; instance.appointment_id=appointment.id if appointment else None; instance.treatment_id=treatment.id if treatment else None; instance.professional_user_id=user.id; instance.dentist_profile_id=dentist.id; instance.clinical_date=clinical_date; instance.timezone_name=timezone_name; instance.variable_values_snapshot=values; instance.context_snapshot=snapshot; instance.rendered_content_snapshot=rendered; instance.missing_variables=missing; apply_signer_snapshot(instance, signer); instance.signer_selected_by=context.user.id; _save_responsible_snapshot(session, context, instance, signer); instance.updated_by=context.user.id; instance.row_version += 1
    session.execute(delete(ConsentInstanceProcedure).where(ConsentInstanceProcedure.instance_id == instance.id))
    for order, item in enumerate(procedure_data, 1): session.add(ConsentInstanceProcedure(company_id=company.id, instance_id=instance.id, procedure_catalog_id=item["catalog_id"], treatment_procedure_id=item["treatment_id"], code_snapshot=item["code"], name_snapshot=item["name"], description_snapshot=item["description"], order_number=order))
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_CONTEXT_UPDATED", detail={"row_version": instance.row_version})
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_VARIABLES_RESOLVED", detail={"missing_variable_count": len(missing)})
    session.commit(); return _response(session, instance)


def resolve_instance(session: Session, context: AuthContext, instance_id: UUID, metadata: RequestMetadata) -> ConsentInstanceResponse:
    instance = _require_instance(session, context, instance_id)
    if instance.status != "DRAFT": raise ConsentInstanceError("El contenido sellado no puede resolverse nuevamente.", 409)
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_VARIABLES_RESOLVED", detail={"missing_variable_count": len(instance.missing_variables)})
    session.commit(); return _response(session, instance)


def preview_instance(session: Session, context: AuthContext, instance_id: UUID, metadata: RequestMetadata) -> ConsentInstancePreviewResponse:
    instance = _require_instance(session, context, instance_id)
    _ensure_patient_facing_snapshot(instance.rendered_content_snapshot, instance.document_kind, getattr(instance, "signer_policy", "PATIENT_SELF"))
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_PREVIEWED", detail={"missing_variable_count": len(instance.missing_variables)})
    session.commit(); return ConsentInstancePreviewResponse(warning=PREVIEW_WARNING, instance=_response(session, instance))


def confirm_professionally(session: Session, context: AuthContext, instance_id: UUID, payload: ConsentInstanceConfirmRequest, metadata: RequestMetadata) -> ConsentInstanceResponse:
    if not payload.confirmed: raise ConsentInstanceError("Debes confirmar expresamente la revisión profesional.", 422)
    instance = _require_instance(session, context, instance_id, lock=True)
    if instance.status != "DRAFT": raise ConsentInstanceError("La instancia ya no está disponible para revisión.", 409)
    if payload.row_version != instance.row_version: raise ConsentInstanceError("La instancia cambió. Recarga antes de confirmar.", 409)
    if instance.missing_variables: raise ConsentInstanceError("No se puede confirmar mientras existan datos faltantes: " + ", ".join(_label(code) for code in instance.missing_variables), 422)
    _ensure_patient_facing_snapshot(instance.rendered_content_snapshot, instance.document_kind, getattr(instance, "signer_policy", "PATIENT_SELF"))
    dentist = session.scalar(select(Dentist).where(Dentist.company_id == context.user.company_id, Dentist.user_id == context.user.id, Dentist.is_active.is_(True)))
    if dentist is None or instance.professional_user_id != context.user.id:
        raise ConsentInstanceError("La confirmación debe realizarla el profesional seleccionado con perfil odontológico activo.", 403)
    before = instance.status; now = _now(); instance.status="READY_FOR_REVIEW"; instance.professional_confirmed_at=now; instance.professional_confirmed_by=context.user.id; instance.ready_at=now; instance.ready_by=context.user.id; instance.instance_content_sha256=_sha(instance.rendered_content_snapshot or ""); instance.context_sha256=_sha(instance.context_snapshot); instance.integrity_hash=_sha({"instance_id": str(instance.id), "template_hash": instance.template_content_sha256, "template_snapshot_hash": _sha(instance.template_content_snapshot), "content_hash": instance.instance_content_sha256, "context_hash": instance.context_sha256, "version": instance.template_version_number}); instance.updated_by=context.user.id; instance.row_version += 1
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_PROFESSIONAL_CONFIRMED", before=before, detail={"integrity_hash": instance.integrity_hash})
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_READY_FOR_REVIEW", before=before)
    session.commit(); return _response(session, instance)


def mark_pending_signature(session: Session, context: AuthContext, instance_id: UUID) -> None:
    _require_instance(session, context, instance_id)
    raise ConsentInstanceError("PENDING_SIGNATURE requiere emitir una sesión o enlace y está reservado para C019A.3.", 409)


def void_instance(session: Session, context: AuthContext, instance_id: UUID, payload: ConsentInstanceVoidRequest, metadata: RequestMetadata) -> ConsentInstanceResponse:
    instance = _require_instance(session, context, instance_id, lock=True)
    if instance.status == "VOIDED": raise ConsentInstanceError("La instancia ya está anulada.", 409)
    if instance.status == "SIGNED": raise ConsentInstanceError("Una instancia firmada es inmutable y no puede anularse desde este flujo.", 409)
    before=instance.status; instance.status="VOIDED"; instance.voided_at=_now(); instance.voided_by=context.user.id; instance.void_reason=payload.reason; instance.updated_by=context.user.id; instance.row_version += 1
    for access in session.scalars(select(ConsentAccessSession).where(ConsentAccessSession.consent_instance_id == instance.id, ConsentAccessSession.status.notin_(["REVOKED", "EXPIRED"])).with_for_update()):
        access.status = "REVOKED"; access.revoked_at = _now(); access.revoked_by = context.user.id; access.revoke_reason = "INSTANCE_VOIDED"; access.row_version += 1
        for challenge in session.scalars(select(ConsentOtpChallenge).where(ConsentOtpChallenge.access_session_id == access.id, ConsentOtpChallenge.status == "PENDING")): challenge.status = "INVALIDATED"
        for public_session in session.scalars(select(ConsentPublicSession).where(ConsentPublicSession.access_session_id == access.id, ConsentPublicSession.status == "ACTIVE")): public_session.status = "REVOKED"; public_session.revoked_at = _now()
    _audit(session, context, metadata, instance, "CONSENT_INSTANCE_VOIDED", before=before, detail={"reason": payload.reason})
    session.commit(); return _response(session, instance)


def list_audit(session: Session, context: AuthContext, instance_id: UUID) -> list[ConsentInstanceAuditResponse]:
    instance = _require_instance(session, context, instance_id)
    rows = list(session.scalars(select(AuditEvent).where(AuditEvent.company_id == context.user.company_id, AuditEvent.entity == "consent_instance", AuditEvent.entity_id == instance.id).order_by(AuditEvent.occurred_at.desc()).limit(100)))
    return [ConsentInstanceAuditResponse(id=row.id, action=row.action, result=row.result, user_id=row.user_id, occurred_at=row.occurred_at, detail=row.detail) for row in rows]
