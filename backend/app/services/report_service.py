from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.agenda import Appointment, Dentist, Patient
from app.models.audit_event import AuditEvent
from app.models.clinical_record import ClinicalAllergy, ClinicalEvolution, ClinicalRecord
from app.models.company import Company
from app.models.followup import PatientFollowup
from app.models.site import Site
from app.models.treatment import Budget, Treatment, TreatmentPayment, TreatmentProcedure
from app.schemas.report_schema import (
    ActionItemsResponse,
    AppointmentReportsResponse,
    ClinicalAggregateReportsResponse,
    ClinicalDraftItem,
    ExecutiveSummaryResponse,
    FinanceReportsResponse,
    FollowupReportsResponse,
    OverdueFollowupItem,
    PatientReceivableItem,
    PatientReportsResponse,
    PendingConfirmationItem,
    ReportChartItem,
    ReportMetric,
    StaleTreatmentItem,
    TreatmentReportsResponse,
)
from app.services.auth_service import AuthContext, RequestMetadata
from app.services.site_access_service import authorized_site_ids


FALLBACK_TIMEZONE = "America/Bogota"
MAX_RANGE_DAYS = 366
ACTIVE_TREATMENT_STATUSES = {"Aprobado", "En ejecución", "Pausado"}
APPROVED_BUDGET_STATUSES = {"Aprobado", "En ejecución", "Finalizado"}
VALID_PAYMENT_STATUS = "valido"
OPEN_FOLLOWUP_STATUSES = {"Pendiente", "Contactado", "Cita programada"}
ELIGIBLE_APPOINTMENT_STATUSES = {
    "Programada",
    "Confirmada",
    "Atendida",
    "Cancelada",
    "No Asistió",
}
CENT = Decimal("0.01")


class ReportError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _money(value) -> Decimal:
    return Decimal(value or 0).quantize(CENT, rounding=ROUND_HALF_UP)


