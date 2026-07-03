from datetime import date, datetime, time, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.agenda import Appointment, Dentist, DentistSite, Patient
from app.models.audit_event import AuditEvent
from app.models.site import Site
from app.models.treatment import (
    Budget,
    BudgetDetail,
    Treatment,
    TreatmentEvent,
    TreatmentPayment,
    TreatmentProcedure,
)
from app.schemas.treatment_schema import (
    BudgetCreateRequest,
    BudgetDetailResponse,
    BudgetResponse,
    FinanceBreakdownItem,
    FinanceBreakdownResponse,
    FinanceDashboardResponse,
    PatientBalanceItem,
    PatientBalancesResponse,
    PaymentCreateRequest,
    PaymentResponse,
    ProcedureCreateRequest,
    ProcedureResponse,
    ProcedureUpdateRequest,
    TreatmentCreateRequest,
    TreatmentListItemResponse,
    TreatmentListResponse,
    TreatmentResponse,
    TreatmentSummaryResponse,
    TreatmentUpdateRequest,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import authorized_site_ids


TREATMENT_ACTIVE_STATUSES = {"Borrador", "Presupuestado", "Aprobado", "En ejecución", "Pausado"}
TREATMENT_FINAL_STATUSES = {"Finalizado", "Cancelado"}
APPROVED_BUDGET_STATUSES = {"Aprobado", "En ejecución", "Finalizado"}
VALID_PAYMENT_STATUS = "valido"
REVERSED_PAYMENT_STATUS = "reversado"
CENT = Decimal("0.01")


class TreatmentError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _money(value: Decimal | int | float | None) -> Decimal:
    return Decimal(value or 0).quantize(CENT, rounding=ROUND_HALF_UP)


def _audit(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    entity: str,
    entity_id: UUID,
    action: str,
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
            result="SUCCESS",
            detail=detail,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )


def _event(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    event_type: str,
    description: str,
    metadata: dict | None = None,
) -> None:
    session.add(
        TreatmentEvent(
            company_id=context.user.company_id,
            treatment_id=treatment_id,
            event_type=event_type,
            description=description,
            event_metadata=metadata,
            user_id=context.user.id,
        )
    )


def _authorized_sites(session: Session, context: AuthContext) -> set[UUID]:
    return authorized_site_ids(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        active_only=True,
    )


def _require_site(session: Session, context: AuthContext, site_id: UUID) -> Site:
    if site_id not in _authorized_sites(session, context):
        raise TreatmentError("No tienes acceso a la sede seleccionada.", 403)
    site = session.scalar(
        select(Site).where(
            Site.id == site_id,
            Site.company_id == context.user.company_id,
            Site.is_active.is_(True),
            Site.status == "Activa",
        )
    )
    if site is None:
        raise TreatmentError("La sede no existe o no está activa.")
    return site


def _require_patient(session: Session, context: AuthContext, patient_id: UUID) -> Patient:
    patient = session.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.company_id == context.user.company_id,
            Patient.is_active.is_(True),
        )
    )
    if patient is None:
        raise TreatmentError("Paciente no encontrado.", 404)
    return patient


def _require_dentist(
    session: Session,
    context: AuthContext,
    dentist_id: UUID,
    site_id: UUID | None = None,
) -> Dentist:
    statement = select(Dentist).where(
        Dentist.id == dentist_id,
        Dentist.company_id == context.user.company_id,
        Dentist.is_active.is_(True),
        Dentist.status == "Activo",
    )
    if site_id:
        statement = statement.join(DentistSite, DentistSite.dentist_id == Dentist.id).where(
            DentistSite.site_id == site_id,
            DentistSite.is_active.is_(True),
        )
    dentist = session.scalar(statement)
    if dentist is None:
        raise TreatmentError("Odontólogo no disponible para la sede seleccionada.")
    return dentist


def _require_treatment(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    *,
    lock: bool = False,
) -> Treatment:
    statement = select(Treatment).where(
        Treatment.id == treatment_id,
        Treatment.company_id == context.user.company_id,
    )
    if lock:
        statement = statement.with_for_update()
    treatment = session.scalar(statement)
    if treatment is None:
        raise TreatmentError("Tratamiento no encontrado.", 404)
    if treatment.main_site_id and treatment.main_site_id not in _authorized_sites(session, context):
        raise TreatmentError("No tienes acceso a este tratamiento.", 403)
    return treatment


def _require_procedure(
    session: Session,
    context: AuthContext,
    treatment: Treatment,
    procedure_id: UUID,
    *,
    lock: bool = False,
) -> TreatmentProcedure:
    statement = select(TreatmentProcedure).where(
        TreatmentProcedure.id == procedure_id,
        TreatmentProcedure.company_id == context.user.company_id,
        TreatmentProcedure.treatment_id == treatment.id,
    )
    if lock:
        statement = statement.with_for_update()
    procedure = session.scalar(statement)
    if procedure is None:
        raise TreatmentError("Procedimiento no encontrado.", 404)
    return procedure


