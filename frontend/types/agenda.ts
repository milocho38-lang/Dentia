export interface PatientOption {
  id: string;
  full_name: string;
  document_type: string;
  document: string | null;
  mobile: string;
}

export interface DentistOption {
  id: string;
  name: string;
  site_ids: string[];
}

export interface SiteOption {
  id: string;
  name: string;
  address: string;
  timezone: string;
}

export interface AppointmentTypeOption {
  id: string;
  name: string;
  suggested_duration_minutes: number;
}

export interface AgendaOptions {
  timezone: string;
  active_site_id: string | null;
  dentists: DentistOption[];
  sites: SiteOption[];
  appointment_types: AppointmentTypeOption[];
}

export interface Appointment {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_mobile: string;
  dentist_id: string;
  dentist_name: string;
  site_id: string;
  site_name: string;
  appointment_type_id: string;
  appointment_type_name: string;
  origin_appointment_id: string | null;
  starts_at: string;
  ends_at: string;
  starts_at_local: string;
  ends_at_local: string;
  timezone: string;
  reason: string;
  notes: string | null;
  status: string;
  is_overbook: boolean;
  overbook_reason: string | null;
  confirmation_method: string | null;
  confirmed_at: string | null;
  clinical_record_exists: boolean;
  clinical_evolution_id: string | null;
  clinical_evolution_status: string | null;
  clinical_evolution_version: number | null;
}

export interface AppointmentCreateInput {
  patient_id: string;
  dentist_id: string;
  site_id: string;
  appointment_type_id: string;
  starts_at: string;
  ends_at: string;
  reason: string;
  notes?: string | null;
  is_overbook?: boolean;
  overbook_reason?: string | null;
}

export interface AppointmentRescheduleInput {
  site_id: string;
  dentist_id: string;
  starts_at: string;
  ends_at: string;
  reason: string;
  is_overbook?: boolean;
  overbook_reason?: string | null;
}

export interface AppointmentTimeAdjustInput extends AppointmentRescheduleInput {}

export interface ConflictPayload {
  message: string;
  conflicts: Appointment[];
  can_overbook: boolean;
}

export interface AppointmentClinicalTreatment {
  id: string;
  name: string;
  status: string;
}

export interface AppointmentClinicalProcedure {
  id: string;
  treatment_id: string;
  treatment_name: string | null;
  name: string;
  status: string;
  scope_label: string;
  clinical_action: "PLANNED" | "PERFORMED" | "REVIEWED" | "SUSPENDED" | null;
}

export interface AppointmentClinicalContext {
  appointment: Appointment;
  clinical_record_exists: boolean;
  clinical_record_id: string | null;
  clinical_evolution_id: string | null;
  clinical_evolution_status: string | null;
  clinical_evolution_version: number | null;
  terminology: {
    record: string;
    open_record: string;
    summary: string;
  };
  treatments: AppointmentClinicalTreatment[];
  procedures: AppointmentClinicalProcedure[];
  permissions: Record<string, boolean>;
}

export interface ClinicalCareCompletionInput {
  complete_appointment: boolean;
  sign_evolution: boolean;
  evolution_id?: string | null;
  evolution_version?: number | null;
  mark_procedure_ids_done: string[];
  followup_payload?: {
    attention_description: string;
    prescribed_medications?: string | null;
    requires_followup: boolean;
    recommended_followup_date?: string | null;
    followup_reason?: string | null;
  } | null;
  control_appointment_payload?: AppointmentCreateInput | null;
}

export interface ClinicalCareActionResult {
  success: boolean;
  message: string;
  entity_id: string | null;
}

export interface ClinicalCareCompletionResult {
  appointment: ClinicalCareActionResult | null;
  evolution: ClinicalCareActionResult | null;
  procedures: ClinicalCareActionResult[];
  followup: ClinicalCareActionResult | null;
  control_appointment: ClinicalCareActionResult | null;
  partial_failure: boolean;
}
