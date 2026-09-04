declare module "@/lib/publicConsentClient.mjs" {
  export const PUBLIC_CONSENT_TIMEOUT_MS: number;

  export type PublicConsentLink = {
    status: string;
    recipient_masked: string;
    expires_at: string;
    message: string;
  };

  export type PublicConsentValidationResult =
    | { kind: "ready"; data: PublicConsentLink }
    | { kind: "unavailable" | "rate_limited" | "network" | "timeout" };

  export function createTokenValidationGate(): {
    shouldValidate(token: string, options?: { force?: boolean }): boolean;
  };

  export function validatePublicConsentLink(token: string): Promise<PublicConsentValidationResult>;
}

declare module "@/lib/secureClipboard.mjs" {
  export function copyTextSecurely(value: string): Promise<boolean>;
}

declare module "@/services/refreshConcurrency.mjs" {
  export const REFRESH_CROSS_TAB_LOCK_NAME: string;
  export const REFRESH_RACE_ERROR_CODE: string;
  export const REFRESH_RACE_RETRY_DELAYS_MS: readonly number[];

  export function isRefreshRaceError(error: unknown): boolean;

  export function runRefreshWithCrossTabLock<T>(
    operation: () => Promise<T>,
    options?: {
      lockManager?: {
        request<Result>(
          name: string,
          options: { mode: "exclusive" },
          callback: () => Promise<Result>,
        ): Promise<Result>;
      } | null;
    },
  ): Promise<T>;

  export function runRefreshWithRaceRetry<T>(
    operation: () => Promise<T>,
    options?: {
      delays?: readonly number[];
      sleep?: (delayMs: number) => Promise<void>;
    },
  ): Promise<T>;
}
