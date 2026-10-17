export interface ClinicalFile {
  id: string; patient_id: string; treatment_id: string | null; appointment_id: string | null;
  file_type: string; category: string; original_name: string; mime_type: string;
  size_bytes: number; sha256: string; description: string | null; uploaded_at: string; uploaded_by: string;
}
export interface ClinicalFileListResponse { items: ClinicalFile[]; total: number }