def _budget_value(session: Session, treatment_id: UUID) -> tuple[Decimal, Decimal, Decimal]:
    budget = session.scalar(
        select(Budget)
        .where(
            Budget.treatment_id == treatment_id,
            Budget.status.in_(APPROVED_BUDGET_STATUSES),
        )
        .order_by(Budget.version.desc())
        .limit(1)
    )
    if budget:
        return (
            _money(budget.gross_value),
            _money(budget.discount_calculated_value),
            _money(budget.final_value),
        )
    gross = _money(
        session.scalar(
            select(func.coalesce(func.sum(TreatmentProcedure.total_value), 0)).where(
                TreatmentProcedure.treatment_id == treatment_id,
                TreatmentProcedure.status != "Cancelado",
            )
        )
    )
    return gross, Decimal("0.00"), gross


def _paid_value(session: Session, treatment_id: UUID) -> Decimal:
    return _money(
        session.scalar(
            select(func.coalesce(func.sum(TreatmentPayment.value), 0)).where(
                TreatmentPayment.treatment_id == treatment_id,
                TreatmentPayment.status == VALID_PAYMENT_STATUS,
            )
        )
    )


def _summary(session: Session, treatment_id: UUID) -> TreatmentSummaryResponse:
    gross, discount, final = _budget_value(session, treatment_id)
    paid = _paid_value(session, treatment_id)
    procedures_total = session.scalar(
        select(func.count(TreatmentProcedure.id)).where(
            TreatmentProcedure.treatment_id == treatment_id,
            TreatmentProcedure.status != "Cancelado",
        )
    ) or 0
    procedures_done = session.scalar(
        select(func.count(TreatmentProcedure.id)).where(
            TreatmentProcedure.treatment_id == treatment_id,
            TreatmentProcedure.status == "Realizado",
        )
    ) or 0
    return TreatmentSummaryResponse(
        gross_value=gross,
        discount_value=discount,
        final_value=final,
        paid_value=paid,
        balance=max(final - paid, Decimal("0.00")),
        procedures_total=procedures_total,
        procedures_done=procedures_done,
    )


def _treatment_item(session: Session, treatment: Treatment) -> TreatmentListItemResponse:
    patient = session.get(Patient, treatment.patient_id)
    dentist = (
        session.get(Dentist, treatment.responsible_dentist_id)
        if treatment.responsible_dentist_id
        else None
    )
    site = session.get(Site, treatment.main_site_id) if treatment.main_site_id else None
    if patient is None:
        raise TreatmentError("Tratamiento sin paciente válido.", 500)
    summary = _summary(session, treatment.id)
    return TreatmentListItemResponse(
        id=treatment.id,
        patient_id=treatment.patient_id,
        patient_name=f"{patient.first_names} {patient.last_names}".strip(),
        name=treatment.name,
        status=treatment.status,
        responsible_dentist_id=treatment.responsible_dentist_id,
        responsible_dentist_name=dentist.name if dentist else None,
        main_site_id=treatment.main_site_id,
        main_site_name=site.name if site else None,
        final_value=summary.final_value,
        paid_value=summary.paid_value,
        balance=summary.balance,
        updated_at=treatment.updated_at,
    )


def _treatment_response(session: Session, treatment: Treatment) -> TreatmentResponse:
    item = _treatment_item(session, treatment)
    return TreatmentResponse(
        **item.model_dump(),
        description=treatment.description,
        specialty=treatment.specialty,
        start_date=treatment.start_date,
        end_date=treatment.end_date,
        observations=treatment.observations,
        created_at=treatment.created_at,
        summary=_summary(session, treatment.id),
    )