def _pct(numerator: int | Decimal, denominator: int | Decimal) -> Decimal:
    if not denominator:
        return Decimal("0.00")
    return (Decimal(numerator) * Decimal("100") / Decimal(denominator)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _company_timezone(session: Session, context: AuthContext) -> str:
    company = session.get(Company, context.user.company_id)
    return (company.timezone if company else None) or FALLBACK_TIMEZONE


def _local_bounds(date_from: date, date_to: date, timezone_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(timezone_name)
    start = datetime.combine(date_from, time.min, tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=tz).astimezone(timezone.utc)
    return start, end


def _today_in_timezone(timezone_name: str) -> date:
    return datetime.now(ZoneInfo(timezone_name)).date()


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _resolve_dates(
    *,
    preset: str | None,
    date_from: date | None,
    date_to: date | None,
    timezone_name: str,
) -> tuple[date, date, str]:
    today = _today_in_timezone(timezone_name)
    selected = preset or "month_current"
    if selected == "today":
        start = end = today
    elif selected == "yesterday":
        start = end = today - timedelta(days=1)
    elif selected == "week_current":
        start = today - timedelta(days=today.weekday())
        end = today
    elif selected == "month_previous":
        current_month = _month_start(today)
        previous_month = _month_start(current_month - timedelta(days=1))
        start = previous_month
        end = current_month - timedelta(days=1)
    elif selected == "year_current":
        start = date(today.year, 1, 1)
        end = today
    elif selected == "custom":
        if date_from is None or date_to is None:
            raise ReportError("El rango personalizado requiere fecha inicial y final.")
        start, end = date_from, date_to
    else:
        selected = "month_current"
        start = _month_start(today)
        end = today
    if end < start:
        raise ReportError("El rango de fechas no es válido.")
    if (end - start).days > MAX_RANGE_DAYS:
        raise ReportError("El rango máximo permitido es de 12 meses.")
    return start, end, selected


def _site_ids(session: Session, context: AuthContext, site_id: UUID | None) -> set[UUID]:
    ids = authorized_site_ids(
        session,
        company_id=context.user.company_id,
        user_id=context.user.id,
        roles=context.roles,
        active_only=False,
    )
    if site_id:
        if site_id not in ids:
            raise ReportError("No tienes acceso a la sede seleccionada.", 403)
        return {site_id}
    return ids


def _current_dentist_id(session: Session, context: AuthContext) -> UUID | None:
    dentist = session.scalar(
        select(Dentist).where(
            Dentist.company_id == context.user.company_id,
            Dentist.user_id == context.user.id,
            Dentist.is_active.is_(True),
        )
    )
    return dentist.id if dentist else None


def _dentist_scope(session: Session, context: AuthContext, dentist_id: UUID | None) -> UUID | None:
    own_only = "reports.own_scope" in context.permissions and not (
        "reports.cross_site" in context.permissions or "ADMINISTRATOR" in context.roles or "DENTIST_ADMIN" in context.roles
    )
    current = _current_dentist_id(session, context)
    if own_only:
        if dentist_id and current and dentist_id != current:
            raise ReportError("Solo puedes consultar tu propio alcance.", 403)
        return current
    return dentist_id


def _permissions(context: AuthContext) -> dict[str, bool]:
    return {
        "operational": "reports.operational" in context.permissions,
        "financial": "reports.financial" in context.permissions,
        "clinical_aggregate": "reports.clinical_aggregate" in context.permissions,
        "cross_site": "reports.cross_site" in context.permissions,
        "own_scope": "reports.own_scope" in context.permissions,
    }


def _audit_report_view(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    section: str,
    filters: dict,
) -> None:
    session.add(
        AuditEvent(
            company_id=context.user.company_id,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            entity="report",
            entity_id=None,
            action="REPORT_VIEWED",
            result="SUCCESS",
            detail={"section": section, "filters": filters},
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
    )
    session.commit()


def _patient_name(patient: Patient | None) -> str:
    if patient is None:
        return "Paciente no disponible"
    return f"{patient.first_names} {patient.last_names}".strip()


def _appointment_filters(
    context: AuthContext,
    site_ids: set[UUID],
    start_utc: datetime,
    end_utc: datetime,
    dentist_id: UUID | None,
) -> list:
    filters = [
        Appointment.company_id == context.user.company_id,
        Appointment.site_id.in_(site_ids),
        Appointment.starts_at >= start_utc,
        Appointment.starts_at < end_utc,
        Appointment.is_active.is_(True),
    ]
    if dentist_id:
        filters.append(Appointment.dentist_id == dentist_id)
    return filters


def _appointments_report(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID],
    start_utc: datetime,
    end_utc: datetime,
    dentist_id: UUID | None,
) -> AppointmentReportsResponse:
    filters = _appointment_filters(context, site_ids, start_utc, end_utc, dentist_id)
    rows = session.execute(
        select(Appointment.status, func.count(Appointment.id))
        .where(*filters)
        .group_by(Appointment.status)
    ).all()
    counts = {row[0]: int(row[1]) for row in rows}
    eligible = sum(counts.get(status, 0) for status in ELIGIBLE_APPOINTMENT_STATUSES)
    by_site = session.execute(
        select(Site.name, func.count(Appointment.id))
        .join(Appointment, Appointment.site_id == Site.id)
        .where(*filters)
        .group_by(Site.name)
        .order_by(func.count(Appointment.id).desc())
    ).all()
    by_dentist = session.execute(
        select(Dentist.name, func.count(Appointment.id))
        .join(Appointment, Appointment.dentist_id == Dentist.id)
        .where(*filters)
        .group_by(Dentist.name)
        .order_by(func.count(Appointment.id).desc())
    ).all()
    return AppointmentReportsResponse(
        created=int(session.scalar(select(func.count(Appointment.id)).where(*filters)) or 0),
        attended=counts.get("Atendida", 0),
        confirmed=counts.get("Confirmada", 0),
        cancelled=counts.get("Cancelada", 0),
        no_show=counts.get("No Asistió", 0),
        overbooked=int(
            session.scalar(
                select(func.count(Appointment.id)).where(*filters, Appointment.is_overbook.is_(True))
            )
            or 0
        ),
        attendance_rate=_pct(counts.get("Atendida", 0), eligible),
        cancellation_rate=_pct(counts.get("Cancelada", 0), eligible),
        no_show_rate=_pct(counts.get("No Asistió", 0), eligible),
        by_status=[
            ReportChartItem(label=status, value=counts.get(status, 0))
            for status in ["Programada", "Confirmada", "Atendida", "Cancelada", "No Asistió"]
        ],
        by_site=[ReportChartItem(label=row[0], value=int(row[1])) for row in by_site],
        by_dentist=[ReportChartItem(label=row[0], value=int(row[1])) for row in by_dentist],
    )


def _latest_budget_rows(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID] | None = None,
    dentist_id: UUID | None = None,
) -> list[Budget]:
    treatment_filters = [Treatment.company_id == context.user.company_id]
    if site_ids is not None:
        treatment_filters.append(or_(Treatment.main_site_id.is_(None), Treatment.main_site_id.in_(site_ids)))
    if dentist_id:
        treatment_filters.append(Treatment.responsible_dentist_id == dentist_id)
    budgets: list[Budget] = []
    treatment_ids = list(
        session.scalars(select(Treatment.id).where(*treatment_filters))
    )
    for treatment_id in treatment_ids:
        budget = session.scalar(
            select(Budget)
            .where(
                Budget.company_id == context.user.company_id,
                Budget.treatment_id == treatment_id,
                Budget.status.in_(APPROVED_BUDGET_STATUSES),
            )
            .order_by(Budget.version.desc())
            .limit(1)
        )
        if budget:
            budgets.append(budget)
    return budgets


def _paid_by_treatment(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID] | None = None,
    dentist_id: UUID | None = None,
) -> dict[UUID, Decimal]:
    filters = [
        TreatmentPayment.company_id == context.user.company_id,
        TreatmentPayment.status == VALID_PAYMENT_STATUS,
    ]
    if site_ids is not None:
        filters.append(TreatmentPayment.site_id.in_(site_ids))
    if dentist_id:
        filters.append(TreatmentPayment.dentist_id == dentist_id)
    rows = session.execute(
        select(TreatmentPayment.treatment_id, func.coalesce(func.sum(TreatmentPayment.value), 0))
        .where(*filters)
        .group_by(TreatmentPayment.treatment_id)
    ).all()
    return {row[0]: _money(row[1]) for row in rows}


