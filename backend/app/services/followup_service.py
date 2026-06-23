import math
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agenda import (
    Appointment,
    AppointmentHistory,
    Dentist,
    Patient,
    PatientResponsible,
)
from app.models.audit_event import AuditEvent
from app.models.followup import AppointmentCare, FollowupManagement, PatientFollowup
from app.models.site import Site
from app.schemas.agenda_schema import AppointmentCreateRequest
from app.schemas.followup_schema import (
    CompleteAppointmentRequest,
    CompleteAppointmentResponse,
    FollowupActionResponse,
    FollowupAppointmentRequest,
    FollowupContactRequest,
    FollowupDashboardResponse,
    FollowupListResponse,
    FollowupResponse,
    ManagementResponse,
    WhatsAppLinkResponse,
)
from app.services.agenda_service import AgendaError, create_appointment
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import authorized_site_ids


CONTACT_LEAD_DAYS = 15
UPCOMING_DAYS = 7
OPEN_STATUSES = {"Pendiente", "Contactado", "Cita programada"}
BOGOTA_TZ = ZoneInfo("America/Bogota")


def _today() -> date:
    return datetime.now(BOGOTA_TZ).date()


class FollowupError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _site_ids(session: Session, context: AuthContext) -> set[UUID]:
    return authorized_site_ids(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        active_only=False,
    )


def _dentist_scope(session: Session, context: AuthContext) -> UUID | None:
    if "DENTIST" in context.roles and not any(
        role in context.roles for role in {"ADMINISTRATOR", "DENTIST_ADMIN"}
    ):
        return session.scalar(select(Dentist.id).where(
            Dentist.company_id == context.user.company_id,
            Dentist.user_id == context.user.id,
            Dentist.is_active.is_(True),
        ))
    return None


def _classification(item: PatientFollowup) -> str:
    if item.status == "Cita programada" and item.scheduled_appointment_id:
        return "Con cita futura"
    if item.status not in OPEN_STATUSES:
        return "Cerrado"
    today = _today()
    if item.followup_date < today:
        return "Vencido"
    if item.followup_date <= today + timedelta(days=UPCOMING_DAYS):
        return "Próximo a vencer"
    if item.contact_from <= today:
        return "Pendiente por contactar"
    return "Aún no requiere contacto"


def _contact_mobile(session: Session, patient: Patient) -> str:
    if patient.birth_date:
        today = _today()
        age = today.year - patient.birth_date.year - (
            (today.month, today.day)
            < (patient.birth_date.month, patient.birth_date.day)
        )
        if age < 18:
            responsible = session.scalar(select(PatientResponsible).where(
                PatientResponsible.patient_id == patient.id,
                PatientResponsible.is_active.is_(True),
                PatientResponsible.is_primary.is_(True),
            ))
            if responsible:
                return responsible.mobile
    return patient.mobile


def _managements(session: Session, followup_id: UUID) -> list[ManagementResponse]:
    items = session.scalars(select(FollowupManagement).where(
        FollowupManagement.followup_id == followup_id
    ).order_by(FollowupManagement.occurred_at.desc()))
    return [
        ManagementResponse(
            id=item.id, management_type=item.management_type,
            result=item.result, observation=item.observation,
            next_contact_at=item.next_contact_at,
            message_content=item.message_content, user_id=item.user_id,
            occurred_at=item.occurred_at,
        ) for item in items
    ]


def _response(session: Session, context: AuthContext, item: PatientFollowup, detail=False) -> FollowupResponse:
    patient = session.get(Patient, item.patient_id)
    dentist = session.get(Dentist, item.dentist_id)
    site = session.get(Site, item.site_id)
    care = session.get(AppointmentCare, item.care_id)
    scheduled = session.get(Appointment, item.scheduled_appointment_id) if item.scheduled_appointment_id else None
    can_view_clinical = "followups.view_clinical_summary" in context.permissions
    return FollowupResponse(
        id=item.id, patient_id=item.patient_id,
        patient_name=f"{patient.first_names} {patient.last_names}".strip(),
        contact_mobile=_contact_mobile(session, patient),
        origin_appointment_id=item.origin_appointment_id, care_id=item.care_id,
        dentist_id=item.dentist_id, dentist_name=dentist.name,
        site_id=item.site_id, site_name=site.name,
        followup_date=item.followup_date, contact_from=item.contact_from,
        reason=item.reason, status=item.status,
        classification=_classification(item),
        scheduled_appointment_id=item.scheduled_appointment_id,
        scheduled_appointment_at=scheduled.starts_at if scheduled else None,
        last_contact_at=item.last_contact_at, next_contact_at=item.next_contact_at,
        close_reason=item.close_reason,
        attention_description=care.attention_description if can_view_clinical else None,
        prescribed_medications=care.prescribed_medications if can_view_clinical else None,
        managements=_managements(session, item.id) if detail else [],
    )


