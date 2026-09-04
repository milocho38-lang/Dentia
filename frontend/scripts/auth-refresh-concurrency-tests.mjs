import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  REFRESH_CROSS_TAB_LOCK_NAME,
  REFRESH_RACE_ERROR_CODE,
  REFRESH_RACE_RETRY_DELAYS_MS,
  isRefreshRaceError,
  runRefreshWithCrossTabLock,
  runRefreshWithRaceRetry,
} from "../services/refreshConcurrency.mjs";

function raceError() {
  return Object.assign(new Error("refresh race"), {
    status: 409,
    payload: { code: REFRESH_RACE_ERROR_CODE },
  });
}

assert.equal(REFRESH_RACE_RETRY_DELAYS_MS.length, 4);
assert.equal(isRefreshRaceError(raceError()), true);
assert.equal(
  isRefreshRaceError(
    Object.assign(new Error("replay"), {
      status: 401,
      payload: { code: "REFRESH_TOKEN_REUSE" },
    }),
  ),
  false,
);

let attempts = 0;
const delays = [];
const recovered = await runRefreshWithRaceRetry(
  async () => {
    attempts += 1;
    if (attempts < 3) {
      throw raceError();
    }
    return "authenticated";
  },
  {
    delays: [10, 20, 30],
    sleep: async (delay) => delays.push(delay),
  },
);
assert.equal(recovered, "authenticated");
assert.equal(attempts, 3);
assert.deepEqual(delays, [10, 20]);

let sharedCookie = "T1";
let releaseWinner;
const winnerReady = new Promise((resolve) => {
  releaseWinner = resolve;
});
let secondContextAttempts = 0;

const contextA = runRefreshWithRaceRetry(async () => {
  assert.equal(sharedCookie, "T1");
  sharedCookie = "T2";
  releaseWinner();
  return "context-a-authenticated";
});

const contextB = runRefreshWithRaceRetry(
  async () => {
    secondContextAttempts += 1;
    if (secondContextAttempts === 1) {
      await winnerReady;
      throw raceError();
    }
    assert.equal(sharedCookie, "T2");
    sharedCookie = "T3";
    return "context-b-authenticated";
  },
  { delays: [0], sleep: async () => {} },
);

assert.deepEqual(await Promise.all([contextA, contextB]), [
  "context-a-authenticated",
  "context-b-authenticated",
]);
assert.equal(sharedCookie, "T3");

const replayError = Object.assign(new Error("real replay"), {
  status: 401,
  payload: { code: "REFRESH_TOKEN_REUSE" },
});
await assert.rejects(
  runRefreshWithRaceRetry(async () => {
    throw replayError;
  }),
  (error) => error === replayError,
);

let boundedAttempts = 0;
await assert.rejects(
  runRefreshWithRaceRetry(
    async () => {
      boundedAttempts += 1;
      throw raceError();
    },
    { delays: [0, 0], sleep: async () => {} },
  ),
  isRefreshRaceError,
);
assert.equal(boundedAttempts, 3, "initial request plus two bounded retries");

function createExclusiveLockManager() {
  let tail = Promise.resolve();
  const calls = [];
  return {
    calls,
    request(name, options, callback) {
      calls.push({ name, options });
      const current = tail.then(callback, callback);
      tail = current.catch(() => undefined);
      return current;
    },
  };
}

const lockManager = createExclusiveLockManager();
const browserCookieJar = { generation: 0 };
const backendSession = { generation: 0, refreshes: 0 };
let activeRefreshes = 0;
let maximumConcurrentRefreshes = 0;

async function bootstrapBrowserContext(contextName) {
  return runRefreshWithCrossTabLock(
    async () => {
      const sentGeneration = browserCookieJar.generation;
      activeRefreshes += 1;
      maximumConcurrentRefreshes = Math.max(
        maximumConcurrentRefreshes,
        activeRefreshes,
      );
      await Promise.resolve();
      assert.equal(
        sentGeneration,
        backendSession.generation,
        `${contextName} must send the browser's current refresh cookie`,
      );
      backendSession.generation += 1;
      backendSession.refreshes += 1;
      browserCookieJar.generation = backendSession.generation;
      activeRefreshes -= 1;
      return `${contextName}-authenticated`;
    },
    { lockManager },
  );
}

assert.deepEqual(
  await Promise.all([
    bootstrapBrowserContext("tab-a"),
    bootstrapBrowserContext("tab-b"),
  ]),
  ["tab-a-authenticated", "tab-b-authenticated"],
);
assert.equal(maximumConcurrentRefreshes, 1);
assert.equal(browserCookieJar.generation, 2);
assert.equal(backendSession.generation, 2);
assert.equal(backendSession.refreshes, 2);
assert.deepEqual(
  lockManager.calls,
  [
    { name: REFRESH_CROSS_TAB_LOCK_NAME, options: { mode: "exclusive" } },
    { name: REFRESH_CROSS_TAB_LOCK_NAME, options: { mode: "exclusive" } },
  ],
);

let fallbackCalls = 0;
assert.equal(
  await runRefreshWithCrossTabLock(
    async () => {
      fallbackCalls += 1;
      return "fallback-authenticated";
    },
    { lockManager: null },
  ),
  "fallback-authenticated",
);
assert.equal(fallbackCalls, 1);

const apiClientSource = await readFile(
  new URL("../services/apiClient.ts", import.meta.url),
  "utf8",
);
assert.match(
  apiClientSource,
  /runRefreshWithCrossTabLock\(\(\) =>\s*runRefreshWithRaceRetry/,
  "the production refresh must hold the cross-tab lock across all race retries",
);

console.log("auth-refresh-concurrency-tests OK");
