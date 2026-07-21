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
  country: string | null;
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
  country: string | null;
  timezone: string;
}

export interface Branding {
  id: string;
  name: string;
  legal_name: string | null;
  company_type: string | null;
  tax_id: string | null;
  address: string | null;
  city: string | null;
  department: string | null;
  country: string | null;
  phone: string | null;
  mobile: string | null;
  email: string | null;
  website: string | null;
  social_media: Record<string, string> | null;
  logo_filename: string | null;
  logo_url: string | null;
  signature_filename: string | null;
  signature_url: string | null;
  primary_dentist_name: string | null;
  professional_specialty: string | null;
  professional_license: string | null;
  university: string | null;
  experience_years: number | null;
  header_text: string | null;
  footer_text: string | null;
  legal_observations: string | null;
  cancellation_policy: string | null;
  thank_you_message: string | null;
  payment_receipt_title: string;
  primary_color: string;
  secondary_color: string;
  button_color: string;
  heading_color: string;
  updated_at: string;
}

export type BrandingInput = Omit<
  Branding,
  | "id"
  | "logo_filename"
  | "logo_url"
  | "signature_filename"
  | "signature_url"
  | "updated_at"
>;

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

export interface DentistSiteOption {
  id: string;
  name: string;
  address: string;
  timezone: string;
  assigned: boolean;
}

export interface DentistSiteManagement {
  id: string;
  name: string;
  status: string;
  user_id: string | null;
  site_ids: string[];
  sites: DentistSiteOption[];
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
