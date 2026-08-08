import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.consent_template import (
    ConsentTemplate,
    ConsentTemplateVersion,
    ConsentTemplateVersionProcedure,
    ConsentTemplateVersionSite,
    ConsentTemplateVersionSpecialty,
)
from app.models.site import Site
from app.models.treatment import ProcedureCatalogItem
from app.schemas.consent_template_schema import (
    ApplicableTemplateCandidate,
    CatalogItemResponse,
    ConsentPreviewResponse,
    ConsentReasonRequest,
    ConsentTemplateCreateRequest,
    ConsentTemplateAuditResponse,
    ConsentTemplateListResponse,
    ConsentTemplateResponse,
    ConsentTemplateUpdateRequest,
    ConsentVersionCreateFromRequest,
    ConsentVersionDraftInput,
    ConsentVersionResponse,
    ConsentVersionUpdateRequest,
    SpecialtyInput,
    VariableValidationResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.consent_library_normalization import assess_legacy_patient_content


CONTENT_FORMAT = "RESTRICTED_MARKDOWN_V1"
PREVIEW_WARNING = "BORRADOR DE DEMOSTRACIÓN — NO APROBADO PARA USO CLÍNICO"
VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)\s*\}\}")
ANY_TEMPLATE_PATTERN = re.compile(r"\{\{.*?\}\}", re.DOTALL)
HTML_PATTERN = re.compile(r"<\s*/?\s*[a-zA-Z!][^>]*>")
DANGEROUS_URI_PATTERN = re.compile(r"(?:javascript|vbscript|data\s*:\s*text/html)\s*:", re.IGNORECASE)
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\([^)]*\)")

OFFICIAL_STANDARD_CONSENT_KINDS = {"GENERAL_CLINICAL_CONSENT", "PROCEDURE_CONSENT", "TREATMENT_AUTHORIZATION"}

DOCUMENT_KIND_CATALOG = (
    ("GENERAL_CLINICAL_CONSENT", "Consentimiento clínico general"),
    ("PROCEDURE_CONSENT", "Consentimiento por procedimiento"),
    ("TREATMENT_AUTHORIZATION", "Autorización de tratamiento"),
    ("IMAGE_USE_AUTHORIZATION", "Autorización de uso de imágenes"),
    ("DATA_PROCESSING_AUTHORIZATION", "Autorización de tratamiento de datos"),
    ("COMMUNICATIONS_AUTHORIZATION", "Autorización de comunicaciones"),
    ("REPRESENTATIVE_CONSENT", "Consentimiento de representante"),
    ("TREATMENT_REJECTION", "Rechazo de tratamiento"),
    ("CONSENT_REVOCATION", "Revocación de consentimiento"),
    ("INFORMATION_ACKNOWLEDGEMENT", "Constancia de información"),
    ("OTHER", "Otro documento configurable"),
)

