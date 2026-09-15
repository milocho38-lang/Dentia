from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalTimelineEvent
from app.models.company import Company
from app.models.orthodontics import (
    OrthodonticCase,
    OrthodonticClinicalRecord,
    OrthodonticClinicalRecordVersion,
)
from app.schemas.orthodontic_record_schema import (
    OrthodonticRecordActionResponse,
    OrthodonticRecordFinalizeRequest,
    OrthodonticRecordNewVersionRequest,
    OrthodonticRecordResponse,
    OrthodonticRecordUpdateRequest,
    OrthodonticRecordVersionResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.orthodontic_record_schema_service import (
    ORTHODONTIC_RECORD_SCHEMA_VERSION,
    OrthodonticRecordSchemaError,
    orthodontic_record_content_snapshot,
    orthodontic_record_schema_payload,
    orthodontic_record_section_progress,
    validate_orthodontic_record_content,
)
from app.services.orthodontics_entitlement_service import (
    OrthodonticsError,
    orthodontics_historical_read_allowed,
    require_orthodontics_clinical_access,
)


class OrthodonticRecordError(OrthodonticsError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _case(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    *,
    lock: bool = False,
) -> OrthodonticCase:
    statement = select(OrthodonticCase).where(
        OrthodonticCase.id == case_id,
        OrthodonticCase.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    case = session.scalar(statement)
    if case is None:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_CASE_NOT_FOUND",
            "Caso de Ortodoncia no encontrado.",
            404,
        )
    return case


def _record(
    session: Session,
    case: OrthodonticCase,
    *,
    lock: bool = False,
) -> OrthodonticClinicalRecord | None:
    statement = select(OrthodonticClinicalRecord).where(
        OrthodonticClinicalRecord.company_id == case.company_id,
        OrthodonticClinicalRecord.orthodontic_case_id == case.id,
    )
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def _required_record(
    session: Session,
    case: OrthodonticCase,
    *,
    lock: bool = False,
) -> OrthodonticClinicalRecord:
    record = _record(session, case, lock=lock)
    if record is None:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_NOT_FOUND",
            "La historia clínica de Ortodoncia todavía no ha sido creada.",
            404,
        )
    return record


def _version(
    session: Session,
    record: OrthodonticClinicalRecord,
    version_id: UUID,
    *,
    lock: bool = False,
) -> OrthodonticClinicalRecordVersion:
    statement = select(OrthodonticClinicalRecordVersion).where(
        OrthodonticClinicalRecordVersion.id == version_id,
        OrthodonticClinicalRecordVersion.record_id == record.id,
        OrthodonticClinicalRecordVersion.company_id == record.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    version = session.scalar(statement)
    if version is None:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_VERSION_NOT_FOUND",
            "Versión de la historia de Ortodoncia no encontrada.",
            404,
        )
    return version


def _label(session: Session, company_id: UUID) -> str:
    company = session.get(Company, company_id)
    country = (company.country if company else "").strip().upper()
    return (
        "Ficha clínica de Ortodoncia"
        if country in {"CL", "CHILE"}
        else "Historia clínica de Ortodoncia"
    )


def _require_read_access(
    session: Session,
    context: AuthContext,
    case: OrthodonticCase,
) -> None:
    try:
        require_orthodontics_clinical_access(session, context)
    except OrthodonticsError:
        if not orthodontics_historical_read_allowed(
            session, context, site_id=case.primary_site_id
        ):
            raise


def _require_write_access(
    session: Session,
    context: AuthContext,
    case: OrthodonticCase,
) -> None:
    require_orthodontics_clinical_access(session, context, write=True)
    if case.status != "ACTIVE":
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_CASE_READ_ONLY",
            "La historia solo puede modificarse mientras el caso está activo.",
            409,
        )


def _can_edit(
    session: Session,
    context: AuthContext,
    case: OrthodonticCase,
) -> bool:
    if case.status != "ACTIVE":
        return False
    try:
        require_orthodontics_clinical_access(session, context, write=True)
    except OrthodonticsError:
        return False
    return True


