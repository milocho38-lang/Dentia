export interface Company {
  id: string;
  name: string;
  slug: string;
  company_type: string | null;
  tax_id: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  city: string | null;
  timezone: string;
  status: string;
  profile_complete: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyInput {
  name: string;
  company_type: string | null;
  tax_id: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  city: string | null;
  timezone: string;
}

export interface Site {
  id: string;
  name: string;
  address: string;
  city: string;
  phone: string | null;
  timezone: string | null;
  effective_timezone: string;
  status: "Activa" | "Inactiva";
  is_active: boolean;
  assigned_users: number;
  dentists: number;
  future_appointments: number;
  open_followups: number;
  created_at: string;
  updated_at: string;
}

export interface SiteInput {
  name: string;
  address: string;
  city: string;
  phone: string | null;
  timezone: string | null;
}

export interface SiteImpact {
  future_appointments: number;
  assigned_users: number;
  default_for_users: number;
  users_without_alternative: number;
  active_sessions: number;
  dentists: number;
  open_followups: number;
  active_sites_after: number;
  can_deactivate: boolean;
  blocking_reasons: string[];
}
