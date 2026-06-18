export interface RoleOption {
  id: string;
  code: string;
  name: string;
  description: string | null;
}

export interface SiteOption {
  id: string;
  name: string;
}

export interface AccessOptions {
  roles: RoleOption[];
  sites: SiteOption[];
}

export interface UserRole {
  id: string;
  code: string;
  name: string;
}

export interface UserSite {
  id: string;
  name: string;
  is_default: boolean;
}

export interface ManagedUser {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  status: string;
  is_active: boolean;
  is_locked: boolean;
  locked_until: string | null;
  must_change_password: boolean;
  last_login_at: string | null;
  default_site_id: string | null;
  default_site_name: string | null;
  roles: UserRole[];
  sites: UserSite[];
  active_sessions: number;
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  items: ManagedUser[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface UserCreateInput {
  name: string;
  email: string;
  phone: string | null;
  role_ids: string[];
  site_ids: string[];
  default_site_id: string;
}

export interface UserUpdateInput {
  name: string;
  email: string;
  phone: string | null;
}

export interface TemporaryPasswordResponse {
  user: ManagedUser;
  temporary_password: string;
}

export interface UserSession {
  id: string;
  active_site_id: string | null;
  active_site_name: string | null;
  ip_address: string | null;
  user_agent: string | null;
  device_name: string | null;
  created_at: string;
  last_seen_at: string;
  expires_at: string;
  revoked_at: string | null;
  revoke_reason: string | null;
  is_active: boolean;
}

export interface UserAuditEvent {
  id: string;
  action: string;
  result: string;
  detail: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  occurred_at: string;
  actor_user_id: string | null;
}
