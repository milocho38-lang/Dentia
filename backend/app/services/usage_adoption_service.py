from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import case, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.models.agenda import Appointment, AppointmentHistory, Dentist, Patient
from app.models.associations import UserRole
from app.models.audit_event import AuditEvent
from app.models.clinical_record import (
    ClinicalEvolution,
    ClinicalEvolutionAddendum,
    ClinicalRecord,
)
from app.models.company import Company
from app.models.consent_template import ConsentAccessSession, ConsentInstance
from app.models.orthodontics import (
    OrthodonticCase,
    OrthodonticClinicalRecord,
    OrthodonticClinicalRecordVersion,
    OrthodonticEvolution,
    OrthodonticsEntitlement,
)
from app.models.role import Role
from app.models.site import Site
from app.models.treatment import Budget, Treatment, TreatmentPayment, TreatmentProcedure
from app.models.user import User
from app.schemas.usage_adoption_schema import (
    UsageAdministrativeMetrics,
    UsageAdoptionResponse,
    UsageAgendaMetrics,
    UsageClinicalMetrics,
    UsageConsentMetrics,
    UsageContextCompany,
    UsageContextDentist,
    UsageContextResponse,
    UsageContextSite,
    UsageContextUser,
    UsageGeneralMetrics,
    UsageOrthodonticsMetrics,
    UsagePatientMetrics,
    UsagePeriod,
    UsageTreatmentMetrics,
    UsageUnsupportedMetric,
    UsageWeeklyTrendItem,
)


METRIC_CATALOG_VERSION = "USAGE_1_V1"
MAX_RANGE_DAYS = 366
FUNCTIONAL_AUDIT_ACTIONS = frozenset(
    {
        "APPOINTMENT_CREATED",
        "APPOINTMENT_CONFIRMED",
        "APPOINTMENT_RESCHEDULED",
        "APPOINTMENT_CANCELLED",
        "APPOINTMENT_COMPLETED",
        "PATIENT_CREATED",
        "PATIENT_QUICK_CREATED",
        "PATIENT_UPDATED",
        "CLINICAL_RECORD_CREATED",
        "CLINICAL_RECORD_UPDATED",
        "CLINICAL_EVOLUTION_CREATED",
        "CLINICAL_EVOLUTION_DRAFT_UPDATED",
        "CLINICAL_EVOLUTION_SIGNED",
        "CLINICAL_EVOLUTION_ADDENDUM_CREATED",
        "TREATMENT_CREATED",
        "TREATMENT_CREATED_FROM_ODONTOGRAM",
        "TREATMENT_UPDATED",
        "TREATMENT_CLOSED",
        "PROCEDURE_CREATED",
        "TREATMENT_PROCEDURE_CREATED",
        "PROCEDURE_MARKED_DONE",
        "BUDGET_CREATED_FROM_TREATMENT_PROCEDURES",
        "BUDGET_VERSION_CREATED",
        "BUDGET_APPROVED",
        "CONSENT_INSTANCE_CREATED",
        "CONSENT_ACCESS_SESSION_ISSUED",
        "CONSENT_ACCESS_SESSION_REISSUED",
        "CONSENT_PAPER_FINALIZED",
        "ORTHODONTIC_CASE_CREATED",
        "ORTHODONTIC_EVOLUTION_CREATED",
        "ORTHODONTIC_EVOLUTION_SIGNED",
        "ORTHODONTIC_RECORD_FINALIZED",
        "PAYMENT_REGISTERED",
        "PAYMENT_REVERSED",
    }
)


