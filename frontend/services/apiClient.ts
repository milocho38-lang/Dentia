import type { TokenResponse } from "@/types/auth";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type SessionListener = (session: TokenResponse | null) => void;

let accessToken: string | null = null;
let refreshPromise: Promise<TokenResponse> | null = null;
let sessionListener: SessionListener | null = null;

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }

  let detail: string | undefined;
  try {
    const body = (await response.json()) as { detail?: string };
    detail = body.detail;
  } catch {
    detail = undefined;
  }

  throw new ApiError(
    detail ?? "No fue posible completar la solicitud.",
    response.status,
    detail,
  );
}

async function directRefresh(): Promise<TokenResponse> {
  const response = await fetch("/api/auth/refresh", {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });
  const session = await parseResponse<TokenResponse>(response);
  accessToken = session.access_token;
  sessionListener?.(session);
  return session;
}

export function setSessionListener(listener: SessionListener | null): void {
  sessionListener = listener;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function clearClientSession(): void {
  accessToken = null;
  sessionListener?.(null);
}

export async function refreshSession(): Promise<TokenResponse> {
  if (!refreshPromise) {
    refreshPromise = directRefresh()
      .catch((error) => {
        accessToken = null;
        sessionListener?.(null);
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface ApiRequestOptions extends RequestInit {
  retryOnUnauthorized?: boolean;
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { retryOnUnauthorized = true, headers, ...requestOptions } = options;
  const requestHeaders = new Headers(headers);
  requestHeaders.set("Accept", "application/json");
  if (accessToken) {
    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  let response = await fetch(path, {
    ...requestOptions,
    credentials: "include",
    headers: requestHeaders,
  });

  if (
    response.status === 401 &&
    retryOnUnauthorized &&
    path !== "/api/auth/refresh" &&
    path !== "/api/auth/login"
  ) {
    try {
      await refreshSession();
    } catch {
      return parseResponse<T>(response);
    }

    const retryHeaders = new Headers(headers);
    retryHeaders.set("Accept", "application/json");
    if (accessToken) {
      retryHeaders.set("Authorization", `Bearer ${accessToken}`);
    }
    response = await fetch(path, {
      ...requestOptions,
      credentials: "include",
      headers: retryHeaders,
    });
  }

  return parseResponse<T>(response);
}