def _get(session: Session, context: AuthContext, followup_id: UUID, lock=False) -> PatientFollowup:
    statement = select(PatientFollowup).where(
        PatientFollowup.id == followup_id,
        PatientFollowup.company_id == context.user.company_id,
        PatientFollowup.site_id.in_(_site_ids(session, context)),
    )
    dentist_id = _dentist_scope(session, context)
    if dentist_id:
        statement = statement.where(PatientFollowup.dentist_id == dentist_id)
    if lock:
        statement = statement.with_for_update()
    item = session.scalar(statement)
    if not item:
        raise FollowupError("Seguimiento no encontrado.", 404)
    return item


def _audit(session, context, metadata, item, action, detail=None):
    session.add(AuditEvent(
        company_id=context.user.company_id, user_id=context.user.id,
        session_id=context.auth_session.id, entity="followup",
        entity_id=item.id, action=action, result="SUCCESS", detail=detail,
        ip_address=metadata.ip_address, user_agent=metadata.user_agent,
    ))


def complete_appointment(session: Session, context: AuthContext, appointment_id: UUID,
                         payload: CompleteAppointmentRequest, metadata: RequestMetadata) -> CompleteAppointmentResponse:
    appointment = session.scalar(select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.company_id == context.user.company_id,
        Appointment.site_id.in_(_site_ids(session, context)),
    ).with_for_update())
    if not appointment:
        raise FollowupError("Cita no encontrada.", 404)
    if appointment.status not in {"Programada", "Confirmada"}:
        raise FollowupError("Esta cita no puede finalizarse.", 409)
    dentist_id = _dentist_scope(session, context)
    if dentist_id is not None and appointment.dentist_id != dentist_id:
        raise FollowupError("Solo puede finalizar sus propias citas.", 403)
    if session.scalar(select(AppointmentCare.id).where(AppointmentCare.appointment_id == appointment.id)):
        raise FollowupError("La atención de esta cita ya fue finalizada.", 409)
    now = datetime.now(timezone.utc)
    care = AppointmentCare(
        company_id=appointment.company_id, appointment_id=appointment.id,
        patient_id=appointment.patient_id, dentist_id=appointment.dentist_id,
        attention_description=payload.attention_description,
        prescribed_medications=payload.prescribed_medications,
        requires_followup=payload.requires_followup,
        recommended_followup_date=payload.recommended_followup_date,
        followup_reason=payload.followup_reason,
        registered_by=context.user.id, registered_at=now,
    )
    session.add(care)
    session.flush()
    followup = None
    if payload.requires_followup:
        followup = PatientFollowup(
            company_id=appointment.company_id, patient_id=appointment.patient_id,
            origin_appointment_id=appointment.id, care_id=care.id,
            dentist_id=appointment.dentist_id, site_id=appointment.site_id,
            followup_date=payload.recommended_followup_date,
            contact_from=payload.recommended_followup_date - timedelta(days=CONTACT_LEAD_DAYS),
            reason=payload.followup_reason, status="Pendiente",
            created_by=context.user.id, updated_by=context.user.id,
        )
        session.add(followup)
        session.flush()
    previous_status = appointment.status
    appointment.status = "Atendida"
    appointment.updated_by = context.user.id
    session.add(AppointmentHistory(
        company_id=appointment.company_id,
        appointment_id=appointment.id,
        previous_status=previous_status,
        new_status="Atendida",
        reason="Atención finalizada",
        user_id=context.user.id,
    ))
    _audit(session, context, metadata, followup or care, "APPOINTMENT_COMPLETED",
           {"appointment_id": str(appointment.id), "followup_created": bool(followup)})
    session.commit()
    return CompleteAppointmentResponse(
        appointment_id=appointment.id, appointment_status=appointment.status,
        care_id=care.id,
        followup=_response(session, context, followup, True) if followup else None,
    )