def list_treatments(
    session: Session,
    context: AuthContext,
    *,
    patient_id: UUID | None = None,
    status: str | None = None,
    site_id: UUID | None = None,
    dentist_id: UUID | None = None,
    has_balance: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> TreatmentListResponse:
    statement = select(Treatment).where(Treatment.company_id == context.user.company_id)
    authorized = _authorized_sites(session, context)
    statement = statement.where(
        or_(Treatment.main_site_id.is_(None), Treatment.main_site_id.in_(authorized))
    )
    if patient_id:
        statement = statement.where(Treatment.patient_id == patient_id)
    if status:
        statement = statement.where(Treatment.status == status)
    if site_id:
        _require_site(session, context, site_id)
        statement = statement.where(Treatment.main_site_id == site_id)
    if dentist_id:
        statement = statement.where(Treatment.responsible_dentist_id == dentist_id)
    if date_from:
        statement = statement.where(Treatment.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        statement = statement.where(Treatment.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
    treatments = session.scalars(statement.order_by(Treatment.updated_at.desc())).all()
    items = [_treatment_item(session, treatment) for treatment in treatments]
    if has_balance is not None:
        items = [item for item in items if (item.balance > 0) is has_balance]
    return TreatmentListResponse(items=items, total=len(items))


def create_treatment(
    session: Session,
    context: AuthContext,
    payload: TreatmentCreateRequest,
    metadata: RequestMetadata,
) -> TreatmentResponse:
    _require_patient(session, context, payload.patient_id)
    if payload.main_site_id:
        _require_site(session, context, payload.main_site_id)
    if payload.responsible_dentist_id:
        _require_dentist(session, context, payload.responsible_dentist_id, payload.main_site_id)
    treatment = Treatment(
        company_id=context.user.company_id,
        patient_id=payload.patient_id,
        name=payload.name,
        description=payload.description,
        specialty=payload.specialty,
        status="Borrador",
        responsible_dentist_id=payload.responsible_dentist_id,
        main_site_id=payload.main_site_id,
        start_date=payload.start_date,
        observations=payload.observations,
        created_by=context.user.id,
    )
    session.add(treatment)
    session.flush()
    _event(session, context, treatment.id, "TREATMENT_CREATED", "Tratamiento creado.")
    _audit(session, context, metadata, entity="treatment", entity_id=treatment.id, action="TREATMENT_CREATED")
    session.commit()
    session.refresh(treatment)
    return _treatment_response(session, treatment)


def get_treatment(session: Session, context: AuthContext, treatment_id: UUID) -> TreatmentResponse:
    return _treatment_response(session, _require_treatment(session, context, treatment_id))


def update_treatment(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    payload: TreatmentUpdateRequest,
    metadata: RequestMetadata,
) -> TreatmentResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    if treatment.status in TREATMENT_FINAL_STATUSES:
        raise TreatmentError("No se puede editar un tratamiento finalizado o cancelado.")
    data = payload.model_dump(exclude_unset=True)
    if "main_site_id" in data and data["main_site_id"]:
        _require_site(session, context, data["main_site_id"])
    if "responsible_dentist_id" in data and data["responsible_dentist_id"]:
        _require_dentist(session, context, data["responsible_dentist_id"], data.get("main_site_id", treatment.main_site_id))
    mapping = {
        "name": "name",
        "description": "description",
        "specialty": "specialty",
        "responsible_dentist_id": "responsible_dentist_id",
        "main_site_id": "main_site_id",
        "start_date": "start_date",
        "end_date": "end_date",
        "observations": "observations",
    }
    for key, attr in mapping.items():
        if key in data:
            setattr(treatment, attr, data[key])
    treatment.updated_by = context.user.id
    _event(session, context, treatment.id, "TREATMENT_UPDATED", "Tratamiento actualizado.", data)
    _audit(session, context, metadata, entity="treatment", entity_id=treatment.id, action="TREATMENT_UPDATED", detail=data)
    session.commit()
    session.refresh(treatment)
    return _treatment_response(session, treatment)


def change_treatment_status(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    status: str,
    action: str,
    metadata: RequestMetadata,
    reason: str | None = None,
) -> TreatmentResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    if treatment.status == "Cancelado" and status != "Cancelado":
        raise TreatmentError("No se puede cambiar un tratamiento cancelado.")
    if status == "Finalizado":
        pending = session.scalar(
            select(func.count(TreatmentProcedure.id)).where(
                TreatmentProcedure.treatment_id == treatment.id,
                TreatmentProcedure.status.in_(["Pendiente", "Agendado", "En proceso"]),
            )
        )
        if pending:
            raise TreatmentError("No se puede cerrar con procedimientos pendientes.")
        treatment.end_date = date.today()
    if status == "Cancelado" and not reason:
        raise TreatmentError("Cancelar tratamiento requiere motivo.")
    treatment.status = status
    treatment.updated_by = context.user.id
    _event(session, context, treatment.id, action, reason or f"Estado cambiado a {status}.")
    _audit(session, context, metadata, entity="treatment", entity_id=treatment.id, action=action, detail={"status": status, "reason": reason})
    session.commit()
    session.refresh(treatment)
    return _treatment_response(session, treatment)


def list_procedures(session: Session, context: AuthContext, treatment_id: UUID) -> list[ProcedureResponse]:
    treatment = _require_treatment(session, context, treatment_id)
    rows = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.treatment_id == treatment.id)
        .order_by(TreatmentProcedure.created_at)
    ).all()
    return [_procedure_response(*row) for row in rows]


def _procedure_response(
    procedure: TreatmentProcedure,
    dentist: Dentist | None = None,
    site: Site | None = None,
) -> ProcedureResponse:
    return ProcedureResponse(
        id=procedure.id,
        treatment_id=procedure.treatment_id,
        patient_id=procedure.patient_id,
        name=procedure.name,
        category=procedure.category,
        dentist_id=procedure.dentist_id,
        dentist_name=dentist.name if dentist else None,
        site_id=procedure.site_id,
        site_name=site.name if site else None,
        appointment_id=procedure.appointment_id,
        unit_value=_money(procedure.unit_value),
        quantity=Decimal(procedure.quantity),
        total_value=_money(procedure.total_value),
        status=procedure.status,
        estimated_date=procedure.estimated_date,
        performed_at=procedure.performed_at,
        observations=procedure.observations,
        requires_tooth=procedure.requires_tooth,
        tooth=procedure.tooth,
    )


def create_procedure(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    payload: ProcedureCreateRequest,
    metadata: RequestMetadata,
) -> ProcedureResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    if treatment.status in TREATMENT_FINAL_STATUSES:
        raise TreatmentError("No se pueden agregar procedimientos a este tratamiento.")
    if payload.site_id:
        _require_site(session, context, payload.site_id)
    if payload.dentist_id:
        _require_dentist(session, context, payload.dentist_id, payload.site_id)
    procedure = TreatmentProcedure(
        company_id=context.user.company_id,
        treatment_id=treatment.id,
        patient_id=treatment.patient_id,
        name=payload.name,
        category=payload.category,
        dentist_id=payload.dentist_id,
        site_id=payload.site_id,
        unit_value=_money(payload.unit_value),
        quantity=payload.quantity,
        total_value=_money(payload.unit_value * payload.quantity),
        status=payload.status,
        estimated_date=payload.estimated_date,
        observations=payload.observations,
        requires_tooth=payload.requires_tooth,
        tooth=payload.tooth,
        created_by=context.user.id,
    )
    session.add(procedure)
    treatment.updated_by = context.user.id
    session.flush()
    _event(session, context, treatment.id, "PROCEDURE_CREATED", "Procedimiento creado.", {"procedure_id": str(procedure.id)})
    _audit(session, context, metadata, entity="treatment_procedure", entity_id=procedure.id, action="PROCEDURE_CREATED")
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def update_procedure(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    procedure_id: UUID,
    payload: ProcedureUpdateRequest,
    metadata: RequestMetadata,
) -> ProcedureResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    if procedure.status == "Realizado":
        raise TreatmentError("No se puede modificar un procedimiento realizado sin flujo de corrección.")
    data = payload.model_dump(exclude_unset=True)
    if "site_id" in data and data["site_id"]:
        _require_site(session, context, data["site_id"])
    if "dentist_id" in data and data["dentist_id"]:
        _require_dentist(session, context, data["dentist_id"], data.get("site_id", procedure.site_id))
    for key, attr in {
        "name": "name",
        "category": "category",
        "dentist_id": "dentist_id",
        "site_id": "site_id",
        "status": "status",
        "estimated_date": "estimated_date",
        "observations": "observations",
        "requires_tooth": "requires_tooth",
        "tooth": "tooth",
    }.items():
        if key in data:
            setattr(procedure, attr, data[key])
    if "unit_value" in data:
        procedure.unit_value = _money(data["unit_value"])
    if "quantity" in data:
        procedure.quantity = data["quantity"]
    procedure.total_value = _money(procedure.unit_value * procedure.quantity)
    procedure.updated_by = context.user.id
    _event(session, context, treatment.id, "PROCEDURE_UPDATED", "Procedimiento actualizado.", data)
    _audit(session, context, metadata, entity="treatment_procedure", entity_id=procedure.id, action="PROCEDURE_UPDATED", detail=data)
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def mark_procedure_done(session: Session, context: AuthContext, treatment_id: UUID, procedure_id: UUID, metadata: RequestMetadata) -> ProcedureResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    if procedure.status == "Cancelado":
        raise TreatmentError("No se puede realizar un procedimiento cancelado.")
    procedure.status = "Realizado"
    procedure.performed_at = datetime.now(timezone.utc)
    procedure.updated_by = context.user.id
    if treatment.status in {"Borrador", "Presupuestado", "Aprobado"}:
        treatment.status = "En ejecución"
    _event(session, context, treatment.id, "PROCEDURE_MARKED_DONE", "Procedimiento marcado como realizado.", {"procedure_id": str(procedure.id)})
    _audit(session, context, metadata, entity="treatment_procedure", entity_id=procedure.id, action="PROCEDURE_MARKED_DONE")
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def cancel_procedure(session: Session, context: AuthContext, treatment_id: UUID, procedure_id: UUID, metadata: RequestMetadata, reason: str | None) -> ProcedureResponse:
    if not reason:
        raise TreatmentError("Cancelar procedimiento requiere motivo.")
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    if procedure.status == "Realizado":
        raise TreatmentError("No se puede cancelar un procedimiento realizado.")
    procedure.status = "Cancelado"
    procedure.updated_by = context.user.id
    _event(session, context, treatment.id, "PROCEDURE_CANCELLED", reason, {"procedure_id": str(procedure.id)})
    _audit(session, context, metadata, entity="treatment_procedure", entity_id=procedure.id, action="PROCEDURE_CANCELLED", detail={"reason": reason})
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def link_procedure_appointment(
    session: Session,
    context: AuthContext,
    treatment_id: UUID,
    procedure_id: UUID,
    appointment_id: UUID,
    metadata: RequestMetadata,
) -> ProcedureResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
    appointment = session.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.company_id == context.user.company_id,
            Appointment.patient_id == treatment.patient_id,
        )
    )
    if appointment is None:
        raise TreatmentError("Cita no encontrada para este paciente.", 404)
    _require_site(session, context, appointment.site_id)
    appointment.treatment_id = treatment.id
    appointment.treatment_procedure_id = procedure.id
    procedure.appointment_id = appointment.id
    procedure.status = "Agendado" if procedure.status == "Pendiente" else procedure.status
    _event(session, context, treatment.id, "PROCEDURE_LINKED_APPOINTMENT", "Procedimiento asociado a cita.", {"appointment_id": str(appointment.id), "procedure_id": str(procedure.id)})
    _audit(session, context, metadata, entity="appointment", entity_id=appointment.id, action="APPOINTMENT_LINKED_TREATMENT_PROCEDURE")
    session.commit()
    row = session.execute(
        select(TreatmentProcedure, Dentist, Site)
        .outerjoin(Dentist, Dentist.id == TreatmentProcedure.dentist_id)
        .outerjoin(Site, Site.id == TreatmentProcedure.site_id)
        .where(TreatmentProcedure.id == procedure.id)
    ).one()
    return _procedure_response(*row)