def _balances(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID] | None = None,
    dentist_id: UUID | None = None,
) -> dict[UUID, Decimal]:
    paid = _paid_by_treatment(session, context, site_ids, dentist_id)
    balances: dict[UUID, Decimal] = {}
    for budget in _latest_budget_rows(session, context, site_ids, dentist_id):
        balance = max(_money(budget.final_value) - paid.get(budget.treatment_id, Decimal("0.00")), Decimal("0.00"))
        if balance > 0:
            balances[budget.treatment_id] = balance
    return balances


def _patients_report(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID],
    start_utc: datetime,
    end_utc: datetime,
    dentist_id: UUID | None,
    today: date,
) -> PatientReportsResponse:
    new_patients = int(
        session.scalar(
            select(func.count(Patient.id)).where(
                Patient.company_id == context.user.company_id,
                Patient.created_at >= start_utc,
                Patient.created_at < end_utc,
                Patient.is_active.is_(True),
            )
        )
        or 0
    )
    appointment_filters = _appointment_filters(context, site_ids, start_utc, end_utc, dentist_id)
    attended_ids = set(
        session.scalars(
            select(Appointment.patient_id).where(*appointment_filters, Appointment.status == "Atendida")
        )
    )
    last_year_start = datetime.combine(today - timedelta(days=365), time.min, tzinfo=timezone.utc)
    active_ids = set(
        session.scalars(
            select(Appointment.patient_id).where(
                Appointment.company_id == context.user.company_id,
                Appointment.site_id.in_(site_ids),
                Appointment.starts_at >= last_year_start,
                Appointment.status == "Atendida",
            )
        )
    )
    treatment_active_filters = [
        Treatment.company_id == context.user.company_id,
        Treatment.status.in_(ACTIVE_TREATMENT_STATUSES),
        or_(Treatment.main_site_id.is_(None), Treatment.main_site_id.in_(site_ids)),
    ]
    if dentist_id:
        treatment_active_filters.append(Treatment.responsible_dentist_id == dentist_id)
    active_ids.update(
        session.scalars(select(Treatment.patient_id).where(*treatment_active_filters))
    )
    followup_active_filters = [
        PatientFollowup.company_id == context.user.company_id,
        PatientFollowup.site_id.in_(site_ids),
        PatientFollowup.status.in_(OPEN_FOLLOWUP_STATUSES),
    ]
    if dentist_id:
        followup_active_filters.append(PatientFollowup.dentist_id == dentist_id)
    active_ids.update(
        session.scalars(select(PatientFollowup.patient_id).where(*followup_active_filters))
    )
    future_appointment_filters = [
        Appointment.company_id == context.user.company_id,
        Appointment.site_id.in_(site_ids),
        Appointment.starts_at >= datetime.now(timezone.utc),
        Appointment.status.in_(["Programada", "Confirmada"]),
    ]
    if dentist_id:
        future_appointment_filters.append(Appointment.dentist_id == dentist_id)
    active_ids.update(
        session.scalars(select(Appointment.patient_id).where(*future_appointment_filters))
    )
    balances = _balances(session, context, site_ids, dentist_id)
    patient_balance_ids: set[UUID] = set()
    if balances:
        patient_balance_ids = set(
            session.scalars(
                select(Treatment.patient_id).where(
                    Treatment.company_id == context.user.company_id,
                    Treatment.id.in_(list(balances.keys())),
                )
            )
        )
    overdue_followup_ids = set(
        session.scalars(
            select(PatientFollowup.patient_id).where(
                PatientFollowup.company_id == context.user.company_id,
                PatientFollowup.site_id.in_(site_ids),
                PatientFollowup.status.in_(OPEN_FOLLOWUP_STATUSES),
                PatientFollowup.followup_date < today,
            )
        )
    )
    with_active_treatment = int(
        session.scalar(
            select(func.count(func.distinct(Treatment.patient_id))).where(
                *treatment_active_filters,
            )
        )
        or 0
    )
    return PatientReportsResponse(
        new_patients=new_patients,
        attended_patients=len(attended_ids),
        active_patients=len(active_ids),
        with_active_treatment=with_active_treatment,
        with_balance=len(patient_balance_ids),
        with_overdue_followup=len(overdue_followup_ids),
        active_definition="Paciente con cita atendida últimos 12 meses, tratamiento activo, seguimiento abierto o cita futura programada/confirmada.",
    )