VARIABLE_CATALOG: dict[str, tuple[str, str, str, str]] = {
    "patient.full_name": ("Nombre completo del paciente", "Paciente", "Nombre completo registrado en la ficha del paciente.", "Paciente de demostración"),
    "patient.document_type": ("Tipo de documento", "Paciente", "Tipo de identificación registrado para el paciente.", "Documento demo"),
    "patient.document_number": ("Número de documento", "Paciente", "Número de identificación registrado para el paciente.", "DEMO-000000"),
    "patient.birth_date": ("Fecha de nacimiento", "Paciente", "Fecha de nacimiento registrada en la ficha.", "01/01/1990"),
    "patient.age": ("Edad en la fecha clínica", "Paciente", "Edad calculada para la fecha clínica del documento.", "36 años"),
    "company.name": ("Nombre de la empresa", "Empresa", "Nombre institucional configurado por la empresa.", "Clínica de demostración Dentia"),
    "company.tax_id": ("Identificación de la empresa", "Empresa", "Identificación tributaria configurada para la empresa.", "DEMO-EMPRESA"),
    "company.contact": ("Contacto institucional", "Empresa", "Dato institucional de contacto configurado.", "contacto@example.test"),
    "site.name": ("Nombre de la sede", "Sede", "Nombre de la sede asociada al documento.", "Sede de demostración"),
    "site.address": ("Dirección de la sede", "Sede", "Dirección institucional de la sede.", "Dirección ficticia 123"),
    "site.city": ("Ciudad de la sede", "Sede", "Ciudad configurada para la sede.", "Ciudad de demostración"),
    "site.country": ("País de la sede", "Sede", "País configurado para la sede.", "País de demostración"),
    "professional.name": ("Nombre del profesional", "Profesional", "Nombre del profesional responsable; alias compatible.", "Dra. Profesional de demostración"),
    "professional.full_name": ("Nombre completo del profesional", "Profesional", "Nombre completo del profesional responsable.", "Dra. Profesional de demostración"),
    "professional.specialty": ("Especialidad profesional", "Profesional", "Especialidad registrada para el profesional.", "Especialidad de demostración"),
    "professional.registration": ("Registro profesional", "Profesional", "Registro profesional; alias compatible.", "REG-DEMO"),
    "professional.license_number": ("Registro profesional", "Profesional", "Número de registro o licencia profesional.", "REG-DEMO"),
    "treatment.name": ("Nombre del tratamiento", "Tratamiento", "Nombre del tratamiento asociado.", "Tratamiento de demostración"),
    "treatment.diagnosis": ("Diagnóstico", "Tratamiento", "Diagnóstico registrado en el tratamiento.", "Diagnóstico ficticio de demostración"),
    "treatment.description": ("Descripción del tratamiento", "Tratamiento", "Descripción clínica general del tratamiento.", "Descripción ficticia"),
    "treatment.plan_number": ("Número del plan", "Tratamiento", "Número identificador del plan de tratamiento.", "PLAN-DEMO-001"),
    "procedure.name": ("Nombre del procedimiento", "Procedimiento", "Nombre del procedimiento asociado.", "Procedimiento de demostración"),
    "procedure.code": ("Código del procedimiento", "Procedimiento", "Código interno del procedimiento asociado.", "PROC-DEMO"),
    "procedure.description": ("Descripción del procedimiento", "Procedimiento", "Descripción del procedimiento asociado.", "Descripción ficticia"),
    "procedures.list": ("Lista de procedimientos", "Procedimiento", "Listado de todos los procedimientos cubiertos por el consentimiento.", "Procedimiento de demostración 1; Procedimiento de demostración 2"),
    "document.clinical_date": ("Fecha clínica", "Documento", "Fecha clínica en la zona horaria correspondiente.", "01/08/2026"),
    "document.generated_date": ("Fecha de generación", "Documento", "Fecha local en que se genera el documento.", "01/08/2026"),
    "document.local_time": ("Hora local", "Documento", "Hora local en que se genera el documento.", "10:30 a. m."),
    "document.country": ("País del documento", "Documento", "País configurado para el documento.", "País configurado"),
    "document.language": ("Idioma del documento", "Documento", "Idioma configurado para el documento.", "Español"),
    "document.version": ("Versión de plantilla", "Documento", "Número de la versión de plantilla utilizada.", "1"),
}


class ConsentTemplateError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(session: Session, context: AuthContext, metadata: RequestMetadata, *, action: str, template_id: UUID, version_id: UUID | None = None, detail: dict | None = None, result: str = "SUCCESS") -> None:
    safe_detail = {"version_id": str(version_id) if version_id else None, **(detail or {})}
    session.add(AuditEvent(company_id=context.user.company_id, user_id=context.user.id, session_id=context.auth_session.id, entity="consent_template", entity_id=template_id, action=action, result=result, detail=safe_detail, ip_address=metadata.ip_address, user_agent=metadata.user_agent))


def document_kind_catalog() -> list[CatalogItemResponse]:
    return [CatalogItemResponse(code=code, label=label, description="Tipo documental configurable; no constituye contenido jurídico aprobado.") for code, label in DOCUMENT_KIND_CATALOG]


def variable_catalog() -> list[CatalogItemResponse]:
    return [CatalogItemResponse(code=code, label=label, description=description, category=category, sample_value=sample) for code, (label, category, description, sample) in VARIABLE_CATALOG.items()]


def validate_content(content: str, *, require_registered: bool = False) -> VariableValidationResponse:
    syntax_errors: list[str] = []
    if HTML_PATTERN.search(content):
        syntax_errors.append("El HTML arbitrario no está permitido.")
    if DANGEROUS_URI_PATTERN.search(content):
        syntax_errors.append("El contenido contiene una URL peligrosa.")
    if MARKDOWN_LINK_PATTERN.search(content):
        syntax_errors.append("Los enlaces e imágenes Markdown no están permitidos en C019A.1.")
    if "{%" in content or "%}" in content or "{{{" in content or "}}}" in content:
        syntax_errors.append("La sintaxis de plantilla no es válida.")

    matched_tokens = VARIABLE_PATTERN.findall(content)
    all_tokens = ANY_TEMPLATE_PATTERN.findall(content)
    if len(all_tokens) != len(matched_tokens):
        syntax_errors.append("Existe una variable o expresión con sintaxis no permitida.")
    if content.count("{{") != len(all_tokens) or content.count("}}") != len(all_tokens):
        syntax_errors.append("Existen delimitadores de variable incompletos.")

    used = sorted(set(matched_tokens))
    invalid = sorted(item for item in used if item not in VARIABLE_CATALOG)
    if len(used) > 50:
        syntax_errors.append("Una versión no puede utilizar más de 50 variables distintas.")
    return VariableValidationResponse(valid=not syntax_errors and (not require_registered or not invalid), used_variables=used, invalid_variables=invalid, syntax_errors=syntax_errors)