def link_appointment_treatment_procedure(
    session: Session,
    context: AuthContext,
    appointment_id: UUID,
    treatment_id: UUID,
    procedure_id: UUID | None,
    metadata: RequestMetadata,
) -> None:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    appointment = session.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.company_id == context.user.company_id,
            Appointment.patient_id == treatment.patient_id,
        )
    )
    if appointment is None:
        raise TreatmentError("Cita no encontrada para este paciente.", 404)
    _require_site(session, context, appointment.site_id)
    appointment.treatment_id = treatment.id
    if procedure_id:
        procedure = _require_procedure(session, context, treatment, procedure_id, lock=True)
        procedure.appointment_id = appointment.id
        procedure.status = "Agendado" if procedure.status == "Pendiente" else procedure.status
        appointment.treatment_procedure_id = procedure.id
    _audit(session, context, metadata, entity="appointment", entity_id=appointment.id, action="APPOINTMENT_LINKED_TREATMENT_PROCEDURE")
    session.commit()


def _calculate_discount(gross: Decimal, discount_type: str | None, discount_value: Decimal) -> Decimal:
    if not discount_type or discount_value == 0:
        return Decimal("0.00")
    if discount_type == "porcentaje":
        if discount_value > 100:
            raise TreatmentError("El descuento porcentual no puede superar 100%.")
        return _money(gross * discount_value / Decimal("100"))
    if discount_type == "valor":
        if discount_value > gross:
            raise TreatmentError("El descuento no puede superar el valor bruto.")
        return _money(discount_value)
    raise TreatmentError("Tipo de descuento no válido.")