def _treatment_last_activity(
    session: Session,
    treatment: Treatment,
) -> datetime:
    values = [treatment.updated_at or treatment.created_at]
    for value in session.scalars(
        select(TreatmentProcedure.updated_at).where(TreatmentProcedure.treatment_id == treatment.id)
    ):
        if value:
            values.append(value)
    for value in session.scalars(
        select(TreatmentPayment.paid_at).where(
            TreatmentPayment.treatment_id == treatment.id,
            TreatmentPayment.status == VALID_PAYMENT_STATUS,
        )
    ):
        if value:
            values.append(value)
    for value in session.scalars(
        select(ClinicalEvolution.attended_at).where(ClinicalEvolution.treatment_id == treatment.id)
    ):
        if value:
            values.append(value)
    return max(values)


def _treatments_report(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID],
    now_utc: datetime,
    dentist_id: UUID | None,
) -> TreatmentReportsResponse:
    treatment_filters = [
        Treatment.company_id == context.user.company_id,
        or_(Treatment.main_site_id.is_(None), Treatment.main_site_id.in_(site_ids)),
    ]
    if dentist_id:
        treatment_filters.append(Treatment.responsible_dentist_id == dentist_id)
    treatments = list(session.scalars(select(Treatment).where(*treatment_filters)))
    counts = defaultdict(int)
    progress_values: list[Decimal] = []
    stale_count = 0
    without_next = 0
    balances = _balances(session, context, site_ids, dentist_id)
    for treatment in treatments:
        counts[treatment.status] += 1
        if treatment.status in ACTIVE_TREATMENT_STATUSES:
            if now_utc - _treatment_last_activity(session, treatment) > timedelta(days=30):
                stale_count += 1
            future = session.scalar(
                select(Appointment.id).where(
                    Appointment.treatment_id == treatment.id,
                    Appointment.status.in_(["Programada", "Confirmada"]),
                    Appointment.starts_at >= now_utc,
                )
            )
            if future is None:
                without_next += 1
        total = session.scalar(
            select(func.count(TreatmentProcedure.id)).where(
                TreatmentProcedure.treatment_id == treatment.id,
                TreatmentProcedure.status != "Cancelado",
            )
        ) or 0
        done = session.scalar(
            select(func.count(TreatmentProcedure.id)).where(
                TreatmentProcedure.treatment_id == treatment.id,
                TreatmentProcedure.status == "Realizado",
            )
        ) or 0
        if total:
            progress_values.append(_pct(done, total))
    return TreatmentReportsResponse(
        active=sum(counts[status] for status in ACTIVE_TREATMENT_STATUSES),
        approved=counts["Aprobado"],
        in_progress=counts["En ejecución"],
        paused=counts["Pausado"],
        finalized=counts["Finalizado"],
        cancelled=counts["Cancelado"],
        with_balance=len(balances),
        without_movement=stale_count,
        without_next_appointment=without_next,
        average_progress=(
            sum(progress_values, Decimal("0.00")) / len(progress_values)
        ).quantize(Decimal("0.01")) if progress_values else Decimal("0.00"),
        by_status=[
            ReportChartItem(label=status, value=counts[status])
            for status in ["Borrador", "Presupuestado", "Aprobado", "En ejecución", "Pausado", "Finalizado", "Cancelado"]
        ],
    )


