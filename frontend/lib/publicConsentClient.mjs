export const PUBLIC_CONSENT_TIMEOUT_MS = 10_000;

export function createTokenValidationGate() {
  let lastToken = null;
  return {
    shouldValidate(token, { force = false } = {}) {
      if (!token) return false;
      if (!force && token === lastToken) return false;
      lastToken = token;
      return true;
    },
  };
}

export async function validatePublicConsentLink(
  token,
  {
    fetchImpl = globalThis.fetch,
    timeoutMs = PUBLIC_CONSENT_TIMEOUT_MS,
    setTimeoutImpl = globalThis.setTimeout,
    clearTimeoutImpl = globalThis.clearTimeout,
  } = {},
) {
  if (!token || typeof fetchImpl !== "function") return { kind: "network" };

  const controller = new AbortController();
  let timedOut = false;
  const timeout = setTimeoutImpl(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetchImpl(
      `/api/public/consents/${encodeURIComponent(token)}`,
      {
        credentials: "include",
        cache: "no-store",
        headers: { Accept: "application/json" },
        signal: controller.signal,
      },
    );
    if (response.ok) return { kind: "ready", data: await response.json() };
    if (response.status === 404) return { kind: "unavailable" };
    if (response.status === 429) return { kind: "rate_limited" };
    return { kind: "network" };
  } catch {
    return { kind: timedOut ? "timeout" : "network" };
  } finally {
    clearTimeoutImpl(timeout);
  }
}
