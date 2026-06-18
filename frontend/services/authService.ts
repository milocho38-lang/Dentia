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
