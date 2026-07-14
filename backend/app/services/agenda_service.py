from datetime import datetime, timezone
from urllib.parse import quote
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.agenda import (
    Appointment,
    AppointmentHistory,
    AppointmentType,
    Dentist,
    DentistSite,
    Patient,
    PatientResponsible,
)
from app.models.audit_event import AuditEvent
from app.models.clinical_record import (
    ClinicalEvolution,
    ClinicalEvolutionProcedure,
    ClinicalRecord,
)
from app.models.company import Company
from app.models.site import Site
from app.models.treatment import Treatment, TreatmentProcedure
from app.models.user import User
from app.schemas.agenda_schema import (
    AgendaEventsResponse,
    AgendaOptionsResponse,
    AppointmentClinicalContextResponse,
    AppointmentClinicalProcedureResponse,
    AppointmentClinicalTreatmentResponse,
    AppointmentCreateRequest,
    AppointmentResponse,
    AppointmentRescheduleRequest,
    AppointmentTimeAdjustRequest,
    AppointmentTypeOptionResponse,
    AppointmentUpdateRequest,
    AppointmentWhatsAppLinkResponse,
    ClinicalCareActionResult,
    ClinicalCareCompletionRequest,
    ClinicalCareCompletionResponse,
    DentistOptionResponse,
    SiteOptionResponse,
)
from app.schemas.clinical_record_schema import ClinicalEvolutionSignRequest
from app.schemas.followup_schema import CompleteAppointmentRequest
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import authorized_site_ids


ACTIVE_CONFLICT_STATES = {"Programada", "Confirmada"}
TERMINAL_STATES = {"Atendida", "Cancelada", "No Asistió", "Reprogramada"}
INITIAL_APPOINTMENT_TYPES = (
    ("Valoración", 30),
    ("Control", 30),
    ("Limpieza", 45),
    ("Tratamiento", 60),
    ("Urgencia", 30),
    ("Retiro de puntos", 15),
    ("Impresión", 15),
)
FALLBACK_TIMEZONE = "America/Bogota"
ZONE_LABELS = {
    "UPPER_ARCH": "Arcada superior",
    "LOWER_ARCH": "Arcada inferior",
    "FULL_MOUTH": "Boca completa",
    "QUADRANT_1": "Cuadrante 1",
    "QUADRANT_2": "Cuadrante 2",
    "QUADRANT_3": "Cuadrante 3",
    "QUADRANT_4": "Cuadrante 4",
    "ANTERIOR": "Anterior",
    "POSTERIOR": "Posterior",
}
SURFACE_LABELS = {
    "VESTIBULAR": "Vestibular",
    "LINGUAL": "Lingual",
    "PALATAL": "Palatal",
    "MESIAL": "Mesial",
    "DISTAL": "Distal",
    "OCCLUSAL": "Oclusal",
    "INCISAL": "Incisal",
}


class AgendaError(RuntimeError):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        *,
        conflicts: list[AppointmentResponse] | None = None,
        can_overbook: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.conflicts = conflicts
        self.can_overbook = can_overbook


def _authorized_site_ids(
    session: Session,
    context: AuthContext,
    *,
    active_only: bool = False,
) -> set[UUID]:
    return authorized_site_ids(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        active_only=active_only,
    )


def _require_site(
    session: Session,
    context: AuthContext,
    site_id: UUID,
) -> Site:
    if site_id not in _authorized_site_ids(
        session, context, active_only=True
    ):
        raise AgendaError("No tienes acceso a la sede seleccionada.", 403)
    site = session.scalar(
        select(Site).where(
            Site.id == site_id,
            Site.company_id == context.user.company_id,
            Site.is_active.is_(True),
            Site.status == "Activa",
        )
    )
    if site is None:
        raise AgendaError("La sede seleccionada no está disponible.")
    return site


def _require_patient(
    session: Session,
    context: AuthContext,
    patient_id: UUID,
) -> Patient:
    patient = session.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.company_id == context.user.company_id,
            Patient.is_active.is_(True),
        )
    )
    if patient is None:
        raise AgendaError("El paciente no existe o no está disponible.")
    return patient


def _require_type(
    session: Session,
    context: AuthContext,
    appointment_type_id: UUID,
) -> AppointmentType:
    appointment_type = session.scalar(
        select(AppointmentType).where(
            AppointmentType.id == appointment_type_id,
            AppointmentType.company_id == context.user.company_id,
            AppointmentType.is_active.is_(True),
        )
    )
    if appointment_type is None:
        raise AgendaError("El tipo de cita no existe o no está disponible.")
    return appointment_type


def _require_dentist_site(
    session: Session,
    context: AuthContext,
    dentist_id: UUID,
    site_id: UUID,
) -> Dentist:
    dentist = session.scalar(
        select(Dentist)
        .join(DentistSite, DentistSite.dentist_id == Dentist.id)
        .where(
            Dentist.id == dentist_id,
            Dentist.company_id == context.user.company_id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
            DentistSite.site_id == site_id,
            DentistSite.is_active.is_(True),
        )
    )
    if dentist is None:
        raise AgendaError("El odontólogo no está asociado a la sede.")
    return dentist


