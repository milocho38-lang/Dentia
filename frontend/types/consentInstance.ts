export interface ConsentContextInput {
  patient_id: string;
  site_id: string;
  appointment_id: string | null;
  treatment_id: string | null;
  treatment_procedure_ids: string[];
  procedure_catalog_ids: string[];
  dentist_profile_id: string;
  clinical_date: string | null;
}

export interface ApplicableConsentTemplate {
  template_id: string;
  version_id: string;
  template_name: string;
  title: string;
  document_kind: string;
  country_code: string;
  language_code: string;
  version_number: number;
  applicability_reason_codes: string[];
  applicability_reasons: string[];
  covered_procedure_ids: string[];
  required_variables: string[];
  required_variable_labels: string[];
  missing_variables: string[];
  missing_variable_labels: string[];
  rendered_preview: string;
}

export interface ConsentInstanceProcedure {
  id: string;
  procedure_catalog_id: string | null;
  treatment_procedure_id: string | null;
  code: string | null;
  name: string;
  description: string | null;
  order: number;
}

export interface ConsentInstance {
  id: string;
  visible_number: string;
  patient_id: string;
  site_id: string;
  template_id: string;
  template_version_id: string;
  appointment_id: string | null;
  treatment_id: string | null;
  professional_user_id: string;
  dentist_profile_id: string | null;
  status: "DRAFT" | "READY_FOR_REVIEW" | "VOIDED";
  document_kind: string;
  country_code: string;
  language_code: string;
  clinical_date: string;
  timezone: string;
  display_title: string;
  rendered_content: string | null;
  template_version_number: number;
  template_content_sha256: string;
  instance_content_sha256: string | null;
  context_sha256: string | null;
  integrity_hash: string | null;
  variable_values: Record<string, string | null>;
  missing_variables: string[];
  missing_variable_labels: string[];
  context_snapshot: Record<string, unknown>;
  procedures: ConsentInstanceProcedure[];
  professional_confirmed_at: string | null;
  professional_confirmed_by: string | null;
  ready_at: string | null;
  voided_at: string | null;
  voided_by: string | null;
  void_reason: string | null;
  row_version: number;
  created_by: string;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConsentInstanceAudit {
  id: string;
  action: string;
  result: string;
  user_id: string | null;
  occurred_at: string;
  detail: Record<string, unknown> | null;
}