def _read_only_reason(case: OrthodonticCase, can_edit: bool) -> str | None:
    if can_edit:
        return None
    if case.status == "SUSPENDED":
        return "El caso está suspendido. Reactívalo para modificar la historia."
    if case.status == "COMPLETED":
        return "El caso está finalizado y se conserva en modo de solo lectura."
    if case.status == "DRAFT":
        return "Activa el caso para comenzar la historia clínica de Ortodoncia."
    return "El acceso histórico se conserva en modo de solo lectura."


def _version_response(
    version: OrthodonticClinicalRecordVersion,
) -> OrthodonticRecordVersionResponse:
    return OrthodonticRecordVersionResponse(
        id=version.id,
        record_id=version.record_id,
        version_number=version.version_number,
        status=version.status,
        schema_version=version.schema_version,
        row_version=version.row_version,
        content=version.content,
        schema_snapshot=version.schema_snapshot,
        content_snapshot=version.content_snapshot,
        based_on_version_id=version.based_on_version_id,
        clinical_date=version.clinical_date,
        timezone_name=version.timezone_name,
        content_hash=version.content_hash,
        created_by_user_id=version.created_by_user_id,
        updated_by_user_id=version.updated_by_user_id,
        finalized_by_user_id=version.finalized_by_user_id,
        finalized_at=version.finalized_at,
        created_at=version.created_at,
        updated_at=version.updated_at,
        section_progress=orthodontic_record_section_progress(version.content),
    )


def _record_response(
    session: Session,
    context: AuthContext,
    case: OrthodonticCase,
    record: OrthodonticClinicalRecord,
    *,
    selected_version_id: UUID | None = None,
) -> OrthodonticRecordResponse:
    versions = list(
        session.scalars(
            select(OrthodonticClinicalRecordVersion)
            .where(
                OrthodonticClinicalRecordVersion.company_id == record.company_id,
                OrthodonticClinicalRecordVersion.record_id == record.id,
            )
            .order_by(OrthodonticClinicalRecordVersion.version_number.desc())
        )
    )
    current = next(
        (item for item in versions if item.id == selected_version_id),
        next((item for item in versions if item.status == "DRAFT"), versions[0] if versions else None),
    )
    can_edit = _can_edit(session, context, case)
    return OrthodonticRecordResponse(
        id=record.id,
        company_id=record.company_id,
        patient_id=record.patient_id,
        orthodontic_case_id=record.orthodontic_case_id,
        label=_label(session, record.company_id),
        case_status=case.status,
        can_edit=can_edit,
        read_only_reason=_read_only_reason(case, can_edit),
        record_schema=orthodontic_record_schema_payload(),
        current_version=_version_response(current) if current else None,
        versions=[_version_response(item) for item in versions],
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    record: OrthodonticClinicalRecord,
    action: str,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=record.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="orthodontic_clinical_record",
            entity_id=record.id,
            action=action,
            result="SUCCESS",
            detail={"orthodontic_case_id": str(record.orthodontic_case_id), **(detail or {})},
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _canonical_hash(payload: dict) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def get_orthodontic_record(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    *,
    version_id: UUID | None = None,
) -> OrthodonticRecordResponse:
    case = _case(session, context, case_id)
    _require_read_access(session, context, case)
    record = _required_record(session, case)
    if version_id is not None:
        _version(session, record, version_id)
    return _record_response(
        session, context, case, record, selected_version_id=version_id
    )


def create_orthodontic_record(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    metadata: RequestMetadata,
) -> OrthodonticRecordActionResponse:
    case = _case(session, context, case_id, lock=True)
    _require_write_access(session, context, case)
    if _record(session, case) is not None:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_ALREADY_EXISTS",
            "El caso ya tiene una historia clínica de Ortodoncia.",
            409,
        )
    record = OrthodonticClinicalRecord(
        company_id=case.company_id,
        patient_id=case.patient_id,
        orthodontic_case_id=case.id,
        created_by_user_id=context.user.id,
    )
    session.add(record)
    session.flush()
    version = OrthodonticClinicalRecordVersion(
        company_id=case.company_id,
        record_id=record.id,
        version_number=1,
        status="DRAFT",
        schema_version=ORTHODONTIC_RECORD_SCHEMA_VERSION,
        row_version=1,
        content={},
        schema_snapshot=orthodontic_record_schema_payload(),
        created_by_user_id=context.user.id,
        updated_by_user_id=context.user.id,
    )
    session.add(version)
    _audit(
        session,
        context,
        metadata,
        record,
        "ORTHODONTIC_RECORD_CREATED",
        {"version_number": 1},
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_ALREADY_EXISTS",
            "El caso ya tiene una historia clínica de Ortodoncia.",
            409,
        ) from exc
    return OrthodonticRecordActionResponse(
        message="Historia clínica de Ortodoncia creada en borrador.",
        record=_record_response(session, context, case, record),
    )


