export interface PlatformCompanyListItem {
  id: string;
  name: string;
  company_type: string | null;
  tax_id: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  city: string | null;
  country: string | null;
  timezone: string;
  status: string;
  is_active: boolean;
  site_count: number;
  user_count: number;
  created_at: string;
  updated_at: string;
}

export interface PlatformSiteSummary {
  id: string;
  name: string;
  city: string;
  timezone: string | null;
  effective_timezone: string;
  status: string;
}

export interface PlatformUserSummary {
  id: string;
  name: string;
  email: string;
  status: string;
  roles: string[];
}

export interface PlatformCompanyDetail extends PlatformCompanyListItem {
  sites: PlatformSiteSummary[];
  users: PlatformUserSummary[];
}

export interface PlatformCompanyInput {
  company_name: string;
  company_type: string;
  tax_id: string | null;
  phone: string | null;
  email: string | null;
  address: string;
  city: string;
  country: string;
  timezone: string;
  admin_name: string;
  admin_email: string;
  admin_password: string | null;
}

export interface PlatformCompanyCreateResponse {
  company: PlatformCompanyDetail;
  admin_user: PlatformUserSummary;
  temporary_password: string;
}
