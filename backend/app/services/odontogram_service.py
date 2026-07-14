import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agenda import Appointment, Dentist, Patient
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalEvolution, ClinicalRecord
from app.models.company import Company
from app.models.odontogram import (
    Odontogram,
    OdontogramCatalogItem,
    OdontogramEvent,
    OdontogramEventDetail,
)
from app.models.site import Site
from app.models.treatment import Treatment, TreatmentProcedure
from app.schemas.odontogram_schema import (
    OdontogramCatalogItemResponse,
    OdontogramCreateRequest,
    OdontogramCurrentStateResponse,
    OdontogramEnvelope,
    OdontogramEventConfirmRequest,
    OdontogramEventCorrectRequest,
    OdontogramEventCreateRequest,
    OdontogramEventDetailInput,
    OdontogramEventDetailResponse,
    OdontogramEventListResponse,
    OdontogramEventResponse,
    OdontogramEventUpdateRequest,
    OdontogramResponse,
    OdontogramToothHistoryResponse,
    OdontogramToothState,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import is_authorized_site


FALLBACK_TIMEZONE = "America/Bogota"
VALID_DENTITIONS = {"PERMANENT", "PRIMARY", "MIXED"}
VALID_EVENT_STATUSES = {"DRAFT", "CONFIRMED", "VOIDED_BY_COMPENSATING_EVENT"}
VALID_EVENT_TYPES = {
    "STRUCTURAL_STATE_CHANGED",
    "FINDING_ADDED",
    "DIAGNOSIS_ADDED",
    "PLANNED_PROCEDURE_ADDED",
    "PROCEDURE_PERFORMED",
    "OBSERVATION_ADDED",
    "CORRECTION",
    "COMPENSATING_EVENT",
}
VALID_SCOPES = {"GENERAL", "ZONE", "TOOTH", "TOOTH_SURFACE"}
VALID_LAYERS = {"STRUCTURAL", "FINDING", "DIAGNOSIS", "PLANNED", "PERFORMED", "OBSERVATION"}
VALID_SURFACES = {"VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"}
PERMANENT_TEETH = {
    "11", "12", "13", "14", "15", "16", "17", "18",
    "21", "22", "23", "24", "25", "26", "27", "28",
    "31", "32", "33", "34", "35", "36", "37", "38",
    "41", "42", "43", "44", "45", "46", "47", "48",
}
PRIMARY_TEETH = {
    "51", "52", "53", "54", "55",
    "61", "62", "63", "64", "65",
    "71", "72", "73", "74", "75",
    "81", "82", "83", "84", "85",
}


class OdontogramError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _require_permission(context: AuthContext, permission: str) -> None:
    if permission not in context.permissions:
        raise OdontogramError("No tienes permisos para esta acción odontográfica.", 403)


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    action: str,
    entity: str,
    entity_id: UUID | None,
    patient_id: UUID,
    result: str = "SUCCESS",
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            result=result,
            detail={"patient_id": str(patient_id), **(detail or {})},
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _require_patient(session: Session, context: AuthContext, patient_id: UUID) -> Patient:
    patient = session.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.company_id == context.user.company_id,
        )
    )
    if patient is None:
        raise OdontogramError("Paciente no encontrado.", 404)
    return patient


def _clinical_record(session: Session, context: AuthContext, patient_id: UUID) -> ClinicalRecord | None:
    return session.scalar(
        select(ClinicalRecord).where(
            ClinicalRecord.company_id == context.user.company_id,
            ClinicalRecord.patient_id == patient_id,
            ClinicalRecord.status == "ACTIVA",
        )
    )


def _require_clinical_record(session: Session, context: AuthContext, patient_id: UUID) -> ClinicalRecord:
    record = _clinical_record(session, context, patient_id)
    if record is None:
        raise OdontogramError("El paciente debe tener historia clínica activa antes de crear odontograma.", 422)
    return record


def _get_odontogram(session: Session, context: AuthContext, patient_id: UUID) -> Odontogram | None:
    return session.scalar(
        select(Odontogram).where(
            Odontogram.company_id == context.user.company_id,
            Odontogram.patient_id == patient_id,
        )
    )


def _require_odontogram(session: Session, context: AuthContext, patient_id: UUID) -> Odontogram:
    odontogram = _get_odontogram(session, context, patient_id)
    if odontogram is None:
        raise OdontogramError("Este paciente aún no tiene odontograma.", 404)
    return odontogram