def update_orthodontic_record_version(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    version_id: UUID,
    payload: OrthodonticRecordUpdateRequest,
    metadata: RequestMetadata,
) -> OrthodonticRecordActionResponse:
    case = _case(session, context, case_id)
    _require_write_access(session, context, case)
    record = _required_record(session, case)
    version = _version(session, record, version_id, lock=True)
    if version.status != "DRAFT":
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_VERSION_IMMUTABLE",
            "Las versiones finalizadas son inmutables. Crea una nueva versión.",
            409,
        )
    if version.row_version != payload.row_version:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_VERSION_CONFLICT",
            "La versión cambió desde la última consulta. Actualiza e inténtalo nuevamente.",
            409,
        )
    try:
        version.content = validate_orthodontic_record_content(payload.content)
    except OrthodonticRecordSchemaError as exc:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_SCHEMA_INVALID", str(exc), 422
        ) from exc
    version.row_version += 1
    version.updated_by_user_id = context.user.id
    record.updated_at = _now()
    _audit(
        session,
        context,
        metadata,
        record,
        "ORTHODONTIC_RECORD_DRAFT_UPDATED",
        {"version_id": str(version.id), "version_number": version.version_number},
    )
    session.commit()
    return OrthodonticRecordActionResponse(
        message="Borrador guardado.",
        record=_record_response(session, context, case, record),
    )


def finalize_orthodontic_record_version(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    version_id: UUID,
    payload: OrthodonticRecordFinalizeRequest,
    metadata: RequestMetadata,
) -> OrthodonticRecordActionResponse:
    case = _case(session, context, case_id)
    _require_write_access(session, context, case)
    if "clinical_evolutions.sign" not in context.permissions:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_FINALIZE_DENIED",
            "No tienes permiso para finalizar documentos clínicos.",
            403,
        )
    record = _required_record(session, case)
    version = _version(session, record, version_id, lock=True)
    if version.status != "DRAFT":
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_VERSION_IMMUTABLE",
            "La versión ya está finalizada.",
            409,
        )
    if version.row_version != payload.row_version:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_VERSION_CONFLICT",
            "La versión cambió desde la última consulta. Actualiza e inténtalo nuevamente.",
            409,
        )
    try:
        normalized = validate_orthodontic_record_content(version.content)
    except OrthodonticRecordSchemaError as exc:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_SCHEMA_INVALID", str(exc), 422
        ) from exc
    now = _now()
    company = session.get(Company, case.company_id)
    timezone_name = company.timezone if company else "UTC"
    snapshot = orthodontic_record_content_snapshot(normalized)
    frozen_payload = {
        "schema_version": version.schema_version,
        "schema_snapshot": version.schema_snapshot,
        "content": normalized,
        "content_snapshot": snapshot,
    }
    version.content = normalized
    version.content_snapshot = snapshot
    version.content_hash = _canonical_hash(frozen_payload)
    version.clinical_date = now
    version.timezone_name = timezone_name
    version.status = "FINALIZED"
    version.finalized_at = now
    version.finalized_by_user_id = context.user.id
    version.updated_by_user_id = context.user.id
    version.row_version += 1
    record.updated_at = now
    session.add(
        ClinicalTimelineEvent(
            company_id=case.company_id,
            patient_id=case.patient_id,
            clinical_record_id=case.clinical_record_id,
            event_type="ORTHODONTIC_RECORD_FINALIZED",
            entity_type="orthodontic_clinical_record_version",
            entity_id=version.id,
            title=f"{_label(session, case.company_id)} finalizada",
            summary=f"Versión {version.version_number}",
            clinical_date=now,
            site_id=case.primary_site_id,
            dentist_id=case.responsible_dentist_id,
            created_by=context.user.id,
            event_metadata={
                "record_id": str(record.id),
                "version_number": version.version_number,
                "content_hash": version.content_hash,
            },
        )
    )
    _audit(
        session,
        context,
        metadata,
        record,
        "ORTHODONTIC_RECORD_FINALIZED",
        {
            "version_id": str(version.id),
            "version_number": version.version_number,
            "content_hash": version.content_hash,
        },
    )
    session.commit()
    return OrthodonticRecordActionResponse(
        message="Versión finalizada. El contenido quedó inmutable.",
        record=_record_response(session, context, case, record),
    )


