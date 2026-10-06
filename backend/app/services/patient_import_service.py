from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Patient
from app.models.audit_event import AuditEvent
from app.models.patient_import import PatientExternalReference, PatientImportSource
from app.schemas.patient_import_schema import (
    PatientImportConfirmResponse,
    PatientImportCounts,
    PatientImportPreviewResponse,
    PatientImportPreviewRow,
    PatientImportSourceListResponse,
    PatientImportSourceResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.dentalink_xlsx_parser import (
    SOURCE_SYSTEM,
    ParsedDentalinkRow,
    ParsedDentalinkWorkbook,
    parse_dentalink_workbook,
)
from app.services.patient_service import _refresh_normalized_fields, normalize_document


PREVIEW_AUDIENCE = "dentia-patient-import"
PREVIEW_TOKEN_MINUTES = 15


class PatientImportError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _source_response(source: PatientImportSource) -> PatientImportSourceResponse:
    return PatientImportSourceResponse(
        id=source.id,
        code=source.code,
        label=source.label,
        source_system=source.source_system,
    )


def list_import_sources(
    session: Session, context: AuthContext
) -> PatientImportSourceListResponse:
    sources = list(
        session.scalars(
            select(PatientImportSource)
            .where(
                PatientImportSource.company_id == context.user.company_id,
                PatientImportSource.source_system == SOURCE_SYSTEM,
                PatientImportSource.is_active.is_(True),
            )
            .order_by(PatientImportSource.created_at, PatientImportSource.id)
        )
    )
    return PatientImportSourceListResponse(items=[_source_response(item) for item in sources])


def create_import_source(
    session: Session, context: AuthContext, *, label: str
) -> PatientImportSourceResponse:
    source = PatientImportSource(
        company_id=context.user.company_id,
        source_system=SOURCE_SYSTEM,
        code=f"dl-{uuid4().hex[:16]}",
        label=label.strip(),
        created_by=context.user.id,
    )
    session.add(source)
    session.commit()
    return _source_response(source)


def _get_source(
    session: Session, context: AuthContext, source_id: UUID
) -> PatientImportSource:
    source = session.scalar(
        select(PatientImportSource).where(
            PatientImportSource.id == source_id,
            PatientImportSource.company_id == context.user.company_id,
            PatientImportSource.source_system == SOURCE_SYSTEM,
            PatientImportSource.is_active.is_(True),
        )
    )
    if source is None:
        raise PatientImportError("El origen Dentalink no existe en esta clínica.", 404)
    return source


def _row_response(row: ParsedDentalinkRow) -> PatientImportPreviewRow:
    return PatientImportPreviewRow(
        row_number=row.row_number,
        source_patient_id=row.source_patient_id,
        display_name=row.display_name,
        status=row.status,
        issues=row.issues,
        pending_fields=sorted(set(row.pending_fields)),
    )


def _counts(rows: list[ParsedDentalinkRow]) -> PatientImportCounts:
    values = PatientImportCounts()
    fields = {
        "READY": "ready",
        "INCOMPLETE": "incomplete",
        "REVIEW": "review",
        "REJECTED": "rejected",
        "ALREADY_IMPORTED": "already_imported",
    }
    for row in rows:
        field = fields[row.status]
        setattr(values, field, getattr(values, field) + 1)
    return values


def _append_issue(row: ParsedDentalinkRow, status: str, issue: str) -> None:
    priority = {
        "READY": 0,
        "INCOMPLETE": 1,
        "REVIEW": 2,
        "REJECTED": 3,
        "ALREADY_IMPORTED": 4,
    }
    if priority[status] > priority[row.status]:
        row.status = status
    if issue not in row.issues:
        row.issues.append(issue)


def _annotate_database_state(
    session: Session,
    context: AuthContext,
    workbook: ParsedDentalinkWorkbook,
    source: PatientImportSource,
) -> None:
    source_patient_ids = [row.source_patient_id for row in workbook.rows if row.source_patient_id]
    imported_ids = set(
        session.scalars(
            select(PatientExternalReference.source_patient_id).where(
                PatientExternalReference.company_id == context.user.company_id,
                PatientExternalReference.source_id == source.id,
                PatientExternalReference.source_patient_id.in_(source_patient_ids),
            )
        )
    )
    normalized_ruts = [normalize_document(row.rut) for row in workbook.rows if row.rut]
    existing_ruts = set(
        session.scalars(
            select(Patient.normalized_document).where(
                Patient.company_id == context.user.company_id,
                Patient.document_type == "RUT",
                Patient.normalized_document.in_(normalized_ruts),
            )
        )
    )
    for row in workbook.rows:
        if row.source_patient_id in imported_ids:
            _append_issue(row, "ALREADY_IMPORTED", "Este # Paciente ya fue importado.")
        elif row.rut and normalize_document(row.rut) in existing_ruts:
            _append_issue(row, "REVIEW", "Ya existe un paciente con este RUT en la clínica.")


def _create_preview_token(
    *, context: AuthContext, source: PatientImportSource, file_sha256: str
) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "type": "patient_import_preview",
            "sub": str(context.user.id),
            "company_id": str(context.user.company_id),
            "source_id": str(source.id),
            "file_sha256": file_sha256,
            "iss": settings.jwt_issuer,
            "aud": PREVIEW_AUDIENCE,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=PREVIEW_TOKEN_MINUTES),
            "jti": str(uuid4()),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def _verify_preview_token(
    token: str,
    *,
    context: AuthContext,
    source: PatientImportSource,
    file_sha256: str,
) -> None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=PREVIEW_AUDIENCE,
            options={"require": ["type", "sub", "company_id", "source_id", "file_sha256", "iat", "nbf", "exp", "jti"]},
        )
    except InvalidTokenError as exc:
        raise PatientImportError("La vista previa expiró o no es válida.", 409) from exc
    expected = {
        "type": "patient_import_preview",
        "sub": str(context.user.id),
        "company_id": str(context.user.company_id),
        "source_id": str(source.id),
        "file_sha256": file_sha256,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise PatientImportError("La vista previa no corresponde a esta confirmación.", 409)


def preview_dentalink_import(
    session: Session,
    context: AuthContext,
    *,
    source_id: UUID,
    content: bytes,
) -> PatientImportPreviewResponse:
    source = _get_source(session, context, source_id)
    workbook = parse_dentalink_workbook(content)
    _annotate_database_state(session, context, workbook, source)
    return PatientImportPreviewResponse(
        preview_token=_create_preview_token(context=context, source=source, file_sha256=workbook.file_sha256),
        file_sha256=workbook.file_sha256,
        source=_source_response(source),
        sheet_name=workbook.sheet_name,
        total_rows=len(workbook.rows),
        counts=_counts(workbook.rows),
        extra_headers=workbook.extra_headers,
        missing_headers=workbook.missing_headers,
        rows=[_row_response(row) for row in workbook.rows],
    )


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    entity: str,
    entity_id: UUID,
    action: str,
    detail: dict,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result="SUCCESS",
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _existing_reference(
    session: Session,
    context: AuthContext,
    source: PatientImportSource,
    source_patient_id: str,
) -> PatientExternalReference | None:
    return session.scalar(
        select(PatientExternalReference).where(
            PatientExternalReference.company_id == context.user.company_id,
            PatientExternalReference.source_id == source.id,
            PatientExternalReference.source_patient_id == source_patient_id,
        )
    )


def confirm_dentalink_import(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    source_id: UUID,
    preview_token: str,
    content: bytes,
) -> PatientImportConfirmResponse:
    source = _get_source(session, context, source_id)
    workbook = parse_dentalink_workbook(content)
    _verify_preview_token(
        preview_token, context=context, source=source, file_sha256=workbook.file_sha256
    )
    _annotate_database_state(session, context, workbook, source)
    batch_id = uuid4()
    imported = already_imported = skipped_review = rejected = 0

    for row in workbook.rows:
        if row.status == "ALREADY_IMPORTED":
            already_imported += 1
            continue
        if row.status == "REVIEW":
            skipped_review += 1
            continue
        if row.status == "REJECTED":
            rejected += 1
            continue
        try:
            with session.begin_nested():
                if _existing_reference(session, context, source, row.source_patient_id):
                    raise IntegrityError("reference exists", {}, None)
                if row.rut and session.scalar(
                    select(Patient.id).where(
                        Patient.company_id == context.user.company_id,
                        Patient.document_type == "RUT",
                        Patient.normalized_document == normalize_document(row.rut),
                    )
                ):
                    raise IntegrityError("patient RUT exists", {}, None)
                patient = Patient(
                    company_id=context.user.company_id,
                    first_names=row.first_names,
                    last_names=row.last_names,
                    document_type="RUT" if row.rut else "Sin documento",
                    document=row.rut,
                    mobile=row.mobile,
                    birth_date=row.birth_date,
                    sex=row.sex,
                    email=row.email,
                    alternate_phone=row.alternate_phone,
                    address=row.address,
                    city=row.city,
                    department=None,
                    emergency_contact_name=None,
                    emergency_contact_mobile=None,
                    administrative_notes=None,
                    status="Activo",
                    created_by=context.user.id,
                    updated_by=context.user.id,
                )
                _refresh_normalized_fields(patient)
                session.add(patient)
                session.flush()
                session.add(
                    PatientExternalReference(
                        company_id=context.user.company_id,
                        source_id=source.id,
                        patient_id=patient.id,
                        source_patient_id=row.source_patient_id,
                        source_file_sha256=workbook.file_sha256,
                        imported_by=context.user.id,
                    )
                )
                _audit(
                    session,
                    context,
                    metadata,
                    entity="patient",
                    entity_id=patient.id,
                    action="PATIENT_IMPORTED",
                    detail={
                        "batch_id": str(batch_id),
                        "source_id": str(source.id),
                        "profile_complete": patient.profile_complete,
                        "pending_field_count": len(row.pending_fields),
                    },
                )
                session.flush()
            imported += 1
        except IntegrityError:
            if _existing_reference(session, context, source, row.source_patient_id):
                _append_issue(row, "ALREADY_IMPORTED", "Este # Paciente ya fue importado.")
                already_imported += 1
            else:
                _append_issue(row, "REVIEW", "Conflicto detectado al confirmar; no se importó.")
                skipped_review += 1

    _audit(
        session,
        context,
        metadata,
        entity="patient_import",
        entity_id=batch_id,
        action="PATIENT_IMPORT_COMPLETED",
        detail={
            "source_id": str(source.id),
            "file_sha256": workbook.file_sha256,
            "total_rows": len(workbook.rows),
            "imported": imported,
            "already_imported": already_imported,
            "skipped_review": skipped_review,
            "rejected": rejected,
        },
    )
    session.commit()
    return PatientImportConfirmResponse(
        batch_id=str(batch_id),
        imported=imported,
        skipped_already_imported=already_imported,
        skipped_review=skipped_review,
        rejected=rejected,
        rows=[_row_response(row) for row in workbook.rows],
    )