def create_budget(session: Session, context: AuthContext, treatment_id: UUID, payload: BudgetCreateRequest, metadata: RequestMetadata) -> BudgetResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    procedures = session.scalars(
        select(TreatmentProcedure).where(
            TreatmentProcedure.treatment_id == treatment.id,
            TreatmentProcedure.status != "Cancelado",
        ).order_by(TreatmentProcedure.created_at)
    ).all()
    if not procedures:
        raise TreatmentError("No se puede crear presupuesto sin procedimientos.")
    gross = _money(sum((procedure.total_value for procedure in procedures), Decimal("0")))
    discount = _calculate_discount(gross, payload.discount_type, payload.discount_value)
    version = (session.scalar(select(func.coalesce(func.max(Budget.version), 0)).where(Budget.treatment_id == treatment.id)) or 0) + 1
    budget = Budget(
        company_id=context.user.company_id,
        patient_id=treatment.patient_id,
        treatment_id=treatment.id,
        number=f"P-{version}",
        version=version,
        status="Borrador",
        gross_value=gross,
        discount_type=payload.discount_type,
        discount_value=_money(payload.discount_value),
        discount_calculated_value=discount,
        final_value=_money(gross - discount),
        observations=payload.observations,
        issued_at=datetime.now(timezone.utc),
        expires_on=payload.expires_on,
        created_by=context.user.id,
    )
    session.add(budget)
    session.flush()
    for index, procedure in enumerate(procedures, start=1):
        session.add(
            BudgetDetail(
                company_id=context.user.company_id,
                budget_id=budget.id,
                procedure_id=procedure.id,
                name=procedure.name,
                category=procedure.category,
                quantity=procedure.quantity,
                unit_value=procedure.unit_value,
                total_value=procedure.total_value,
                order=index,
                observations=procedure.observations,
            )
        )
    treatment.status = "Presupuestado" if treatment.status == "Borrador" else treatment.status
    _event(session, context, treatment.id, "BUDGET_CREATED", "Presupuesto creado.", {"budget_id": str(budget.id)})
    _audit(session, context, metadata, entity="budget", entity_id=budget.id, action="BUDGET_CREATED")
    session.commit()
    return get_budget(session, context, budget.id)


