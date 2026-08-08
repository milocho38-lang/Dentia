export type ConsentVersionStatus = "DRAFT" | "PUBLISHED" | "SUPERSEDED" | "RETIRED" | "VOIDED";

export interface ConsentCatalogItem {
  code: string;
  label: string;
  description: string;
  category: string | null;
  sample_value: string | null;
}

export interface ConsentSpecialty {
  code: string;
  name: string;
}

export interface ConsentVersion {
  id: string;
  template_id: string;
  version_number: number;
  status: ConsentVersionStatus;
  title: string;
  content: string;
  content_format: "RESTRICTED_MARKDOWN_V1";
  used_variables: string[];
  variable_schema_snapshot: Record<string, unknown> | null;
  content_sha256: string | null;
  source_library_version_id: string | null;
  source_document_hash: string | null;
  legacy_quarantined: boolean;
  legacy_quarantine_reasons: string[];
  legacy_quarantine_message: string | null;
  based_on_version_id: string | null;
  change_summary: string | null;
  scope_type: "GENERAL" | "SPECIFIC";
  priority: number;
  site_ids: string[];
  procedure_ids: string[];
  specialties: ConsentSpecialty[];
  row_version: number;
  published_at: string | null;
  published_by: string | null;
  retired_at: string | null;
  retire_reason: string | null;
  voided_at: string | null;
  void_reason: string | null;
  created_by: string;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConsentTemplate {
  id: string;
  company_id: string;
  code: string;
  name: string;
  description: string | null;
  document_kind: string;
  country_code: "CL" | "CO";
  language_code: "es-CL" | "es-CO";
  is_active: boolean;
  template_origin: string;
  content_responsibility: string;
  source_library_document_id: string | null;
  published_version: ConsentVersion | null;
  draft_versions: ConsentVersion[];
  versions_count: number;
  created_by: string;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConsentVersionInput {
  title: string;
  content: string;
  change_summary: string | null;
  scope_type: "GENERAL" | "SPECIFIC";
  priority: number;
  site_ids: string[];
  procedure_ids: string[];
  specialties: ConsentSpecialty[];
}

export interface ConsentTemplateCreateInput {
  code: string;
  name: string;
  description: string | null;
  document_kind: string;
  country_code: "CL" | "CO";
  language_code: "es-CL" | "es-CO";
  initial_version: ConsentVersionInput;
}

export interface ConsentValidation {
  valid: boolean;
  used_variables: string[];
  invalid_variables: string[];
  syntax_errors: string[];
}

export interface ConsentPreview {
  warning: string;
  title: string;
  rendered_content: string;
  used_variables: string[];
  validation: ConsentValidation;
}
