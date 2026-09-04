export const REFRESH_RACE_ERROR_CODE = "REFRESH_RACE_RETRY";
export const REFRESH_CROSS_TAB_LOCK_NAME = "dentia-auth-refresh-v1";
export const REFRESH_RACE_RETRY_DELAYS_MS = Object.freeze([
  100,
  200,
  400,
  800,
]);

function defaultSleep(delayMs) {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}

function browserLockManager() {
  if (typeof navigator === "undefined") {
    return null;
  }
  return navigator.locks ?? null;
}

export async function runRefreshWithCrossTabLock(
  operation,
  { lockManager = browserLockManager() } = {},
) {
  if (!lockManager || typeof lockManager.request !== "function") {
    return operation();
  }

  return lockManager.request(
    REFRESH_CROSS_TAB_LOCK_NAME,
    { mode: "exclusive" },
    operation,
  );
}

export function isRefreshRaceError(error) {
  return (
    error !== null &&
    typeof error === "object" &&
    error.status === 409 &&
    error.payload !== null &&
    typeof error.payload === "object" &&
    error.payload.code === REFRESH_RACE_ERROR_CODE
  );
}

export async function runRefreshWithRaceRetry(
  operation,
  {
    delays = REFRESH_RACE_RETRY_DELAYS_MS,
    sleep = defaultSleep,
  } = {},
) {
  for (let attempt = 0; ; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      if (!isRefreshRaceError(error) || attempt >= delays.length) {
        throw error;
      }
      await sleep(delays[attempt]);
    }
  }
}
