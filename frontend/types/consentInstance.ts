export interface ConsentContextInput {
  patient_id: string;
  site_id: string;
  appointment_id: string | null;
  treatment_id: string | null;
  treatment_procedure_ids: string[];
  procedure_catalog_ids: string[];
  dentist_profile_id: string;
  clinical_date: string | null;
  signer_actor_type?: "PATIENT_SELF" | "RESPONSIBLE_ADULT" | null;
  responsible_adult?: ConsentResponsibleAdultInput | null;
  minor_participation_status?: string | null;
  minor_participation_observation?: string | null;
}

export interface ConsentResponsibleAdultInput {
  patient_responsible_id?: string | null;
  full_name?: string | null;
  document_type?: string | null;
  document_number?: string | null;
  relationship_type: string;
  relationship_other?: string | null;
  email?: string | null;
  phone?: string | null;
  identity_verified: boolean;
}

export interface ConsentResponsibleAdultResponse {
  id: string | null;
  patient_responsible_id: string | null;
  full_name: string | null;
  document_type: string | null;
  document_number: string | null;
  relationship_type: string | null;
  relationship_other: string | null;
  relationship_label: string | null;
  email_masked: string | null;
  phone: string | null;
  identity_verified_at: string | null;
  identity_verified_by: string | null;
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
  signer_policy: string;
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
  status: "DRAFT" | "READY_FOR_REVIEW" | "PENDING_SIGNATURE" | "SIGNED" | "VOIDED";
  completion_channel: "ELECTRONIC" | "PAPER" | null;
  paper_status: "PRINTED" | "SIGNED_PENDING_DIGITIZATION" | "DIGITIZING" | "FINALIZED" | null;
  document_kind: string;
  country_code: string;
  language_code: string;
  clinical_date: string;
  timezone: string;
  display_title: string;
  signer_policy: string;
  signer_actor_type: "PATIENT_SELF" | "RESPONSIBLE_ADULT";
  signer_name: string | null;
  signer_email_masked: string | null;
  responsible_adult: ConsentResponsibleAdultResponse | null;
  minor_participation_status: string | null;
  minor_participation_observation: string | null;
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
  acceptance_compatible: boolean;
  acceptance_block_code: string | null;
  acceptance_block_message: string | null;
  is_test_document: boolean;
  test_notice: string | null;
  legal_review_status: string | null;
  declaration_set_code: string | null;
  declaration_set_version: string | null;
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

export interface ConsentAccessSession {
  id: string; status: string; recipient_masked: string; issued_at: string; expires_at: string;
  verified_at: string | null; viewed_at: string | null; clarification_requested_at: string | null;
  last_activity_at: string; row_version: number; public_url?: string; public_path?: string;
}
export interface ConsentClarification { id: string; status: string; message: string | null; requested_at: string; resolved_at: string | null; }
export interface ConsentAccessAudit { id:string; action:string; result:string; user_id:string|null; occurred_at:string; detail:Record<string,unknown>|null; }

export interface ConsentPaperPage {
  id: string; position: number; sha256: string; byte_size: number; source_mime_type: string; original_page_number: number;
}
export interface ConsentPaperPacket {
  id: string; consent_instance_id: string; status: "PRINTED" | "SIGNED_PENDING_DIGITIZATION" | "DIGITIZING" | "FINALIZED";
  expected_page_count: number; uploaded_page_count: number; print_sha256: string; print_byte_size: number;
  printed_at: string; printed_by: string; paper_signed_at: string | null; paper_signed_recorded_by: string | null;
  digitalization_started_at: string | null; digitization_finalized_at: string | null; finalized_by: string | null;
  final_pdf_sha256: string | null; final_pdf_size: number | null; final_page_count: number | null;
  verification_version: string | null; pages: ConsentPaperPage[]; row_version: number;
}