class UsageAdoptionError(ValueError):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def get_usage_context(
    session: Session,
    *,
    company_id: UUID | None = None,
) -> UsageContextResponse:
    """Return only the selector data required by the Platform usage dashboard."""

    companies = list(session.scalars(select(Company).order_by(Company.name)))
    if not companies:
        return UsageContextResponse()

    company_ids = [company.id for company in companies]
    if company_id is not None and company_id not in company_ids:
        raise UsageAdoptionError("Empresa no encontrada.", 404)
    detail_company_ids = [company_id] if company_id is not None else []
    sites_by_company: dict[UUID, list[UsageContextSite]] = {
        selected_id: [] for selected_id in detail_company_ids
    }
    if detail_company_ids:
        for site in session.scalars(
            select(Site)
            .where(Site.company_id.in_(detail_company_ids))
            .order_by(Site.name)
        ):
            sites_by_company[site.company_id].append(
                UsageContextSite(
                    id=site.id,
                    name=site.name,
                    status=site.status,
                    is_active=site.is_active,
                )
            )

    users = list(
        session.scalars(
            select(User)
            .where(User.company_id.in_(detail_company_ids))
            .order_by(User.name)
        )
    ) if detail_company_ids else []
    user_ids = [user.id for user in users]
    roles_by_user: dict[UUID, list[str]] = {user_id: [] for user_id in user_ids}
    dentists_by_user: dict[UUID, UsageContextDentist] = {}
    active_user_ids: set[UUID] = set()
    if user_ids:
        for user_id, role_name in session.execute(
            select(UserRole.user_id, Role.name)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id.in_(user_ids),
                UserRole.is_active.is_(True),
                Role.is_active.is_(True),
            )
            .order_by(Role.name)
        ):
            roles_by_user[user_id].append(role_name)
        for dentist in session.scalars(
            select(Dentist).where(
                Dentist.company_id.in_(detail_company_ids),
                Dentist.user_id.in_(user_ids),
            )
        ):
            if dentist.user_id is not None:
                dentists_by_user[dentist.user_id] = UsageContextDentist(
                    id=dentist.id,
                    name=dentist.name,
                    status=dentist.status,
                    is_active=dentist.is_active,
                )
        active_user_ids = set(
            session.scalars(
                select(AuditEvent.user_id)
                .where(
                    AuditEvent.company_id.in_(detail_company_ids),
                    AuditEvent.user_id.in_(user_ids),
                    AuditEvent.result == "SUCCESS",
                    AuditEvent.action.in_(FUNCTIONAL_AUDIT_ACTIONS),
                )
                .distinct()
            )
        )

    users_by_company: dict[UUID, list[UsageContextUser]] = {
        selected_id: [] for selected_id in detail_company_ids
    }
    for user in users:
        users_by_company[user.company_id].append(
            UsageContextUser(
                id=user.id,
                name=user.name,
                status=user.status,
                is_active=user.is_active,
                role_names=roles_by_user[user.id],
                dentist=dentists_by_user.get(user.id),
                has_attributed_activity=user.id in active_user_ids,
            )
        )
    for company_users in users_by_company.values():
        company_users.sort(
            key=lambda user: (
                not bool(user.dentist and user.dentist.is_active),
                not bool(user.is_active and user.has_attributed_activity),
                not user.is_active,
                user.name.casefold(),
            )
        )

    return UsageContextResponse(
        companies=[
            UsageContextCompany(
                id=company.id,
                name=company.name,
                status=company.status,
                is_active=company.is_active,
                timezone=company.timezone or "America/Bogota",
                sites=sites_by_company.get(company.id, []),
                users=users_by_company.get(company.id, []),
            )
            for company in companies
        ]
    )


def _orthodontics_enabled(session: Session, company_id: UUID) -> bool:
    entitlement = session.scalar(
        select(OrthodonticsEntitlement).where(
            OrthodonticsEntitlement.company_id == company_id
        )
    )
    if entitlement is None or entitlement.status != "ACTIVE":
        return False
    now = datetime.now(timezone.utc)
    if entitlement.effective_from and entitlement.effective_from > now:
        return False
    if entitlement.effective_until and entitlement.effective_until < now:
        return False
    return True


def resolve_usage_dates(
    *,
    start_date: date | None,
    end_date: date | None,
    preset: str | None,
    today: date | None = None,
) -> tuple[date, date, str | None]:
    current = today or datetime.now(timezone.utc).date()
    normalized = preset.lower() if preset else None
    if normalized == "last_7_days":
        return current - timedelta(days=6), current, normalized
    if normalized == "last_30_days":
        return current - timedelta(days=29), current, normalized
    if normalized == "pilot_to_date":
        if start_date is None:
            raise UsageAdoptionError(
                "pilot_to_date requiere una fecha de inicio explícita mientras no exista pilot_started_at."
            )
        return start_date, end_date or current, normalized
    if normalized is not None:
        raise UsageAdoptionError("Preset de periodo no soportado.")
    if start_date is None or end_date is None:
        raise UsageAdoptionError("start_date y end_date son obligatorios.")
    return start_date, end_date, None