def _ensure_safe_draft(content: str) -> VariableValidationResponse:
    validation = validate_content(content)
    if validation.syntax_errors:
        raise ConsentTemplateError(" ".join(validation.syntax_errors), 422)
    return validation


def _require_publishable(version: ConsentTemplateVersion) -> VariableValidationResponse:
    if not version.title.strip() or not version.content.strip():
        raise ConsentTemplateError("El título y el contenido son obligatorios para publicar.", 422)
    validation = validate_content(version.content, require_registered=True)
    if not validation.valid:
        detail = (["No se puede publicar. Corrige las siguientes variables no registradas: " + ", ".join(validation.invalid_variables)] if validation.invalid_variables else []) + validation.syntax_errors
        raise ConsentTemplateError(" ".join(detail), 422)
    return validation


def _require_template(session: Session, context: AuthContext, template_id: UUID, *, lock: bool = False) -> ConsentTemplate:
    statement = select(ConsentTemplate).where(ConsentTemplate.id == template_id, ConsentTemplate.company_id == context.user.company_id)
    if lock:
        statement = statement.with_for_update()
    template = session.scalar(statement)
    if template is None:
        raise ConsentTemplateError("Plantilla no encontrada.", 404)
    return template


def _ensure_not_read_only(template: ConsentTemplate) -> None:
    if getattr(template, "template_origin", "CLINIC_CUSTOM") == "DENTIA_LIBRARY":
        raise ConsentTemplateError("Las plantillas oficiales Dentia instaladas de forma exacta no se pueden editar. Crea una copia editable si necesitas cambios.", 409)


def _require_version(session: Session, context: AuthContext, template_id: UUID, version_id: UUID, *, lock: bool = False) -> tuple[ConsentTemplate, ConsentTemplateVersion]:
    template = _require_template(session, context, template_id, lock=lock)
    statement = select(ConsentTemplateVersion).where(ConsentTemplateVersion.id == version_id, ConsentTemplateVersion.template_id == template.id, ConsentTemplateVersion.company_id == context.user.company_id)
    if lock:
        statement = statement.with_for_update()
    version = session.scalar(statement)
    if version is None:
        raise ConsentTemplateError("Versión no encontrada.", 404)
    return template, version


def _can_edit_draft(context: AuthContext, version: ConsentTemplateVersion) -> bool:
    elevated = bool({"ADMINISTRATOR", "DENTIST_ADMIN"}.intersection(context.roles))
    return elevated or version.created_by == context.user.id


def _association_maps(session: Session, version_ids: list[UUID]):
    sites: dict[UUID, list[UUID]] = defaultdict(list)
    procedures: dict[UUID, list[UUID]] = defaultdict(list)
    specialties: dict[UUID, list[SpecialtyInput]] = defaultdict(list)
    if not version_ids:
        return sites, procedures, specialties
    for item in session.scalars(select(ConsentTemplateVersionSite).where(ConsentTemplateVersionSite.version_id.in_(version_ids))):
        sites[item.version_id].append(item.site_id)
    for item in session.scalars(select(ConsentTemplateVersionProcedure).where(ConsentTemplateVersionProcedure.version_id.in_(version_ids))):
        procedures[item.version_id].append(item.procedure_catalog_id)
    for item in session.scalars(select(ConsentTemplateVersionSpecialty).where(ConsentTemplateVersionSpecialty.version_id.in_(version_ids))):
        specialties[item.version_id].append(SpecialtyInput(code=item.specialty_code, name=item.specialty_name))
    return sites, procedures, specialties


def _legacy_assessment(version: ConsentTemplateVersion):
    return assess_legacy_patient_content(version.content)


def _version_response(version: ConsentTemplateVersion, maps) -> ConsentVersionResponse:
    sites, procedures, specialties = maps
    validation = validate_content(version.content)
    legacy = _legacy_assessment(version)
    return ConsentVersionResponse(id=version.id, template_id=version.template_id, version_number=version.version_number, status=version.status, title=version.title, content=version.content, content_format=version.content_format, used_variables=validation.used_variables, variable_schema_snapshot=version.variable_schema_snapshot, content_sha256=version.content_sha256, source_library_version_id=version.source_library_version_id, source_document_hash=version.source_document_hash, legacy_quarantined=legacy.is_legacy, legacy_quarantine_reasons=legacy.reasons, legacy_quarantine_message="Versión anterior no apta para nuevos consentimientos" if legacy.is_legacy else None, legal_review_status=version.legal_review_status, clinical_review_status=version.clinical_review_status, reviewed_countries=version.reviewed_countries or [], based_on_version_id=version.based_on_version_id, change_summary=version.change_summary, scope_type=version.scope_type, priority=version.priority, site_ids=sorted(sites[version.id], key=str), procedure_ids=sorted(procedures[version.id], key=str), specialties=sorted(specialties[version.id], key=lambda item: item.code), row_version=version.row_version, published_at=version.published_at, published_by=version.published_by, retired_at=version.retired_at, retire_reason=version.retire_reason, voided_at=version.voided_at, void_reason=version.void_reason, created_by=version.created_by, updated_by=version.updated_by, created_at=version.created_at, updated_at=version.updated_at)


