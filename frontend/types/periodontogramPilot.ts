export interface PeriodontogramPilotDentist {
  authorization_id: string | null;
  dentist_id: string;
  user_id: string | null;
  dentist_name: string;
  dentist_status: string;
  dentist_is_active: boolean;
  user_is_active: boolean;
  authorized: boolean;
  authorized_at: string | null;
  authorized_by_user_id: string | null;
  revoked_at: string | null;
  revoked_by_user_id: string | null;
}

export interface PeriodontogramPilot {
  company_id: string;
  enabled: boolean;
  enabled_at: string | null;
  enabled_by_user_id: string | null;
  disabled_at: string | null;
  disabled_by_user_id: string | null;
  dentists: PeriodontogramPilotDentist[];
}

export interface PeriodontogramPilotAccess {
  allowed: boolean;
  code: string;
  message: string;
  company_id: string;
  dentist_id: string | null;
  company_enabled: boolean;
  dentist_authorized: boolean;
}
