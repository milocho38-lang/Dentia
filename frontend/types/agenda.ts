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
