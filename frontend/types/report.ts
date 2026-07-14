export interface ReportMetric {
  key: string;
  label: string;
  value: number | string;
  unit: "count" | "money" | string;
  description: string | null;
}

export interface ReportChartItem {
  label: string;
  value: number | string;
  secondary_value: number | string | null;
}

export interface AppointmentReports {
  created: number;
  attended: number;
  confirmed: number;
  cancelled: number;
  no_show: number;
  overbooked: number;
  attendance_rate: string;
  cancellation_rate: string;
  no_show_rate: string;
  by_status: ReportChartItem[];
  by_site: ReportChartItem[];
  by_dentist: ReportChartItem[];
}

export interface PatientReports {
  new_patients: number;
  attended_patients: number;
  active_patients: number;
  with_active_treatment: number;
  with_balance: number;
  with_overdue_followup: number;
  active_definition: string;
}

export interface TreatmentReports {
  active: number;
  approved: number;
  in_progress: number;
  paused: number;
  finalized: number;
  cancelled: number;
  with_balance: number;
  without_movement: number;
  without_next_appointment: number;
  average_progress: string;
  by_status: ReportChartItem[];
}

export interface FinanceReports {
  income_today: string;
  income_month: string;
  income_range: string;
  clinical_production_range: string;
  approved_sales_range: string;
  approved_budgets_count: number;
  receivables_total: string;
  patients_with_balance: number;
  income_by_site: ReportChartItem[];
  income_by_dentist: ReportChartItem[];
  income_by_method: ReportChartItem[];
  income_by_month: ReportChartItem[];
  production_by_procedure: ReportChartItem[];
  receivables_aging: ReportChartItem[];
}

export interface FollowupReports {
  open: number;
  overdue: number;
  scheduled: number;
  completed: number;
  with_future_appointment: number;
  by_reason: ReportChartItem[];
  by_site: ReportChartItem[];
  by_dentist: ReportChartItem[];
}

export interface ClinicalAggregateReports {
  performed_procedures: number;
  attended_patients: number;
  evolutions_created: number;
  evolutions_signed: number;
  evolutions_draft: number;
  clinical_records_opened: number;
  patients_with_critical_alerts: number;
  top_procedures: ReportChartItem[];
}

export interface PendingConfirmationItem {
  appointment_id: string;
  patient_id: string;
  patient_name: string;
  starts_at: string;
  site_name: string;
  dentist_name: string;
  phone: string;
}

export interface OverdueFollowupItem {
  followup_id: string;
  patient_id: string;
  patient_name: string;
  reason: string;
  due_date: string;
  days_overdue: number;
  dentist_name: string;
  site_name: string;
}

export interface StaleTreatmentItem {
  treatment_id: string;
  patient_id: string;
  patient_name: string;
  treatment_name: string;
  days_without_movement: number;
  balance: string;
  last_activity_at: string;
}

export interface PatientReceivableItem {
  patient_id: string;
  patient_name: string;
  treatment_id: string;
  treatment_name: string;
  balance: string;
  aging_days: number;
  site_name: string | null;
}

export interface ClinicalDraftItem {
  evolution_id: string;
  patient_id: string;
  patient_name: string;
  dentist_name: string;
  attended_at: string;
  days_in_draft: number;
}

export interface ActionItems {
  pending_confirmations: PendingConfirmationItem[];
  overdue_followups: OverdueFollowupItem[];
  stale_treatments: StaleTreatmentItem[];
  patient_receivables: PatientReceivableItem[];
  clinical_drafts: ClinicalDraftItem[];
}

export interface ExecutiveSummary {
  generated_at: string;
  timezone: string;
  date_from: string;
  date_to: string;
  preset: string;
  permissions: {
    operational: boolean;
    financial: boolean;
    clinical_aggregate: boolean;
    cross_site: boolean;
    own_scope: boolean;
  };
  metrics: ReportMetric[];
  appointments: AppointmentReports | null;
  patients: PatientReports | null;
  treatments: TreatmentReports | null;
  finance: FinanceReports | null;
  followups: FollowupReports | null;
  clinical: ClinicalAggregateReports | null;
  action_items: ActionItems | null;
}

export interface ReportFilters {
  preset: string;
  date_from?: string;
  date_to?: string;
  site_id?: string;
  dentist_id?: string;
}