def _effective_timezone(company: Company | None, site: Site | None) -> str:
    candidate = (site.timezone if site else None) or (company.timezone if company else None) or FALLBACK_TIMEZONE
    try:
        ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        return FALLBACK_TIMEZONE
    return candidate


def _normalize_datetime(value: datetime | None, timezone_name: str) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(timezone_name)).astimezone(timezone.utc)
    return value.astimezone(timezone.utc)


def _require_site(session: Session, context: AuthContext, site_id: UUID | None) -> Site:
    selected_site_id = site_id or context.auth_session.active_site_id
    if selected_site_id is None:
        raise OdontogramError("Selecciona una sede activa para registrar el odontograma.", 422)
    site = session.get(Site, selected_site_id)
    if site is None or site.company_id != context.user.company_id or not site.is_active or site.status != "Activa":
        raise OdontogramError("Sede no disponible.", 422)
    if not is_authorized_site(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        site_id=selected_site_id,
    ):
        raise OdontogramError("No tienes acceso a la sede seleccionada.", 403)
    return site


def _current_dentist(session: Session, context: AuthContext) -> Dentist | None:
    return session.scalar(
        select(Dentist).where(
            Dentist.company_id == context.user.company_id,
            Dentist.user_id == context.user.id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
        )
    )


def _require_dentist(session: Session, context: AuthContext, dentist_id: UUID | None) -> Dentist:
    if dentist_id is not None:
        dentist = session.get(Dentist, dentist_id)
        if dentist is None or dentist.company_id != context.user.company_id or not dentist.is_active:
            raise OdontogramError("Odontólogo no disponible.", 422)
        if "DENTIST_ADMIN" not in context.roles and dentist.user_id != context.user.id:
            raise OdontogramError("Solo puedes registrar odontogramas propios.", 403)
        return dentist
    dentist = _current_dentist(session, context)
    if dentist is None:
        raise OdontogramError("Tu usuario no tiene perfil odontólogo activo.", 403)
    return dentist


def _catalog_item(session: Session, context: AuthContext, item_id: UUID) -> OdontogramCatalogItem:
    item = session.scalar(
        select(OdontogramCatalogItem).where(
            OdontogramCatalogItem.id == item_id,
            OdontogramCatalogItem.is_active.is_(True),
            (
                (OdontogramCatalogItem.company_id == context.user.company_id)
                | (OdontogramCatalogItem.company_id.is_(None))
            ),
        )
    )
    if item is None:
        raise OdontogramError("Elemento de catálogo no disponible.", 422)
    return item


def _tooth_dentition(tooth_code: str | None) -> str | None:
    if tooth_code in PERMANENT_TEETH:
        return "PERMANENT"
    if tooth_code in PRIMARY_TEETH:
        return "PRIMARY"
    return None


def _validate_detail(detail: OdontogramEventDetailInput, catalog: OdontogramCatalogItem) -> None:
    if detail.scope_type not in VALID_SCOPES:
        raise OdontogramError("Alcance odontográfico no válido.", 422)
    if detail.layer not in VALID_LAYERS:
        raise OdontogramError("Capa odontográfica no válida.", 422)
    if detail.scope_type not in (catalog.allowed_scopes or []):
        raise OdontogramError("El elemento seleccionado no permite ese alcance.", 422)
    if detail.scope_type == "ZONE" and not detail.zone:
        raise OdontogramError("Debe seleccionar una zona.", 422)
    if detail.scope_type in {"TOOTH", "TOOTH_SURFACE"}:
        if not detail.tooth_code:
            raise OdontogramError("Debe seleccionar un diente.", 422)
        if detail.tooth_code not in PERMANENT_TEETH and detail.tooth_code not in PRIMARY_TEETH:
            raise OdontogramError("Diente no válido.", 422)
    if detail.scope_type == "TOOTH_SURFACE":
        if not detail.surfaces:
            raise OdontogramError("Debe seleccionar al menos una superficie.", 422)
        invalid = [surface for surface in detail.surfaces if surface not in VALID_SURFACES]
        if invalid:
            raise OdontogramError("Superficie dental no válida.", 422)
        allowed = set(catalog.allowed_surfaces or VALID_SURFACES)
        if not set(detail.surfaces).issubset(allowed):
            raise OdontogramError("El elemento seleccionado no permite una de las superficies elegidas.", 422)
    if detail.scope_type == "GENERAL":
        detail.zone = None
        detail.tooth_code = None
        detail.dentition = None
        detail.surfaces = None