def _period(
    company: Company,
    start_date: date,
    end_date: date,
    preset: str | None,
) -> UsagePeriod:
    if end_date < start_date:
        raise UsageAdoptionError("end_date no puede ser anterior a start_date.")
    if (end_date - start_date).days + 1 > MAX_RANGE_DAYS:
        raise UsageAdoptionError("El periodo máximo permitido es de 366 días.")
    try:
        local_zone = ZoneInfo(company.timezone or "America/Bogota")
    except ZoneInfoNotFoundError as exc:
        raise UsageAdoptionError("La zona horaria de la empresa no es válida.") from exc
    start_at = datetime.combine(start_date, time.min, tzinfo=local_zone).astimezone(
        timezone.utc
    )
    end_at = datetime.combine(
        end_date + timedelta(days=1), time.min, tzinfo=local_zone
    ).astimezone(timezone.utc)
    return UsagePeriod(
        start_date=start_date,
        end_date=end_date,
        start_at=start_at,
        end_at=end_at,
        timezone=company.timezone or "America/Bogota",
        preset=preset,
    )


def _between(column, period: UsagePeriod):
    return (column >= period.start_at) & (column < period.end_at)


def _site(column, site_id: UUID | None):
    return literal(True) if site_id is None else column == site_id


def _count_distinct_patients(session: Session, *statements) -> int:
    activity = union_all(*statements).subquery()
    return int(
        session.scalar(select(func.count(func.distinct(activity.c.patient_id)))) or 0
    )


def _weekly_trend(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
    site_id: UUID | None,
    period: UsagePeriod,
) -> list[UsageWeeklyTrendItem]:
    events = []

    def event(metric: str, timestamp, patient_id, *conditions):
        events.append(
            select(
                literal(metric).label("metric"),
                timestamp.label("occurred_at"),
                patient_id.label("patient_id"),
            ).where(*conditions)
        )

    event(
        "appointments",
        Appointment.created_at,
        Appointment.patient_id,
        Appointment.company_id == company_id,
        Appointment.created_by == user_id,
        _between(Appointment.created_at, period),
        _site(Appointment.site_id, site_id),
    )
    event(
        "appointments",
        AppointmentHistory.created_at,
        Appointment.patient_id,
        AppointmentHistory.company_id == company_id,
        AppointmentHistory.user_id == user_id,
        AppointmentHistory.new_status.in_(
            ("Confirmada", "Reprogramada", "Atendida", "Cancelada")
        ),
        _between(AppointmentHistory.created_at, period),
        Appointment.id == AppointmentHistory.appointment_id,
        _site(Appointment.site_id, site_id),
    )
    event(
        "evolutions_signed",
        ClinicalEvolution.signed_at,
        ClinicalEvolution.patient_id,
        ClinicalEvolution.company_id == company_id,
        ClinicalEvolution.signed_by == user_id,
        ClinicalEvolution.signed_at.is_not(None),
        _between(ClinicalEvolution.signed_at, period),
        _site(ClinicalEvolution.site_id, site_id),
    )
    event(
        "treatments_created",
        Treatment.created_at,
        Treatment.patient_id,
        Treatment.company_id == company_id,
        Treatment.created_by == user_id,
        _between(Treatment.created_at, period),
        _site(Treatment.main_site_id, site_id),
    )
    event(
        "consents_created",
        ConsentInstance.created_at,
        ConsentInstance.patient_id,
        ConsentInstance.company_id == company_id,
        ConsentInstance.created_by == user_id,
        _between(ConsentInstance.created_at, period),
        _site(ConsentInstance.site_id, site_id),
    )
    event(
        "orthodontics",
        OrthodonticCase.created_at,
        OrthodonticCase.patient_id,
        OrthodonticCase.company_id == company_id,
        OrthodonticCase.created_by_user_id == user_id,
        _between(OrthodonticCase.created_at, period),
        _site(OrthodonticCase.primary_site_id, site_id),
    )
    events.append(
        select(
            literal("orthodontics").label("metric"),
            ClinicalEvolution.created_at.label("occurred_at"),
            ClinicalEvolution.patient_id.label("patient_id"),
        )
        .select_from(OrthodonticEvolution)
        .join(
            ClinicalEvolution,
            ClinicalEvolution.id == OrthodonticEvolution.clinical_evolution_id,
        )
        .where(
            OrthodonticEvolution.company_id == company_id,
            ClinicalEvolution.created_by == user_id,
            _between(ClinicalEvolution.created_at, period),
            _site(ClinicalEvolution.site_id, site_id),
        )
    )
    events.append(
        select(
            literal("orthodontics").label("metric"),
            ClinicalEvolution.signed_at.label("occurred_at"),
            ClinicalEvolution.patient_id.label("patient_id"),
        )
        .select_from(OrthodonticEvolution)
        .join(
            ClinicalEvolution,
            ClinicalEvolution.id == OrthodonticEvolution.clinical_evolution_id,
        )
        .where(
            OrthodonticEvolution.company_id == company_id,
            ClinicalEvolution.signed_by == user_id,
            ClinicalEvolution.signed_at.is_not(None),
            _between(ClinicalEvolution.signed_at, period),
            _site(ClinicalEvolution.site_id, site_id),
        )
    )
    events.append(
        select(
            literal("orthodontics").label("metric"),
            OrthodonticClinicalRecordVersion.finalized_at.label("occurred_at"),
            OrthodonticClinicalRecord.patient_id.label("patient_id"),
        )
        .select_from(OrthodonticClinicalRecordVersion)
        .join(
            OrthodonticClinicalRecord,
            OrthodonticClinicalRecord.id == OrthodonticClinicalRecordVersion.record_id,
        )
        .join(
            OrthodonticCase,
            OrthodonticCase.id == OrthodonticClinicalRecord.orthodontic_case_id,
        )
        .where(
            OrthodonticClinicalRecordVersion.company_id == company_id,
            OrthodonticClinicalRecordVersion.status == "FINALIZED",
            OrthodonticClinicalRecordVersion.finalized_by_user_id == user_id,
            OrthodonticClinicalRecordVersion.finalized_at.is_not(None),
            _between(OrthodonticClinicalRecordVersion.finalized_at, period),
            _site(OrthodonticCase.primary_site_id, site_id),
        )
    )
    trend_events = union_all(*events).subquery()
    week = func.date_trunc(
        "week", func.timezone(period.timezone, trend_events.c.occurred_at)
    ).label("week")
    rows = session.execute(
        select(
            week,
            func.sum(case((trend_events.c.metric == "appointments", 1), else_=0)),
            func.count(func.distinct(trend_events.c.patient_id)),
            func.sum(case((trend_events.c.metric == "evolutions_signed", 1), else_=0)),
            func.sum(case((trend_events.c.metric == "treatments_created", 1), else_=0)),
            func.sum(case((trend_events.c.metric == "consents_created", 1), else_=0)),
            func.sum(case((trend_events.c.metric == "orthodontics", 1), else_=0)),
        )
        .group_by(week)
        .order_by(week)
    ).all()
    by_week = {
        row[0].date(): tuple(int(value or 0) for value in row[1:]) for row in rows
    }
    cursor = period.start_date - timedelta(days=period.start_date.weekday())
    final_week = period.end_date - timedelta(days=period.end_date.weekday())
    result: list[UsageWeeklyTrendItem] = []
    while cursor <= final_week:
        values = by_week.get(cursor, (0, 0, 0, 0, 0, 0))
        result.append(
            UsageWeeklyTrendItem(
                week_start=cursor,
                appointments_activity=values[0],
                unique_patients=values[1],
                evolutions_signed=values[2],
                treatments_created=values[3],
                consents_created=values[4],
                orthodontic_activity=values[5],
            )
        )
        cursor += timedelta(days=7)
    return result


