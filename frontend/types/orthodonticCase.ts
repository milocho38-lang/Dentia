export interface OrthodonticsAccessResponse {
  allowed: boolean; code: string; message: string; company_id: string;
  dentist_id: string | null; entitlement_enabled: boolean; assignment_active: boolean;
}
export interface OrthodonticCase {
  id: string; company_id: string; patient_id: string; clinical_record_id: string;
  primary_site_id: string; responsible_dentist_id: string; responsible_dentist_name: string;
  status: "DRAFT" | "ACTIVE" | "SUSPENDED" | "COMPLETED";
  display_status: "DRAFT" | "ACTIVE" | "SUSPENDED" | "COMPLETED" | "DISCONTINUED";
  started_at: string | null; completed_at: string | null;
  closure_reason_code: string | null; closure_notes: string | null;
  treatment_plan: string | null; current_appliance_summary: string | null;
  row_version: number; created_at: string; updated_at: string;
}
export interface OrthodonticSummary {
  case: OrthodonticCase; last_visit: null; what_was_done: null;
  next_session_instructions: null; next_clinical_control: null; active_alerts: unknown[];
  next_appointment: null | { id: string; starts_at: string; ends_at: string; site_id: string; dentist_id: string; reason: string; status: string };
}
export interface OrthodonticPatientWorkspace {
  access: OrthodonticsAccessResponse; active_case: OrthodonticCase | null;
  historical_cases: OrthodonticCase[]; summary: OrthodonticSummary | null;
  eligible_responsibles: { id: string; name: string }[]; record_label: string;
}
