export interface TreatmentSummary {
  gross_value: string;
  discount_value: string;
  final_value: string;
  paid_value: string;
  balance: string;
  procedures_total: number;
  procedures_done: number;
}

export interface TreatmentListItem {
  id: string;
  patient_id: string;
  patient_name: string;
  name: string;
  status: string;
  responsible_dentist_id: string | null;
  responsible_dentist_name: string | null;
  main_site_id: string | null;
  main_site_name: string | null;
  final_value: string;
  paid_value: string;
  balance: string;
  updated_at: string;
}

export interface Treatment extends TreatmentListItem {
  description: string | null;
  specialty: string | null;
  start_date: string | null;
  end_date: string | null;
  observations: string | null;
  created_at: string;
  summary: TreatmentSummary;
}

export interface TreatmentListResponse {
  items: TreatmentListItem[];
  total: number;
}

export interface Procedure {
  id: string;
  treatment_id: string;
  patient_id: string;
  catalog_procedure_id: string | null;
  name: string;
  category: string | null;
  dentist_id: string | null;
  dentist_name: string | null;
  site_id: string | null;
  site_name: string | null;
  appointment_id: string | null;
  source_odontogram_event_id?: string | null;
  unit_value: string;
  quantity: string;
  total_value: string;
  status: string;
  estimated_date: string | null;
  performed_at: string | null;
  observations: string | null;
  requires_tooth: boolean;
  scope_type: string;
  zone: string | null;
  tooth: string | null;
  surfaces: string[] | null;
  scope_label: string;
}

export interface ProcedureClinicalCompletionInput {
  clinical_evolution_id: string;
  odontogram_catalog_item_id: string;
  idempotency_key: string;
  source_odontogram_event_id?: string | null;
  source_diagnosis_action: "KEEP_ACTIVE" | "RESOLVE_ON_SIGN";
  scope_type: string;
  zone?: string | null;
  tooth?: string | null;
  surfaces?: string[] | null;
  dentition?: string;
  observation?: string | null;
}

export interface ProcedureClinicalCompletionResponse {
  procedure: Procedure;
  odontogram_event_id: string;
  odontogram_event_status: string;
  clinical_evolution_id: string;
  idempotency_key: string;
  idempotent_replay: boolean;
  message: string;
}

export interface ProcedureWithDiagnosisInput {
  catalog_procedure_id: string;
  idempotency_key: string;
  diagnosis_mode: "NONE" | "CREATE_NEW" | "USE_EXISTING";
  diagnosis_catalog_item_id?: string | null;
  existing_odontogram_event_id?: string | null;
  diagnosis_observation?: string | null;
  allow_existing_duplicate?: boolean;
  dentition?: string;
  name: string;
  category?: string | null;
  dentist_id?: string | null;
  site_id?: string | null;
  unit_value: string;
  quantity: string;
  estimated_date?: string | null;
  observations?: string | null;
  scope_type?: string;
  zone?: string | null;
  tooth?: string | null;
  surfaces?: string[] | null;
}

export interface ProcedureWithDiagnosisResponse {
  procedure: Procedure | null;
  diagnosis_event_id: string | null;
  diagnosis_created: boolean;
  diagnosis_reused: boolean;
  compatible_existing_event_id: string | null;
  idempotency_key: string;
  idempotent_replay: boolean;
  message: string;
}

export interface ProcedureCatalogItem {
  id: string;
  name: string;
  category: string | null;
  description: string | null;
  suggested_value: string | null;
  suggested_scope_type: string | null;
  odontogram_behavior: "UNCONFIGURED" | "NO_CHANGE" | "OPTIONAL_DIAGNOSIS" | "REQUIRES_DIAGNOSIS";
  odontogram_scope_type: string | null;
  allowed_diagnosis_catalog_item_ids: string[];
  allowed_diagnoses: Array<{
    id: string;
    code: string;
    name: string;
    type: string;
    category: string | null;
  }>;
  default_performed_catalog_item_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProcedureCatalogListResponse {
  items: ProcedureCatalogItem[];
  total: number;
}

export interface BudgetDetail {
  id: string;
  procedure_id: string | null;
  name: string;
  category: string | null;
  quantity: string;
  unit_value: string;
  total_value: string;
  order: number;
  observations: string | null;
  scope_type: string;
  zone: string | null;
  tooth: string | null;
  surfaces: string[] | null;
  scope_label: string;
}

export interface Budget {
  id: string;
  patient_id: string;
  treatment_id: string;
  number: string | null;
  series_id: string;
  previous_budget_id: string | null;
  superseded_by_id: string | null;
  version: number;
  is_current: boolean;
  is_editable: boolean;
  is_current_draft: boolean;
  version_reason: string | null;
  status: string;
  gross_value: string;
  discount_type: string | null;
  discount_value: string;
  discount_calculated_value: string;
  final_value: string;
  observations: string | null;
  issued_at: string;
  expires_on: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  details: BudgetDetail[];
}

export interface Payment {
  id: string;
  receipt_number: string;
  patient_id: string;
  patient_name: string;
  treatment_id: string;
  treatment_name: string;
  budget_id: string | null;
  site_id: string;
  site_name: string;
  dentist_id: string | null;
  dentist_name: string | null;
  paid_at: string;
  value: string;
  payment_method: string;
  reference: string | null;
  observation: string | null;
  show_remaining_balance: boolean;
  remaining_balance_snapshot: string | null;
  status: string;
  reversed_at: string | null;
  reversal_reason: string | null;
  procedure_ids: string[];
}

export interface FinanceDashboard {
  income_today: string;
  income_month: string;
  income_year: string;
  receivables_total: string;
  active_treatments: number;
  average_ticket: string;
}

export interface FinanceBreakdownItem {
  id: string | null;
  name: string;
  value: string;
}

export interface PatientBalanceItem {
  patient_id: string;
  patient_name: string;
  balance: string;
}