def _appointment_row(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    *,
    lock: bool = False,
):
    statement = (
        select(Appointment, Patient, Dentist, Site, AppointmentType, Company)
        .join(Patient, Patient.id == Appointment.patient_id)
        .join(Dentist, Dentist.id == Appointment.dentist_id)
        .join(Site, Site.id == Appointment.site_id)
        .join(Company, Company.id == Appointment.company_id)
        .join(
            AppointmentType,
            AppointmentType.id == Appointment.appointment_type_id,
        )
        .where(
            Appointment.id == appointment_id,
            Appointment.company_id == context.user.company_id,
            Appointment.is_active.is_(True),
        )
    )
    if lock:
        statement = statement.with_for_update(of=Appointment)
    row = session.execute(statement).one_or_none()
    if row is None:
        raise AgendaError("Cita no encontrada.", 404)
    if row[0].site_id not in _authorized_site_ids(session, context):
        raise AgendaError("No tienes acceso a esta cita.", 403)
    return row


def _local_calendar_iso(value: datetime, timezone_name: str) -> str:
    return (
        value.astimezone(ZoneInfo(timezone_name))
        .replace(tzinfo=None)
        .isoformat(timespec="seconds")
    )


def _clinical_record_for_appointment(
    session: Session,
    appointment: Appointment,
) -> ClinicalRecord | None:
    return session.scalar(
        select(ClinicalRecord).where(
            ClinicalRecord.company_id == appointment.company_id,
            ClinicalRecord.patient_id == appointment.patient_id,
        )
    )


def _clinical_evolution_for_appointment(
    session: Session,
    appointment: Appointment,
) -> ClinicalEvolution | None:
    return session.scalar(
        select(ClinicalEvolution).where(
            ClinicalEvolution.company_id == appointment.company_id,
            ClinicalEvolution.appointment_id == appointment.id,
        )
    )


def _clinical_fields(
    session: Session,
    appointment: Appointment,
) -> dict:
    record = _clinical_record_for_appointment(session, appointment)
    evolution = _clinical_evolution_for_appointment(session, appointment)
    return {
        "clinical_record_exists": record is not None,
        "clinical_evolution_id": evolution.id if evolution else None,
        "clinical_evolution_status": evolution.status if evolution else None,
        "clinical_evolution_version": evolution.version if evolution else None,
    }


def _to_response(session: Session, row) -> AppointmentResponse:
    if len(row) == 6:
        appointment, patient, dentist, site, appointment_type, company = row
    else:
        appointment, patient, dentist, site, appointment_type = row
        company = None
    timezone_name = _effective_timezone(company, site)
    clinical = _clinical_fields(session, appointment)
    return AppointmentResponse(
        id=appointment.id,
        patient_id=patient.id,
        patient_name=f"{patient.first_names} {patient.last_names}".strip(),
        patient_mobile=patient.mobile,
        dentist_id=dentist.id,
        dentist_name=dentist.name,
        site_id=site.id,
        site_name=site.name,
        appointment_type_id=appointment_type.id,
        appointment_type_name=appointment_type.name,
        origin_appointment_id=appointment.origin_appointment_id,
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
        starts_at_local=_local_calendar_iso(appointment.starts_at, timezone_name),
        ends_at_local=_local_calendar_iso(appointment.ends_at, timezone_name),
        timezone=timezone_name,
        reason=appointment.reason,
        notes=appointment.notes,
        status=appointment.status,
        is_overbook=appointment.is_overbook,
        overbook_reason=appointment.overbook_reason,
        confirmation_method=appointment.confirmation_method,
        confirmed_at=appointment.confirmed_at,
        **clinical,
    )


def _effective_timezone(company: Company | None, site: Site | None) -> str:
    return (
        (site.timezone if site else None)
        or (company.timezone if company else None)
        or FALLBACK_TIMEZONE
    )


def _patient_contact_mobile(session: Session, patient: Patient) -> str:
    if patient.birth_date:
        today = datetime.now(ZoneInfo(FALLBACK_TIMEZONE)).date()
        age = today.year - patient.birth_date.year - (
            (today.month, today.day)
            < (patient.birth_date.month, patient.birth_date.day)
        )
        if age < 18:
            responsible = session.scalar(
                select(PatientResponsible).where(
                    PatientResponsible.patient_id == patient.id,
                    PatientResponsible.is_active.is_(True),
                    PatientResponsible.is_primary.is_(True),
                )
            )
            if responsible:
                return responsible.mobile
    return patient.mobile


def _normalize_phone(value: str) -> str:
    phone = "".join(filter(str.isdigit, value))
    if len(phone) == 10:
        phone = f"57{phone}"
    return phone


def _format_local_appointment(value: datetime, timezone_name: str) -> tuple[str, str]:
    local_value = value.astimezone(ZoneInfo(timezone_name))
    return local_value.strftime("%d/%m/%Y"), local_value.strftime("%H:%M")