def list_followups(session: Session, context: AuthContext, classification: str | None,
                   status: str | None, search: str | None, site_id: UUID | None,
                   page: int, page_size: int) -> FollowupListResponse:
    allowed_site_ids = _site_ids(session, context)
    if site_id is not None:
        if site_id not in allowed_site_ids:
            raise FollowupError("No tiene acceso a la sede seleccionada.", 403)
        allowed_site_ids = {site_id}
    statement = select(PatientFollowup).join(Patient, Patient.id == PatientFollowup.patient_id).where(
        PatientFollowup.company_id == context.user.company_id,
        PatientFollowup.site_id.in_(allowed_site_ids),
    )
    dentist_id = _dentist_scope(session, context)
    if dentist_id:
        statement = statement.where(PatientFollowup.dentist_id == dentist_id)
    if status:
        statement = statement.where(PatientFollowup.status == status)
    if search:
        statement = statement.where(Patient.search_text.ilike(f"%{search.strip().casefold()}%"))
    items = list(session.scalars(statement.order_by(PatientFollowup.followup_date).limit(1000)))
    if classification:
        items = [item for item in items if _classification(item) == classification]
    total = len(items)
    items = items[(page - 1) * page_size: page * page_size]
    return FollowupListResponse(
        items=[_response(session, context, item) for item in items],
        page=page, page_size=page_size, total=total,
        pages=max(1, math.ceil(total / page_size)),
    )


def get_followup(session, context, followup_id):
    return _response(session, context, _get(session, context, followup_id), True)


def register_contact(session: Session, context: AuthContext, followup_id: UUID,
                     payload: FollowupContactRequest, metadata: RequestMetadata):
    item = _get(session, context, followup_id, True)
    if item.status not in OPEN_STATUSES:
        raise FollowupError("El seguimiento está cerrado.", 409)
    now = datetime.now(timezone.utc)
    session.add(FollowupManagement(
        company_id=item.company_id, followup_id=item.id, patient_id=item.patient_id,
        management_type=payload.management_type, result=payload.result,
        observation=payload.observation, next_contact_at=payload.next_contact_at,
        user_id=context.user.id, occurred_at=now,
    ))
    item.last_contact_at = now
    item.next_contact_at = payload.next_contact_at
    item.status = "Contactado"
    item.updated_by = context.user.id
    _audit(session, context, metadata, item, "FOLLOWUP_CONTACT_REGISTERED", {"result": payload.result})
    session.commit()
    return FollowupActionResponse(message="Contacto registrado.", followup=_response(session, context, item, True))


def whatsapp_link(session: Session, context: AuthContext, followup_id: UUID, metadata: RequestMetadata):
    item = _get(session, context, followup_id, True)
    patient = session.get(Patient, item.patient_id)
    phone = "".join(filter(str.isdigit, _contact_mobile(session, patient)))
    if len(phone) == 10:
        phone = f"57{phone}"
    if len(phone) < 10:
        raise FollowupError("El paciente no tiene un celular válido.", 409)
    message = (
        f"Hola, {patient.first_names}. En Dentia queremos recordarte que tienes "
        f"un control odontológico recomendado para {item.followup_date.isoformat()}, "
        f"relacionado con {item.reason}. ¿Deseas que programemos tu cita?"
    )
    now = datetime.now(timezone.utc)
    session.add(FollowupManagement(
        company_id=item.company_id, followup_id=item.id, patient_id=item.patient_id,
        management_type="WhatsApp", result="Enlace generado",
        message_content=message, user_id=context.user.id, occurred_at=now,
    ))
    item.last_contact_at = now
    item.updated_by = context.user.id
    _audit(session, context, metadata, item, "FOLLOWUP_WHATSAPP_LINK_GENERATED")
    session.commit()
    return WhatsAppLinkResponse(url=f"https://wa.me/{phone}?text={quote(message)}", phone=phone, message=message)


