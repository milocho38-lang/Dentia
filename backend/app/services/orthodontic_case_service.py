from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.models.agenda import Appointment, Dentist, DentistSite, Patient
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalEvolution, ClinicalRecord, ClinicalTimelineEvent
from app.models.company import Company
from app.models.orthodontics import (
    OrthodonticCase,
    OrthodonticEvolution,
    OrthodonticsDentistAssignment,
)
from app.models.user import User
from app.schemas.orthodontic_case_schema import (
    OrthodonticCaseActionResponse,
    OrthodonticCaseCreateRequest,
    OrthodonticCaseResponse,
    OrthodonticCaseTransitionRequest,
    OrthodonticCaseUpdateRequest,
    OrthodonticDentistOption,
    OrthodonticNextAppointment,
    OrthodonticPatientWorkspaceResponse,
    OrthodonticResponsibleChangeRequest,
    OrthodonticSummaryResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.orthodontics_entitlement_service import (
    OrthodonticsError,
    require_assigned_orthodontist,
    require_orthodontics_clinical_access,
    require_orthodontics_historical_read_access,
    resolve_orthodontics_access,
)


OPEN_STATUSES = ("DRAFT", "ACTIVE", "SUSPENDED")


class OrthodonticCaseError(OrthodonticsError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value: str | None) -> str | None:
    normalized = value.strip() if value else ""
    return normalized or None


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    case: OrthodonticCase,
    action: str,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="orthodontic_case",
            entity_id=case.id,
            action=action,
            result="SUCCESS",
            detail={"patient_id": str(case.patient_id), **(detail or {})},
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _timeline(
    session: Session,
    context: AuthContext,
    case: OrthodonticCase,
    *,
    title: str,
    event_type: str,
    summary: str | None = None,
) -> None:
    session.add(
        ClinicalTimelineEvent(
            company_id=case.company_id,
            patient_id=case.patient_id,
            clinical_record_id=case.clinical_record_id,
            event_type=event_type,
            entity_type="orthodontic_case",
            entity_id=case.id,
            title=title,
            summary=summary,
            clinical_date=_now(),
            site_id=case.primary_site_id,
            dentist_id=case.responsible_dentist_id,
            created_by=context.user.id,
            event_metadata={"status": case.status},
        )
    )


def _patient(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    *,
    lock: bool = False,
) -> Patient:
    statement = select(Patient).where(
        Patient.id == patient_id,
        Patient.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    patient = session.scalar(statement)
    if patient is None:
        raise OrthodonticCaseError(
            "ORTHODONTICS_PATIENT_WRONG_TENANT",
            "Paciente no encontrado en la empresa activa.",
            404,
        )
    return patient


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
        raise OrthodonticCaseError(
            "ORTHODONTICS_CASE_NOT_FOUND",
            "Caso de Ortodoncia no encontrado.",
            404,
        )
    return case


def _current_dentist_id(session: Session, context: AuthContext) -> UUID:
    access = require_orthodontics_clinical_access(session, context, write=True)
    if access.dentist_id is None:
        raise OrthodonticCaseError(
            "ORTHODONTICS_ACCESS_DENIED",
            "No existe identidad odontológica activa para esta acción.",
            403,
        )
    return access.dentist_id


def _require_case_write_access(
    session: Session,
    context: AuthContext,
    case: OrthodonticCase,
) -> UUID:
    """Apply the active module, identity, assignment and case-site gates."""
    access = require_orthodontics_clinical_access(session, context, write=True)
    if access.dentist_id is None:
        raise OrthodonticCaseError(
            "ORTHODONTICS_ACCESS_DENIED",
            "No existe identidad odontológica activa para esta acción.",
            403,
        )
    require_assigned_orthodontist(
        session,
        company_id=case.company_id,
        dentist_id=access.dentist_id,
        site_id=case.primary_site_id,
    )
    return access.dentist_id


def _check_version(case: OrthodonticCase, row_version: int) -> None:
    if case.row_version != row_version:
        raise OrthodonticCaseError(
            "ORTHODONTICS_CASE_VERSION_CONFLICT",
            "El caso cambió desde la última consulta. Actualiza e inténtalo nuevamente.",
            409,
        )


def _case_response(session: Session, case: OrthodonticCase) -> OrthodonticCaseResponse:
    responsible = session.execute(
        select(
            Dentist,
            User,
            OrthodonticsDentistAssignment.id,
            DentistSite.id,
        )
        .outerjoin(User, User.id == Dentist.user_id)
        .outerjoin(
            OrthodonticsDentistAssignment,
            (OrthodonticsDentistAssignment.company_id == case.company_id)
            & (OrthodonticsDentistAssignment.dentist_id == Dentist.id)
            & (OrthodonticsDentistAssignment.is_active.is_(True)),
        )
        .outerjoin(
            DentistSite,
            (DentistSite.company_id == case.company_id)
            & (DentistSite.dentist_id == Dentist.id)
            & (DentistSite.site_id == case.primary_site_id)
            & (DentistSite.is_active.is_(True)),
        )
        .where(
            Dentist.id == case.responsible_dentist_id,
            Dentist.company_id == case.company_id,
        )
    ).first()
    responsible_dentist = responsible[0] if responsible else None
    responsible_user = responsible[1] if responsible else None
    responsible_name = (
        responsible_dentist.name
        if responsible_dentist is not None
        else "Profesional no disponible"
    )
    responsible_available = bool(
        responsible_dentist is not None
        and responsible_dentist.is_active
        and responsible_dentist.status == "Activo"
        and responsible_user is not None
        and responsible_user.is_active
        and responsible_user.status == "Activo"
        and responsible[2] is not None
        and responsible[3] is not None
    )
    display_status = (
        "DISCONTINUED"
        if case.status == "COMPLETED" and case.closure_reason_code == "DISCONTINUED"
        else case.status
    )
    return OrthodonticCaseResponse(
        id=case.id,
        company_id=case.company_id,
        patient_id=case.patient_id,
        clinical_record_id=case.clinical_record_id,
        primary_site_id=case.primary_site_id,
        responsible_dentist_id=case.responsible_dentist_id,
        responsible_dentist_name=responsible_name,
        responsible_dentist_available=responsible_available,
        status=case.status,
        display_status=display_status,
        started_at=case.started_at,
        completed_at=case.completed_at,
        closure_reason_code=case.closure_reason_code,
        closure_notes=case.closure_notes,
        treatment_plan=case.treatment_plan,
        current_appliance_summary=case.current_appliance_summary,
        row_version=case.row_version,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


def _next_appointment(
    session: Session,
    case: OrthodonticCase,
) -> OrthodonticNextAppointment | None:
    appointment = session.scalar(
        select(Appointment)
        .where(
            Appointment.company_id == case.company_id,
            Appointment.patient_id == case.patient_id,
            Appointment.site_id == case.primary_site_id,
            Appointment.starts_at >= _now(),
            Appointment.status.notin_(("Cancelada", "Atendida")),
            Appointment.is_active.is_(True),
        )
        .order_by(Appointment.starts_at, Appointment.id)
        .limit(1)
    )
    if appointment is None:
        return None
    return OrthodonticNextAppointment(
        id=appointment.id,
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
        site_id=appointment.site_id,
        dentist_id=appointment.dentist_id,
        reason=appointment.reason,
        status=appointment.status,
    )


def _summary(session: Session, case: OrthodonticCase) -> OrthodonticSummaryResponse:
    latest = session.execute(
        select(OrthodonticEvolution, ClinicalEvolution, Dentist.name)
        .join(
            ClinicalEvolution,
            ClinicalEvolution.id == OrthodonticEvolution.clinical_evolution_id,
        )
        .join(Dentist, Dentist.id == ClinicalEvolution.dentist_id)
        .where(
            OrthodonticEvolution.company_id == case.company_id,
            OrthodonticEvolution.orthodontic_case_id == case.id,
            ClinicalEvolution.status == "SIGNED",
        )
        .order_by(ClinicalEvolution.attended_at.desc(), OrthodonticEvolution.id.desc())
        .limit(1)
    ).first()
    orthodontic = latest[0] if latest else None
    clinical = latest[1] if latest else None
    professional_name = latest[2] if latest else None
    return OrthodonticSummaryResponse(
        case=_case_response(session, case),
        last_visit=clinical.attended_at if clinical else None,
        last_visit_professional=professional_name,
        what_was_done=clinical.performed_procedure if clinical else None,
        next_session_instructions=(orthodontic.next_session_instructions if orthodontic else None),
        next_clinical_control=(orthodontic.next_control_label if orthodontic else None),
        suggested_next_control_date=(orthodontic.suggested_next_control_date if orthodontic else None),
        active_alerts=(
            [orthodontic.alert_text]
            if orthodontic and orthodontic.alert_active and orthodontic.alert_text
            else []
        ),
        next_appointment=_next_appointment(session, case),
    )


def _eligible_responsibles(
    session: Session,
    company_id: UUID,
    site_id: UUID | None,
) -> list[OrthodonticDentistOption]:
    linked_user = aliased(User)
    dentists = session.execute(
        select(Dentist.id, Dentist.name)
        .join(
            OrthodonticsDentistAssignment,
            OrthodonticsDentistAssignment.dentist_id == Dentist.id,
        )
        .join(linked_user, linked_user.id == Dentist.user_id)
        .join(
            DentistSite,
            DentistSite.dentist_id == Dentist.id,
        )
        .where(
            Dentist.company_id == company_id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
            linked_user.company_id == company_id,
            linked_user.is_active.is_(True),
            linked_user.status == "Activo",
            OrthodonticsDentistAssignment.company_id == company_id,
            OrthodonticsDentistAssignment.is_active.is_(True),
            DentistSite.company_id == company_id,
            DentistSite.site_id == site_id,
            DentistSite.is_active.is_(True),
        )
        .order_by(Dentist.name, Dentist.id)
    ).all()
    return [OrthodonticDentistOption(id=item.id, name=item.name) for item in dentists]


def get_patient_orthodontics(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
) -> OrthodonticPatientWorkspaceResponse:
    _patient(session, context, patient_id)
    cases = list(
        session.scalars(
            select(OrthodonticCase)
            .where(
                OrthodonticCase.company_id == context.user.company_id,
                OrthodonticCase.patient_id == patient_id,
            )
            .order_by(OrthodonticCase.created_at.desc(), OrthodonticCase.id.desc())
        )
    )
    visible_cases: list[OrthodonticCase] = []
    access = None
    denied: OrthodonticsError | None = None
    for item in cases:
        try:
            item_access = require_orthodontics_historical_read_access(
                session,
                context,
                site_id=item.primary_site_id,
            )
        except OrthodonticsError as exc:
            denied = exc
            continue
        visible_cases.append(item)
        if item_access.allowed:
            access = item_access

    if not cases:
        access = require_orthodontics_clinical_access(session, context)
    elif not visible_cases:
        if denied is not None:
            raise denied
        raise OrthodonticCaseError(
            "ORTHODONTICS_ACCESS_DENIED",
            "No tienes acceso al historial de Ortodoncia de este paciente.",
            403,
        )
    elif access is None:
        access = resolve_orthodontics_access(session, context)

    cases = visible_cases
    active = next((item for item in cases if item.status in OPEN_STATUSES), None)
    historical = [item for item in cases if item.status not in OPEN_STATUSES]
    company = session.get(Company, context.user.company_id)
    country = (company.country if company else "").strip().upper()
    record_label = (
        "Ficha clínica de Ortodoncia"
        if country in {"CL", "CHILE"}
        else "Historia clínica de Ortodoncia"
    )
    return OrthodonticPatientWorkspaceResponse(
        access=access,
        active_case=_case_response(session, active) if active else None,
        historical_cases=[_case_response(session, item) for item in historical],
        summary=_summary(session, active) if active else None,
        eligible_responsibles=(
            _eligible_responsibles(
                session,
                context.user.company_id,
                context.auth_session.active_site_id,
            )
            if access.allowed
            else []
        ),
        record_label=record_label,
    )


def create_orthodontic_case(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
    payload: OrthodonticCaseCreateRequest,
    metadata: RequestMetadata,
) -> OrthodonticCaseActionResponse:
    current_dentist_id = _current_dentist_id(session, context)
    patient = _patient(session, context, patient_id, lock=True)
    existing = session.scalar(
        select(OrthodonticCase).where(
            OrthodonticCase.company_id == context.user.company_id,
            OrthodonticCase.patient_id == patient.id,
            OrthodonticCase.status.in_(OPEN_STATUSES),
        )
    )
    if existing:
        raise OrthodonticCaseError(
            "ORTHODONTICS_CASE_ALREADY_OPEN",
            "El paciente ya tiene un caso de Ortodoncia abierto.",
            409,
        )
    site_id = context.auth_session.active_site_id
    if site_id is None:
        raise OrthodonticCaseError(
            "ORTHODONTICS_ACCESS_DENIED",
            "Selecciona una sede activa antes de crear el caso.",
            403,
        )
    responsible_id = payload.responsible_dentist_id or current_dentist_id
    require_assigned_orthodontist(
        session,
        company_id=context.user.company_id,
        dentist_id=responsible_id,
        site_id=site_id,
    )
    record = session.scalar(
        select(ClinicalRecord).where(
            ClinicalRecord.company_id == context.user.company_id,
            ClinicalRecord.patient_id == patient.id,
        )
    )
    if record is None:
        record = ClinicalRecord(
            company_id=context.user.company_id,
            patient_id=patient.id,
            opening_site_id=site_id,
            opening_dentist_id=current_dentist_id,
            created_by=context.user.id,
            updated_by=context.user.id,
        )
        session.add(record)
        session.flush()
    case = OrthodonticCase(
        company_id=context.user.company_id,
        patient_id=patient.id,
        clinical_record_id=record.id,
        primary_site_id=site_id,
        responsible_dentist_id=responsible_id,
        status="DRAFT",
        treatment_plan=_clean(payload.treatment_plan),
        current_appliance_summary=_clean(payload.current_appliance_summary),
        created_by_user_id=context.user.id,
        updated_by_user_id=context.user.id,
    )
    session.add(case)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise OrthodonticCaseError(
            "ORTHODONTICS_CASE_ALREADY_OPEN",
            "El paciente ya tiene un caso de Ortodoncia abierto.",
            409,
        ) from exc
    _timeline(
        session,
        context,
        case,
        title="Caso de Ortodoncia creado",
        event_type="ORTHODONTIC_CASE_CREATED",
    )
    _audit(session, context, metadata, case, "ORTHODONTIC_CASE_CREATED")
    session.commit()
    session.refresh(case)
    return OrthodonticCaseActionResponse(
        message="Caso de Ortodoncia creado en borrador.",
        case=_case_response(session, case),
    )


def get_orthodontic_case(
    session: Session,
    context: AuthContext,
    case_id: UUID,
) -> OrthodonticSummaryResponse:
    case = _case(session, context, case_id)
    require_orthodontics_historical_read_access(
        session,
        context,
        site_id=case.primary_site_id,
    )
    return _summary(session, case)


def update_orthodontic_case(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    payload: OrthodonticCaseUpdateRequest,
    metadata: RequestMetadata,
) -> OrthodonticCaseActionResponse:
    case = _case(session, context, case_id, lock=True)
    _require_case_write_access(session, context, case)
    if case.status not in {"DRAFT", "ACTIVE"}:
        suspended = case.status == "SUSPENDED"
        message = "El caso suspendido es de solo lectura. Reactívalo para modificarlo." if suspended else "El caso cerrado es de solo lectura."
        raise OrthodonticCaseError(
            "ORTHODONTICS_CASE_SUSPENDED" if suspended else "ORTHODONTICS_CASE_CLOSED",
            message,
            409,
        )
    _check_version(case, payload.row_version)
    changed: list[str] = []
    if "treatment_plan" in payload.model_fields_set:
        plan = _clean(payload.treatment_plan)
        if case.treatment_plan != plan:
            case.treatment_plan = plan
            changed.append("treatment_plan")
    if "current_appliance_summary" in payload.model_fields_set:
        appliance = _clean(payload.current_appliance_summary)
        if case.current_appliance_summary != appliance:
            case.current_appliance_summary = appliance
            changed.append("current_appliance_summary")
    if changed:
        case.row_version += 1
        case.updated_by_user_id = context.user.id
        if "treatment_plan" in changed:
            _audit(session, context, metadata, case, "ORTHODONTIC_CASE_PLAN_UPDATED", {"fields": ["treatment_plan"]})
        if "current_appliance_summary" in changed:
            _audit(session, context, metadata, case, "ORTHODONTIC_CASE_APPLIANCE_UPDATED", {"fields": ["current_appliance_summary"]})
        session.commit()
        session.refresh(case)
    return OrthodonticCaseActionResponse(
        message="Resumen clínico actualizado." if changed else "Sin cambios.",
        case=_case_response(session, case),
    )


def activate_orthodontic_case(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    metadata: RequestMetadata,
) -> OrthodonticCaseActionResponse:
    case = _case(session, context, case_id, lock=True)
    _require_case_write_access(session, context, case)
    _check_version(case, payload.row_version)
    if case.status != "DRAFT":
        raise OrthodonticCaseError(
            "ORTHODONTICS_INVALID_TRANSITION",
            "Solo un caso en borrador puede activarse.",
            409,
        )
    require_assigned_orthodontist(
        session,
        company_id=case.company_id,
        dentist_id=case.responsible_dentist_id,
        site_id=case.primary_site_id,
    )
    case.status = "ACTIVE"
    case.started_at = _now()
    case.row_version += 1
    case.updated_by_user_id = context.user.id
    _timeline(session, context, case, title="Tratamiento de Ortodoncia iniciado", event_type="ORTHODONTIC_CASE_ACTIVATED")
    _audit(session, context, metadata, case, "ORTHODONTIC_CASE_ACTIVATED")
    session.commit()
    session.refresh(case)
    return OrthodonticCaseActionResponse(message="Caso de Ortodoncia iniciado.", case=_case_response(session, case))


def suspend_orthodontic_case(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    metadata: RequestMetadata,
) -> OrthodonticCaseActionResponse:
    case = _case(session, context, case_id, lock=True)
    _require_case_write_access(session, context, case)
    _check_version(case, payload.row_version)
    if case.status != "ACTIVE":
        raise OrthodonticCaseError(
            "ORTHODONTICS_INVALID_TRANSITION",
            "Solo un caso activo puede suspenderse.",
            409,
        )
    case.status = "SUSPENDED"
    case.row_version += 1
    case.updated_by_user_id = context.user.id
    _timeline(
        session,
        context,
        case,
        title="Tratamiento de Ortodoncia suspendido",
        event_type="ORTHODONTIC_CASE_SUSPENDED",
    )
    _audit(
        session,
        context,
        metadata,
        case,
        "ORTHODONTIC_CASE_SUSPENDED",
        {"reason_provided": bool(_clean(payload.reason))},
    )
    session.commit()
    session.refresh(case)
    return OrthodonticCaseActionResponse(
        message="Caso de Ortodoncia suspendido.",
        case=_case_response(session, case),
    )


def resume_orthodontic_case(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    metadata: RequestMetadata,
) -> OrthodonticCaseActionResponse:
    case = _case(session, context, case_id, lock=True)
    _require_case_write_access(session, context, case)
    _check_version(case, payload.row_version)
    if case.status != "SUSPENDED":
        raise OrthodonticCaseError(
            "ORTHODONTICS_INVALID_TRANSITION",
            "Solo un caso suspendido puede reanudarse.",
            409,
        )
    require_assigned_orthodontist(
        session,
        company_id=case.company_id,
        dentist_id=case.responsible_dentist_id,
        site_id=case.primary_site_id,
    )
    case.status = "ACTIVE"
    case.row_version += 1
    case.updated_by_user_id = context.user.id
    _timeline(
        session,
        context,
        case,
        title="Tratamiento de Ortodoncia reactivado",
        event_type="ORTHODONTIC_CASE_REACTIVATED",
    )
    _audit(session, context, metadata, case, "ORTHODONTIC_CASE_REACTIVATED")
    session.commit()
    session.refresh(case)
    return OrthodonticCaseActionResponse(
        message="Caso de Ortodoncia reactivado.",
        case=_case_response(session, case),
    )


def _close_case(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    payload: OrthodonticCaseTransitionRequest,
    metadata: RequestMetadata,
    *,
    discontinued: bool,
) -> OrthodonticCaseActionResponse:
    case = _case(session, context, case_id, lock=True)
    _require_case_write_access(session, context, case)
    _check_version(case, payload.row_version)
    if case.status not in {"ACTIVE", "SUSPENDED"}:
        raise OrthodonticCaseError(
            "ORTHODONTICS_INVALID_TRANSITION",
            "Solo un caso activo o suspendido puede cerrarse.",
            409,
        )
    reason = _clean(payload.reason)
    if discontinued and not reason:
        raise OrthodonticCaseError(
            "ORTHODONTICS_DISCONTINUATION_REASON_REQUIRED",
            "Registra el motivo de interrupción del caso.",
            422,
        )
    case.status = "COMPLETED"
    case.completed_at = _now()
    case.closed_by_user_id = context.user.id
    case.closure_reason_code = "DISCONTINUED" if discontinued else "COMPLETED"
    case.closure_notes = reason
    case.row_version += 1
    case.updated_by_user_id = context.user.id
    action = "ORTHODONTIC_CASE_DISCONTINUED" if discontinued else "ORTHODONTIC_CASE_COMPLETED"
    title = "Tratamiento de Ortodoncia interrumpido" if discontinued else "Tratamiento de Ortodoncia completado"
    _timeline(session, context, case, title=title, event_type=action)
    _audit(session, context, metadata, case, action, {"closure_reason_code": case.closure_reason_code})
    session.commit()
    session.refresh(case)
    return OrthodonticCaseActionResponse(message=f"{title}.", case=_case_response(session, case))


def complete_orthodontic_case(session: Session, context: AuthContext, case_id: UUID, payload: OrthodonticCaseTransitionRequest, metadata: RequestMetadata) -> OrthodonticCaseActionResponse:
    return _close_case(session, context, case_id, payload, metadata, discontinued=False)


def discontinue_orthodontic_case(session: Session, context: AuthContext, case_id: UUID, payload: OrthodonticCaseTransitionRequest, metadata: RequestMetadata) -> OrthodonticCaseActionResponse:
    return _close_case(session, context, case_id, payload, metadata, discontinued=True)


def change_responsible_orthodontist(
    session: Session,
    context: AuthContext,
    case_id: UUID,
    payload: OrthodonticResponsibleChangeRequest,
    metadata: RequestMetadata,
) -> OrthodonticCaseActionResponse:
    case = _case(session, context, case_id, lock=True)
    _require_case_write_access(session, context, case)
    if case.status == "COMPLETED":
        raise OrthodonticCaseError("ORTHODONTICS_CASE_CLOSED", "El caso cerrado es de solo lectura.", 409)
    _check_version(case, payload.row_version)
    new_responsible = require_assigned_orthodontist(
        session,
        company_id=case.company_id,
        dentist_id=payload.responsible_dentist_id,
        site_id=case.primary_site_id,
    )
    previous = case.responsible_dentist_id
    if previous != new_responsible.id:
        case.responsible_dentist_id = new_responsible.id
        case.row_version += 1
        case.updated_by_user_id = context.user.id
        _timeline(
            session,
            context,
            case,
            title="Responsable de Ortodoncia actualizado",
            event_type="ORTHODONTIC_CASE_RESPONSIBLE_CHANGED",
        )
        _audit(session, context, metadata, case, "ORTHODONTIC_CASE_RESPONSIBLE_CHANGED", {"previous_dentist_id": str(previous), "new_dentist_id": str(new_responsible.id)})
        session.commit()
        session.refresh(case)
    return OrthodonticCaseActionResponse(message="Responsable clínico actualizado.", case=_case_response(session, case))