def _load_responses(
    session: Session,
    appointment_ids: list[UUID],
) -> list[AppointmentResponse]:
    if not appointment_ids:
        return []
    rows = session.execute(
        select(Appointment, Patient, Dentist, Site, AppointmentType, Company)
        .join(Patient, Patient.id == Appointment.patient_id)
        .join(Dentist, Dentist.id == Appointment.dentist_id)
        .join(Site, Site.id == Appointment.site_id)
        .join(Company, Company.id == Appointment.company_id)
        .join(
            AppointmentType,
            AppointmentType.id == Appointment.appointment_type_id,
        )
        .where(Appointment.id.in_(appointment_ids))
        .order_by(Appointment.starts_at)
    )
    return [_to_response(session, row) for row in rows]


def _find_conflicts(
    session: Session,
    *,
    company_id: UUID,
    patient_id: UUID,
    dentist_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
    exclude_id: UUID | None = None,
) -> tuple[list[UUID], list[UUID]]:
    common = [
        Appointment.company_id == company_id,
        Appointment.is_active.is_(True),
        Appointment.status.in_(ACTIVE_CONFLICT_STATES),
        Appointment.starts_at < ends_at,
        Appointment.ends_at > starts_at,
    ]
    if exclude_id:
        common.append(Appointment.id != exclude_id)
    dentist_ids = list(
        session.scalars(
            select(Appointment.id).where(
                *common,
                Appointment.dentist_id == dentist_id,
            )
        )
    )
    patient_ids = list(
        session.scalars(
            select(Appointment.id).where(
                *common,
                Appointment.patient_id == patient_id,
            )
        )
    )
    return dentist_ids, patient_ids


