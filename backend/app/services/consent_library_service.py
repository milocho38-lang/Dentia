from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from copy import deepcopy
from datetime import datetime, time, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.consent_template import (
    ConsentLibraryDocument,
    ConsentLibraryInstallation,
    ConsentLibraryVersion,
    ConsentTemplate,
    ConsentTemplateVersion,
)
from app.schemas.consent_library_schema import (
    ConsentLibraryEquivalenceApprovalRequest,
    ConsentLibraryDocumentResponse,
    ConsentLibraryInstallRequest,
    ConsentLibraryInstallResponse,
    ConsentLibraryListResponse,
    ConsentLibrarySourceResponse,
    ConsentLibraryVersionResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.tenant_country import TenantCountryError, company_country_code
from app.services.consent_library_normalization import (
    NORM3_SCHEMA_VERSION,
    NORM5_SCHEMA_VERSION,
    NORMALIZED_CONTENT_FIELD,
    assess_electronic_readiness,
    parse_normalization_metadata,
    sha256_text,
    validate_patient_facing_content,
)
from app.services.consent_template_service import CONTENT_FORMAT, VARIABLE_CATALOG, validate_content

PACKAGE_PATH = Path(__file__).resolve().parents[1] / "library_data" / "consents" / "v4" / "documents.json"
ODONTOPEDIATRIC_DOCUMENT_CODE = "CONS_ODONTOPEDIATRIA"
ODONTOPEDIATRIC_PRODUCTION_VERSION = 4
ODONTOPEDIATRIC_PRODUCTION_PACKAGE = "LIB1_NORM_V2_NORM5_PRODUCTION_READINESS"
MAX_TEMPLATE_CODE_LENGTH = 80
MAX_CLONE_CODE_ATTEMPTS = 25
TEMPLATE_CODE_UNIQUE_CONSTRAINT = "uq_consent_template_empresa_codigo"
EXACT_INSTALL_UNIQUE_INDEX = "uq_consent_library_install_exact_company_version"
STANDARD_CONSENT_DOCUMENT_KINDS = frozenset({"GENERAL_CLINICAL_CONSENT", "PROCEDURE_CONSENT", "TREATMENT_AUTHORIZATION"})
REQUIRED_APPROVAL_CHECKS = (
    "clinical_text_faithful",
    "risks_preserved",
    "warnings_preserved",
    "values_preserved",
    "variables_correct",
    "titles_limits_correct",
    "signer_correct",
    "classification_correct",
    "country_approved",
    "odontological_review",
    "legal_equivalence_review",
)
logger = logging.getLogger(__name__)


def _production_ready_library_item(item: dict) -> dict:
    """Derive the immutable odontopediatric metadata correction from NORM5.

    Version 3 remains untouched in the database. Version 4 freezes the exact
    same patient-facing text and hashes while correcting the obsolete channel
    capability metadata after the responsible-adult flow was validated.
    """
    if item.get("code") != ODONTOPEDIATRIC_DOCUMENT_CODE:
        return item
    corrected = deepcopy(item)
    corrected["supports_electronic_signature"] = True
    corrected["source_package_version"] = ODONTOPEDIATRIC_PRODUCTION_PACKAGE
    derived_versions: list[dict] = []
    for version in corrected.get("versions", []):
        derived = deepcopy(version)
        if derived.get("version_number") == ODONTOPEDIATRIC_PRODUCTION_VERSION - 1:
            derived["version_number"] = ODONTOPEDIATRIC_PRODUCTION_VERSION
            notes = list(derived.get("transformation_notes", []))
            notes.append("production_readiness_change=legacy_supports_electronic_signature_corrected_true")
            notes.append("content_change=none")
            derived["transformation_notes"] = notes
            derived["review_notes"] = (
                "Nueva versión inmutable: corrige únicamente la capacidad electrónica legacy; "
                "el contenido normalizado y sus hashes permanecen sin cambios."
            )
        derived_versions.append(derived)
    corrected["versions"] = derived_versions
    return corrected


def _variable_schema_snapshot(variable_codes: list[str]) -> dict:
    return {code: {"label": VARIABLE_CATALOG[code][0], "category": VARIABLE_CATALOG[code][1]} for code in variable_codes if code in VARIABLE_CATALOG}


def default_source_pdf_path() -> Path:
    override = os.environ.get("DENTIA_CONSENT_LIBRARY_SOURCE_PDF")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "local_inputs" / "consent_library" / "CONSENTIMIENTOS_PROPUESTOS.pdf"


def verify_source_pdf_hash(expected_sha256: str, source_pdf_path: Path | None = None) -> dict:
    path = source_pdf_path or default_source_pdf_path()
    if not path.exists():
        return {"checked": False, "path": str(path), "reason": "source_pdf_not_available"}
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ConsentLibraryError("El hash del PDF fuente no coincide con el paquete de biblioteca.", 422)
    return {"checked": True, "path": str(path), "sha256": actual}


DOCUMENT_KIND_MAP = {
    "INFORMED_CONSENT": "PROCEDURE_CONSENT",
    "TREATMENT_REFUSAL": "TREATMENT_REJECTION",
    "CERTIFICATE": "INFORMATION_ACKNOWLEDGEMENT",
    "POST_CARE_INSTRUCTIONS": "INFORMATION_ACKNOWLEDGEMENT",
    "PRE_CARE_INSTRUCTIONS": "INFORMATION_ACKNOWLEDGEMENT",
    "NO_WARRANTY_ACKNOWLEDGEMENT": "INFORMATION_ACKNOWLEDGEMENT",
    "AESTHETIC_APPROVAL": "INFORMATION_ACKNOWLEDGEMENT",
    "TREATMENT_TERMINATION_ACKNOWLEDGEMENT": "INFORMATION_ACKNOWLEDGEMENT",
}


class ConsentLibraryError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(session: Session, context: AuthContext, metadata: RequestMetadata, *, action: str, document_id: UUID | None = None, version_id: UUID | None = None, detail: dict | None = None, result: str = "SUCCESS") -> None:
    session.add(AuditEvent(company_id=context.user.company_id, user_id=context.user.id, session_id=context.auth_session.id, entity="consent_library", entity_id=document_id, action=action, result=result, detail={"library_version_id": str(version_id) if version_id else None, **(detail or {})}, ip_address=metadata.ip_address, user_agent=metadata.user_agent))


def _is_norm_v2_version(version: ConsentLibraryVersion) -> bool:
    metadata = parse_normalization_metadata(version.transformation_notes)
    schema = metadata.get("normalization_schema_version")
    return isinstance(schema, str) and schema.startswith("LIB1_NORM_V2")


def _version_sort_key(version: ConsentLibraryVersion) -> tuple:
    return (
        version.country_code,
        version.language_code,
        0 if _is_norm_v2_version(version) else 1,
        -version.version_number,
        version.created_at or datetime.min.replace(tzinfo=timezone.utc),
    )


def _current_version_ids(versions: list[ConsentLibraryVersion]) -> set[UUID]:
    grouped: dict[tuple[str, str], list[ConsentLibraryVersion]] = {}
    for version in versions:
        if version.publication_status == "RETIRED":
            continue
        grouped.setdefault((version.country_code, version.language_code), []).append(version)
    current: set[UUID] = set()
    for candidates in grouped.values():
        norm_v2 = [item for item in candidates if _is_norm_v2_version(item)]
        pool = norm_v2 or candidates
        selected = sorted(pool, key=lambda item: (item.version_number, item.created_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)[0]
        current.add(selected.id)
    return current


def _version_response(version: ConsentLibraryVersion, *, is_current: bool = False, document_type: str | None = None) -> ConsentLibraryVersionResponse:
    response = ConsentLibraryVersionResponse.model_validate(version)
    metadata = parse_normalization_metadata(version.transformation_notes)
    signer_compatibility = metadata["signer_compatibility"] if metadata["signer_compatibility"] != "UNKNOWN" else "UNKNOWN"
    readiness_status = metadata["electronic_readiness_status"]
    readiness_findings = list(metadata["electronic_readiness_findings"])
    if readiness_status == "UNKNOWN":
        assessed = assess_electronic_readiness(
            version.content,
            country_code=version.country_code,
            document_type=document_type,
            signer_compatibility=signer_compatibility,
        )
        readiness_status = assessed.status
        readiness_findings = [f"{item.severity}:{item.code}" for item in assessed.findings]
    response.normalization_schema_version = metadata["normalization_schema_version"]
    response.normalization_status = metadata["normalization_status"]
    response.signer_compatibility = metadata["signer_compatibility"]
    response.signer_blocking_category = metadata["signer_blocking_category"]
    response.signer_blocking_reason = metadata["signer_blocking_reason"]
    response.signer_blocking_term = metadata["signer_blocking_term"]
    response.signer_blocking_line = metadata["signer_blocking_line"]
    response.signer_blocking_context = metadata["signer_blocking_context"]
    response.adult_variant_required = bool(metadata["adult_variant_required"])
    response.normalization_alerts = metadata["normalization_alerts"]
    response.electronic_readiness_status = readiness_status
    response.electronic_readiness_findings = readiness_findings
    response.norm5_result = metadata["norm5_result"]
    response.is_current = is_current
    response.is_legacy = not _is_norm_v2_version(version)
    response.historical_message = "Versión histórica no apta para nuevos consentimientos." if response.is_legacy and not is_current else None
    return response


def _document_response(document: ConsentLibraryDocument, versions: list[ConsentLibraryVersion], installs: set[tuple[UUID, str]]) -> ConsentLibraryDocumentResponse:
    response = ConsentLibraryDocumentResponse.model_validate(document)
    current_ids = _current_version_ids(versions)
    response.versions = [_version_response(item, is_current=item.id in current_ids, document_type=document.document_type) for item in sorted(versions, key=_version_sort_key)]
    response.installed_exact = any((version.id, "EXACT") in installs for version in versions)
    response.installed_clone = any((version.id, "CLONE") in installs for version in versions)
    return response


def list_library(session: Session, context: AuthContext, *, text_query: str | None = None, country: str | None = None, document_type: str | None = None, specialty: str | None = None, category: str | None = None, signer_scope: str | None = None, publication_status: str | None = None) -> ConsentLibraryListResponse:
    if "PLATFORM_ADMIN" not in context.roles:
        company = session.get(Company, context.user.company_id)
        if company is None:
            raise ConsentLibraryError("Empresa no encontrada.", 404)
        try:
            country = company_country_code(company)
        except TenantCountryError as exc:
            raise ConsentLibraryError(str(exc), 409) from exc
    statement = select(ConsentLibraryDocument).where(ConsentLibraryDocument.is_active.is_(True))
    if text_query:
        pattern = f"%{text_query.strip()}%"
        statement = statement.where(ConsentLibraryDocument.title.ilike(pattern) | ConsentLibraryDocument.code.ilike(pattern))
    if document_type:
        statement = statement.where(ConsentLibraryDocument.document_type == document_type.upper())
    if specialty:
        statement = statement.where(ConsentLibraryDocument.specialty_code == specialty.upper())
    if category:
        statement = statement.where(ConsentLibraryDocument.category.ilike(f"%{category.strip()}%"))
    if signer_scope:
        statement = statement.where(ConsentLibraryDocument.signer_scope == signer_scope.upper())
    documents = list(session.scalars(statement.order_by(ConsentLibraryDocument.category, ConsentLibraryDocument.title)))
    if not documents:
        return ConsentLibraryListResponse(items=[], total=0)
    version_statement = select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id.in_([item.id for item in documents]))
    if country:
        version_statement = version_statement.where(ConsentLibraryVersion.country_code == country.upper())
    if publication_status:
        version_statement = version_statement.where(ConsentLibraryVersion.publication_status == publication_status.upper())
    versions = list(session.scalars(version_statement))
    versions_by_document: dict[UUID, list[ConsentLibraryVersion]] = {}
    for version in versions:
        versions_by_document.setdefault(version.library_document_id, []).append(version)
    install_rows = session.scalars(select(ConsentLibraryInstallation).where(ConsentLibraryInstallation.company_id == context.user.company_id))
    installs = {(row.library_version_id, row.installation_mode) for row in install_rows}
    items = [_document_response(document, versions_by_document.get(document.id, []), installs) for document in documents if versions_by_document.get(document.id)]
    return ConsentLibraryListResponse(items=items, total=len(items))


def get_library_version(session: Session, version_id: UUID) -> tuple[ConsentLibraryDocument, ConsentLibraryVersion]:
    version = session.get(ConsentLibraryVersion, version_id)
    if version is None:
        raise ConsentLibraryError("Versión de biblioteca no encontrada.", 404)
    document = session.get(ConsentLibraryDocument, version.library_document_id)
    if document is None or not document.is_active:
        raise ConsentLibraryError("Documento de biblioteca no disponible.", 404)
    return document, version


def get_library_source_for_review(session: Session, version_id: UUID) -> ConsentLibrarySourceResponse:
    document, version = get_library_version(session, version_id)
    return ConsentLibrarySourceResponse(
        document_id=document.id,
        version_id=version.id,
        document_code=document.code,
        title=document.title,
        country_code=version.country_code,
        language_code=version.language_code,
        source_text=version.source_text,
        normalized_content=version.content,
        source_text_sha256=version.source_text_sha256,
        normalized_content_sha256=version.normalized_content_sha256,
        source_pages=version.source_pages or [],
        source_reference=document.source_reference,
    )


def _sanitize_template_code_part(value: object) -> str:
    cleaned = re.sub(r"[^A-Z0-9_-]+", "_", str(value or "").upper()).strip("_-")
    return cleaned or "DOC"


def _fit_template_code(raw_code: str, sequence: int = 1) -> str:
    suffix = "" if sequence == 1 else f"-{sequence}"
    candidate = f"{raw_code}{suffix}"
    if len(candidate) <= MAX_TEMPLATE_CODE_LENGTH:
        return candidate
    digest = hashlib.sha1(raw_code.encode("utf-8")).hexdigest()[:8].upper()
    reserved = len(suffix) + len(digest) + 1
    prefix = raw_code[: MAX_TEMPLATE_CODE_LENGTH - reserved].rstrip("_-")
    return f"{prefix}-{digest}{suffix}"


def _template_code(document: ConsentLibraryDocument, version: ConsentLibraryVersion, mode: str, sequence: int = 1) -> str:
    document_code = _sanitize_template_code_part(document.code)
    country = _sanitize_template_code_part(version.country_code)
    if mode == "EXACT":
        return _fit_template_code(f"DENTIA-{document_code}-{country}-OFICIAL")
    return _fit_template_code(f"DENTIA-{document_code}-{country}-V{version.version_number}-COPIA", sequence)


def _integrity_constraint_name(exc: IntegrityError) -> str | None:
    diagnostic = getattr(getattr(exc, "orig", None), "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    return str(constraint_name) if constraint_name else None


def _ensure_installable(document: ConsentLibraryDocument, version: ConsentLibraryVersion, *, exact: bool) -> None:
    validation = validate_content(version.content, require_registered=True)
    if not validation.valid:
        raise ConsentLibraryError("La versión de biblioteca contiene variables no registradas o sintaxis inválida.", 422)
    metadata = parse_normalization_metadata(version.transformation_notes)
    if metadata["electronic_readiness_status"] == "BLOCKED":
        raise ConsentLibraryError("Pendiente de adaptación para flujo electrónico.", 409)
    patient_validation = validate_patient_facing_content(
        version.content,
        allowed_variables=set(VARIABLE_CATALOG.keys()),
        document_type=document.document_type,
        signer_compatibility=metadata["signer_compatibility"] if metadata["signer_compatibility"] != "UNKNOWN" else document.signer_scope,
        normalized_hash=version.normalized_content_sha256,
        source_text=version.source_text,
        country_code=version.country_code,
        enforce_electronic_readiness=exact,
    )
    if patient_validation.status == "BLOCKED" or metadata["normalization_status"] == "BLOCKED":
        reason = metadata.get("signer_blocking_reason") or ", ".join(patient_validation.blockers) or "normalización o compatibilidad del firmante"
        raise ConsentLibraryError(f"La versión de biblioteca está bloqueada para uso con pacientes: {reason}", 409)
    if not exact and (document.document_type != "INFORMED_CONSENT" or (metadata["signer_compatibility"] not in {"UNKNOWN", "ADULT_SELF", "PATIENT_SELF", "ADULT_OR_REPRESENTATIVE", "PATIENT_OR_RESPONSIBLE_ADULT", "REPRESENTATIVE_REQUIRED", "RESPONSIBLE_ADULT_REQUIRED"})):
        raise ConsentLibraryError("Esta versión no puede clonarse para el flujo electrónico actual porque requiere un flujo documental o firmante diferente.", 409)
    if document.document_type != "INFORMED_CONSENT" or document.signer_scope not in {"ADULT_SELF", "PATIENT_SELF", "ADULT_OR_REPRESENTATIVE", "PATIENT_OR_RESPONSIBLE_ADULT", "REPRESENTATIVE_REQUIRED", "RESPONSIBLE_ADULT_REQUIRED"}:
        # Se puede clonar para trabajo futuro, pero no activar como consentimiento común oficial.
        if exact:
            raise ConsentLibraryError("Este documento está clasificado como especial y no puede instalarse como consentimiento común oficial.", 409)


def install_library_version(session: Session, context: AuthContext, version_id: UUID, payload: ConsentLibraryInstallRequest, metadata: RequestMetadata, *, mode: str) -> ConsentLibraryInstallResponse:
    exact = mode == "EXACT"
    document, version = get_library_version(session, version_id)
    company = session.get(Company, context.user.company_id)
    if company is None:
        raise ConsentLibraryError("Empresa no encontrada.", 404)
    try:
        tenant_country = company_country_code(company)
    except TenantCountryError as exc:
        raise ConsentLibraryError(str(exc), 409) from exc
    if version.country_code != tenant_country:
        raise ConsentLibraryError(
            "La variante seleccionada no corresponde al país configurado para la empresa.",
            409,
        )
    sibling_versions = list(session.scalars(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == version.country_code, ConsentLibraryVersion.language_code == version.language_code)))
    if version.id not in _current_version_ids(sibling_versions):
        raise ConsentLibraryError("Esta es una versión histórica y no puede utilizarse para crear nuevos consentimientos.", 409)
    _ensure_installable(document, version, exact=exact)
    existing = None
    if exact:
        existing = session.scalar(select(ConsentLibraryInstallation).where(ConsentLibraryInstallation.company_id == context.user.company_id, ConsentLibraryInstallation.library_version_id == version.id, ConsentLibraryInstallation.installation_mode == mode))
    if existing:
        return ConsentLibraryInstallResponse(mode=mode, template_id=existing.installed_template_id, version_id=existing.installed_version_id, already_installed=True, content_responsibility=existing.content_responsibility, message="La versión ya estaba instalada en esta clínica.")
    version_status = "DRAFT"
    validation = validate_content(version.content)
    patient_validation = validate_patient_facing_content(
        version.content,
        allowed_variables=set(VARIABLE_CATALOG.keys()),
        document_type=document.document_type,
        signer_compatibility=parse_normalization_metadata(version.transformation_notes)["signer_compatibility"],
        normalized_hash=version.normalized_content_sha256,
        source_text=version.source_text,
        country_code=version.country_code,
        enforce_electronic_readiness=exact,
    )
    if patient_validation.status == "BLOCKED":
        raise ConsentLibraryError("La plantilla instalada no superó la validación posterior de contenido para paciente.", 422)
    attempts = 1 if exact else MAX_CLONE_CODE_ATTEMPTS
    for sequence in range(1, attempts + 1):
        try:
            template = ConsentTemplate(
                company_id=context.user.company_id,
                code=_template_code(document, version, mode, sequence),
                name=document.title,
                description=document.summary,
                document_kind=DOCUMENT_KIND_MAP[document.document_type],
                country_code=version.country_code,
                language_code=version.language_code,
                is_active=True,
                template_origin="DENTIA_LIBRARY" if exact else "CLONED_FROM_DENTIA",
                source_library_document_id=document.id,
                content_responsibility="CLINIC",
                created_by=context.user.id,
                updated_by=context.user.id,
            )
            session.add(template)
            session.flush()
            installed_version = ConsentTemplateVersion(
                company_id=context.user.company_id,
                template_id=template.id,
                version_number=1,
                status=version_status,
                title=version.content.split("\n", 1)[0].replace("#", "").strip() or document.title,
                content=version.content,
                content_format=CONTENT_FORMAT,
                variable_schema_snapshot=_variable_schema_snapshot(validation.used_variables),
                content_sha256=None,
                source_library_version_id=version.id,
                source_document_hash=document.source_document_hash,
                legal_review_status=version.legal_review_status if exact else "CLINIC_REVIEW_REQUIRED_AFTER_CLONE",
                clinical_review_status=version.clinical_review_status if exact else "CLINIC_REVIEW_REQUIRED_AFTER_CLONE",
                reviewed_countries=version.reviewed_countries if exact else [],
                change_summary=payload.change_summary or ("Instalación exacta desde biblioteca Dentia." if exact else f"Copia editable creada desde biblioteca Dentia v{version.version_number}."),
                scope_type="GENERAL",
                priority=0,
                published_at=None,
                published_by=None,
                installed_from_library_at=_now(),
                created_by=context.user.id,
                updated_by=context.user.id,
            )
            session.add(installed_version)
            session.flush()
            install = ConsentLibraryInstallation(
                company_id=context.user.company_id,
                library_document_id=document.id,
                library_version_id=version.id,
                installed_template_id=template.id,
                installed_version_id=installed_version.id,
                installation_mode=mode,
                content_responsibility="CLINIC",
                installed_by=context.user.id,
                installed_at=_now(),
            )
            session.add(install)
            _audit(
                session,
                context,
                metadata,
                action="CONSENT_LIBRARY_INSTALLED" if exact else "CONSENT_LIBRARY_CLONED",
                document_id=document.id,
                version_id=version.id,
                detail={
                    "mode": mode,
                    "template_id": str(template.id),
                    "installed_version_id": str(installed_version.id),
                    "template_code": template.code,
                    "source_library_version_number": version.version_number,
                    "source_normalized_content_hash": version.normalized_content_sha256,
                },
            )
            session.commit()
            return ConsentLibraryInstallResponse(mode=mode, template_id=template.id, version_id=installed_version.id, already_installed=False, content_responsibility=install.content_responsibility, message="Plantilla sugerida por Dentia agregada para revisión de la clínica." if exact else "Copia editable creada para la clínica.")
        except IntegrityError as exc:
            session.rollback()
            constraint_name = _integrity_constraint_name(exc)
            if exact and constraint_name in {TEMPLATE_CODE_UNIQUE_CONSTRAINT, EXACT_INSTALL_UNIQUE_INDEX, "uq_consent_library_install_company_version_mode"}:
                recovered = session.scalar(select(ConsentLibraryInstallation).where(ConsentLibraryInstallation.company_id == context.user.company_id, ConsentLibraryInstallation.library_version_id == version.id, ConsentLibraryInstallation.installation_mode == mode))
                if recovered:
                    return ConsentLibraryInstallResponse(mode=mode, template_id=recovered.installed_template_id, version_id=recovered.installed_version_id, already_installed=True, content_responsibility=recovered.content_responsibility, message="La versión ya estaba instalada en esta clínica.")
            if not exact and constraint_name == TEMPLATE_CODE_UNIQUE_CONSTRAINT:
                continue
            logger.exception("Unexpected integrity error while installing consent library version %s for company %s.", version.id, context.user.company_id)
            raise ConsentLibraryError("No fue posible instalar la plantilla. Intente nuevamente." if exact else "No fue posible crear la copia editable. Intente nuevamente.", 500) from exc
    raise ConsentLibraryError("No fue posible crear la copia editable. Intente nuevamente.", 409)


def approve_library_equivalence(session: Session, context: AuthContext, version_id: UUID, payload: ConsentLibraryEquivalenceApprovalRequest, metadata: RequestMetadata) -> ConsentLibraryVersionResponse:
    document, version = get_library_version(session, version_id)
    missing = [field for field in REQUIRED_APPROVAL_CHECKS if not getattr(payload, field)]
    if missing:
        raise ConsentLibraryError("No es posible aprobar equivalencia: faltan casillas obligatorias del checklist.", 422)
    reviewed_at = datetime.combine(payload.reviewed_date, time.min, tzinfo=timezone.utc)
    checklist_snapshot = payload.model_dump(mode="json")
    version.legal_review_status = "APPROVED"
    version.clinical_review_status = "APPROVED"
    version.publication_status = "PUBLISHED"
    version.reviewed_countries = sorted(set([*(version.reviewed_countries or []), version.country_code]))
    version.reviewed_at = reviewed_at
    version.review_reference = payload.review_reference
    version.review_notes = f"Equivalencia aprobada por {payload.reviewer_name}. Motivo: {payload.reason}"
    version.equivalence_reviewer_name = payload.reviewer_name
    version.equivalence_review_reason = payload.reason
    version.equivalence_checklist_snapshot = checklist_snapshot
    _audit(
        session,
        context,
        metadata,
        action="CONSENT_LIBRARY_EQUIVALENCE_APPROVED",
        document_id=document.id,
        version_id=version.id,
        detail={
            "document_code": document.code,
            "country_code": version.country_code,
            "language_code": version.language_code,
            "review_reference": payload.review_reference,
            "reviewer_name": payload.reviewer_name,
            "reviewed_date": payload.reviewed_date.isoformat(),
            "checklist": checklist_snapshot,
        },
    )
    session.commit()
    return _version_response(version, document_type=document.document_type)


def _canonical_document_hash(document_payload: dict) -> str:
    return hashlib.sha256(json.dumps(document_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_library_package(path: Path = PACKAGE_PATH, *, verify_source: bool = True, source_pdf_path: Path | None = None) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("source_page_count") != 39:
        raise ConsentLibraryError("El paquete debe referenciar exclusivamente el PDF autoritativo de 39 páginas.", 422)
    if payload.get("source_file_sha256") and len(payload["source_file_sha256"]) != 64:
        raise ConsentLibraryError("Hash de fuente inválido en paquete de biblioteca.", 422)
    if verify_source:
        payload["source_pdf_verification"] = verify_source_pdf_hash(payload.get("source_file_sha256", ""), source_pdf_path)
    seen_codes: set[str] = set()
    strict_norm3 = payload.get("normalization_schema_version") in {NORM3_SCHEMA_VERSION, NORM5_SCHEMA_VERSION} or str(payload.get("package_version") or "").startswith("LIB1_NORM_V2")
    for document in payload.get("documents", []):
        code = document.get("code")
        if not code or code in seen_codes:
            raise ConsentLibraryError("El paquete contiene códigos duplicados o vacíos.", 422)
        seen_codes.add(code)
        for version in document.get("versions", []):
            if version.get("country_code") not in {"CO", "CL"}:
                raise ConsentLibraryError(f"País inválido en {code}.", 422)
            if version.get("language_code") != f"es-{version.get('country_code')}":
                raise ConsentLibraryError(f"Idioma inválido en {code}.", 422)
            normalized_content = version.get(NORMALIZED_CONTENT_FIELD) if strict_norm3 else version.get(NORMALIZED_CONTENT_FIELD) or version.get("content", "")
            if strict_norm3 and not normalized_content:
                raise ConsentLibraryError(f"Contenido normalizado ausente en {code}.", 422)
            if strict_norm3 and version.get("content") != normalized_content:
                raise ConsentLibraryError(f"Contenido ambiguo en {code}: content debe coincidir con normalized_content_markdown.", 422)
            if hashlib.sha256(version.get("source_text", "").encode("utf-8")).hexdigest() != version.get("source_text_sha256"):
                raise ConsentLibraryError(f"Hash de texto fuente no coincide en {code}.", 422)
            if sha256_text(normalized_content) != version.get("normalized_content_sha256"):
                raise ConsentLibraryError(f"Hash de contenido normalizado no coincide en {code}.", 422)
            validation = validate_content(normalized_content, require_registered=True)
            if not validation.valid:
                raise ConsentLibraryError(f"Contenido inválido en {code}: {validation.syntax_errors or validation.invalid_variables}", 422)
            if strict_norm3:
                patient_validation = validate_patient_facing_content(
                    normalized_content,
                    allowed_variables=set(VARIABLE_CATALOG.keys()),
                    document_type=document["document_type"],
                    signer_compatibility=version.get("signer_compatibility") or document["signer_scope"],
                    normalized_hash=version.get("normalized_content_sha256"),
                    source_text=version.get("source_text", ""),
                    country_code=version.get("country_code"),
                    enforce_electronic_readiness=False,
                )
                if any(blocker not in {"incompatible_signer_for_standard_electronic_flow:" + (version.get("signer_compatibility") or document["signer_scope"])} for blocker in patient_validation.blockers):
                    raise ConsentLibraryError(f"Contenido para paciente contiene artefactos prohibidos en {code}: {patient_validation.blockers}", 422)
                metadata = parse_normalization_metadata(version.get("transformation_notes", []))
                assessed = assess_electronic_readiness(
                    normalized_content,
                    country_code=version.get("country_code"),
                    document_type=document["document_type"],
                    signer_compatibility=version.get("signer_compatibility") or document["signer_scope"],
                )
                if metadata["electronic_readiness_status"] not in {"UNKNOWN", assessed.status}:
                    raise ConsentLibraryError(f"Estado de aptitud electrónica inconsistente en {code}.", 422)
                if version.get("electronic_readiness_status") and version.get("electronic_readiness_status") != assessed.status:
                    raise ConsentLibraryError(f"Estado de aptitud electrónica declarado no coincide en {code}.", 422)
    return payload


def import_library_package(session: Session, *, path: Path = PACKAGE_PATH, dry_run: bool = False, source_pdf_path: Path | None = None) -> dict:
    payload = load_library_package(path, verify_source=True, source_pdf_path=source_pdf_path)
    counters = {
        "documents_seen": 0,
        "documents_created": 0,
        "documents_updated": 0,
        "versions_seen": 0,
        "versions_created": 0,
        "versions_updated": 0,
        "new_versions": 0,
        "unchanged_versions": 0,
        "conflicts": 0,
        "legacy_versions": 0,
        "blocked": 0,
        "ready": 0,
        "needs_structured_field": 0,
        "needs_human_review": 0,
        "conflict_items": [],
        "dry_run": dry_run,
    }
    for source_item in payload["documents"]:
        item = _production_ready_library_item(source_item)
        counters["documents_seen"] += 1
        document = session.scalar(select(ConsentLibraryDocument).where(ConsentLibraryDocument.code == item["code"]))
        document_values = {
            "title": item["title"],
            "summary": item.get("summary"),
            "document_type": item["document_type"],
            "category": item["category"],
            "specialty_code": item.get("specialty_code"),
            "specialty_name": item.get("specialty_name"),
            "signer_scope": item["signer_scope"],
            "requires_patient_signature": item["requires_patient_signature"],
            "supports_electronic_signature": item["supports_electronic_signature"],
            "source_package_version": item["source_package_version"],
            "source_document_hash": item["source_document_hash"],
            "source_page_start": item["source_page_start"],
            "source_page_end": item["source_page_end"],
            "source_title_exact": item.get("source_title_exact"),
            "source_origin_note": item["source_origin_note"],
            "source_reference": item["source_reference"],
            "is_active": True,
        }
        if document is None:
            counters["documents_created"] += 1
            if not dry_run:
                document = ConsentLibraryDocument(code=item["code"], **document_values)
                session.add(document)
                session.flush()
        else:
            counters["documents_updated"] += 1
            if not dry_run:
                for key, value in document_values.items():
                    setattr(document, key, value)
                session.flush()
        if document is not None:
            existing_versions = list(session.scalars(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id)))
            counters["legacy_versions"] += sum(1 for existing_version in existing_versions if not _is_norm_v2_version(existing_version))
        for version_payload in item["versions"]:
            counters["versions_seen"] += 1
            metadata = parse_normalization_metadata(version_payload.get("transformation_notes", []))
            assessed = assess_electronic_readiness(
                version_payload["content"],
                country_code=version_payload["country_code"],
                document_type=item["document_type"],
                signer_compatibility=version_payload.get("signer_compatibility") or item["signer_scope"],
            )
            readiness_status = version_payload.get("electronic_readiness_status") or (metadata["electronic_readiness_status"] if metadata["electronic_readiness_status"] != "UNKNOWN" else assessed.status)
            if readiness_status == "BLOCKED":
                counters["blocked"] += 1
            elif readiness_status == "READY":
                counters["ready"] += 1
            norm5_result = version_payload.get("norm5_result") or metadata["norm5_result"]
            if norm5_result == "NEEDS_STRUCTURED_FIELD":
                counters["needs_structured_field"] += 1
            elif norm5_result == "NEEDS_HUMAN_REVIEW":
                counters["needs_human_review"] += 1
            version = None
            if document is not None:
                version = session.scalar(select(ConsentLibraryVersion).where(ConsentLibraryVersion.library_document_id == document.id, ConsentLibraryVersion.country_code == version_payload["country_code"], ConsentLibraryVersion.language_code == version_payload["language_code"], ConsentLibraryVersion.version_number == version_payload["version_number"]))
            values = {
                "publication_status": version_payload["publication_status"],
                "legal_review_status": version_payload["legal_review_status"],
                "clinical_review_status": version_payload["clinical_review_status"],
                "reviewed_countries": version_payload.get("reviewed_countries", []),
                "content_format": version_payload.get("content_format", CONTENT_FORMAT),
                "content": version_payload["content"],
                "source_text": version_payload["source_text"],
                "source_text_sha256": version_payload["source_text_sha256"],
                "normalized_content_sha256": version_payload["normalized_content_sha256"],
                "variable_schema_snapshot": version_payload.get("variables", []),
                "source_pages": version_payload.get("source_pages", []),
                "transformation_notes": version_payload.get("transformation_notes", []),
                "review_notes": version_payload.get("review_notes"),
                "imported_at": _now(),
            }
            if version is None:
                counters["versions_created"] += 1
                counters["new_versions"] += 1
                if not dry_run:
                    session.add(ConsentLibraryVersion(library_document_id=document.id, country_code=version_payload["country_code"], language_code=version_payload["language_code"], version_number=version_payload["version_number"], **values))
            else:
                existing_metadata = parse_normalization_metadata(version.transformation_notes)
                incoming_metadata = parse_normalization_metadata(version_payload.get("transformation_notes", []))
                same_identity = (
                    version.source_text_sha256 == version_payload["source_text_sha256"]
                    and version.normalized_content_sha256 == version_payload["normalized_content_sha256"]
                    and (existing_metadata["signer_compatibility"] or "UNKNOWN") == (incoming_metadata["signer_compatibility"] or "UNKNOWN")
                    and (existing_metadata["normalization_schema_version"] or None) == (incoming_metadata["normalization_schema_version"] or None)
                )
                if same_identity:
                    counters["unchanged_versions"] += 1
                    continue
                conflict = {
                    "document_code": item["code"],
                    "country_code": version_payload["country_code"],
                    "language_code": version_payload["language_code"],
                    "version_number": version_payload["version_number"],
                    "existing_version_id": str(version.id),
                    "existing_normalized_content_sha256": version.normalized_content_sha256,
                    "incoming_normalized_content_sha256": version_payload["normalized_content_sha256"],
                    "existing_signer_policy": existing_metadata["signer_compatibility"],
                    "incoming_signer_policy": incoming_metadata["signer_compatibility"],
                }
                counters["conflicts"] += 1
                counters["conflict_items"].append(conflict)
    if counters["conflicts"] and not dry_run:
        session.rollback()
        raise ConsentLibraryError(f"Conflicto de versionado en biblioteca Dentia: {counters['conflicts']} versión(es) usan el mismo número con contenido o política diferente.", 409)
    if dry_run:
        session.rollback()
    else:
        session.commit()
    return counters


def build_equivalence_report(path: Path = PACKAGE_PATH) -> dict:
    payload = load_library_package(path, verify_source=True)
    rows = []
    for document in payload.get("documents", []):
        for version in document.get("versions", []):
            source_text = version.get("source_text", "")
            content = version.get("content", "")
            text_preserved = bool(source_text.strip()) and "pendiente de extracción" not in content.lower()
            removed_lines = ["Campos de firma manual y datos institucionales fuente cuando fueron sustituidos por variables Dentia."]
            if not source_text.strip():
                removed_lines.append("Texto fuente estructurado no disponible en el paquete normalizado; requiere revisión de equivalencia contra el PDF autoritativo.")
            if "pendiente de extracción" in content.lower():
                removed_lines.append("Contenido normalizado contiene marcador de extracción pendiente; no debe aprobarse sin revisión legal/clinical.")
            rows.append({
                "code": document["code"],
                "source_title": document["source_title_exact"],
                "pages": version.get("source_pages", []),
                "source_text_sha256": version["source_text_sha256"],
                "normalized_content_sha256": version["normalized_content_sha256"],
                "variables": version.get("variables", []),
                "removed_lines": removed_lines,
                "text_preserved": text_preserved,
                "structural_changes": version.get("transformation_notes", []),
                "punctuation_or_format_changes": "Normalización menor de espacios, saltos de línea y encabezados Dentia.",
                "country": version["country_code"],
                "locale": version["language_code"],
                "source_legal_review_status": version.get("source_legal_review_status", "APPROVED"),
                "source_clinical_review_status": version.get("source_clinical_review_status", "APPROVED"),
                "normalized_legal_review_status": version["legal_review_status"],
                "normalized_clinical_review_status": version["clinical_review_status"],
            })
    return {"source_file_sha256": payload["source_file_sha256"], "source_page_count": payload["source_page_count"], "documents": len(payload.get("documents", [])), "versions": len(rows), "items": rows}