def _odontogram_response(odontogram: Odontogram) -> OdontogramResponse:
    return OdontogramResponse(
        id=odontogram.id,
        patient_id=odontogram.patient_id,
        clinical_record_id=odontogram.clinical_record_id,
        status=odontogram.status,
        preferred_dentition=odontogram.preferred_dentition,
        created_on=odontogram.created_on,
        version=odontogram.version,
    )


def _catalog_response(item: OdontogramCatalogItem) -> OdontogramCatalogItemResponse:
    return OdontogramCatalogItemResponse(
        id=item.id,
        company_id=item.company_id,
        code=item.code,
        name=item.name,
        type=item.type,
        category=item.category,
        description=item.description,
        color=item.color,
        pattern=item.pattern,
        symbol=item.symbol,
        allowed_scopes=item.allowed_scopes or [],
        allowed_surfaces=item.allowed_surfaces,
        is_active=item.is_active,
    )


def _detail_response(session: Session, detail: OdontogramEventDetail) -> OdontogramEventDetailResponse:
    catalog = session.get(OdontogramCatalogItem, detail.catalog_item_id)
    return OdontogramEventDetailResponse(
        id=detail.id,
        catalog_item_id=detail.catalog_item_id,
        catalog_code=catalog.code if catalog else "",
        catalog_name=catalog.name if catalog else "Elemento no disponible",
        catalog_type=catalog.type if catalog else "",
        color=catalog.color if catalog else None,
        pattern=catalog.pattern if catalog else None,
        symbol=catalog.symbol if catalog else None,
        scope_type=detail.scope_type,
        zone=detail.zone,
        tooth_code=detail.tooth_code,
        dentition=detail.dentition,
        surfaces=detail.surfaces,
        layer=detail.layer,
        status_after=detail.status_after,
        metadata=detail.detail_metadata,
    )


def _event_response(session: Session, event: OdontogramEvent) -> OdontogramEventResponse:
    details = list(
        session.scalars(
            select(OdontogramEventDetail)
            .where(OdontogramEventDetail.event_id == event.id)
            .order_by(OdontogramEventDetail.created_at)
        )
    )
    site = session.get(Site, event.site_id)
    dentist = session.get(Dentist, event.dentist_id)
    return OdontogramEventResponse(
        id=event.id,
        patient_id=event.patient_id,
        odontogram_id=event.odontogram_id,
        evolution_id=event.evolution_id,
        appointment_id=event.appointment_id,
        treatment_id=event.treatment_id,
        procedure_id=event.procedure_id,
        event_type=event.event_type,
        status=event.status,
        clinical_date=event.clinical_date,
        timezone=event.timezone_name,
        observation=event.observation,
        correction_reason=event.correction_reason,
        parent_event_id=event.parent_event_id,
        version=event.version,
        content_hash=event.content_hash,
        confirmed_at=event.confirmed_at,
        confirmed_by=event.confirmed_by,
        site_id=event.site_id,
        site_name=site.name if site else None,
        dentist_id=event.dentist_id,
        dentist_name=dentist.name if dentist else None,
        created_by=event.created_by,
        details=[_detail_response(session, detail) for detail in details],
    )