def _validate_conflicts(
    session: Session,
    context: AuthContext,
    *,
    patient_id: UUID,
    dentist_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
    is_overbook: bool,
    appointment_type: AppointmentType,
    exclude_id: UUID | None = None,
) -> None:
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
        {"key": f"agenda:{context.user.company_id}:{dentist_id}"},
    )
    dentist_ids, patient_ids = _find_conflicts(
        session,
        company_id=context.user.company_id,
        patient_id=patient_id,
        dentist_id=dentist_id,
        starts_at=starts_at,
        ends_at=ends_at,
        exclude_id=exclude_id,
    )
    if patient_ids:
        raise AgendaError(
            "El paciente ya tiene una cita en ese horario.",
            409,
            conflicts=_load_responses(session, patient_ids),
        )
    if dentist_ids:
        can_overbook = (
            "appointments.overbook" in context.permissions
            and appointment_type.allows_overbook
        )
        if not is_overbook:
            raise AgendaError(
                "El odontólogo ya tiene una cita en ese horario.",
                409,
                conflicts=_load_responses(session, dentist_ids),
                can_overbook=can_overbook,
            )
        if not can_overbook:
            raise AgendaError(
                "No tienes permiso para crear sobrecupos.",
                403,
                conflicts=_load_responses(session, dentist_ids),
            )
    elif is_overbook:
        raise AgendaError(
            "Solo puedes marcar sobrecupo cuando existe un cruce de horario."
        )


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    appointment_id: UUID,
    action: str,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="appointment",
            entity_id=appointment_id,
            action=action,
            result="SUCCESS",
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _audit_result(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    appointment_id: UUID,
    action: str,
    result: str,
    detail: dict | None = None,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="appointment",
            entity_id=appointment_id,
            action=action,
            result=result,
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _scope_label(procedure: TreatmentProcedure) -> str:
    scope_type = (procedure.scope_type or "GENERAL").upper()
    if scope_type == "ZONE":
        return ZONE_LABELS.get(procedure.zone or "", procedure.zone or "Zona")
    if scope_type == "TOOTH":
        return f"Diente {procedure.tooth}" if procedure.tooth else "Diente"
    if scope_type == "TOOTH_SURFACE":
        surfaces = ", ".join(
            SURFACE_LABELS.get(surface, surface.title())
            for surface in (procedure.surfaces or [])
        )
        return f"Diente {procedure.tooth} — {surfaces}" if surfaces else f"Diente {procedure.tooth}"
    return "General"


def _clinical_permissions(context: AuthContext) -> dict[str, bool]:
    codes = {
        "can_view_record": "clinical_records.view",
        "can_create_record": "clinical_records.create",
        "can_view_sensitive": "clinical_records.view_sensitive",
        "can_view_evolution": "clinical_evolutions.view",
        "can_create_evolution": "clinical_evolutions.create",
        "can_update_evolution": "clinical_evolutions.update_draft",
        "can_sign_evolution": "clinical_evolutions.sign",
        "can_update_treatments": "treatments.update",
        "can_create_followup": "followups.manage",
        "can_create_appointment": "appointments.create",
        "can_complete_appointment": "appointments.complete",
    }
    return {name: code in context.permissions for name, code in codes.items()}


def get_appointment_clinical_context(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    metadata: RequestMetadata,
) -> AppointmentClinicalContextResponse:
    row = _appointment_row(session, context, appointment_id)
    appointment = row[0]
    company = row[5] if len(row) == 6 else session.get(Company, context.user.company_id)
    record = _clinical_record_for_appointment(session, appointment)
    evolution = _clinical_evolution_for_appointment(session, appointment)
    permissions = _clinical_permissions(context)

    from app.services.clinical_record_service import terminology_for_country

    treatments: list[AppointmentClinicalTreatmentResponse] = []
    procedures: list[AppointmentClinicalProcedureResponse] = []
    if permissions["can_view_sensitive"] and permissions["can_view_evolution"]:
        treatment_items = list(
            session.scalars(
                select(Treatment)
                .where(
                    Treatment.company_id == context.user.company_id,
                    Treatment.patient_id == appointment.patient_id,
                    Treatment.status != "Cancelado",
                )
                .order_by(Treatment.created_at.desc())
            )
        )
        treatment_names = {item.id: item.name for item in treatment_items}
        treatments = [
            AppointmentClinicalTreatmentResponse(
                id=item.id,
                name=item.name,
                status=item.status,
            )
            for item in treatment_items
        ]
        procedure_items = list(
            session.scalars(
                select(TreatmentProcedure)
                .where(
                    TreatmentProcedure.company_id == context.user.company_id,
                    TreatmentProcedure.patient_id == appointment.patient_id,
                    TreatmentProcedure.status != "Cancelado",
                )
                .order_by(TreatmentProcedure.created_at.desc())
            )
        )
        evolution_actions: dict[UUID, str] = {}
        if evolution is not None:
            for link in session.scalars(
                select(ClinicalEvolutionProcedure).where(
                    ClinicalEvolutionProcedure.evolution_id == evolution.id
                )
            ):
                evolution_actions[link.procedure_id] = link.action
        procedures = [
            AppointmentClinicalProcedureResponse(
                id=item.id,
                treatment_id=item.treatment_id,
                treatment_name=treatment_names.get(item.treatment_id),
                name=item.name,
                status=item.status,
                scope_label=_scope_label(item),
                clinical_action=evolution_actions.get(item.id),
            )
            for item in procedure_items
        ]

    _audit(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action="APPOINTMENT_CLINICAL_CONTEXT_VIEWED",
    )
    session.commit()
    return AppointmentClinicalContextResponse(
        appointment=_to_response(session, row),
        clinical_record_exists=record is not None,
        clinical_record_id=record.id if record else None,
        clinical_evolution_id=evolution.id if evolution else None,
        clinical_evolution_status=evolution.status if evolution else None,
        clinical_evolution_version=evolution.version if evolution else None,
        terminology=terminology_for_country(company.country if company else None),
        treatments=treatments,
        procedures=procedures,
        permissions=permissions,
    )


def _action_success(message: str, entity_id: UUID | None = None) -> ClinicalCareActionResult:
    return ClinicalCareActionResult(success=True, message=message, entity_id=entity_id)


def _action_failure(message: str, entity_id: UUID | None = None) -> ClinicalCareActionResult:
    return ClinicalCareActionResult(success=False, message=message, entity_id=entity_id)


def complete_clinical_care(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    payload: ClinicalCareCompletionRequest,
    metadata: RequestMetadata,
) -> ClinicalCareCompletionResponse:
    row = _appointment_row(session, context, appointment_id)
    appointment = row[0]
    permissions = _clinical_permissions(context)
    result = ClinicalCareCompletionResponse()

    _audit_result(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action="CLINICAL_CARE_COMPLETION_STARTED",
        result="SUCCESS",
        detail={
            "sign_evolution": payload.sign_evolution,
            "mark_procedure_ids_done": [str(item) for item in payload.mark_procedure_ids_done],
            "complete_appointment": payload.complete_appointment,
            "create_followup": bool(payload.followup_payload and payload.followup_payload.requires_followup),
            "create_control_appointment": payload.control_appointment_payload is not None,
        },
    )
    session.commit()

    if payload.sign_evolution:
        if not permissions["can_sign_evolution"]:
            result.evolution = _action_failure("No tienes permiso para firmar la evolución.")
            result.partial_failure = True
        elif payload.evolution_id is None or payload.evolution_version is None:
            result.evolution = _action_failure("Selecciona una evolución en borrador para firmar.")
            result.partial_failure = True
        else:
            try:
                from app.services.clinical_record_service import sign_clinical_evolution

                signed = sign_clinical_evolution(
                    session,
                    context,
                    payload.evolution_id,
                    ClinicalEvolutionSignRequest(
                        version=payload.evolution_version,
                        confirm_complete=True,
                    ),
                    metadata,
                )
                result.evolution = _action_success("Evolución firmada.", signed.id)
            except Exception as exc:  # noqa: BLE001 - se reporta fallo parcial al usuario
                session.rollback()
                result.evolution = _action_failure(str(exc), payload.evolution_id)
                result.partial_failure = True

    if payload.mark_procedure_ids_done:
        if "treatments.update" not in context.permissions:
            result.procedures = [
                _action_failure("No tienes permiso para marcar procedimientos realizados.", item)
                for item in payload.mark_procedure_ids_done
            ]
            result.partial_failure = True
        else:
            from app.services.treatment_service import mark_procedure_done

            for procedure_id in payload.mark_procedure_ids_done:
                procedure = session.get(TreatmentProcedure, procedure_id)
                if (
                    procedure is None
                    or procedure.company_id != context.user.company_id
                    or procedure.patient_id != appointment.patient_id
                ):
                    result.procedures.append(
                        _action_failure("Procedimiento no disponible para esta atención.", procedure_id)
                    )
                    result.partial_failure = True
                    continue
                if procedure.status == "Realizado":
                    result.procedures.append(
                        _action_success("El procedimiento ya estaba realizado.", procedure.id)
                    )
                    continue
                try:
                    updated = mark_procedure_done(
                        session,
                        context,
                        procedure.treatment_id,
                        procedure.id,
                        metadata,
                    )
                    _audit(
                        session,
                        context,
                        metadata,
                        appointment_id=appointment.id,
                        action="TREATMENT_PROCEDURE_MARKED_DONE_FROM_CLINICAL_CARE",
                        detail={"procedure_id": str(updated.id)},
                    )
                    session.commit()
                    result.procedures.append(
                        _action_success("Procedimiento marcado como realizado.", updated.id)
                    )
                except Exception as exc:  # noqa: BLE001
                    session.rollback()
                    result.procedures.append(_action_failure(str(exc), procedure_id))
                    result.partial_failure = True

    if payload.complete_appointment:
        if not permissions["can_complete_appointment"]:
            result.appointment = _action_failure("No tienes permiso para finalizar la cita.", appointment.id)
            result.partial_failure = True
        else:
            try:
                from app.services.followup_service import complete_appointment

                followup_payload = payload.followup_payload
                completed = complete_appointment(
                    session,
                    context,
                    appointment.id,
                    CompleteAppointmentRequest(
                        attention_description=(
                            followup_payload.attention_description
                            if followup_payload
                            else "Atención finalizada desde flujo clínico."
                        ),
                        prescribed_medications=(
                            followup_payload.prescribed_medications
                            if followup_payload
                            else None
                        ),
                        requires_followup=(
                            followup_payload.requires_followup
                            if followup_payload
                            else False
                        ),
                        recommended_followup_date=(
                            followup_payload.recommended_followup_date
                            if followup_payload
                            else None
                        ),
                        followup_reason=(
                            followup_payload.followup_reason
                            if followup_payload
                            else None
                        ),
                    ),
                    metadata,
                )
                result.appointment = _action_success("Cita finalizada.", appointment.id)
                if completed.followup:
                    result.followup = _action_success(
                        "Seguimiento creado.",
                        completed.followup.id,
                    )
                    _audit(
                        session,
                        context,
                        metadata,
                        appointment_id=appointment.id,
                        action="FOLLOWUP_CREATED_FROM_CLINICAL_CARE",
                        detail={"followup_id": str(completed.followup.id)},
                    )
                    session.commit()
                elif followup_payload and followup_payload.requires_followup:
                    result.followup = _action_failure("No se creó seguimiento.")
                    result.partial_failure = True
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                result.appointment = _action_failure(str(exc), appointment.id)
                result.partial_failure = True

    if payload.control_appointment_payload is not None:
        if not permissions["can_create_appointment"]:
            result.control_appointment = _action_failure("No tienes permiso para crear la cita de control.")
            result.partial_failure = True
        else:
            try:
                control = create_appointment(
                    session,
                    context,
                    payload.control_appointment_payload,
                    metadata,
                )
                result.control_appointment = _action_success("Cita de control creada.", control.id)
                _audit(
                    session,
                    context,
                    metadata,
                    appointment_id=appointment.id,
                    action="CONTROL_APPOINTMENT_CREATED_FROM_CLINICAL_CARE",
                    detail={"control_appointment_id": str(control.id)},
                )
                session.commit()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                result.control_appointment = _action_failure(str(exc))
                result.partial_failure = True

    _audit_result(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action=(
            "CLINICAL_CARE_COMPLETION_PARTIAL_FAILURE"
            if result.partial_failure
            else "CLINICAL_CARE_COMPLETION_COMPLETED"
        ),
        result="PARTIAL_FAILURE" if result.partial_failure else "SUCCESS",
        detail=result.model_dump(mode="json"),
    )
    session.commit()
    return result


def _history(
    session: Session,
    context: AuthContext,
    appointment: Appointment,
    *,
    previous_status: str | None,
    new_status: str,
    reason: str | None = None,
    related_id: UUID | None = None,
    previous_starts_at: datetime | None = None,
    new_starts_at: datetime | None = None,
) -> None:
    session.add(
        AppointmentHistory(
            company_id=context.user.company_id,
            appointment_id=appointment.id,
            related_appointment_id=related_id,
            previous_status=previous_status,
            new_status=new_status,
            previous_starts_at=previous_starts_at,
            new_starts_at=new_starts_at,
            reason=reason,
            user_id=context.user.id,
        )
    )


def get_options(
    session: Session,
    context: AuthContext,
) -> AgendaOptionsResponse:
    site_ids = _authorized_site_ids(session, context, active_only=True)
    sites = list(
        session.scalars(
            select(Site)
            .where(
                Site.company_id == context.user.company_id,
                Site.id.in_(site_ids),
                Site.is_active.is_(True),
                Site.status == "Activa",
            )
            .order_by(Site.name)
        )
    )
    dentist_rows = session.execute(
        select(Dentist, DentistSite.site_id)
        .join(DentistSite, DentistSite.dentist_id == Dentist.id)
        .where(
            Dentist.company_id == context.user.company_id,
            Dentist.is_active.is_(True),
            Dentist.status == "Activo",
            DentistSite.site_id.in_(site_ids),
            DentistSite.is_active.is_(True),
        )
        .order_by(Dentist.name)
    )
    dentists_by_id: dict[UUID, DentistOptionResponse] = {}
    for dentist, site_id in dentist_rows:
        option = dentists_by_id.get(dentist.id)
        if option is None:
            option = DentistOptionResponse(
                id=dentist.id,
                name=dentist.name,
                site_ids=[],
            )
            dentists_by_id[dentist.id] = option
        option.site_ids.append(site_id)
    appointment_types = list(
        session.scalars(
            select(AppointmentType)
            .where(
                AppointmentType.company_id == context.user.company_id,
                AppointmentType.is_active.is_(True),
            )
            .order_by(AppointmentType.name)
        )
    )
    company = session.get(Company, context.user.company_id)
    site_by_id = {site.id: site for site in sites}
    active_site = site_by_id.get(context.auth_session.active_site_id)
    return AgendaOptionsResponse(
        timezone=_effective_timezone(company, active_site),
        active_site_id=context.auth_session.active_site_id,
        dentists=list(dentists_by_id.values()),
        sites=[
            SiteOptionResponse(
                id=site.id,
                name=site.name,
                address=site.address,
                timezone=_effective_timezone(company, site),
            )
            for site in sites
        ],
        appointment_types=[
            AppointmentTypeOptionResponse(
                id=item.id,
                name=item.name,
                suggested_duration_minutes=item.suggested_duration_minutes,
            )
            for item in appointment_types
        ],
    )


def get_events(
    session: Session,
    context: AuthContext,
    *,
    starts_at: datetime,
    ends_at: datetime,
    dentist_id: UUID | None,
    site_id: UUID | None,
) -> AgendaEventsResponse:
    if starts_at.tzinfo is None or ends_at.tzinfo is None or ends_at <= starts_at:
        raise AgendaError("El rango de consulta no es válido.")
    site_ids = _authorized_site_ids(session, context)
    if site_id:
        _require_site(session, context, site_id)
        site_ids = {site_id}
    filters = [
        Appointment.company_id == context.user.company_id,
        Appointment.site_id.in_(site_ids),
        Appointment.is_active.is_(True),
        Appointment.starts_at < ends_at,
        Appointment.ends_at > starts_at,
    ]
    if dentist_id:
        filters.append(Appointment.dentist_id == dentist_id)
    rows = session.execute(
        select(Appointment, Patient, Dentist, Site, AppointmentType, Company)
        .join(Patient, Patient.id == Appointment.patient_id)
        .join(Dentist, Dentist.id == Appointment.dentist_id)
        .join(Site, Site.id == Appointment.site_id)
        .join(Company, Company.id == Appointment.company_id)
        .join(
            AppointmentType,
            AppointmentType.id == Appointment.appointment_type_id,
        )
        .where(*filters)
        .order_by(Appointment.starts_at)
    )
    return AgendaEventsResponse(items=[_to_response(session, row) for row in rows])


def create_appointment(
    session: Session,
    context: AuthContext,
    payload: AppointmentCreateRequest,
    metadata: RequestMetadata,
    *,
    commit: bool = True,
) -> AppointmentResponse:
    _require_site(session, context, payload.site_id)
    _require_patient(session, context, payload.patient_id)
    appointment_type = _require_type(
        session, context, payload.appointment_type_id
    )
    _require_dentist_site(
        session, context, payload.dentist_id, payload.site_id
    )
    _validate_conflicts(
        session,
        context,
        patient_id=payload.patient_id,
        dentist_id=payload.dentist_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        is_overbook=payload.is_overbook,
        appointment_type=appointment_type,
    )
    appointment = Appointment(
        company_id=context.user.company_id,
        patient_id=payload.patient_id,
        dentist_id=payload.dentist_id,
        site_id=payload.site_id,
        appointment_type_id=payload.appointment_type_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        reason=payload.reason,
        notes=payload.notes,
        status="Programada",
        is_overbook=payload.is_overbook,
        overbook_reason=payload.overbook_reason,
        created_by=context.user.id,
        updated_by=context.user.id,
    )
    session.add(appointment)
    session.flush()
    _history(
        session,
        context,
        appointment,
        previous_status=None,
        new_status="Programada",
        new_starts_at=appointment.starts_at,
    )
    _audit(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action="APPOINTMENT_OVERBOOK_CREATED"
        if appointment.is_overbook
        else "APPOINTMENT_CREATED",
    )
    if commit:
        session.commit()
    return _to_response(session, _appointment_row(session, context, appointment.id))


def update_appointment(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    payload: AppointmentUpdateRequest,
    metadata: RequestMetadata,
) -> AppointmentResponse:
    row = _appointment_row(session, context, appointment_id, lock=True)
    appointment = row[0]
    if appointment.status in TERMINAL_STATES:
        raise AgendaError("No puedes editar una cita en estado terminal.", 409)
    if payload.appointment_type_id is not None:
        _require_type(session, context, payload.appointment_type_id)
        appointment.appointment_type_id = payload.appointment_type_id
    if payload.reason is not None:
        appointment.reason = payload.reason
    if "notes" in payload.model_fields_set:
        appointment.notes = payload.notes
    appointment.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action="APPOINTMENT_UPDATED",
    )
    session.commit()
    return _to_response(session, _appointment_row(session, context, appointment.id))