def create_orthodontic_record_version(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    payload: OrthodonticRecordNewVersionRequest,
    metadata: RequestMetadata,
) -> OrthodonticRecordActionResponse:
    case = _case(session, context, case_id, lock=True)
    _require_write_access(session, context, case)
    record = _required_record(session, case, lock=True)
    existing_draft = session.scalar(
        select(OrthodonticClinicalRecordVersion).where(
            OrthodonticClinicalRecordVersion.record_id == record.id,
            OrthodonticClinicalRecordVersion.status == "DRAFT",
        )
    )
    if existing_draft is not None:
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_DRAFT_EXISTS",
            "Ya existe una versión en borrador.",
            409,
        )
    if payload.based_on_version_id:
        source = _version(session, record, payload.based_on_version_id)
    else:
        source = session.scalar(
            select(OrthodonticClinicalRecordVersion)
            .where(
                OrthodonticClinicalRecordVersion.record_id == record.id,
                OrthodonticClinicalRecordVersion.status == "FINALIZED",
            )
            .order_by(OrthodonticClinicalRecordVersion.version_number.desc())
            .limit(1)
        )
    if source is None or source.status != "FINALIZED":
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_FINALIZED_SOURCE_REQUIRED",
            "La nueva versión debe partir de una versión finalizada.",
            409,
        )
    next_number = int(
        session.scalar(
            select(func.max(OrthodonticClinicalRecordVersion.version_number)).where(
                OrthodonticClinicalRecordVersion.record_id == record.id
            )
        )
        or 0
    ) + 1
    version = OrthodonticClinicalRecordVersion(
        company_id=record.company_id,
        record_id=record.id,
        version_number=next_number,
        status="DRAFT",
        schema_version=ORTHODONTIC_RECORD_SCHEMA_VERSION,
        row_version=1,
        content=dict(source.content),
        schema_snapshot=orthodontic_record_schema_payload(),
        based_on_version_id=source.id,
        created_by_user_id=context.user.id,
        updated_by_user_id=context.user.id,
    )
    session.add(version)
    record.updated_at = _now()
    _audit(
        session,
        context,
        metadata,
        record,
        "ORTHODONTIC_RECORD_NEW_VERSION_CREATED",
        {
            "version_number": next_number,
            "based_on_version_id": str(source.id),
        },
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise OrthodonticRecordError(
            "ORTHODONTIC_RECORD_DRAFT_EXISTS",
            "Otra sesión creó una versión en borrador. Actualiza para continuar.",
            409,
        ) from exc
    return OrthodonticRecordActionResponse(
        message=f"Versión {next_number} creada en borrador.",
        record=_record_response(session, context, case, record),
    )
