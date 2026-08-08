export type ConsentLibraryPublicationStatus = "READY_FOR_REVIEW" | "PUBLISHED" | "RETIRED";

export interface ConsentLibraryVersion {
  id: string;
  library_document_id: string;
  country_code: "CO" | "CL";
  language_code: "es-CO" | "es-CL";
  version_number: number;
  publication_status: ConsentLibraryPublicationStatus;
  legal_review_status: string;
  clinical_review_status: string;
  reviewed_countries: string[];
  reviewed_at: string | null;
  review_reference: string | null;
  content_format: "RESTRICTED_MARKDOWN_V1";
  content: string;
  source_text_sha256: string;
  normalized_content_sha256: string;
  variable_schema_snapshot: string[];
  source_pages: number[];
  transformation_notes: string[];
  review_notes: string | null;
  equivalence_reviewer_name: string | null;
  equivalence_review_reason: string | null;
  equivalence_checklist_snapshot: Record<string, unknown> | null;
  normalization_schema_version: string | null;
  normalization_status: "PASS" | "WARNING" | "NEEDS_REVIEW" | "BLOCKED" | "UNKNOWN";
  signer_compatibility: "PATIENT_SELF" | "PATIENT_OR_RESPONSIBLE_ADULT" | "RESPONSIBLE_ADULT_REQUIRED" | "ADULT_SELF" | "ADULT_OR_REPRESENTATIVE" | "REPRESENTATIVE_REQUIRED" | "NO_PATIENT_SIGNATURE" | "FUTURE_WORKFLOW" | "SPECIAL_WORKFLOW" | "NO_SIGNATURE" | "UNKNOWN";
  signer_blocking_category: string | null;
  signer_blocking_reason: string | null;
  signer_blocking_term: string | null;
  signer_blocking_line: number | null;
  signer_blocking_context: string | null;
  adult_variant_required: boolean;
  normalization_alerts: string[];
  electronic_readiness_status: "READY" | "BLOCKED" | "UNKNOWN";
  electronic_readiness_findings: string[];
  norm5_result: "SAFE_NORMALIZED" | "NEEDS_STRUCTURED_FIELD" | "NEEDS_HUMAN_REVIEW" | "NO_CHANGE" | null;
  is_current: boolean;
  is_legacy: boolean;
  historical_message: string | null;
  imported_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConsentLibraryDocument {
  id: string;
  code: string;
  title: string;
  summary: string | null;
  document_type: string;
  category: string;
  specialty_code: string | null;
  specialty_name: string | null;
  signer_scope: string;
  requires_patient_signature: boolean;
  supports_electronic_signature: boolean;
  source_package_version: string;
  source_document_hash: string;
  source_page_start: number;
  source_page_end: number;
  source_title_exact: string | null;
  source_origin_note: string;
  source_reference: string;
  is_active: boolean;
  versions: ConsentLibraryVersion[];
  installed_exact: boolean;
  installed_clone: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConsentLibraryInstallResponse {
  mode: "EXACT" | "CLONE";
  template_id: string;
  version_id: string;
  already_installed: boolean;
  content_responsibility: "DENTIA" | "CLINIC";
  message: string;
}

export interface ConsentLibraryEquivalenceApprovalInput {
  reviewer_name: string;
  reviewed_date: string;
  review_reference: string;
  reason: string;
  clinical_text_faithful: boolean;
  risks_preserved: boolean;
  warnings_preserved: boolean;
  values_preserved: boolean;
  variables_correct: boolean;
  titles_limits_correct: boolean;
  signer_correct: boolean;
  classification_correct: boolean;
  country_approved: boolean;
  odontological_review: boolean;
  legal_equivalence_review: boolean;
}

export interface ConsentLibrarySourceReview {
  document_id: string;
  version_id: string;
  document_code: string;
  title: string;
  country_code: "CO" | "CL";
  language_code: "es-CO" | "es-CL";
  source_text: string;
  normalized_content: string;
  source_text_sha256: string;
  normalized_content_sha256: string;
  source_pages: number[];
  source_reference: string;
}