def _finance_report(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID],
    start_utc: datetime,
    end_utc: datetime,
    today_start: datetime,
    month_start: datetime,
    timezone_name: str,
    dentist_id: UUID | None,
) -> FinanceReportsResponse:
    payment_filters = [
        TreatmentPayment.company_id == context.user.company_id,
        TreatmentPayment.site_id.in_(site_ids),
        TreatmentPayment.status == VALID_PAYMENT_STATUS,
    ]
    if dentist_id:
        payment_filters.append(TreatmentPayment.dentist_id == dentist_id)

    def income_between(start: datetime, end: datetime) -> Decimal:
        return _money(
            session.scalar(
                select(func.coalesce(func.sum(TreatmentPayment.value), 0)).where(
                    *payment_filters,
                    TreatmentPayment.paid_at >= start,
                    TreatmentPayment.paid_at < end,
                )
            )
        )

    range_payment_filters = [
        *payment_filters,
        TreatmentPayment.paid_at >= start_utc,
        TreatmentPayment.paid_at < end_utc,
    ]
    by_site = session.execute(
        select(Site.name, func.coalesce(func.sum(TreatmentPayment.value), 0))
        .join(TreatmentPayment, TreatmentPayment.site_id == Site.id)
        .where(*range_payment_filters)
        .group_by(Site.name)
        .order_by(func.sum(TreatmentPayment.value).desc())
    ).all()
    by_dentist = session.execute(
        select(Dentist.name, func.coalesce(func.sum(TreatmentPayment.value), 0))
        .join(TreatmentPayment, TreatmentPayment.dentist_id == Dentist.id)
        .where(*range_payment_filters)
        .group_by(Dentist.name)
        .order_by(func.sum(TreatmentPayment.value).desc())
    ).all()
    by_method = session.execute(
        select(TreatmentPayment.payment_method, func.coalesce(func.sum(TreatmentPayment.value), 0))
        .where(*range_payment_filters)
        .group_by(TreatmentPayment.payment_method)
    ).all()
    payments = list(session.scalars(select(TreatmentPayment).where(*range_payment_filters)))
    monthly: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for payment in payments:
        local = payment.paid_at.astimezone(ZoneInfo(timezone_name))
        monthly[f"{local.year}-{local.month:02d}"] += _money(payment.value)

    production_filters = [
        TreatmentProcedure.company_id == context.user.company_id,
        or_(TreatmentProcedure.site_id.is_(None), TreatmentProcedure.site_id.in_(site_ids)),
        TreatmentProcedure.status == "Realizado",
        TreatmentProcedure.performed_at >= start_utc,
        TreatmentProcedure.performed_at < end_utc,
    ]
    if dentist_id:
        production_filters.append(TreatmentProcedure.dentist_id == dentist_id)
    production_range = _money(
        session.scalar(select(func.coalesce(func.sum(TreatmentProcedure.total_value), 0)).where(*production_filters))
    )
    production_top = session.execute(
        select(TreatmentProcedure.name, func.coalesce(func.sum(TreatmentProcedure.total_value), 0))
        .where(*production_filters)
        .group_by(TreatmentProcedure.name)
        .order_by(func.sum(TreatmentProcedure.total_value).desc())
        .limit(8)
    ).all()
    approved_filters = [
        Budget.company_id == context.user.company_id,
        Budget.status.in_(APPROVED_BUDGET_STATUSES),
        Budget.approved_at >= start_utc,
        Budget.approved_at < end_utc,
    ]
    approved_sales = _money(session.scalar(select(func.coalesce(func.sum(Budget.final_value), 0)).where(*approved_filters)))
    approved_count = int(session.scalar(select(func.count(Budget.id)).where(*approved_filters)) or 0)
    balances = _balances(session, context, site_ids, dentist_id)
    latest_budgets = {
        budget.treatment_id: budget
        for budget in _latest_budget_rows(session, context, site_ids, dentist_id)
    }
    aging = {"0–30": Decimal("0.00"), "31–60": Decimal("0.00"), "61–90": Decimal("0.00"), ">90": Decimal("0.00")}
    today = _today_in_timezone(timezone_name)
    for treatment_id, balance in balances.items():
        budget = latest_budgets.get(treatment_id)
        if not budget:
            continue
        base_date = budget.expires_on or (budget.approved_at.astimezone(ZoneInfo(timezone_name)).date() if budget.approved_at else today)
        days = max((today - base_date).days, 0)
        bucket = "0–30" if days <= 30 else "31–60" if days <= 60 else "61–90" if days <= 90 else ">90"
        aging[bucket] += balance
    return FinanceReportsResponse(
        income_today=income_between(today_start, today_start + timedelta(days=1)),
        income_month=income_between(month_start, end_utc),
        income_range=income_between(start_utc, end_utc),
        clinical_production_range=production_range,
        approved_sales_range=approved_sales,
        approved_budgets_count=approved_count,
        receivables_total=_money(sum(balances.values(), Decimal("0.00"))),
        patients_with_balance=len({
            session.get(Treatment, treatment_id).patient_id
            for treatment_id in balances
            if session.get(Treatment, treatment_id)
        }),
        income_by_site=[ReportChartItem(label=row[0], value=_money(row[1])) for row in by_site],
        income_by_dentist=[ReportChartItem(label=row[0], value=_money(row[1])) for row in by_dentist],
        income_by_method=[ReportChartItem(label=row[0], value=_money(row[1])) for row in by_method],
        income_by_month=[
            ReportChartItem(label=label, value=value)
            for label, value in sorted(monthly.items())
        ],
        production_by_procedure=[ReportChartItem(label=row[0], value=_money(row[1])) for row in production_top],
        receivables_aging=[ReportChartItem(label=label, value=value) for label, value in aging.items()],
    )