def _template_response(template: ConsentTemplate, versions: list[ConsentTemplateVersion], maps) -> ConsentTemplateResponse:
    published = next((item for item in versions if item.status == "PUBLISHED"), None)
    drafts = [item for item in versions if item.status == "DRAFT"]
    return ConsentTemplateResponse(id=template.id, company_id=template.company_id, code=template.code, name=template.name, description=template.description, document_kind=template.document_kind, country_code=template.country_code, language_code=template.language_code, is_active=template.is_active, template_origin=template.template_origin, content_responsibility=template.content_responsibility, source_library_document_id=template.source_library_document_id, published_version=_version_response(published, maps) if published else None, draft_versions=[_version_response(item, maps) for item in drafts], versions_count=len(versions), created_by=template.created_by, updated_by=template.updated_by, created_at=template.created_at, updated_at=template.updated_at)


def _validate_associations(session: Session, context: AuthContext, payload: ConsentVersionDraftInput) -> None:
    company_id = context.user.company_id
    if payload.site_ids:
        count = session.scalar(select(func.count()).select_from(Site).where(Site.id.in_(payload.site_ids), Site.company_id == company_id)) or 0
        if count != len(payload.site_ids):
            raise ConsentTemplateError("Una o más sedes no pertenecen a la empresa activa.", 403)
    if payload.procedure_ids:
        count = session.scalar(select(func.count()).select_from(ProcedureCatalogItem).where(ProcedureCatalogItem.id.in_(payload.procedure_ids), ProcedureCatalogItem.company_id == company_id)) or 0
        if count != len(payload.procedure_ids):
            raise ConsentTemplateError("Uno o más procedimientos no pertenecen a la empresa activa.", 403)


def _replace_associations(session: Session, version: ConsentTemplateVersion, payload: ConsentVersionDraftInput) -> None:
    session.execute(delete(ConsentTemplateVersionSite).where(ConsentTemplateVersionSite.version_id == version.id))
    session.execute(delete(ConsentTemplateVersionProcedure).where(ConsentTemplateVersionProcedure.version_id == version.id))
    session.execute(delete(ConsentTemplateVersionSpecialty).where(ConsentTemplateVersionSpecialty.version_id == version.id))
    session.add_all([ConsentTemplateVersionSite(company_id=version.company_id, version_id=version.id, site_id=item) for item in payload.site_ids])
    session.add_all([ConsentTemplateVersionProcedure(company_id=version.company_id, version_id=version.id, procedure_catalog_id=item) for item in payload.procedure_ids])
    session.add_all([ConsentTemplateVersionSpecialty(company_id=version.company_id, version_id=version.id, specialty_code=item.code, specialty_name=item.name) for item in payload.specialties])


