export interface UsageContextSite {
  id: string;
  name: string;
  status: string;
  is_active: boolean;
}

export interface UsageContextDentist {
  id: string;
  name: string;
  status: string;
  is_active: boolean;
}

export interface UsageContextUser {
  id: string;
  name: string;
  status: string;
  is_active: boolean;
  role_names: string[];
  dentist: UsageContextDentist | null;
  has_attributed_activity: boolean;
}

export interface UsageContextCompany {
  id: string;
  name: string;
  status: string;
  is_active: boolean;
  timezone: string;
  sites: UsageContextSite[];
  users: UsageContextUser[];
}

export interface UsageContextResponse {
  companies: UsageContextCompany[];
}

export interface UsagePeriod {
  start_date: string;
  end_date: string;
  start_at: string;
  end_at: string;
  timezone: string;
  preset: string | null;
}

export interface UsageWeeklyTrendItem {
  week_start: string;
  appointments_activity: number;
  unique_patients: number;
  evolutions_signed: number;
  treatments_created: number;
  consents_created: number;
  orthodontic_activity: number;
}

export interface UsageUnsupportedMetric {
  code: string;
  reason: string;
}

export interface UsageAdoptionResponse {
  metric_catalog_version: string;
  company_id: string;
  user_id: string;
  dentist_id: string | null;
  site_id: string | null;
  orthodontics_enabled: boolean;
  period: UsagePeriod;
  general: {
    last_login_at: string | null;
    first_login_at: string | null;
    first_activity_at: string | null;
    last_activity_at: string | null;
    active_days: number;
  };
  agenda: {
    appointments_created: number;
    appointments_confirmed_by_actor: number;
    appointments_rescheduled_by_actor: number;
    appointments_completed_by_actor: number;
    appointments_cancelled_by_actor: number;
    appointment_active_days: number;
    unique_patients_with_appointment_activity: number;
  };
  patients: {
    patients_created_by_actor: number;
    unique_patients_with_actor_activity: number;
  };
  clinical: {
    clinical_records_opened: number;
    clinical_evolutions_created: number;
    clinical_evolutions_signed: number;
    addenda_created: number;
    current_drafts_created_in_period: number;
    unique_patients_with_clinical_activity: number;
  };
  treatments: {
    treatments_created: number;
    treatment_procedures_registered: number;
    treatments_completed_by_actor: number;
    budgets_created: number;
    budget_versions_created: number;
    budgets_accepted_by_actor: number;
    unique_patients_with_treatment_activity: number;
  };
  consents: {
    consents_created: number;
    consents_shared: number;
    consents_accepted: number;
    consents_pending: number;
    unique_patients_with_consent_activity: number;
  };
  orthodontics: {
    orthodontic_cases_created: number;
    orthodontic_cases_active: number;
    orthodontic_evolutions_created: number;
    orthodontic_evolutions_signed: number;
    orthodontic_records_finalized: number;
    unique_patients_with_orthodontic_activity: number;
  };
  administrative_activity: {
    payments_registered: number;
    payments_reversed: number;
  };
  weekly_trend: UsageWeeklyTrendItem[];
  unsupported_metrics: UsageUnsupportedMetric[];
}

export type UsagePeriodMode =
  | "last_7_days"
  | "last_30_days"
  | "pilot_to_date"
  | "custom";

export interface UsageQueryFilters {
  companyId: string;
  userId: string;
  dentistId?: string;
  siteId?: string;
  periodMode: UsagePeriodMode;
  startDate?: string;
  endDate?: string;
}