def confirm_appointment(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    method: str,
    metadata: RequestMetadata,
) -> AppointmentResponse:
    appointment = _appointment_row(
        session, context, appointment_id, lock=True
    )[0]
    if appointment.status not in {"Programada", "Confirmada"}:
        raise AgendaError("Esta cita no puede confirmarse.", 409)
    previous = appointment.status
    appointment.status = "Confirmada"
    appointment.confirmation_method = method
    appointment.confirmed_at = datetime.now(timezone.utc)
    appointment.confirmed_by = context.user.id
    appointment.updated_by = context.user.id
    _history(
        session,
        context,
        appointment,
        previous_status=previous,
        new_status="Confirmada",
        reason=f"Confirmación por {method}",
    )
    _audit(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action="APPOINTMENT_CONFIRMED",
        detail={"method": method},
    )
    session.commit()
    return _to_response(session, _appointment_row(session, context, appointment.id))


def appointment_whatsapp_link(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    metadata: RequestMetadata,
) -> AppointmentWhatsAppLinkResponse:
    row = _appointment_row(session, context, appointment_id)
    appointment, patient, dentist, site, _appointment_type, company = row
    phone = _normalize_phone(_patient_contact_mobile(session, patient))
    if len(phone) < 10:
        raise AgendaError("El paciente no tiene un celular válido.", 409)
    timezone_name = _effective_timezone(company, site)
    date_text, time_text = _format_local_appointment(
        appointment.starts_at,
        timezone_name,
    )
    patient_name = f"{patient.first_names} {patient.last_names}".strip()
    message = (
        f"Hola, {patient_name}. ¿Nos confirmas tu asistencia a la cita "
        f"odontológica con {dentist.name} en {site.name}, ubicada en "
        f"{site.address}, el {date_text} a las {time_text}?"
    )
    _audit(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action="APPOINTMENT_WHATSAPP_LINK_GENERATED",
        detail={"phone": phone, "message": message},
    )
    session.commit()
    return AppointmentWhatsAppLinkResponse(
        url=f"https://wa.me/{phone}?text={quote(message)}",
        phone=phone,
        message=message,
    )