def _canonical_hash(template: ConsentTemplate, version: ConsentTemplateVersion, validation: VariableValidationResponse, maps) -> str:
    sites, procedures, specialties = maps
    payload = {
        "template": {
            "code": template.code,
            "document_kind": template.document_kind,
            "country_code": template.country_code,
            "language_code": template.language_code,
        },
        "version": {
            "number": version.version_number,
            "title": version.title,
            "content": version.content,
            "content_format": version.content_format,
            "scope_type": version.scope_type,
            "priority": version.priority,
            "variables": validation.used_variables,
            "site_ids": sorted(str(item) for item in sites[version.id]),
            "procedure_ids": sorted(str(item) for item in procedures[version.id]),
            "specialties": sorted(
                ({"code": item.code, "name": item.name} for item in specialties[version.id]),
                key=lambda item: item["code"],
            ),
        },
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def list_templates(session: Session, context: AuthContext, *, text_query: str | None = None, status: str | None = None, country: str | None = None, document_kind: str | None = None, site_id: UUID | None = None, procedure_id: UUID | None = None, specialty: str | None = None) -> ConsentTemplateListResponse:
    statement = select(ConsentTemplate).where(ConsentTemplate.company_id == context.user.company_id)
    if text_query:
        pattern = f"%{text_query.strip()}%"
        statement = statement.where(ConsentTemplate.name.ilike(pattern) | ConsentTemplate.code.ilike(pattern))
    if country:
        statement = statement.where(ConsentTemplate.country_code == country.upper())
    if document_kind:
        statement = statement.where(ConsentTemplate.document_kind == document_kind.upper())
    templates = list(session.scalars(statement.order_by(ConsentTemplate.updated_at.desc())))
    versions = list(session.scalars(select(ConsentTemplateVersion).where(ConsentTemplateVersion.template_id.in_([item.id for item in templates])).order_by(ConsentTemplateVersion.version_number.desc()))) if templates else []
    maps = _association_maps(session, [item.id for item in versions])
    versions_by_template: dict[UUID, list[ConsentTemplateVersion]] = defaultdict(list)
    for version in versions:
        versions_by_template[version.template_id].append(version)
    if status:
        normalized = status.upper()
        templates = [
            item
            for item in templates
            if (normalized == "ACTIVE" and item.is_active)
            or (normalized == "INACTIVE" and not item.is_active)
            or any(version.status == normalized for version in versions_by_template[item.id])
        ]
    responses = [_template_response(item, versions_by_template[item.id], maps) for item in templates]
    if site_id:
        responses = [item for item in responses if any(site_id in version.site_ids for version in [*(item.draft_versions), *([item.published_version] if item.published_version else [])])]
    if procedure_id:
        responses = [item for item in responses if any(procedure_id in version.procedure_ids for version in [*(item.draft_versions), *([item.published_version] if item.published_version else [])])]
    if specialty:
        normalized = specialty.strip().upper()
        responses = [item for item in responses if any(any(spec.code == normalized for spec in version.specialties) for version in [*(item.draft_versions), *([item.published_version] if item.published_version else [])])]
    return ConsentTemplateListResponse(items=responses, total=len(responses))


def get_template(session: Session, context: AuthContext, template_id: UUID) -> ConsentTemplateResponse:
    template = _require_template(session, context, template_id)
    versions = list(session.scalars(select(ConsentTemplateVersion).where(ConsentTemplateVersion.template_id == template.id).order_by(ConsentTemplateVersion.version_number.desc())))
    return _template_response(template, versions, _association_maps(session, [item.id for item in versions]))


def list_template_audit(session: Session, context: AuthContext, template_id: UUID) -> list[ConsentTemplateAuditResponse]:
    template = _require_template(session, context, template_id)
    events = list(session.scalars(select(AuditEvent).where(AuditEvent.company_id == context.user.company_id, AuditEvent.entity == "consent_template", AuditEvent.entity_id == template.id).order_by(AuditEvent.occurred_at.desc()).limit(100)))
    return [ConsentTemplateAuditResponse(id=item.id, action=item.action, result=item.result, user_id=item.user_id, occurred_at=item.occurred_at, detail=item.detail) for item in events]


def create_template(session: Session, context: AuthContext, payload: ConsentTemplateCreateRequest, metadata: RequestMetadata) -> ConsentTemplateResponse:
    _ensure_safe_draft(payload.initial_version.content)
    _validate_associations(session, context, payload.initial_version)
    template = ConsentTemplate(company_id=context.user.company_id, code=payload.code, name=payload.name, description=payload.description, document_kind=payload.document_kind, country_code=payload.country_code, language_code=payload.language_code, created_by=context.user.id, updated_by=context.user.id)
    session.add(template)
    try:
        session.flush()
        version = ConsentTemplateVersion(company_id=context.user.company_id, template_id=template.id, version_number=1, status="DRAFT", title=payload.initial_version.title, content=payload.initial_version.content, content_format=CONTENT_FORMAT, change_summary=payload.initial_version.change_summary, scope_type=payload.initial_version.scope_type, priority=payload.initial_version.priority, created_by=context.user.id, updated_by=context.user.id)
        session.add(version)
        session.flush()
        _replace_associations(session, version, payload.initial_version)
        _audit(session, context, metadata, action="CONSENT_TEMPLATE_CREATED", template_id=template.id, version_id=version.id, detail={"code": template.code})
        _audit(session, context, metadata, action="CONSENT_TEMPLATE_DRAFT_CREATED", template_id=template.id, version_id=version.id, detail={"version_number": 1})
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConsentTemplateError("Ya existe una plantilla con ese código en la empresa.", 409) from exc
    return get_template(session, context, template.id)


def update_template(session: Session, context: AuthContext, template_id: UUID, payload: ConsentTemplateUpdateRequest, metadata: RequestMetadata) -> ConsentTemplateResponse:
    template = _require_template(session, context, template_id, lock=True)
    _ensure_not_read_only(template)
    if not {"ADMINISTRATOR", "DENTIST_ADMIN"}.intersection(context.roles) and template.created_by != context.user.id:
        raise ConsentTemplateError("Solo el autor o un rol superior puede actualizar esta plantilla.", 403)
    has_published_history = bool(session.scalar(select(func.count()).select_from(ConsentTemplateVersion).where(ConsentTemplateVersion.template_id == template.id, ConsentTemplateVersion.status.in_(["PUBLISHED", "SUPERSEDED", "RETIRED"]))))
    protected = {"document_kind", "country_code", "language_code"}
    changes = payload.model_dump(exclude_unset=True)
    if has_published_history and protected.intersection(changes):
        raise ConsentTemplateError("País, idioma y tipo documental son inmutables después de la primera publicación.", 409)
    next_country = changes.get("country_code", template.country_code)
    next_language = changes.get("language_code", template.language_code)
    if next_language != f"es-{next_country}":
        raise ConsentTemplateError("El idioma debe corresponder al país de la plantilla.", 422)
    for field, value in changes.items():
        setattr(template, field, value)
    template.updated_by = context.user.id
    try:
        _audit(session, context, metadata, action="CONSENT_TEMPLATE_METADATA_UPDATED", template_id=template.id, detail={"fields": sorted(changes)})
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConsentTemplateError("El código ya está en uso dentro de la empresa.", 409) from exc
    return get_template(session, context, template.id)


def list_versions(session: Session, context: AuthContext, template_id: UUID) -> list[ConsentVersionResponse]:
    template = _require_template(session, context, template_id)
    versions = list(session.scalars(select(ConsentTemplateVersion).where(ConsentTemplateVersion.template_id == template.id).order_by(ConsentTemplateVersion.version_number.desc())))
    maps = _association_maps(session, [item.id for item in versions])
    return [_version_response(item, maps) for item in versions]


def get_version(session: Session, context: AuthContext, template_id: UUID, version_id: UUID) -> ConsentVersionResponse:
    _, version = _require_version(session, context, template_id, version_id)
    return _version_response(version, _association_maps(session, [version.id]))


def create_draft(session: Session, context: AuthContext, template_id: UUID, payload: ConsentVersionDraftInput, metadata: RequestMetadata) -> ConsentVersionResponse:
    template = _require_template(session, context, template_id, lock=True)
    _ensure_not_read_only(template)
    _ensure_safe_draft(payload.content)
    _validate_associations(session, context, payload)
    next_number = (session.scalar(select(func.max(ConsentTemplateVersion.version_number)).where(ConsentTemplateVersion.template_id == template.id)) or 0) + 1
    version = ConsentTemplateVersion(company_id=template.company_id, template_id=template.id, version_number=next_number, status="DRAFT", title=payload.title, content=payload.content, content_format=CONTENT_FORMAT, change_summary=payload.change_summary, scope_type=payload.scope_type, priority=payload.priority, created_by=context.user.id, updated_by=context.user.id)
    session.add(version)
    session.flush()
    _replace_associations(session, version, payload)
    _audit(session, context, metadata, action="CONSENT_TEMPLATE_DRAFT_CREATED", template_id=template.id, version_id=version.id, detail={"version_number": next_number})
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConsentTemplateError("No fue posible asignar el siguiente número de versión por una edición concurrente.", 409) from exc
    return get_version(session, context, template_id, version.id)


def update_draft(session: Session, context: AuthContext, template_id: UUID, version_id: UUID, payload: ConsentVersionUpdateRequest, metadata: RequestMetadata) -> ConsentVersionResponse:
    template, version = _require_version(session, context, template_id, version_id, lock=True)
    _ensure_not_read_only(template)
    if version.status != "DRAFT":
        raise ConsentTemplateError("Solo las versiones en borrador pueden editarse.", 409)
    if not _can_edit_draft(context, version):
        raise ConsentTemplateError("Solo el autor o un rol superior puede editar este borrador.", 403)
    if payload.row_version != version.row_version:
        raise ConsentTemplateError("El borrador fue actualizado por otro usuario. Recarga antes de continuar.", 409)
    _ensure_safe_draft(payload.content)
    _validate_associations(session, context, payload)
    version.title = payload.title
    version.content = payload.content
    version.change_summary = payload.change_summary
    version.scope_type = payload.scope_type
    version.priority = payload.priority
    version.row_version += 1
    version.updated_by = context.user.id
    _replace_associations(session, version, payload)
    _audit(session, context, metadata, action="CONSENT_TEMPLATE_DRAFT_UPDATED", template_id=template_id, version_id=version.id, detail={"row_version": version.row_version})
    _audit(session, context, metadata, action="CONSENT_TEMPLATE_ASSOCIATIONS_UPDATED", template_id=template_id, version_id=version.id, detail={"sites": len(payload.site_ids), "procedures": len(payload.procedure_ids), "specialties": len(payload.specialties)})
    session.commit()
    return get_version(session, context, template_id, version.id)


def preview_version(session: Session, context: AuthContext, template_id: UUID, version_id: UUID, metadata: RequestMetadata) -> ConsentPreviewResponse:
    _, version = _require_version(session, context, template_id, version_id)
    validation = validate_content(version.content, require_registered=True)
    rendered = version.content
    for key, (_, _, _, sample) in VARIABLE_CATALOG.items():
        rendered = re.sub(r"\{\{\s*" + re.escape(key) + r"\s*\}\}", sample, rendered)
    for invalid in validation.invalid_variables:
        rendered = re.sub(r"\{\{\s*" + re.escape(invalid) + r"\s*\}\}", f"[VARIABLE NO REGISTRADA: {invalid}]", rendered)
    _audit(session, context, metadata, action="CONSENT_TEMPLATE_PREVIEW_GENERATED", template_id=template_id, version_id=version.id, detail={"valid": validation.valid, "used_variables": validation.used_variables})
    session.commit()
    return ConsentPreviewResponse(warning=PREVIEW_WARNING, title=version.title, rendered_content=rendered, used_variables=validation.used_variables, validation=validation)


def validate_version(session: Session, context: AuthContext, template_id: UUID, version_id: UUID) -> VariableValidationResponse:
    _, version = _require_version(session, context, template_id, version_id)
    return validate_content(version.content, require_registered=True)


def publish_version(session: Session, context: AuthContext, template_id: UUID, version_id: UUID, metadata: RequestMetadata) -> ConsentVersionResponse:
    template, version = _require_version(session, context, template_id, version_id, lock=True)
    _ensure_not_read_only(template)
    if version.status == "PUBLISHED":
        raise ConsentTemplateError("La versión ya está publicada.", 409)
    if version.status != "DRAFT":
        raise ConsentTemplateError("Solo un borrador puede publicarse.", 409)
    validation = _require_publishable(version)
    current = session.scalar(select(ConsentTemplateVersion).where(ConsentTemplateVersion.template_id == template.id, ConsentTemplateVersion.status == "PUBLISHED").with_for_update())
    if current and current.id != version.id:
        current.status = "SUPERSEDED"
        current.updated_by = context.user.id
        current.row_version += 1
        _audit(session, context, metadata, action="CONSENT_TEMPLATE_VERSION_SUPERSEDED", template_id=template.id, version_id=current.id, detail={"replaced_by": str(version.id)})
        # PostgreSQL's partial unique index is immediate. Flush the old status
        # first so the new PUBLISHED row can enter the index in the same
        # transaction without a transient two-published state.
        session.flush()
    maps = _association_maps(session, [version.id])
    version.variable_schema_snapshot = {key: {"label": VARIABLE_CATALOG[key][0], "category": VARIABLE_CATALOG[key][1]} for key in validation.used_variables}
    version.content_sha256 = _canonical_hash(template, version, validation, maps)
    version.status = "PUBLISHED"
    version.published_at = _now()
    version.published_by = context.user.id
    version.updated_by = context.user.id
    version.row_version += 1
    _audit(session, context, metadata, action="CONSENT_TEMPLATE_VERSION_PUBLISHED", template_id=template.id, version_id=version.id, detail={"version_number": version.version_number, "content_sha256": version.content_sha256})
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConsentTemplateError("Otra publicación concurrente cambió la versión vigente. Recarga e intenta nuevamente.", 409) from exc
    return get_version(session, context, template_id, version.id)


def create_draft_from_version(session: Session, context: AuthContext, template_id: UUID, version_id: UUID, payload: ConsentVersionCreateFromRequest, metadata: RequestMetadata) -> ConsentVersionResponse:
    template, source = _require_version(session, context, template_id, version_id, lock=True)
    _ensure_not_read_only(template)
    if source.status == "VOIDED":
        raise ConsentTemplateError("Un borrador anulado no puede usarse como base.", 409)
    next_number = (session.scalar(select(func.max(ConsentTemplateVersion.version_number)).where(ConsentTemplateVersion.template_id == template.id)) or 0) + 1
    version = ConsentTemplateVersion(company_id=template.company_id, template_id=template.id, version_number=next_number, status="DRAFT", title=source.title, content=source.content, content_format=source.content_format, based_on_version_id=source.id, change_summary=payload.change_summary, scope_type=source.scope_type, priority=source.priority, created_by=context.user.id, updated_by=context.user.id)
    session.add(version)
    session.flush()
    maps = _association_maps(session, [source.id])
    source_payload = ConsentVersionDraftInput(title=source.title, content=source.content, change_summary=payload.change_summary, scope_type=source.scope_type, priority=source.priority, site_ids=maps[0][source.id], procedure_ids=maps[1][source.id], specialties=maps[2][source.id])
    _replace_associations(session, version, source_payload)
    _audit(session, context, metadata, action="CONSENT_TEMPLATE_VERSION_DRAFTED_FROM_VERSION", template_id=template.id, version_id=version.id, detail={"based_on_version_id": str(source.id), "version_number": next_number})
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConsentTemplateError("No fue posible asignar el siguiente número de versión por una edición concurrente.", 409) from exc
    return get_version(session, context, template_id, version.id)


def retire_version(session: Session, context: AuthContext, template_id: UUID, version_id: UUID, payload: ConsentReasonRequest, metadata: RequestMetadata) -> ConsentVersionResponse:
    template, version = _require_version(session, context, template_id, version_id, lock=True)
    _ensure_not_read_only(template)
    if version.status != "PUBLISHED":
        raise ConsentTemplateError("Solo la versión publicada vigente puede retirarse.", 409)
    version.status = "RETIRED"
    version.retired_at = _now()
    version.retired_by = context.user.id
    version.retire_reason = payload.reason
    version.updated_by = context.user.id
    version.row_version += 1
    _audit(session, context, metadata, action="CONSENT_TEMPLATE_VERSION_RETIRED", template_id=template_id, version_id=version.id, detail={"reason": payload.reason})
    session.commit()
    return get_version(session, context, template_id, version.id)


def void_draft(session: Session, context: AuthContext, template_id: UUID, version_id: UUID, payload: ConsentReasonRequest, metadata: RequestMetadata) -> ConsentVersionResponse:
    template, version = _require_version(session, context, template_id, version_id, lock=True)
    _ensure_not_read_only(template)
    if version.status != "DRAFT":
        raise ConsentTemplateError("Solo un borrador puede anularse.", 409)
    if not _can_edit_draft(context, version):
        raise ConsentTemplateError("Solo el autor o un rol superior puede anular este borrador.", 403)
    version.status = "VOIDED"
    version.voided_at = _now()
    version.voided_by = context.user.id
    version.void_reason = payload.reason
    version.updated_by = context.user.id
    version.row_version += 1
    _audit(session, context, metadata, action="CONSENT_TEMPLATE_DRAFT_VOIDED", template_id=template_id, version_id=version.id, detail={"reason": payload.reason})
    session.commit()
    return get_version(session, context, template_id, version.id)


def find_applicable_published_templates(session: Session, *, company_id: UUID, country_code: str, language_code: str, site_id: UUID | None = None, procedure_ids: set[UUID] | None = None, specialty_codes: set[str] | None = None) -> list[ApplicableTemplateCandidate]:
    procedures = procedure_ids or set()
    specialties = {item.upper() for item in (specialty_codes or set())}
    templates = list(session.scalars(select(ConsentTemplate).where(ConsentTemplate.company_id == company_id, ConsentTemplate.country_code == country_code.upper(), ConsentTemplate.language_code == language_code, ConsentTemplate.is_active.is_(True), ConsentTemplate.document_kind.in_(OFFICIAL_STANDARD_CONSENT_KINDS))))
    if not templates:
        return []
    versions = list(session.scalars(select(ConsentTemplateVersion).where(ConsentTemplateVersion.template_id.in_([item.id for item in templates]), ConsentTemplateVersion.company_id == company_id, ConsentTemplateVersion.status == "PUBLISHED")))
    maps = _association_maps(session, [item.id for item in versions])
    template_map = {item.id: item for item in templates}
    candidates: list[ApplicableTemplateCandidate] = []
    for version in versions:
        if _legacy_assessment(version).is_legacy:
            continue
        site_scope = set(maps[0][version.id])
        procedure_scope = set(maps[1][version.id])
        specialty_scope = {item.code for item in maps[2][version.id]}
        if site_scope and (site_id is None or site_id not in site_scope):
            continue
        if version.scope_type == "SPECIFIC":
            if procedure_scope and not procedure_scope.intersection(procedures):
                continue
            if specialty_scope and not specialty_scope.intersection(specialties):
                continue
        template = template_map[version.template_id]
        candidates.append(ApplicableTemplateCandidate(template_id=template.id, version_id=version.id, template_code=template.code, template_name=template.name, version_number=version.version_number, country_code=template.country_code, language_code=template.language_code, scope_type=version.scope_type, priority=version.priority, content=version.content, content_sha256=version.content_sha256 or "", variable_schema_snapshot=version.variable_schema_snapshot or {}, site_ids=maps[0][version.id], procedure_ids=maps[1][version.id], specialties=maps[2][version.id]))
    return sorted(candidates, key=lambda item: (item.scope_type == "SPECIFIC", bool(item.procedure_ids), bool(item.specialties), bool(item.site_ids), item.priority, item.version_number), reverse=True)