def _followups_report(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID],
    today: date,
    dentist_id: UUID | None,
) -> FollowupReportsResponse:
    filters = [
        PatientFollowup.company_id == context.user.company_id,
        PatientFollowup.site_id.in_(site_ids),
    ]
    if dentist_id:
        filters.append(PatientFollowup.dentist_id == dentist_id)
    rows = session.execute(
        select(PatientFollowup.status, func.count(PatientFollowup.id))
        .where(*filters)
        .group_by(PatientFollowup.status)
    ).all()
    counts = {row[0]: int(row[1]) for row in rows}
    overdue = int(
        session.scalar(
            select(func.count(PatientFollowup.id)).where(
                *filters,
                PatientFollowup.status.in_(OPEN_FOLLOWUP_STATUSES),
                PatientFollowup.followup_date < today,
            )
        )
        or 0
    )
    by_reason = session.execute(
        select(PatientFollowup.reason, func.count(PatientFollowup.id))
        .where(*filters)
        .group_by(PatientFollowup.reason)
        .order_by(func.count(PatientFollowup.id).desc())
        .limit(8)
    ).all()
    by_site = session.execute(
        select(Site.name, func.count(PatientFollowup.id))
        .join(PatientFollowup, PatientFollowup.site_id == Site.id)
        .where(*filters)
        .group_by(Site.name)
    ).all()
    by_dentist = session.execute(
        select(Dentist.name, func.count(PatientFollowup.id))
        .join(PatientFollowup, PatientFollowup.dentist_id == Dentist.id)
        .where(*filters)
        .group_by(Dentist.name)
    ).all()
    return FollowupReportsResponse(
        open=sum(counts.get(status, 0) for status in OPEN_FOLLOWUP_STATUSES),
        overdue=overdue,
        scheduled=counts.get("Cita programada", 0),
        completed=counts.get("Cerrado con cita", 0) + counts.get("Cerrado sin cita", 0),
        with_future_appointment=int(
            session.scalar(select(func.count(PatientFollowup.id)).where(*filters, PatientFollowup.scheduled_appointment_id.is_not(None)))
            or 0
        ),
        by_reason=[ReportChartItem(label=row[0], value=int(row[1])) for row in by_reason],
        by_site=[ReportChartItem(label=row[0], value=int(row[1])) for row in by_site],
        by_dentist=[ReportChartItem(label=row[0], value=int(row[1])) for row in by_dentist],
    )


def _clinical_report(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID],
    start_utc: datetime,
    end_utc: datetime,
    dentist_id: UUID | None,
) -> ClinicalAggregateReportsResponse:
    procedure_filters = [
        TreatmentProcedure.company_id == context.user.company_id,
        or_(TreatmentProcedure.site_id.is_(None), TreatmentProcedure.site_id.in_(site_ids)),
        TreatmentProcedure.status == "Realizado",
        TreatmentProcedure.performed_at >= start_utc,
        TreatmentProcedure.performed_at < end_utc,
    ]
    if dentist_id:
        procedure_filters.append(TreatmentProcedure.dentist_id == dentist_id)
    evolution_filters = [
        ClinicalEvolution.company_id == context.user.company_id,
        ClinicalEvolution.site_id.in_(site_ids),
        ClinicalEvolution.attended_at >= start_utc,
        ClinicalEvolution.attended_at < end_utc,
    ]
    if dentist_id:
        evolution_filters.append(ClinicalEvolution.dentist_id == dentist_id)
    top = session.execute(
        select(TreatmentProcedure.name, func.count(TreatmentProcedure.id))
        .where(*procedure_filters)
        .group_by(TreatmentProcedure.name)
        .order_by(func.count(TreatmentProcedure.id).desc())
        .limit(8)
    ).all()
    return ClinicalAggregateReportsResponse(
        performed_procedures=int(session.scalar(select(func.count(TreatmentProcedure.id)).where(*procedure_filters)) or 0),
        attended_patients=int(
            session.scalar(
                select(func.count(func.distinct(Appointment.patient_id))).where(
                    Appointment.company_id == context.user.company_id,
                    Appointment.site_id.in_(site_ids),
                    Appointment.status == "Atendida",
                    Appointment.starts_at >= start_utc,
                    Appointment.starts_at < end_utc,
                )
            )
            or 0
        ),
        evolutions_created=int(session.scalar(select(func.count(ClinicalEvolution.id)).where(*evolution_filters)) or 0),
        evolutions_signed=int(session.scalar(select(func.count(ClinicalEvolution.id)).where(*evolution_filters, ClinicalEvolution.status == "SIGNED")) or 0),
        evolutions_draft=int(session.scalar(select(func.count(ClinicalEvolution.id)).where(*evolution_filters, ClinicalEvolution.status == "DRAFT")) or 0),
        clinical_records_opened=int(
            session.scalar(
                select(func.count(ClinicalRecord.id)).where(
                    ClinicalRecord.company_id == context.user.company_id,
                    ClinicalRecord.opened_at >= start_utc,
                    ClinicalRecord.opened_at < end_utc,
                )
            )
            or 0
        ),
        patients_with_critical_alerts=int(
            session.scalar(
                select(func.count(func.distinct(ClinicalAllergy.patient_id))).where(
                    ClinicalAllergy.company_id == context.user.company_id,
                    ClinicalAllergy.critical_alert.is_(True),
                    ClinicalAllergy.status == "confirmada",
                )
            )
            or 0
        ),
        top_procedures=[ReportChartItem(label=row[0], value=int(row[1])) for row in top],
    )


