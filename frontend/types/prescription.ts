export type PrescriptionStatus = "DRAFT" | "FINALIZED" | "VOIDED";

export interface PrescriptionItemInput {
  generic_name: string;
  brand_name?: string | null;
  pharmaceutical_form: string;
  concentration: string;
  dose: string;
  route: string;
  frequency: string;
  duration: string;
  total_quantity: string;
  quantity_unit?: string | null;
  instructions?: string | null;
}

export interface PrescriptionItem extends PrescriptionItemInput {
  id: string;
  position: number;
  brand_name: string | null;
  quantity_unit: string | null;
  instructions: string | null;
}

export interface Prescription {
  id: string;
  company_id: string;
  site_id: string;
  site_name: string | null;
  patient_id: string;
  patient_name: string;
  professional_user_id: string | null;
  dentist_profile_id: string | null;
  professional_name: string | null;
  status: PrescriptionStatus;
  prescription_number: string | null;
  clinical_date: string;
  related_treatment_id: string | null;
  related_evolution_id: string | null;
  related_appointment_id: string | null;
  previous_prescription_id: string | null;
  general_instructions: string | null;
  notes: string | null;
  allergies_reviewed: boolean;
  finalized_at: string | null;
  voided_at: string | null;
  void_reason: string | null;
  pdf_sha256: string | null;
  integrity_hash: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  items: PrescriptionItem[];
  clinical_alerts: {
    allergies?: Array<{
      substance: string;
      reaction: string | null;
      severity: string;
      status: string;
      critical_alert: boolean;
    }>;
    active_medications?: Array<{
      name: string;
      dose: string | null;
      frequency: string | null;
      route: string | null;
      reason: string | null;
    }>;
    warning?: string;
  } | null;
}

export interface PrescriptionInput {
  site_id: string;
  dentist_profile_id?: string | null;
  clinical_date: string;
  related_treatment_id?: string | null;
  related_evolution_id?: string | null;
  related_appointment_id?: string | null;
  general_instructions?: string | null;
  notes?: string | null;
  items: PrescriptionItemInput[];
}

export interface PrescriptionListResponse {
  items: Prescription[];
  total: number;
}

export interface PrescriptionPreviewResponse {
  content_base64: string;
  filename: string;
}
