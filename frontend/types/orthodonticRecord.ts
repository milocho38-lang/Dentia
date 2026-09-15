export type OrthodonticRecordFieldType = "text" | "single" | "multi" | "boolean";

export interface OrthodonticRecordOption { code: string; label: string }
export interface OrthodonticRecordSection { key: string; label: string; order: number }
export interface OrthodonticRecordField {
  key: string; label: string; type: OrthodonticRecordFieldType; section: string;
  order: number;
  options: OrthodonticRecordOption[]; clinical_pending_flag: string | null;
  max_length: number | null;
}
export interface OrthodonticRecordSchema {
  version: string; sections: OrthodonticRecordSection[]; fields: OrthodonticRecordField[];
}
export interface OrthodonticRecordVersion {
  id: string; record_id: string; version_number: number; status: "DRAFT" | "FINALIZED";
  schema_version: string; row_version: number; content: Record<string, unknown>;
  schema_snapshot: Record<string, unknown>; content_snapshot: Record<string, unknown> | null;
  based_on_version_id: string | null; clinical_date: string | null; timezone_name: string | null;
  content_hash: string | null; integrity_status: "NOT_APPLICABLE" | "PASS" | "FAIL";
  created_by_user_id: string; updated_by_user_id: string;
  finalized_by_user_id: string | null; finalized_at: string | null;
  created_at: string; updated_at: string;
  section_progress: Record<string, "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED">;
}
export interface OrthodonticRecord {
  id: string; company_id: string; patient_id: string; orthodontic_case_id: string;
  label: string; case_status: string; can_edit: boolean; read_only_reason: string | null;
  schema: OrthodonticRecordSchema; current_version: OrthodonticRecordVersion | null;
  versions: OrthodonticRecordVersion[]; created_at: string; updated_at: string;
}
export interface OrthodonticRecordAction {
  success: boolean; message: string; record: OrthodonticRecord;
}