def _budget_response(session: Session, budget: Budget) -> BudgetResponse:
    details = session.scalars(
        select(BudgetDetail).where(BudgetDetail.budget_id == budget.id).order_by(BudgetDetail.order)
    ).all()
    return BudgetResponse(
        id=budget.id,
        patient_id=budget.patient_id,
        treatment_id=budget.treatment_id,
        number=budget.number,
        version=budget.version,
        status=budget.status,
        gross_value=_money(budget.gross_value),
        discount_type=budget.discount_type,
        discount_value=_money(budget.discount_value),
        discount_calculated_value=_money(budget.discount_calculated_value),
        final_value=_money(budget.final_value),
        observations=budget.observations,
        issued_at=budget.issued_at,
        expires_on=budget.expires_on,
        approved_at=budget.approved_at,
        rejected_at=budget.rejected_at,
        details=[
            BudgetDetailResponse(
                id=detail.id,
                procedure_id=detail.procedure_id,
                name=detail.name,
                category=detail.category,
                quantity=detail.quantity,
                unit_value=_money(detail.unit_value),
                total_value=_money(detail.total_value),
                order=detail.order,
                observations=detail.observations,
            )
            for detail in details
        ],
    )


def get_budget(session: Session, context: AuthContext, budget_id: UUID) -> BudgetResponse:
    budget = session.scalar(
        select(Budget).where(Budget.id == budget_id, Budget.company_id == context.user.company_id)
    )
    if budget is None:
        raise TreatmentError("Presupuesto no encontrado.", 404)
    _require_treatment(session, context, budget.treatment_id)
    return _budget_response(session, budget)


def list_budgets(session: Session, context: AuthContext) -> list[BudgetResponse]:
    budgets = session.scalars(select(Budget).where(Budget.company_id == context.user.company_id).order_by(Budget.issued_at.desc())).all()
    return [_budget_response(session, budget) for budget in budgets if _can_access_treatment(session, context, budget.treatment_id)]


def _can_access_treatment(session: Session, context: AuthContext, treatment_id: UUID) -> bool:
    try:
        _require_treatment(session, context, treatment_id)
        return True
    except TreatmentError:
        return False


def update_budget(session: Session, context: AuthContext, budget_id: UUID, payload: BudgetCreateRequest, metadata: RequestMetadata) -> BudgetResponse:
    budget = session.scalar(select(Budget).where(Budget.id == budget_id, Budget.company_id == context.user.company_id).with_for_update())
    if budget is None:
        raise TreatmentError("Presupuesto no encontrado.", 404)
    if budget.status not in {"Borrador", "Pendiente de aprobación"}:
        raise TreatmentError("Un presupuesto aprobado/rechazado no permite edición económica directa.")
    gross = _money(budget.gross_value)
    discount = _calculate_discount(gross, payload.discount_type, payload.discount_value)
    budget.discount_type = payload.discount_type
    budget.discount_value = _money(payload.discount_value)
    budget.discount_calculated_value = discount
    budget.final_value = _money(gross - discount)
    budget.observations = payload.observations
    budget.expires_on = payload.expires_on
    budget.updated_by = context.user.id
    _event(session, context, budget.treatment_id, "BUDGET_UPDATED", "Presupuesto actualizado.", {"budget_id": str(budget.id)})
    _audit(session, context, metadata, entity="budget", entity_id=budget.id, action="BUDGET_UPDATED")
    session.commit()
    return get_budget(session, context, budget.id)


def change_budget_status(session: Session, context: AuthContext, budget_id: UUID, status: str, action: str, metadata: RequestMetadata) -> BudgetResponse:
    budget = session.scalar(select(Budget).where(Budget.id == budget_id, Budget.company_id == context.user.company_id).with_for_update())
    if budget is None:
        raise TreatmentError("Presupuesto no encontrado.", 404)
    treatment = _require_treatment(session, context, budget.treatment_id, lock=True)
    if status == "Aprobado":
        if budget.final_value < 0:
            raise TreatmentError("No se puede aprobar un presupuesto con valor negativo.")
        budget.approved_at = datetime.now(timezone.utc)
        budget.approved_by = context.user.id
        treatment.status = "Aprobado" if treatment.status in {"Borrador", "Presupuestado"} else treatment.status
    if status == "Rechazado":
        budget.rejected_at = datetime.now(timezone.utc)
        budget.rejected_by = context.user.id
    budget.status = status
    budget.updated_by = context.user.id
    _event(session, context, treatment.id, action, f"Presupuesto {status}.", {"budget_id": str(budget.id)})
    _audit(session, context, metadata, entity="budget", entity_id=budget.id, action=action)
    session.commit()
    return get_budget(session, context, budget.id)


