export type DemoRequestStatus =
  | "NEW"
  | "CONTACTED"
  | "DEMO_SCHEDULED"
  | "DEMO_COMPLETED"
  | "CONVERTED"
  | "NOT_CONTINUING";

export interface DemoRequestOwner {
  id: string;
  name: string;
  email: string;
}

export interface DemoRequestListItem {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  country: string;
  city: string;
  practice_type: string;
  dentist_count: number;
  source: string;
  status: DemoRequestStatus;
  assigned_to: DemoRequestOwner | null;
  scheduled_at: string | null;
  created_at: string;
  updated_at: string;
  row_version: number;
}

export interface DemoRequestNote {
  id: string;
  text: string;
  author: DemoRequestOwner;
  created_at: string;
}

export interface DemoRequestDetail extends DemoRequestListItem {
  phone: string;
  message: string | null;
  timezone: string | null;
  meeting_url: string | null;
  contacted_at: string | null;
  converted_at: string | null;
  consent_at: string;
  consent_version: string;
  notification_status: string;
  notes: DemoRequestNote[];
}

export interface DemoRequestListResponse {
  items: DemoRequestListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DemoRequestFilters {
  search?: string;
  status?: string;
  country?: string;
  assigned_to_user_id?: string;
  created_from?: string;
  created_to?: string;
}
