from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ReportMetric(BaseModel):
    key: str
    label: str
    value: int | Decimal
    unit: str = "count"
    description: str | None = None


class ReportChartItem(BaseModel):
    label: str
    value: int | Decimal
    secondary_value: int | Decimal | None = None


class AppointmentReportsResponse(BaseModel):
    created: int
    attended: int
    confirmed: int
    cancelled: int
    no_show: int
    overbooked: int
    attendance_rate: Decimal
    cancellation_rate: Decimal
    no_show_rate: Decimal
    by_status: list[ReportChartItem] = Field(default_factory=list)
    by_site: list[ReportChartItem] = Field(default_factory=list)
    by_dentist: list[ReportChartItem] = Field(default_factory=list)


class PatientReportsResponse(BaseModel):
    new_patients: int
    attended_patients: int
    active_patients: int
    with_active_treatment: int
    with_balance: int
    with_overdue_followup: int
    active_definition: str


class TreatmentReportsResponse(BaseModel):
    active: int
    approved: int
    in_progress: int
    paused: int
    finalized: int
    cancelled: int
    with_balance: int
    without_movement: int
    without_next_appointment: int
    average_progress: Decimal
    by_status: list[ReportChartItem] = Field(default_factory=list)


class FinanceReportsResponse(BaseModel):
    income_today: Decimal
    income_month: Decimal
    income_range: Decimal
    clinical_production_range: Decimal
    approved_sales_range: Decimal
    approved_budgets_count: int
    receivables_total: Decimal
    patients_with_balance: int
    income_by_site: list[ReportChartItem] = Field(default_factory=list)
    income_by_dentist: list[ReportChartItem] = Field(default_factory=list)
    income_by_method: list[ReportChartItem] = Field(default_factory=list)
    income_by_month: list[ReportChartItem] = Field(default_factory=list)
    production_by_procedure: list[ReportChartItem] = Field(default_factory=list)
    receivables_aging: list[ReportChartItem] = Field(default_factory=list)


class FollowupReportsResponse(BaseModel):
    open: int
    overdue: int
    scheduled: int
    completed: int
    with_future_appointment: int
    by_reason: list[ReportChartItem] = Field(default_factory=list)
    by_site: list[ReportChartItem] = Field(default_factory=list)
    by_dentist: list[ReportChartItem] = Field(default_factory=list)


class ClinicalAggregateReportsResponse(BaseModel):
    performed_procedures: int
    attended_patients: int
    evolutions_created: int
    evolutions_signed: int
    evolutions_draft: int
    clinical_records_opened: int
    patients_with_critical_alerts: int
    top_procedures: list[ReportChartItem] = Field(default_factory=list)


class PendingConfirmationItem(BaseModel):
    appointment_id: UUID
    patient_id: UUID
    patient_name: str
    starts_at: datetime
    site_name: str
    dentist_name: str
    phone: str


class OverdueFollowupItem(BaseModel):
    followup_id: UUID
    patient_id: UUID
    patient_name: str
    reason: str
    due_date: date
    days_overdue: int
    dentist_name: str
    site_name: str


class StaleTreatmentItem(BaseModel):
    treatment_id: UUID
    patient_id: UUID
    patient_name: str
    treatment_name: str
    days_without_movement: int
    balance: Decimal
    last_activity_at: datetime


class PatientReceivableItem(BaseModel):
    patient_id: UUID
    patient_name: str
    treatment_id: UUID
    treatment_name: str
    balance: Decimal
    aging_days: int
    site_name: str | None = None


class ClinicalDraftItem(BaseModel):
    evolution_id: UUID
    patient_id: UUID
    patient_name: str
    dentist_name: str
    attended_at: datetime
    days_in_draft: int


class ActionItemsResponse(BaseModel):
    pending_confirmations: list[PendingConfirmationItem] = Field(default_factory=list)
    overdue_followups: list[OverdueFollowupItem] = Field(default_factory=list)
    stale_treatments: list[StaleTreatmentItem] = Field(default_factory=list)
    patient_receivables: list[PatientReceivableItem] = Field(default_factory=list)
    clinical_drafts: list[ClinicalDraftItem] = Field(default_factory=list)


class ExecutiveSummaryResponse(BaseModel):
    generated_at: datetime
    timezone: str
    date_from: date
    date_to: date
    preset: str
    permissions: dict[str, bool]
    metrics: list[ReportMetric]
    appointments: AppointmentReportsResponse | None = None
    patients: PatientReportsResponse | None = None
    treatments: TreatmentReportsResponse | None = None
    finance: FinanceReportsResponse | None = None
    followups: FollowupReportsResponse | None = None
    clinical: ClinicalAggregateReportsResponse | None = None
    action_items: ActionItemsResponse | None = None