def create_payment(session: Session, context: AuthContext, treatment_id: UUID, payload: PaymentCreateRequest, metadata: RequestMetadata) -> PaymentResponse:
    treatment = _require_treatment(session, context, treatment_id, lock=True)
    site = _require_site(session, context, payload.site_id)
    dentist = _require_dentist(session, context, payload.dentist_id, payload.site_id) if payload.dentist_id else None
    approved_budget = session.scalar(
        select(Budget)
        .where(Budget.treatment_id == treatment.id, Budget.status.in_(APPROVED_BUDGET_STATUSES))
        .order_by(Budget.version.desc())
        .limit(1)
    )
    if approved_budget is None and treatment.status not in {"Aprobado", "En ejecución", "Finalizado"}:
        raise TreatmentError("Para registrar pagos se requiere presupuesto o tratamiento aprobado.")
    summary = _summary(session, treatment.id)
    if payload.value > summary.balance:
        raise TreatmentError("El pago no puede superar el saldo pendiente.")
    payment = TreatmentPayment(
        company_id=context.user.company_id,
        patient_id=treatment.patient_id,
        treatment_id=treatment.id,
        budget_id=approved_budget.id if approved_budget else None,
        site_id=site.id,
        dentist_id=dentist.id if dentist else treatment.responsible_dentist_id,
        paid_at=payload.paid_at,
        value=_money(payload.value),
        payment_method=payload.payment_method,
        reference=payload.reference,
        observation=payload.observation,
        status=VALID_PAYMENT_STATUS,
        registered_by=context.user.id,
    )
    session.add(payment)
    if treatment.status == "Aprobado":
        treatment.status = "En ejecución"
    session.flush()
    _event(session, context, treatment.id, "PAYMENT_REGISTERED", "Pago registrado.", {"payment_id": str(payment.id), "value": str(payment.value)})
    _audit(session, context, metadata, entity="payment", entity_id=payment.id, action="PAYMENT_REGISTERED", detail={"value": str(payment.value)})
    session.commit()
    return get_payment(session, context, payment.id)


def _payment_response(session: Session, payment: TreatmentPayment) -> PaymentResponse:
    patient = session.get(Patient, payment.patient_id)
    treatment = session.get(Treatment, payment.treatment_id)
    site = session.get(Site, payment.site_id)
    dentist = session.get(Dentist, payment.dentist_id) if payment.dentist_id else None
    if patient is None or treatment is None or site is None:
        raise TreatmentError("Pago inválido o incompleto.", 500)
    return PaymentResponse(
        id=payment.id,
        patient_id=payment.patient_id,
        patient_name=f"{patient.first_names} {patient.last_names}".strip(),
        treatment_id=payment.treatment_id,
        treatment_name=treatment.name,
        budget_id=payment.budget_id,
        site_id=payment.site_id,
        site_name=site.name,
        dentist_id=payment.dentist_id,
        dentist_name=dentist.name if dentist else None,
        paid_at=payment.paid_at,
        value=_money(payment.value),
        payment_method=payment.payment_method,
        reference=payment.reference,
        observation=payment.observation,
        status=payment.status,
        reversed_at=payment.reversed_at,
        reversal_reason=payment.reversal_reason,
    )


def get_payment(session: Session, context: AuthContext, payment_id: UUID) -> PaymentResponse:
    payment = session.scalar(
        select(TreatmentPayment).where(
            TreatmentPayment.id == payment_id,
            TreatmentPayment.company_id == context.user.company_id,
        )
    )
    if payment is None:
        raise TreatmentError("Pago no encontrado.", 404)
    _require_treatment(session, context, payment.treatment_id)
    return _payment_response(session, payment)


def list_payments(session: Session, context: AuthContext) -> list[PaymentResponse]:
    payments = session.scalars(
        select(TreatmentPayment).where(TreatmentPayment.company_id == context.user.company_id).order_by(TreatmentPayment.paid_at.desc())
    ).all()
    return [_payment_response(session, payment) for payment in payments if _can_access_treatment(session, context, payment.treatment_id)]