def _action_items(
    session: Session,
    context: AuthContext,
    site_ids: set[UUID],
    start_utc: datetime,
    end_utc: datetime,
    today: date,
    now_utc: datetime,
    dentist_id: UUID | None,
    include_finance: bool,
    include_clinical: bool,
    limit: int,
) -> ActionItemsResponse:
    appointment_filters = _appointment_filters(context, site_ids, start_utc, end_utc, dentist_id)
    pending_rows = session.execute(
        select(Appointment, Patient, Dentist, Site)
        .join(Patient, Patient.id == Appointment.patient_id)
        .join(Dentist, Dentist.id == Appointment.dentist_id)
        .join(Site, Site.id == Appointment.site_id)
        .where(*appointment_filters, Appointment.status == "Programada")
        .order_by(Appointment.starts_at)
        .limit(limit)
    ).all()
    followup_filters = [
        PatientFollowup.company_id == context.user.company_id,
        PatientFollowup.site_id.in_(site_ids),
        PatientFollowup.status.in_(OPEN_FOLLOWUP_STATUSES),
        PatientFollowup.followup_date < today,
    ]
    if dentist_id:
        followup_filters.append(PatientFollowup.dentist_id == dentist_id)
    followup_rows = session.execute(
        select(PatientFollowup, Patient, Dentist, Site)
        .join(Patient, Patient.id == PatientFollowup.patient_id)
        .join(Dentist, Dentist.id == PatientFollowup.dentist_id)
        .join(Site, Site.id == PatientFollowup.site_id)
        .where(*followup_filters)
        .order_by(PatientFollowup.followup_date)
        .limit(limit)
    ).all()

    stale: list[StaleTreatmentItem] = []
    balances = _balances(session, context, site_ids, dentist_id)
    for treatment in session.scalars(
        select(Treatment)
        .where(
            Treatment.company_id == context.user.company_id,
            Treatment.status.in_(ACTIVE_TREATMENT_STATUSES),
            or_(Treatment.main_site_id.is_(None), Treatment.main_site_id.in_(site_ids)),
        )
        .order_by(Treatment.updated_at)
    ):
        last_activity = _treatment_last_activity(session, treatment)
        days = (now_utc - last_activity).days
        if days <= 30:
            continue
        patient = session.get(Patient, treatment.patient_id)
        stale.append(
            StaleTreatmentItem(
                treatment_id=treatment.id,
                patient_id=treatment.patient_id,
                patient_name=_patient_name(patient),
                treatment_name=treatment.name,
                days_without_movement=days,
                balance=balances.get(treatment.id, Decimal("0.00")),
                last_activity_at=last_activity,
            )
        )
        if len(stale) >= limit:
            break

    receivables: list[PatientReceivableItem] = []
    if include_finance:
        latest_budgets = {
            budget.treatment_id: budget
            for budget in _latest_budget_rows(session, context, site_ids, dentist_id)
        }
        for treatment_id, balance in sorted(balances.items(), key=lambda item: item[1], reverse=True):
            treatment = session.get(Treatment, treatment_id)
            budget = latest_budgets.get(treatment_id)
            if not treatment or not budget:
                continue
            patient = session.get(Patient, treatment.patient_id)
            base_date = budget.expires_on or (budget.approved_at.date() if budget.approved_at else today)
            site = session.get(Site, treatment.main_site_id) if treatment.main_site_id else None
            receivables.append(
                PatientReceivableItem(
                    patient_id=treatment.patient_id,
                    patient_name=_patient_name(patient),
                    treatment_id=treatment.id,
                    treatment_name=treatment.name,
                    balance=balance,
                    aging_days=max((today - base_date).days, 0),
                    site_name=site.name if site else None,
                )
            )
            if len(receivables) >= limit:
                break

    drafts: list[ClinicalDraftItem] = []
    if include_clinical:
        draft_filters = [
            ClinicalEvolution.company_id == context.user.company_id,
            ClinicalEvolution.site_id.in_(site_ids),
            ClinicalEvolution.status == "DRAFT",
        ]
        if dentist_id:
            draft_filters.append(ClinicalEvolution.dentist_id == dentist_id)
        for evolution, patient, dentist in session.execute(
            select(ClinicalEvolution, Patient, Dentist)
            .join(Patient, Patient.id == ClinicalEvolution.patient_id)
            .join(Dentist, Dentist.id == ClinicalEvolution.dentist_id)
            .where(*draft_filters)
            .order_by(ClinicalEvolution.attended_at)
            .limit(limit)
        ):
            drafts.append(
                ClinicalDraftItem(
                    evolution_id=evolution.id,
                    patient_id=evolution.patient_id,
                    patient_name=_patient_name(patient),
                    dentist_name=dentist.name,
                    attended_at=evolution.attended_at,
                    days_in_draft=max((now_utc - evolution.attended_at).days, 0),
                )
            )

    return ActionItemsResponse(
        pending_confirmations=[
            PendingConfirmationItem(
                appointment_id=appointment.id,
                patient_id=patient.id,
                patient_name=_patient_name(patient),
                starts_at=appointment.starts_at,
                site_name=site.name,
                dentist_name=dentist.name,
                phone=patient.mobile,
            )
            for appointment, patient, dentist, site in pending_rows
        ],
        overdue_followups=[
            OverdueFollowupItem(
                followup_id=followup.id,
                patient_id=patient.id,
                patient_name=_patient_name(patient),
                reason=followup.reason,
                due_date=followup.followup_date,
                days_overdue=max((today - followup.followup_date).days, 0),
                dentist_name=dentist.name,
                site_name=site.name,
            )
            for followup, patient, dentist, site in followup_rows
        ],
        stale_treatments=stale,
        patient_receivables=receivables,
        clinical_drafts=drafts,
    )


