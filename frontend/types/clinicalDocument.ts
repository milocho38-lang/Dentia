export type ClinicalDocumentType = "REFERRAL" | "CLINICAL_REPORT" | "CERTIFICATE" | "GENERAL_LETTER";
export type ClinicalDocumentStatus = "DRAFT" | "FINALIZED" | "VOIDED";

export interface ClinicalDocument {
  id: string;
  company_id: string;
  site_id: string;
  site_name: string | null;
  patient_id: string;
  patient_name: string;
  professional_user_id: string | null;
  dentist_profile_id: string | null;
  professional_name: string | null;
  document_type: ClinicalDocumentType;
  status: ClinicalDocumentStatus;
  document_number: string | null;
  title: string | null;
  recipient_name: string | null;
  recipient_entity: string | null;
  recipient_specialty: string | null;
  subject: string | null;
  body: string;
  clinical_date: string;
  finalized_at: string | null;
  voided_at: string | null;
  void_reason: string | null;
  related_treatment_id: string | null;
  related_evolution_id: string | null;
  related_appointment_id: string | null;
  previous_document_id: string | null;
  pdf_sha256: string | null;
  integrity_hash: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ClinicalDocumentListResponse {
  items: ClinicalDocument[];
  total: number;
}

export interface ClinicalDocumentInput {
  site_id: string;
  dentist_profile_id?: string | null;
  document_type: ClinicalDocumentType;
  title?: string | null;
  recipient_name?: string | null;
  recipient_entity?: string | null;
  recipient_specialty?: string | null;
  subject?: string | null;
  body: string;
  clinical_date: string;
  related_treatment_id?: string | null;
  related_evolution_id?: string | null;
  related_appointment_id?: string | null;
}

export interface ClinicalDocumentPreviewResponse {
  content_base64: string;
  filename: string;
}