def cancel_appointment(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    reason: str,
    metadata: RequestMetadata,
) -> AppointmentResponse:
    appointment = _appointment_row(
        session, context, appointment_id, lock=True
    )[0]
    if appointment.status in TERMINAL_STATES:
        raise AgendaError("Esta cita no puede cancelarse.", 409)
    previous = appointment.status
    appointment.status = "Cancelada"
    from app.services.followup_service import sync_cancelled_appointment
    sync_cancelled_appointment(session, appointment.id)
    appointment.updated_by = context.user.id
    _history(
        session,
        context,
        appointment,
        previous_status=previous,
        new_status="Cancelada",
        reason=reason,
    )
    _audit(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action="APPOINTMENT_CANCELLED",
        detail={"reason": reason},
    )
    session.commit()
    return _to_response(session, _appointment_row(session, context, appointment.id))


def reschedule_appointment(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    payload: AppointmentRescheduleRequest,
    metadata: RequestMetadata,
) -> AppointmentResponse:
    old = _appointment_row(session, context, appointment_id, lock=True)[0]
    if old.status in TERMINAL_STATES:
        raise AgendaError("Esta cita no puede reprogramarse.", 409)
    _require_site(session, context, payload.site_id)
    _require_dentist_site(
        session, context, payload.dentist_id, payload.site_id
    )
    appointment_type = _require_type(
        session, context, old.appointment_type_id
    )
    _validate_conflicts(
        session,
        context,
        patient_id=old.patient_id,
        dentist_id=payload.dentist_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        is_overbook=payload.is_overbook,
        appointment_type=appointment_type,
        exclude_id=old.id,
    )
    new = Appointment(
        company_id=old.company_id,
        patient_id=old.patient_id,
        dentist_id=payload.dentist_id,
        site_id=payload.site_id,
        appointment_type_id=old.appointment_type_id,
        origin_appointment_id=old.id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        reason=old.reason,
        notes=old.notes,
        status="Programada",
        is_overbook=payload.is_overbook,
        overbook_reason=payload.overbook_reason,
        created_by=context.user.id,
        updated_by=context.user.id,
    )
    session.add(new)
    session.flush()
    previous = old.status
    old.status = "Reprogramada"
    from app.services.followup_service import sync_rescheduled_appointment
    sync_rescheduled_appointment(session, old.id, new.id)
    old.updated_by = context.user.id
    _history(
        session,
        context,
        old,
        previous_status=previous,
        new_status="Reprogramada",
        reason=payload.reason,
        related_id=new.id,
        previous_starts_at=old.starts_at,
        new_starts_at=new.starts_at,
    )
    _history(
        session,
        context,
        new,
        previous_status=None,
        new_status="Programada",
        reason=payload.reason,
        related_id=old.id,
        new_starts_at=new.starts_at,
    )
    _audit(
        session,
        context,
        metadata,
        appointment_id=old.id,
        action="APPOINTMENT_RESCHEDULED",
        detail={"new_appointment_id": str(new.id), "reason": payload.reason},
    )
    session.commit()
    return _to_response(session, _appointment_row(session, context, new.id))


