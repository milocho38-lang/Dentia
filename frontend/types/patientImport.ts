export type PatientImportStatus =
  | "READY"
  | "INCOMPLETE"
  | "REVIEW"
  | "REJECTED"
  | "ALREADY_IMPORTED";

export interface PatientImportRow {
  row_number: number;
  source_patient_id: string;
  display_name: string;
  status: PatientImportStatus;
  issues: string[];
  pending_fields: string[];
}

export interface PatientImportCounts {
  ready: number;
  incomplete: number;
  review: number;
  rejected: number;
  already_imported: number;
}

export interface PatientImportSource {
  id: string;
  code: string;
  label: string;
  source_system: string;
}

export interface PatientImportPreview {
  preview_token: string;
  file_sha256: string;
  source: PatientImportSource;
  sheet_name: string;
  total_rows: number;
  counts: PatientImportCounts;
  extra_headers: string[];
  missing_headers: string[];
  rows: PatientImportRow[];
}

export interface PatientImportResult {
  batch_id: string;
  imported: number;
  skipped_already_imported: number;
  skipped_review: number;
  rejected: number;
  rows: PatientImportRow[];
}
