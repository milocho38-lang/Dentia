from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UsagePeriod(BaseModel):
    start_date: date
    end_date: date
    start_at: datetime
    end_at: datetime
    timezone: str
    preset: str | None = None


class UsageGeneralMetrics(BaseModel):
    last_login_at: datetime | None = None
    first_login_at: datetime | None = None
    first_activity_at: datetime | None = None
    last_activity_at: datetime | None = None
    active_days: int = 0


class UsageAgendaMetrics(BaseModel):
    appointments_created: int = 0
    appointments_confirmed_by_actor: int = 0
    appointments_rescheduled_by_actor: int = 0
    appointments_completed_by_actor: int = 0
    appointments_cancelled_by_actor: int = 0
    appointment_active_days: int = 0
    unique_patients_with_appointment_activity: int = 0


class UsagePatientMetrics(BaseModel):
    patients_created_by_actor: int = 0
    unique_patients_with_actor_activity: int = 0


class UsageClinicalMetrics(BaseModel):
    clinical_records_opened: int = 0
    clinical_evolutions_created: int = 0
    clinical_evolutions_signed: int = 0
    addenda_created: int = 0
    current_drafts_created_in_period: int = 0
    unique_patients_with_clinical_activity: int = 0


class UsageTreatmentMetrics(BaseModel):
    treatments_created: int = 0
    treatment_procedures_registered: int = 0
    treatments_completed_by_actor: int = 0
    budgets_created: int = 0
    budget_versions_created: int = 0
    budgets_accepted_by_actor: int = 0
    unique_patients_with_treatment_activity: int = 0


class UsageConsentMetrics(BaseModel):
    consents_created: int = 0
    consents_shared: int = 0
    consents_accepted: int = 0
    consents_pending: int = 0
    unique_patients_with_consent_activity: int = 0


class UsageOrthodonticsMetrics(BaseModel):
    orthodontic_cases_created: int = 0
    orthodontic_cases_active: int = 0
    orthodontic_evolutions_created: int = 0
    orthodontic_evolutions_signed: int = 0
    orthodontic_records_finalized: int = 0
    unique_patients_with_orthodontic_activity: int = 0


class UsageAdministrativeMetrics(BaseModel):
    payments_registered: int = 0
    payments_reversed: int = 0


class UsageWeeklyTrendItem(BaseModel):
    week_start: date
    appointments_activity: int = 0
    unique_patients: int = 0
    evolutions_signed: int = 0
    treatments_created: int = 0
    consents_created: int = 0
    orthodontic_activity: int = 0


class UsageUnsupportedMetric(BaseModel):
    code: str
    reason: str


class UsageContextSite(BaseModel):
    id: UUID
    name: str
    status: str
    is_active: bool


class UsageContextDentist(BaseModel):
    id: UUID
    name: str
    status: str
    is_active: bool


class UsageContextUser(BaseModel):
    id: UUID
    name: str
    status: str
    is_active: bool
    role_names: list[str] = Field(default_factory=list)
    dentist: UsageContextDentist | None = None
    has_attributed_activity: bool = False


class UsageContextCompany(BaseModel):
    id: UUID
    name: str
    status: str
    is_active: bool
    timezone: str
    sites: list[UsageContextSite] = Field(default_factory=list)
    users: list[UsageContextUser] = Field(default_factory=list)


class UsageContextResponse(BaseModel):
    companies: list[UsageContextCompany] = Field(default_factory=list)


class UsageAdoptionResponse(BaseModel):
    metric_catalog_version: str = "USAGE_1_V1"
    company_id: UUID
    user_id: UUID
    dentist_id: UUID | None = None
    site_id: UUID | None = None
    orthodontics_enabled: bool = False
    period: UsagePeriod
    general: UsageGeneralMetrics
    agenda: UsageAgendaMetrics
    patients: UsagePatientMetrics
    clinical: UsageClinicalMetrics
    treatments: UsageTreatmentMetrics
    consents: UsageConsentMetrics
    orthodontics: UsageOrthodonticsMetrics
    administrative_activity: UsageAdministrativeMetrics
    weekly_trend: list[UsageWeeklyTrendItem] = Field(default_factory=list)
    unsupported_metrics: list[UsageUnsupportedMetric] = Field(default_factory=list)