def _canonical_hash(session: Session, event: OdontogramEvent) -> str:
    details = [
        {
            "catalog_item_id": str(detail.catalog_item_id),
            "scope_type": detail.scope_type,
            "zone": detail.zone,
            "tooth_code": detail.tooth_code,
            "dentition": detail.dentition,
            "surfaces": detail.surfaces or [],
            "layer": detail.layer,
            "status_after": detail.status_after,
            "metadata": detail.detail_metadata or {},
        }
        for detail in session.scalars(
            select(OdontogramEventDetail)
            .where(OdontogramEventDetail.event_id == event.id)
            .order_by(OdontogramEventDetail.created_at, OdontogramEventDetail.id)
        )
    ]
    payload = {
        "event_id": str(event.id),
        "company_id": str(event.company_id),
        "patient_id": str(event.patient_id),
        "odontogram_id": str(event.odontogram_id),
        "event_type": event.event_type,
        "clinical_date": event.clinical_date.isoformat(),
        "site_id": str(event.site_id),
        "dentist_id": str(event.dentist_id),
        "observation": event.observation,
        "details": details,
        "version": event.version,
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def get_odontogram(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    metadata: RequestMetadata,
) -> OdontogramEnvelope:
    _require_permission(context, "odontogram.view")
    _require_patient(session, context, patient_id)
    record = _clinical_record(session, context, patient_id)
    odontogram = _get_odontogram(session, context, patient_id)
    if odontogram:
        _audit(
            session,
            context,
            metadata,
            action="ODONTOGRAM_VIEWED",
            entity="odontogram",
            entity_id=odontogram.id,
            patient_id=patient_id,
        )
        session.commit()
    return OdontogramEnvelope(
        exists=odontogram is not None,
        odontogram=_odontogram_response(odontogram) if odontogram else None,
        clinical_record_exists=record is not None,
    )


def create_odontogram(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: OdontogramCreateRequest,
    metadata: RequestMetadata,
) -> OdontogramResponse:
    _require_permission(context, "odontogram.create")
    _require_patient(session, context, patient_id)
    if payload.preferred_dentition not in VALID_DENTITIONS:
        raise OdontogramError("Dentición preferida no válida.", 422)
    existing = _get_odontogram(session, context, patient_id)
    if existing:
        return _odontogram_response(existing)
    record = _require_clinical_record(session, context, patient_id)
    odontogram = Odontogram(
        company_id=context.user.company_id,
        patient_id=patient_id,
        clinical_record_id=record.id,
        preferred_dentition=payload.preferred_dentition,
        created_by=context.user.id,
    )
    session.add(odontogram)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        existing = _get_odontogram(session, context, patient_id)
        if existing:
            return _odontogram_response(existing)
        raise
    _audit(
        session,
        context,
        metadata,
        action="ODONTOGRAM_CREATED",
        entity="odontogram",
        entity_id=odontogram.id,
        patient_id=patient_id,
    )
    session.commit()
    session.refresh(odontogram)
    return _odontogram_response(odontogram)


def list_catalog(session: Session, context: AuthContext) -> list[OdontogramCatalogItemResponse]:
    _require_permission(context, "odontogram.view")
    items = list(
        session.scalars(
            select(OdontogramCatalogItem)
            .where(
                OdontogramCatalogItem.is_active.is_(True),
                (
                    (OdontogramCatalogItem.company_id == context.user.company_id)
                    | (OdontogramCatalogItem.company_id.is_(None))
                ),
            )
            .order_by(OdontogramCatalogItem.type, OdontogramCatalogItem.name)
        )
    )
    return [_catalog_response(item) for item in items]


def _apply_event_payload(
    session: Session,
    context: AuthContext,
    event: OdontogramEvent,
    payload: OdontogramEventCreateRequest | OdontogramEventUpdateRequest,
) -> None:
    if payload.event_type not in VALID_EVENT_TYPES:
        raise OdontogramError("Tipo de evento odontográfico no válido.", 422)
    site = _require_site(session, context, payload.site_id)
    dentist = _require_dentist(session, context, payload.dentist_id)
    company = session.get(Company, context.user.company_id)
    timezone_name = _effective_timezone(company, site)
    event.event_type = payload.event_type
    if payload.appointment_id is not None:
        appointment = session.get(Appointment, payload.appointment_id)
        if (
            appointment is None
            or appointment.company_id != context.user.company_id
            or appointment.patient_id != event.patient_id
        ):
            raise OdontogramError("La cita vinculada no pertenece al paciente.", 422)
    if payload.evolution_id is not None:
        evolution = session.get(ClinicalEvolution, payload.evolution_id)
        if (
            evolution is None
            or evolution.company_id != context.user.company_id
            or evolution.patient_id != event.patient_id
        ):
            raise OdontogramError("La evolución vinculada no pertenece al paciente.", 422)
    if payload.treatment_id is not None:
        treatment = session.get(Treatment, payload.treatment_id)
        if (
            treatment is None
            or treatment.company_id != context.user.company_id
            or treatment.patient_id != event.patient_id
        ):
            raise OdontogramError("El tratamiento vinculado no pertenece al paciente.", 422)
    if payload.procedure_id is not None:
        procedure = session.get(TreatmentProcedure, payload.procedure_id)
        if (
            procedure is None
            or procedure.company_id != context.user.company_id
            or procedure.patient_id != event.patient_id
        ):
            raise OdontogramError("El procedimiento vinculado no pertenece al paciente.", 422)
        if payload.treatment_id and procedure.treatment_id != payload.treatment_id:
            raise OdontogramError("El procedimiento no pertenece al tratamiento vinculado.", 422)
    event.appointment_id = payload.appointment_id
    event.evolution_id = payload.evolution_id
    event.treatment_id = payload.treatment_id
    event.procedure_id = payload.procedure_id
    event.site_id = site.id
    event.dentist_id = dentist.id
    event.clinical_date = _normalize_datetime(payload.clinical_date, timezone_name)
    event.timezone_name = timezone_name
    event.observation = payload.observation


def _replace_details(
    session: Session,
    context: AuthContext,
    event: OdontogramEvent,
    details: list[OdontogramEventDetailInput],
) -> None:
    session.query(OdontogramEventDetail).filter(OdontogramEventDetail.event_id == event.id).delete()
    for detail in details:
        catalog = _catalog_item(session, context, detail.catalog_item_id)
        _validate_detail(detail, catalog)
        dentition = detail.dentition or _tooth_dentition(detail.tooth_code)
        session.add(
            OdontogramEventDetail(
                company_id=context.user.company_id,
                event_id=event.id,
                catalog_item_id=catalog.id,
                scope_type=detail.scope_type,
                zone=detail.zone if detail.scope_type == "ZONE" else None,
                tooth_code=detail.tooth_code if detail.scope_type in {"TOOTH", "TOOTH_SURFACE"} else None,
                dentition=dentition if detail.scope_type in {"TOOTH", "TOOTH_SURFACE"} else None,
                surfaces=detail.surfaces if detail.scope_type == "TOOTH_SURFACE" else None,
                layer=detail.layer,
                status_after=detail.status_after,
                detail_metadata=detail.metadata,
            )
        )


def create_event(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: OdontogramEventCreateRequest,
    metadata: RequestMetadata,
) -> OdontogramEventResponse:
    _require_permission(context, "odontogram.update_draft")
    _require_patient(session, context, patient_id)
    record = _require_clinical_record(session, context, patient_id)
    odontogram = _require_odontogram(session, context, patient_id)
    if payload.status not in {"DRAFT", "CONFIRMED"}:
        raise OdontogramError("Estado inicial de evento no válido.", 422)
    current_dentist = _current_dentist(session, context)
    event = OdontogramEvent(
        company_id=context.user.company_id,
        patient_id=patient_id,
        clinical_record_id=record.id,
        odontogram_id=odontogram.id,
        event_type=payload.event_type,
        site_id=context.auth_session.active_site_id,
        dentist_id=current_dentist.id if current_dentist else None,
        clinical_date=datetime.now(timezone.utc),
        timezone_name=FALLBACK_TIMEZONE,
        observation=payload.observation,
        created_by=context.user.id,
    )
    _apply_event_payload(session, context, event, payload)
    if payload.status == "CONFIRMED":
        _require_permission(context, "odontogram.confirm")
        event.status = "CONFIRMED"
        event.confirmed_by = context.user.id
        event.confirmed_at = datetime.now(timezone.utc)
    session.add(event)
    session.flush()
    _replace_details(session, context, event, payload.details)
    session.flush()
    if event.status == "CONFIRMED":
        event.content_hash = _canonical_hash(session, event)
    _audit(
        session,
        context,
        metadata,
        action="ODONTOGRAM_EVENT_CREATED",
        entity="odontogram_event",
        entity_id=event.id,
        patient_id=patient_id,
        detail={"status": event.status, "event_type": event.event_type},
    )
    session.commit()
    session.refresh(event)
    return _event_response(session, event)


def _get_event(session: Session, context: AuthContext, event_id: UUID, *, lock: bool = False) -> OdontogramEvent:
    statement = select(OdontogramEvent).where(
        OdontogramEvent.id == event_id,
        OdontogramEvent.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    event = session.scalar(statement)
    if event is None:
        raise OdontogramError("Evento odontográfico no encontrado.", 404)
    return event


def update_event_draft(
    session: Session,
    context: AuthContext,
    event_id: UUID,
    payload: OdontogramEventUpdateRequest,
    metadata: RequestMetadata,
) -> OdontogramEventResponse:
    _require_permission(context, "odontogram.update_draft")
    event = _get_event(session, context, event_id, lock=True)
    if event.status != "DRAFT":
        raise OdontogramError("Solo se pueden editar eventos en borrador.", 409)
    if event.version != payload.version:
        raise OdontogramError("Este evento fue modificado por otro usuario. Recarga la información.", 409)
    if "DENTIST_ADMIN" not in context.roles and event.created_by != context.user.id:
        raise OdontogramError("Solo puedes editar tus propios borradores.", 403)
    _apply_event_payload(session, context, event, payload)
    _replace_details(session, context, event, payload.details)
    event.version += 1
    event.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        action="ODONTOGRAM_EVENT_UPDATED_DRAFT",
        entity="odontogram_event",
        entity_id=event.id,
        patient_id=event.patient_id,
        detail={"version": event.version},
    )
    session.commit()
    session.refresh(event)
    return _event_response(session, event)


def confirm_event(
    session: Session,
    context: AuthContext,
    event_id: UUID,
    payload: OdontogramEventConfirmRequest,
    metadata: RequestMetadata,
) -> OdontogramEventResponse:
    _require_permission(context, "odontogram.confirm")
    event = _get_event(session, context, event_id, lock=True)
    if event.status != "DRAFT":
        raise OdontogramError("Solo se pueden confirmar eventos en borrador.", 409)
    if event.version != payload.version:
        raise OdontogramError("Este evento fue modificado por otro usuario. Recarga la información.", 409)
    if "DENTIST_ADMIN" not in context.roles and event.created_by != context.user.id:
        raise OdontogramError("Solo puedes confirmar tus propios eventos.", 403)
    event.status = "CONFIRMED"
    event.confirmed_by = context.user.id
    event.confirmed_at = datetime.now(timezone.utc)
    event.content_hash = _canonical_hash(session, event)
    event.version += 1
    _audit(
        session,
        context,
        metadata,
        action="ODONTOGRAM_EVENT_CONFIRMED",
        entity="odontogram_event",
        entity_id=event.id,
        patient_id=event.patient_id,
        detail={"version": event.version, "hash": event.content_hash},
    )
    session.commit()
    session.refresh(event)
    return _event_response(session, event)


def correct_event(
    session: Session,
    context: AuthContext,
    event_id: UUID,
    payload: OdontogramEventCorrectRequest,
    metadata: RequestMetadata,
) -> OdontogramEventResponse:
    _require_permission(context, "odontogram.correct")
    event = _get_event(session, context, event_id, lock=True)
    if event.status != "CONFIRMED":
        raise OdontogramError("Solo se pueden corregir eventos confirmados.", 409)
    event.status = "VOIDED_BY_COMPENSATING_EVENT"
    event.correction_reason = payload.reason
    event.version += 1
    correction = OdontogramEvent(
        company_id=event.company_id,
        patient_id=event.patient_id,
        clinical_record_id=event.clinical_record_id,
        odontogram_id=event.odontogram_id,
        site_id=event.site_id,
        dentist_id=event.dentist_id,
        event_type="COMPENSATING_EVENT" if payload.replacement_event else "CORRECTION",
        status="CONFIRMED",
        clinical_date=datetime.now(timezone.utc),
        timezone_name=event.timezone_name,
        observation=payload.reason,
        correction_reason=payload.reason,
        parent_event_id=event.id,
        confirmed_by=context.user.id,
        confirmed_at=datetime.now(timezone.utc),
        created_by=context.user.id,
    )
    session.add(correction)
    session.flush()
    if payload.replacement_event:
        _apply_event_payload(session, context, correction, payload.replacement_event)
        correction.event_type = "COMPENSATING_EVENT"
        _replace_details(session, context, correction, payload.replacement_event.details)
    correction.content_hash = _canonical_hash(session, correction)
    _audit(
        session,
        context,
        metadata,
        action="ODONTOGRAM_EVENT_CORRECTED",
        entity="odontogram_event",
        entity_id=event.id,
        patient_id=event.patient_id,
        detail={"correction_event_id": str(correction.id)},
    )
    session.commit()
    session.refresh(correction)
    return _event_response(session, correction)


def get_event(session: Session, context: AuthContext, event_id: UUID, metadata: RequestMetadata) -> OdontogramEventResponse:
    _require_permission(context, "odontogram.view")
    event = _get_event(session, context, event_id)
    _audit(
        session,
        context,
        metadata,
        action="ODONTOGRAM_VIEWED",
        entity="odontogram_event",
        entity_id=event.id,
        patient_id=event.patient_id,
    )
    session.commit()
    return _event_response(session, event)


def list_events(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    status: str | None = None,
) -> OdontogramEventListResponse:
    _require_permission(context, "odontogram.view")
    _require_patient(session, context, patient_id)
    filters = [
        OdontogramEvent.company_id == context.user.company_id,
        OdontogramEvent.patient_id == patient_id,
    ]
    if status:
        if status not in VALID_EVENT_STATUSES:
            raise OdontogramError("Estado de evento no válido.", 422)
        filters.append(OdontogramEvent.status == status)
    events = list(
        session.scalars(
            select(OdontogramEvent)
            .where(*filters)
            .order_by(OdontogramEvent.clinical_date.desc(), OdontogramEvent.created_at.desc())
        )
    )
    return OdontogramEventListResponse(items=[_event_response(session, event) for event in events])


def current_state(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    metadata: RequestMetadata,
) -> OdontogramCurrentStateResponse:
    _require_permission(context, "odontogram.view")
    odontogram = _require_odontogram(session, context, patient_id)
    events = list(
        session.scalars(
            select(OdontogramEvent)
            .where(
                OdontogramEvent.company_id == context.user.company_id,
                OdontogramEvent.patient_id == patient_id,
                OdontogramEvent.status == "CONFIRMED",
            )
            .order_by(OdontogramEvent.clinical_date, OdontogramEvent.created_at)
        )
    )
    teeth: dict[str, OdontogramToothState] = {}
    general_events: list[OdontogramEventResponse] = []
    for event in events:
        event_response = _event_response(session, event)
        for detail in event_response.details:
            if detail.scope_type not in {"TOOTH", "TOOTH_SURFACE"} or not detail.tooth_code:
                if event_response not in general_events:
                    general_events.append(event_response)
                continue
            tooth = teeth.setdefault(
                detail.tooth_code,
                OdontogramToothState(
                    tooth_code=detail.tooth_code,
                    dentition=detail.dentition or _tooth_dentition(detail.tooth_code) or "PERMANENT",
                    layers={},
                    event_count=0,
                ),
            )
            tooth.layers.setdefault(detail.layer, []).append(detail)
            tooth.event_count += 1
    legend = list_catalog(session, context)
    _audit(
        session,
        context,
        metadata,
        action="ODONTOGRAM_VIEWED",
        entity="odontogram",
        entity_id=odontogram.id,
        patient_id=patient_id,
        detail={"view": "current"},
    )
    session.commit()
    return OdontogramCurrentStateResponse(
        odontogram=_odontogram_response(odontogram),
        preferred_dentition=odontogram.preferred_dentition,
        teeth=sorted(teeth.values(), key=lambda item: item.tooth_code),
        general_events=general_events,
        legend=legend,
    )


def tooth_history(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    tooth_code: str,
    metadata: RequestMetadata,
    *,
    status: str | None = None,
    surface: str | None = None,
    event_type: str | None = None,
) -> OdontogramToothHistoryResponse:
    _require_permission(context, "odontogram.history")
    _require_patient(session, context, patient_id)
    if tooth_code not in PERMANENT_TEETH and tooth_code not in PRIMARY_TEETH:
        raise OdontogramError("Diente no válido.", 422)
    filters = [
        OdontogramEvent.company_id == context.user.company_id,
        OdontogramEvent.patient_id == patient_id,
        OdontogramEventDetail.tooth_code == tooth_code,
    ]
    if status:
        filters.append(OdontogramEvent.status == status)
    if event_type:
        filters.append(OdontogramEvent.event_type == event_type)
    if surface:
        if surface not in VALID_SURFACES:
            raise OdontogramError("Superficie dental no válida.", 422)
        filters.append(OdontogramEventDetail.surfaces.contains([surface]))
    events = list(
        session.scalars(
            select(OdontogramEvent)
            .join(OdontogramEventDetail, OdontogramEventDetail.event_id == OdontogramEvent.id)
            .where(*filters)
            .distinct()
            .order_by(OdontogramEvent.clinical_date.desc(), OdontogramEvent.created_at.desc())
        )
    )
    _audit(
        session,
        context,
        metadata,
        action="ODONTOGRAM_HISTORY_VIEWED",
        entity="odontogram",
        entity_id=None,
        patient_id=patient_id,
        detail={"tooth_code": tooth_code, "surface": surface},
    )
    session.commit()
    return OdontogramToothHistoryResponse(
        tooth_code=tooth_code,
        items=[_event_response(session, event) for event in events],
    )
