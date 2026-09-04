import assert from "node:assert/strict";
import {
  REFRESH_RACE_ERROR_CODE,
  REFRESH_RACE_RETRY_DELAYS_MS,
  isRefreshRaceError,
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

console.log("auth-refresh-concurrency-tests OK");