def adjust_appointment_time(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    payload: AppointmentTimeAdjustRequest,
    metadata: RequestMetadata,
) -> AppointmentResponse:
    row = _appointment_row(session, context, appointment_id, lock=True)
    appointment = row[0]
    if appointment.status not in {"Programada", "Confirmada"}:
        raise AgendaError("Esta cita no permite corrección administrativa de hora.", 409)
    _require_site(session, context, payload.site_id)
    _require_dentist_site(
        session, context, payload.dentist_id, payload.site_id
    )
    appointment_type = _require_type(
        session, context, appointment.appointment_type_id
    )
    _validate_conflicts(
        session,
        context,
        patient_id=appointment.patient_id,
        dentist_id=payload.dentist_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        is_overbook=payload.is_overbook,
        appointment_type=appointment_type,
        exclude_id=appointment.id,
    )
    previous = {
        "site_id": str(appointment.site_id),
        "dentist_id": str(appointment.dentist_id),
        "starts_at": appointment.starts_at.isoformat(),
        "ends_at": appointment.ends_at.isoformat(),
        "status": appointment.status,
    }
    appointment.site_id = payload.site_id
    appointment.dentist_id = payload.dentist_id
    appointment.starts_at = payload.starts_at
    appointment.ends_at = payload.ends_at
    appointment.is_overbook = payload.is_overbook
    appointment.overbook_reason = payload.overbook_reason
    appointment.updated_by = context.user.id
    _audit(
        session,
        context,
        metadata,
        appointment_id=appointment.id,
        action="APPOINTMENT_TIME_ADJUSTED",
        detail={
            "previous": previous,
            "new": {
                "site_id": str(appointment.site_id),
                "dentist_id": str(appointment.dentist_id),
                "starts_at": appointment.starts_at.isoformat(),
                "ends_at": appointment.ends_at.isoformat(),
                "status": appointment.status,
            },
            "reason": payload.reason or "Corrección de error de agenda",
        },
    )
    session.commit()
    return _to_response(session, _appointment_row(session, context, appointment.id))