def schedule_followup_appointment(session: Session, context: AuthContext, followup_id: UUID,
                                  payload: FollowupAppointmentRequest, metadata: RequestMetadata):
    if "appointments.create" not in context.permissions:
        raise FollowupError("No tiene permiso para programar citas.", 403)
    item = _get(session, context, followup_id)
    if item.status not in OPEN_STATUSES:
        raise FollowupError("El seguimiento está cerrado.", 409)
    try:
        appointment = create_appointment(
            session,
            context,
            AppointmentCreateRequest(
                patient_id=item.patient_id, dentist_id=payload.dentist_id,
                site_id=payload.site_id, appointment_type_id=payload.appointment_type_id,
                starts_at=payload.starts_at, ends_at=payload.ends_at, reason=payload.reason,
                notes=payload.notes, is_overbook=payload.is_overbook,
                overbook_reason=payload.overbook_reason,
            ),
            metadata,
            commit=False,
        )
    except AgendaError as exc:
        raise FollowupError(str(exc), exc.status_code) from exc
    item = _get(session, context, followup_id, True)
    item.scheduled_appointment_id = appointment.id
    item.status = "Cita programada"
    item.updated_by = context.user.id
    session.add(FollowupManagement(
        company_id=item.company_id, followup_id=item.id, patient_id=item.patient_id,
        management_type="Agenda", result="Cita programada",
        observation=f"Cita {appointment.id}", user_id=context.user.id,
        occurred_at=datetime.now(timezone.utc),
    ))
    _audit(session, context, metadata, item, "FOLLOWUP_APPOINTMENT_SCHEDULED", {"appointment_id": str(appointment.id)})
    session.commit()
    return FollowupActionResponse(message="Cita programada.", followup=_response(session, context, item, True))


def close_followup(session, context, followup_id, payload, metadata):
    item = _get(session, context, followup_id, True)
    item.status = payload.status
    item.closed_at = datetime.now(timezone.utc)
    item.closed_by = context.user.id
    item.close_reason = payload.reason
    item.updated_by = context.user.id
    _audit(session, context, metadata, item, "FOLLOWUP_CLOSED", {"status": payload.status})
    session.commit()
    return FollowupActionResponse(message="Seguimiento cerrado.", followup=_response(session, context, item, True))


def reopen_followup(session, context, followup_id, metadata):
    item = _get(session, context, followup_id, True)
    item.status = "Pendiente"
    item.closed_at = None
    item.closed_by = None
    item.close_reason = None
    item.updated_by = context.user.id
    _audit(session, context, metadata, item, "FOLLOWUP_REOPENED")
    session.commit()
    return FollowupActionResponse(message="Seguimiento reabierto.", followup=_response(session, context, item, True))


def dashboard(session, context, site_id: UUID | None):
    response = list_followups(
        session, context, None, None, None, site_id, 1, 1000
    )
    open_items = [item for item in response.items if item.status in OPEN_STATUSES]
    return FollowupDashboardResponse(
        pending=sum(item.classification == "Pendiente por contactar" for item in open_items),
        upcoming=sum(item.classification == "Próximo a vencer" for item in open_items),
        overdue=sum(item.classification == "Vencido" for item in open_items),
        scheduled=sum(item.classification == "Con cita futura" for item in open_items),
        priority_items=sorted(
            [item for item in open_items if item.classification in {"Vencido", "Próximo a vencer"}],
            key=lambda item: item.followup_date,
        )[:10],
    )


def sync_cancelled_appointment(session: Session, appointment_id: UUID) -> None:
    item = session.scalar(select(PatientFollowup).where(
        PatientFollowup.scheduled_appointment_id == appointment_id
    ))
    if item:
        item.scheduled_appointment_id = None
        item.status = "Pendiente"


def sync_rescheduled_appointment(session: Session, old_id: UUID, new_id: UUID) -> None:
    item = session.scalar(select(PatientFollowup).where(
        PatientFollowup.scheduled_appointment_id == old_id
    ))
    if item:
        item.scheduled_appointment_id = new_id
        item.status = "Cita programada"
