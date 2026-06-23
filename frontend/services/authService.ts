import {
  apiRequest,
  clearClientSession,
  setAccessToken,
} from "@/services/apiClient";
import type {
  LoginCredentials,
  LogoutResponse,
  TokenResponse,
} from "@/types/auth";

export async function login(
  credentials: LoginCredentials,
): Promise<TokenResponse> {
  const response = await apiRequest<TokenResponse>("/api/auth/login", {
    method: "POST",
    retryOnUnauthorized: false,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
  });
  setAccessToken(response.access_token);
  return response;
}

export async function logout(): Promise<LogoutResponse> {
  try {
    return await apiRequest<LogoutResponse>("/api/auth/logout", {
      method: "POST",
      retryOnUnauthorized: false,
    });
  } finally {
    clearClientSession();
  }
}

export async function changePassword(data: {
  current_password: string;
  new_password: string;
  confirm_password: string;
}): Promise<TokenResponse> {
  const response = await apiRequest<TokenResponse>(
    "/api/auth/change-password",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
  setAccessToken(response.access_token);
  return response;
}

export async function switchSite(siteId: string): Promise<TokenResponse> {
  const response = await apiRequest<TokenResponse>("/api/auth/switch-site", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ site_id: siteId }),
  });
  setAccessToken(response.access_token);
  return response;
}
