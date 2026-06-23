export interface Responsible {
  id: string;
  name: string;
  document_type: string;
  document: string | null;
  relationship: string;
  mobile: string;
  email: string | null;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResponsibleInput {
  name: string;
  document_type: string;
  document: string | null;
  relationship: string;
  mobile: string;
  email: string | null;
  is_primary: boolean;
}

export interface Patient {
  id: string;
  first_names: string;
  last_names: string;
  full_name: string;
  document_type: string;
  document: string | null;
  mobile: string;
  birth_date: string | null;
  age: number | null;
  is_minor: boolean;
  sex: string | null;
  email: string | null;
  alternate_phone: string | null;
  address: string | null;
  city: string | null;
  department: string | null;
  emergency_contact_name: string | null;
  emergency_contact_mobile: string | null;
  administrative_notes: string | null;
  status: string;
  profile_complete: boolean;
  is_active: boolean;
  responsibles: Responsible[];
  created_at: string;
  updated_at: string;
}

export interface PatientInput {
  first_names: string;
  last_names: string;
  document_type: string;
  document: string | null;
  mobile: string;
  birth_date: string;
  sex: string | null;
  email: string | null;
  alternate_phone: string | null;
  address: string | null;
  city: string | null;
  department: string | null;
  emergency_contact_name: string | null;
  emergency_contact_mobile: string | null;
  administrative_notes: string | null;
  acknowledge_duplicate_warning?: boolean;
  responsibles?: ResponsibleInput[];
}

export interface PatientListItem {
  id: string;
  full_name: string;
  document_type: string;
  document: string | null;
  mobile: string;
  age: number | null;
  is_minor: boolean;
  status: string;
  profile_complete: boolean;
  next_appointment_at: string | null;
  last_appointment_at: string | null;
}

export interface PatientListResponse {
  items: PatientListItem[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface DuplicateCandidate {
  id: string;
  full_name: string;
  document_type: string;
  document: string | null;
  mobile: string;
  birth_date: string | null;
  reasons: string[];
}

export interface DuplicateResult {
  exact: DuplicateCandidate[];
  approximate: DuplicateCandidate[];
}

export interface DuplicateErrorPayload {
  message: string;
  duplicates: DuplicateResult;
}

export interface PatientAppointment {
  id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  reason: string;
  is_overbook: boolean;
  confirmation_method: string | null;
  dentist_name: string;
  site_name: string;
  appointment_type_name: string;
  origin_appointment_id: string | null;
}

export interface PatientSummary {
  patient: Patient;
  next_appointment: PatientAppointment | null;
  last_appointment: PatientAppointment | null;
  appointment_count: number;
  active_future_appointment_count: number;
}