def reverse_payment(session: Session, context: AuthContext, payment_id: UUID, reason: str, metadata: RequestMetadata) -> PaymentResponse:
    payment = session.scalar(
        select(TreatmentPayment).where(
            TreatmentPayment.id == payment_id,
            TreatmentPayment.company_id == context.user.company_id,
        ).with_for_update()
    )
    if payment is None:
        raise TreatmentError("Pago no encontrado.", 404)
    if payment.status == REVERSED_PAYMENT_STATUS:
        raise TreatmentError("El pago ya fue reversado.")
    _require_treatment(session, context, payment.treatment_id)
    payment.status = REVERSED_PAYMENT_STATUS
    payment.reversed_at = datetime.now(timezone.utc)
    payment.reversed_by = context.user.id
    payment.reversal_reason = reason
    _event(session, context, payment.treatment_id, "PAYMENT_REVERSED", reason, {"payment_id": str(payment.id), "value": str(payment.value)})
    _audit(session, context, metadata, entity="payment", entity_id=payment.id, action="PAYMENT_REVERSED", detail={"reason": reason})
    session.commit()
    return get_payment(session, context, payment.id)


def finance_dashboard(session: Session, context: AuthContext) -> FinanceDashboardResponse:
    now = datetime.now(timezone.utc)
    start_day = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    start_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    start_year = datetime(now.year, 1, 1, tzinfo=timezone.utc)

    def income_since(start: datetime) -> Decimal:
        return _money(session.scalar(select(func.coalesce(func.sum(TreatmentPayment.value), 0)).where(TreatmentPayment.company_id == context.user.company_id, TreatmentPayment.status == VALID_PAYMENT_STATUS, TreatmentPayment.paid_at >= start)))

    treatments = session.scalars(select(Treatment).where(Treatment.company_id == context.user.company_id)).all()
    balances = [_summary(session, treatment.id).balance for treatment in treatments]
    active_count = sum(1 for treatment in treatments if treatment.status in TREATMENT_ACTIVE_STATUSES)
    approved_finals = [_summary(session, treatment.id).final_value for treatment in treatments if _summary(session, treatment.id).final_value > 0]
    return FinanceDashboardResponse(
        income_today=income_since(start_day),
        income_month=income_since(start_month),
        income_year=income_since(start_year),
        receivables_total=_money(sum(balances, Decimal("0"))),
        active_treatments=active_count,
        average_ticket=_money(sum(approved_finals, Decimal("0")) / len(approved_finals)) if approved_finals else Decimal("0.00"),
    )


def _breakdown(session: Session, context: AuthContext, group: str) -> FinanceBreakdownResponse:
    if group == "site":
        rows = session.execute(
            select(Site.id, Site.name, func.coalesce(func.sum(TreatmentPayment.value), 0))
            .join(TreatmentPayment, TreatmentPayment.site_id == Site.id)
            .where(TreatmentPayment.company_id == context.user.company_id, TreatmentPayment.status == VALID_PAYMENT_STATUS)
            .group_by(Site.id, Site.name)
        ).all()
    elif group == "dentist":
        rows = session.execute(
            select(Dentist.id, Dentist.name, func.coalesce(func.sum(TreatmentPayment.value), 0))
            .join(TreatmentPayment, TreatmentPayment.dentist_id == Dentist.id)
            .where(TreatmentPayment.company_id == context.user.company_id, TreatmentPayment.status == VALID_PAYMENT_STATUS)
            .group_by(Dentist.id, Dentist.name)
        ).all()
    else:
        rows = session.execute(
            select(TreatmentProcedure.id, TreatmentProcedure.name, func.coalesce(func.sum(TreatmentProcedure.total_value), 0))
            .where(TreatmentProcedure.company_id == context.user.company_id, TreatmentProcedure.status == "Realizado")
            .group_by(TreatmentProcedure.id, TreatmentProcedure.name)
        ).all()
    return FinanceBreakdownResponse(items=[FinanceBreakdownItem(id=row[0], name=row[1], value=_money(row[2])) for row in rows])


def finance_by_site(session: Session, context: AuthContext) -> FinanceBreakdownResponse:
    return _breakdown(session, context, "site")


def finance_by_dentist(session: Session, context: AuthContext) -> FinanceBreakdownResponse:
    return _breakdown(session, context, "dentist")


def finance_by_procedure(session: Session, context: AuthContext) -> FinanceBreakdownResponse:
    return _breakdown(session, context, "procedure")


def patient_balances(session: Session, context: AuthContext) -> PatientBalancesResponse:
    patients = {}
    for treatment in session.scalars(select(Treatment).where(Treatment.company_id == context.user.company_id)).all():
        balance = _summary(session, treatment.id).balance
        if balance <= 0:
            continue
        patients[treatment.patient_id] = patients.get(treatment.patient_id, Decimal("0")) + balance
    items = []
    for patient_id, balance in patients.items():
        patient = session.get(Patient, patient_id)
        if patient:
            items.append(PatientBalanceItem(patient_id=patient_id, patient_name=f"{patient.first_names} {patient.last_names}".strip(), balance=_money(balance)))
    return PatientBalancesResponse(items=items)
