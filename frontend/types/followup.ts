export interface FollowupManagement {
  id: string;
  management_type: string;
  result: string;
  observation: string | null;
  next_contact_at: string | null;
  message_content: string | null;
  user_id: string | null;
  occurred_at: string;
}

export interface Followup {
  id: string;
  patient_id: string;
  patient_name: string;
  contact_mobile: string;
  origin_appointment_id: string;
  care_id: string;
  dentist_id: string;
  dentist_name: string;
  site_id: string;
  site_name: string;
  followup_date: string;
  contact_from: string;
  reason: string;
  status: string;
  classification: string;
  scheduled_appointment_id: string | null;
  scheduled_appointment_at: string | null;
  last_contact_at: string | null;
  next_contact_at: string | null;
  close_reason: string | null;
  attention_description: string | null;
  prescribed_medications: string | null;
  managements: FollowupManagement[];
}

export interface FollowupDashboard {
  pending: number;
  upcoming: number;
  overdue: number;
  scheduled: number;
  priority_items: Followup[];
}