def executive_summary(
    session: Session,
    context: AuthContext,
    metadata: RequestMetadata,
    *,
    preset: str | None,
    date_from: date | None,
    date_to: date | None,
    site_id: UUID | None,
    dentist_id: UUID | None,
    page_size: int = 10,
    audit: bool = True,
) -> ExecutiveSummaryResponse:
    timezone_name = _company_timezone(session, context)
    start_date, end_date, selected_preset = _resolve_dates(
        preset=preset,
        date_from=date_from,
        date_to=date_to,
        timezone_name=timezone_name,
    )
    start_utc, end_utc = _local_bounds(start_date, end_date, timezone_name)
    today = _today_in_timezone(timezone_name)
    today_start, _ = _local_bounds(today, today, timezone_name)
    month_start, _ = _local_bounds(_month_start(today), today, timezone_name)
    now_utc = datetime.now(timezone.utc)
    site_ids = _site_ids(session, context, site_id)
    scoped_dentist_id = _dentist_scope(session, context, dentist_id)
    perms = _permissions(context)

    appointments = patients = treatments = followups = None
    finance = None
    clinical = None
    action_items = None
    metrics: list[ReportMetric] = []

    if perms["operational"]:
        appointments = _appointments_report(session, context, site_ids, start_utc, end_utc, scoped_dentist_id)
        patients = _patients_report(session, context, site_ids, start_utc, end_utc, scoped_dentist_id, today)
        treatments = _treatments_report(session, context, site_ids, now_utc, scoped_dentist_id)
        followups = _followups_report(session, context, site_ids, today, scoped_dentist_id)
        metrics.extend(
            [
                ReportMetric(key="appointments_range", label="Citas del rango", value=appointments.created),
                ReportMetric(key="attended_patients", label="Pacientes atendidos", value=patients.attended_patients),
                ReportMetric(key="pending_confirmations", label="Pendientes de confirmar", value=appointments.by_status[0].value),
                ReportMetric(key="cancelled_no_show", label="Canceladas / No asistió", value=appointments.cancelled + appointments.no_show),
                ReportMetric(key="new_patients", label="Pacientes nuevos", value=patients.new_patients),
                ReportMetric(key="overdue_followups", label="Seguimientos vencidos", value=followups.overdue),
                ReportMetric(key="active_treatments", label="Tratamientos activos", value=treatments.active),
                ReportMetric(key="stale_treatments", label="Tratamientos sin movimiento", value=treatments.without_movement),
            ]
        )

    if perms["financial"]:
        finance = _finance_report(
            session,
            context,
            site_ids,
            start_utc,
            end_utc,
            today_start,
            month_start,
            timezone_name,
            scoped_dentist_id,
        )
        metrics.extend(
            [
                ReportMetric(key="income_today", label="Ingresos del día", value=finance.income_today, unit="money"),
                ReportMetric(key="income_month", label="Ingresos del mes", value=finance.income_month, unit="money"),
                ReportMetric(key="receivables", label="Cartera pendiente", value=finance.receivables_total, unit="money"),
                ReportMetric(key="approved_sales", label="Ventas aprobadas", value=finance.approved_sales_range, unit="money"),
            ]
        )

    if perms["clinical_aggregate"]:
        clinical = _clinical_report(session, context, site_ids, start_utc, end_utc, scoped_dentist_id)

    action_items = _action_items(
        session,
        context,
        site_ids,
        start_utc,
        end_utc,
        today,
        now_utc,
        scoped_dentist_id,
        perms["financial"],
        perms["clinical_aggregate"],
        min(max(page_size, 1), 50),
    )

    filters = {
        "preset": selected_preset,
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "site_id": str(site_id) if site_id else None,
        "dentist_id": str(scoped_dentist_id) if scoped_dentist_id else None,
    }
    if audit:
        _audit_report_view(session, context, metadata, "executive-summary", filters)
    return ExecutiveSummaryResponse(
        generated_at=now_utc,
        timezone=timezone_name,
        date_from=start_date,
        date_to=end_date,
        preset=selected_preset,
        permissions=perms,
        metrics=metrics,
        appointments=appointments,
        patients=patients,
        treatments=treatments,
        finance=finance,
        followups=followups,
        clinical=clinical,
        action_items=action_items,
    )