def get_user_usage_adoption(
    session: Session,
    *,
    company_id: UUID,
    user_id: UUID,
    start_date: date | None,
    end_date: date | None,
    dentist_id: UUID | None = None,
    site_id: UUID | None = None,
    preset: str | None = None,
    today: date | None = None,
) -> UsageAdoptionResponse:
    company = session.get(Company, company_id)
    if company is None:
        raise UsageAdoptionError("Empresa no encontrada.", 404)
    user = session.scalar(
        select(User).where(User.id == user_id, User.company_id == company_id)
    )
    if user is None:
        raise UsageAdoptionError("El usuario no pertenece a la empresa indicada.", 404)
    if site_id is not None and session.scalar(
        select(Site.id).where(Site.id == site_id, Site.company_id == company_id)
    ) is None:
        raise UsageAdoptionError("La sede no pertenece a la empresa indicada.", 404)
    dentist = None
    if dentist_id is not None:
        dentist = session.scalar(
            select(Dentist).where(
                Dentist.id == dentist_id,
                Dentist.company_id == company_id,
                Dentist.user_id == user_id,
            )
        )
        if dentist is None:
            raise UsageAdoptionError(
                "El perfil odontológico no corresponde al usuario y empresa indicados.",
                404,
            )
    else:
        dentist = session.scalar(
            select(Dentist).where(
                Dentist.company_id == company_id, Dentist.user_id == user_id
            )
        )
    resolved_start, resolved_end, resolved_preset = resolve_usage_dates(
        start_date=start_date,
        end_date=end_date,
        preset=preset,
        today=today,
    )
    period = _period(company, resolved_start, resolved_end, resolved_preset)

    functional = AuditEvent.action.in_(FUNCTIONAL_AUDIT_ACTIONS)
    general_row = session.execute(
        select(
            func.min(AuditEvent.occurred_at).filter(
                AuditEvent.action == "LOGIN_SUCCESS"
            ),
            func.min(AuditEvent.occurred_at).filter(functional),
            func.max(AuditEvent.occurred_at).filter(functional),
            func.count(
                func.distinct(
                    func.date(func.timezone(period.timezone, AuditEvent.occurred_at))
                )
            ).filter(functional),
        ).where(
            AuditEvent.company_id == company_id,
            AuditEvent.user_id == user_id,
            AuditEvent.result == "SUCCESS",
            _between(AuditEvent.occurred_at, period),
        )
    ).one()
    general = UsageGeneralMetrics(
        last_login_at=user.last_login_at,
        first_login_at=general_row[0],
        first_activity_at=general_row[1],
        last_activity_at=general_row[2],
        active_days=int(general_row[3] or 0),
    )

    appointment_created = session.execute(
        select(func.count(Appointment.id)).where(
            Appointment.company_id == company_id,
            Appointment.created_by == user_id,
            _between(Appointment.created_at, period),
            _site(Appointment.site_id, site_id),
        )
    ).scalar_one()
    appointment_history = session.execute(
        select(
            func.count().filter(AppointmentHistory.new_status == "Confirmada"),
            func.count().filter(AppointmentHistory.new_status == "Reprogramada"),
            func.count().filter(AppointmentHistory.new_status == "Atendida"),
            func.count().filter(AppointmentHistory.new_status == "Cancelada"),
        )
        .join(Appointment, Appointment.id == AppointmentHistory.appointment_id)
        .where(
            AppointmentHistory.company_id == company_id,
            AppointmentHistory.user_id == user_id,
            _between(AppointmentHistory.created_at, period),
            _site(Appointment.site_id, site_id),
        )
    ).one()
    appointment_activity = union_all(
        select(
            Appointment.patient_id.label("patient_id"),
            Appointment.created_at.label("occurred_at"),
        ).where(
            Appointment.company_id == company_id,
            Appointment.created_by == user_id,
            _between(Appointment.created_at, period),
            _site(Appointment.site_id, site_id),
        ),
        select(
            Appointment.patient_id.label("patient_id"),
            AppointmentHistory.created_at.label("occurred_at"),
        )
        .join(Appointment, Appointment.id == AppointmentHistory.appointment_id)
        .where(
            AppointmentHistory.company_id == company_id,
            AppointmentHistory.user_id == user_id,
            AppointmentHistory.new_status.in_(
                ("Confirmada", "Reprogramada", "Atendida", "Cancelada")
            ),
            _between(AppointmentHistory.created_at, period),
            _site(Appointment.site_id, site_id),
        ),
    ).subquery()
    appointment_rollup = session.execute(
        select(
            func.count(func.distinct(appointment_activity.c.patient_id)),
            func.count(
                func.distinct(
                    func.date(
                        func.timezone(period.timezone, appointment_activity.c.occurred_at)
                    )
                )
            ),
        )
    ).one()
    agenda = UsageAgendaMetrics(
        appointments_created=int(appointment_created or 0),
        appointments_confirmed_by_actor=int(appointment_history[0] or 0),
        appointments_rescheduled_by_actor=int(appointment_history[1] or 0),
        appointments_completed_by_actor=int(appointment_history[2] or 0),
        appointments_cancelled_by_actor=int(appointment_history[3] or 0),
        unique_patients_with_appointment_activity=int(appointment_rollup[0] or 0),
        appointment_active_days=int(appointment_rollup[1] or 0),
    )

    patients_created = int(
        session.scalar(
            select(func.count(Patient.id)).where(
                Patient.company_id == company_id,
                Patient.created_by == user_id,
                _between(Patient.created_at, period),
            )
        )
        or 0
    )

    clinical_row = session.execute(
        select(
            func.count(ClinicalEvolution.id).filter(
                ClinicalEvolution.created_by == user_id,
                _between(ClinicalEvolution.created_at, period),
            ),
            func.count(ClinicalEvolution.id).filter(
                ClinicalEvolution.signed_by == user_id,
                ClinicalEvolution.signed_at.is_not(None),
                _between(ClinicalEvolution.signed_at, period),
            ),
            func.count(ClinicalEvolution.id).filter(
                ClinicalEvolution.created_by == user_id,
                ClinicalEvolution.status == "DRAFT",
                _between(ClinicalEvolution.created_at, period),
            ),
        ).where(
            ClinicalEvolution.company_id == company_id,
            _site(ClinicalEvolution.site_id, site_id),
        )
    ).one()
    records_opened = int(
        session.scalar(
            select(func.count(ClinicalRecord.id)).where(
                ClinicalRecord.company_id == company_id,
                ClinicalRecord.created_by == user_id,
                _between(ClinicalRecord.created_at, period),
                _site(ClinicalRecord.opening_site_id, site_id),
            )
        )
        or 0
    )
    addenda_created = int(
        session.scalar(
            select(func.count(ClinicalEvolutionAddendum.id)).where(
                ClinicalEvolutionAddendum.company_id == company_id,
                ClinicalEvolutionAddendum.created_by == user_id,
                _between(ClinicalEvolutionAddendum.created_at, period),
                _site(ClinicalEvolutionAddendum.site_id, site_id),
            )
        )
        or 0
    )
    clinical_patient_selects = (
        select(ClinicalEvolution.patient_id.label("patient_id")).where(
            ClinicalEvolution.company_id == company_id,
            ClinicalEvolution.created_by == user_id,
            _between(ClinicalEvolution.created_at, period),
            _site(ClinicalEvolution.site_id, site_id),
        ),
        select(ClinicalEvolution.patient_id.label("patient_id")).where(
            ClinicalEvolution.company_id == company_id,
            ClinicalEvolution.signed_by == user_id,
            ClinicalEvolution.signed_at.is_not(None),
            _between(ClinicalEvolution.signed_at, period),
            _site(ClinicalEvolution.site_id, site_id),
        ),
        select(ClinicalEvolutionAddendum.patient_id.label("patient_id")).where(
            ClinicalEvolutionAddendum.company_id == company_id,
            ClinicalEvolutionAddendum.created_by == user_id,
            _between(ClinicalEvolutionAddendum.created_at, period),
            _site(ClinicalEvolutionAddendum.site_id, site_id),
        ),
    )
    unique_clinical = _count_distinct_patients(session, *clinical_patient_selects)
    clinical = UsageClinicalMetrics(
        clinical_records_opened=records_opened,
        clinical_evolutions_created=int(clinical_row[0] or 0),
        clinical_evolutions_signed=int(clinical_row[1] or 0),
        current_drafts_created_in_period=int(clinical_row[2] or 0),
        addenda_created=addenda_created,
        unique_patients_with_clinical_activity=unique_clinical,
    )

    treatments_created = int(
        session.scalar(
            select(func.count(Treatment.id)).where(
                Treatment.company_id == company_id,
                Treatment.created_by == user_id,
                _between(Treatment.created_at, period),
                _site(Treatment.main_site_id, site_id),
            )
        )
        or 0
    )
    procedures_registered = int(
        session.scalar(
            select(func.count(TreatmentProcedure.id)).where(
                TreatmentProcedure.company_id == company_id,
                TreatmentProcedure.created_by == user_id,
                _between(TreatmentProcedure.created_at, period),
                _site(TreatmentProcedure.site_id, site_id),
            )
        )
        or 0
    )
    budget_row = session.execute(
        select(
            func.count(Budget.id).filter(
                Budget.created_by == user_id,
                Budget.version == 1,
                _between(Budget.created_at, period),
            ),
            func.count(Budget.id).filter(
                Budget.created_by == user_id,
                _between(Budget.created_at, period),
            ),
            func.count(Budget.id).filter(
                Budget.approved_by == user_id,
                Budget.approved_at.is_not(None),
                _between(Budget.approved_at, period),
            ),
        )
        .join(Treatment, Treatment.id == Budget.treatment_id)
        .where(
            Budget.company_id == company_id,
            _site(Treatment.main_site_id, site_id),
        )
    ).one()
    treatments_completed = int(
        session.scalar(
            select(func.count(func.distinct(AuditEvent.entity_id)))
            .join(Treatment, Treatment.id == AuditEvent.entity_id)
            .where(
                AuditEvent.company_id == company_id,
                AuditEvent.user_id == user_id,
                AuditEvent.action == "TREATMENT_CLOSED",
                AuditEvent.result == "SUCCESS",
                _between(AuditEvent.occurred_at, period),
                _site(Treatment.main_site_id, site_id),
            )
        )
        or 0
    )
    treatment_patient_selects = (
        select(Treatment.patient_id.label("patient_id")).where(
            Treatment.company_id == company_id,
            Treatment.created_by == user_id,
            _between(Treatment.created_at, period),
            _site(Treatment.main_site_id, site_id),
        ),
        select(TreatmentProcedure.patient_id.label("patient_id")).where(
            TreatmentProcedure.company_id == company_id,
            TreatmentProcedure.created_by == user_id,
            _between(TreatmentProcedure.created_at, period),
            _site(TreatmentProcedure.site_id, site_id),
        ),
        select(Budget.patient_id.label("patient_id"))
        .join(Treatment, Treatment.id == Budget.treatment_id)
        .where(
            Budget.company_id == company_id,
            Budget.created_by == user_id,
            _between(Budget.created_at, period),
            _site(Treatment.main_site_id, site_id),
        ),
    )
    unique_treatment = _count_distinct_patients(session, *treatment_patient_selects)
    treatments = UsageTreatmentMetrics(
        treatments_created=treatments_created,
        treatment_procedures_registered=procedures_registered,
        treatments_completed_by_actor=treatments_completed,
        budgets_created=int(budget_row[0] or 0),
        budget_versions_created=int(budget_row[1] or 0),
        budgets_accepted_by_actor=int(budget_row[2] or 0),
        unique_patients_with_treatment_activity=unique_treatment,
    )

    consent_row = session.execute(
        select(
            func.count(ConsentInstance.id).filter(
                ConsentInstance.created_by == user_id,
                _between(ConsentInstance.created_at, period),
            ),
            func.count(ConsentInstance.id).filter(
                ConsentInstance.created_by == user_id,
                ConsentInstance.status == "SIGNED",
                ConsentInstance.signed_at.is_not(None),
                _between(ConsentInstance.signed_at, period),
            ),
            func.count(ConsentInstance.id).filter(
                ConsentInstance.created_by == user_id,
                _between(ConsentInstance.created_at, period),
                ConsentInstance.status.in_(
                    ("DRAFT", "READY_FOR_REVIEW", "PENDING_SIGNATURE")
                )
            ),
        ).where(
            ConsentInstance.company_id == company_id,
            _site(ConsentInstance.site_id, site_id),
        )
    ).one()
    consents_shared = int(
        session.scalar(
            select(func.count(ConsentAccessSession.id)).where(
                ConsentAccessSession.company_id == company_id,
                ConsentAccessSession.created_by == user_id,
                _between(ConsentAccessSession.created_at, period),
                _site(ConsentAccessSession.site_id, site_id),
            )
        )
        or 0
    )
    consent_patient_selects = (
        select(ConsentInstance.patient_id.label("patient_id")).where(
            ConsentInstance.company_id == company_id,
            ConsentInstance.created_by == user_id,
            _between(ConsentInstance.created_at, period),
            _site(ConsentInstance.site_id, site_id),
        ),
    )
    unique_consent = _count_distinct_patients(session, *consent_patient_selects)
    consents = UsageConsentMetrics(
        consents_created=int(consent_row[0] or 0),
        consents_accepted=int(consent_row[1] or 0),
        consents_pending=int(consent_row[2] or 0),
        consents_shared=consents_shared,
        unique_patients_with_consent_activity=unique_consent,
    )

    orthodontic_cases_created = int(
        session.scalar(
            select(func.count(OrthodonticCase.id)).where(
                OrthodonticCase.company_id == company_id,
                OrthodonticCase.created_by_user_id == user_id,
                _between(OrthodonticCase.created_at, period),
                _site(OrthodonticCase.primary_site_id, site_id),
            )
        )
        or 0
    )
    orthodontic_cases_active = 0
    if dentist is not None:
        orthodontic_cases_active = int(
            session.scalar(
                select(func.count(OrthodonticCase.id)).where(
                    OrthodonticCase.company_id == company_id,
                    OrthodonticCase.responsible_dentist_id == dentist.id,
                    OrthodonticCase.status == "ACTIVE",
                    _site(OrthodonticCase.primary_site_id, site_id),
                )
            )
            or 0
        )
    ortho_evolution = session.execute(
        select(
            func.count(OrthodonticEvolution.id).filter(
                ClinicalEvolution.created_by == user_id,
                _between(ClinicalEvolution.created_at, period),
            ),
            func.count(OrthodonticEvolution.id).filter(
                ClinicalEvolution.signed_by == user_id,
                ClinicalEvolution.signed_at.is_not(None),
                _between(ClinicalEvolution.signed_at, period),
            ),
        )
        .select_from(OrthodonticEvolution)
        .join(
            ClinicalEvolution,
            ClinicalEvolution.id == OrthodonticEvolution.clinical_evolution_id,
        )
        .where(
            OrthodonticEvolution.company_id == company_id,
            _site(ClinicalEvolution.site_id, site_id),
        )
    ).one()
    records_finalized = int(
        session.scalar(
            select(func.count(OrthodonticClinicalRecordVersion.id))
            .join(
                OrthodonticClinicalRecord,
                OrthodonticClinicalRecord.id
                == OrthodonticClinicalRecordVersion.record_id,
            )
            .join(
                OrthodonticCase,
                OrthodonticCase.id == OrthodonticClinicalRecord.orthodontic_case_id,
            )
            .where(
                OrthodonticClinicalRecordVersion.company_id == company_id,
                OrthodonticClinicalRecordVersion.status == "FINALIZED",
                OrthodonticClinicalRecordVersion.finalized_by_user_id == user_id,
                OrthodonticClinicalRecordVersion.finalized_at.is_not(None),
                _between(OrthodonticClinicalRecordVersion.finalized_at, period),
                _site(OrthodonticCase.primary_site_id, site_id),
            )
        )
        or 0
    )
    orthodontic_patient_selects = (
        select(OrthodonticCase.patient_id.label("patient_id")).where(
            OrthodonticCase.company_id == company_id,
            OrthodonticCase.created_by_user_id == user_id,
            _between(OrthodonticCase.created_at, period),
            _site(OrthodonticCase.primary_site_id, site_id),
        ),
        select(ClinicalEvolution.patient_id.label("patient_id"))
        .join(
            OrthodonticEvolution,
            OrthodonticEvolution.clinical_evolution_id == ClinicalEvolution.id,
        )
        .where(
            OrthodonticEvolution.company_id == company_id,
            ClinicalEvolution.created_by == user_id,
            _between(ClinicalEvolution.created_at, period),
            _site(ClinicalEvolution.site_id, site_id),
        ),
    )
    unique_ortho = _count_distinct_patients(session, *orthodontic_patient_selects)
    orthodontics = UsageOrthodonticsMetrics(
        orthodontic_cases_created=orthodontic_cases_created,
        orthodontic_cases_active=orthodontic_cases_active,
        orthodontic_evolutions_created=int(ortho_evolution[0] or 0),
        orthodontic_evolutions_signed=int(ortho_evolution[1] or 0),
        orthodontic_records_finalized=records_finalized,
        unique_patients_with_orthodontic_activity=unique_ortho,
    )

    payment_row = session.execute(
        select(
            func.count(TreatmentPayment.id).filter(
                TreatmentPayment.registered_by == user_id,
                _between(TreatmentPayment.paid_at, period),
            ),
            func.count(TreatmentPayment.id).filter(
                TreatmentPayment.reversed_by == user_id,
                TreatmentPayment.reversed_at.is_not(None),
                _between(TreatmentPayment.reversed_at, period),
            ),
        ).where(
            TreatmentPayment.company_id == company_id,
            _site(TreatmentPayment.site_id, site_id),
        )
    ).one()
    administrative = UsageAdministrativeMetrics(
        payments_registered=int(payment_row[0] or 0),
        payments_reversed=int(payment_row[1] or 0),
    )

    overall_unique = _count_distinct_patients(
        session,
        select(appointment_activity.c.patient_id.label("patient_id")),
        *clinical_patient_selects,
        *treatment_patient_selects,
        *consent_patient_selects,
        *orthodontic_patient_selects,
    )
    patients = UsagePatientMetrics(
        patients_created_by_actor=patients_created,
        unique_patients_with_actor_activity=overall_unique,
    )

    return UsageAdoptionResponse(
        metric_catalog_version=METRIC_CATALOG_VERSION,
        company_id=company_id,
        user_id=user_id,
        dentist_id=dentist.id if dentist else None,
        site_id=site_id,
        orthodontics_enabled=_orthodontics_enabled(session, company_id),
        period=period,
        general=general,
        agenda=agenda,
        patients=patients,
        clinical=clinical,
        treatments=treatments,
        consents=consents,
        orthodontics=orthodontics,
        administrative_activity=administrative,
        weekly_trend=_weekly_trend(
            session,
            company_id=company_id,
            user_id=user_id,
            site_id=site_id,
            period=period,
        ),
        unsupported_metrics=[
            UsageUnsupportedMetric(
                code="patients_viewed",
                reason="No existe un evento general fiable de apertura de paciente.",
            ),
            UsageUnsupportedMetric(
                code="session_duration",
                reason="last_seen_at no reconstruye duración real de uso.",
            ),
            UsageUnsupportedMetric(
                code="cash_closures",
                reason="No existe una fuente transaccional canónica con actor para cierres de caja.",
            ),
        ],
    )
