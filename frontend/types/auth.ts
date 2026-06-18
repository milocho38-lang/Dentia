export type AuthStatus = "initializing" | "authenticated" | "unauthenticated";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  company_id: string;
  active_site_id: string | null;
  roles: string[];
  permissions: string[];
  must_change_password: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}