def ensure_agenda_seed_data(
    session: Session,
    *,
    company_id: UUID,
    admin_user: User,
    site: Site,
) -> None:
    for name, duration in INITIAL_APPOINTMENT_TYPES:
        exists = session.scalar(
            select(AppointmentType.id).where(
                AppointmentType.company_id == company_id,
                AppointmentType.name == name,
            )
        )
        if exists is None:
            session.add(
                AppointmentType(
                    company_id=company_id,
                    name=name,
                    suggested_duration_minutes=duration,
                    allows_overbook=True,
                    created_by=admin_user.id,
                )
            )
    dentist = session.scalar(
        select(Dentist).where(
            Dentist.company_id == company_id,
            Dentist.user_id == admin_user.id,
        )
    )
    if dentist is None:
        dentist = Dentist(
            company_id=company_id,
            user_id=admin_user.id,
            name=admin_user.name,
            status="Activo",
            created_by=admin_user.id,
        )
        session.add(dentist)
        session.flush()
    association = session.scalar(
        select(DentistSite).where(
            DentistSite.dentist_id == dentist.id,
            DentistSite.site_id == site.id,
        )
    )
    if association is None:
        session.add(
            DentistSite(
                company_id=company_id,
                dentist_id=dentist.id,
                site_id=site.id,
                created_by=admin_user.id,
            )
        )
