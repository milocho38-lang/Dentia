import assert from "node:assert/strict";
import {
  createTokenValidationGate,
  validatePublicConsentLink,
} from "../lib/publicConsentClient.mjs";
import { copyTextSecurely } from "../lib/secureClipboard.mjs";

const token = "opaque-token-for-test-only";
const gate = createTokenValidationGate();
assert.equal(gate.shouldValidate(token), true);
assert.equal(gate.shouldValidate(token), false, "Strict Mode must not duplicate the initial validation");
assert.equal(gate.shouldValidate(token, { force: true }), true, "manual retry must validate again");

let requestedPath = "";
let requests = 0;
const success = await validatePublicConsentLink(token, {
  fetchImpl: async (path) => {
    requests += 1;
    requestedPath = path;
    return { ok: true, status: 200, json: async () => ({ status: "ISSUED", recipient_masked: "p***@example.test", expires_at: "2026-08-01T12:00:00Z", message: "Pendiente" }) };
  },
});
assert.equal(requests, 1);
assert.equal(requestedPath, `/api/public/consents/${encodeURIComponent(token)}`);
assert.equal(/^https?:\/\//.test(requestedPath), false, "validation must use a relative URL");
assert.equal(success.kind, "ready");

const unavailable = await validatePublicConsentLink(token, { fetchImpl: async () => ({ ok: false, status: 404 }) });
assert.deepEqual(unavailable, { kind: "unavailable" });
assert.equal("data" in unavailable, false, "pre-OTP errors must not contain PII");
const limited = await validatePublicConsentLink(token, { fetchImpl: async () => ({ ok: false, status: 429 }) });
assert.deepEqual(limited, { kind: "rate_limited" });
const network = await validatePublicConsentLink(token, { fetchImpl: async () => { throw new TypeError("offline"); } });
assert.deepEqual(network, { kind: "network" });
const timeout = await validatePublicConsentLink(token, {
  fetchImpl: async (_path, options) => new Promise((_resolve, reject) => {
    if (options.signal.aborted) reject(new Error("aborted"));
    else options.signal.addEventListener("abort", () => reject(new Error("aborted")));
  }),
  setTimeoutImpl: (callback) => { callback(); return 1; },
  clearTimeoutImpl: () => {},
});
assert.deepEqual(timeout, { kind: "timeout" });

function fakeDocument({ copyResult = true, throws = false } = {}) {
  const state = { appended: 0, removed: 0, commands: 0 };
  const textarea = {
    value: "",
    style: {},
    setAttribute() {},
    focus() {},
    select() {},
    setSelectionRange() {},
    remove() { state.removed += 1; },
  };
  return {
    state,
    documentRef: {
      body: { appendChild() { state.appended += 1; } },
      createElement() { return textarea; },
      execCommand(command) { state.commands += 1; assert.equal(command, "copy"); if (throws) throw new Error("blocked"); return copyResult; },
    },
  };
}

let nativeCalls = 0;
assert.equal(await copyTextSecurely(token, { isSecureContext: true, navigatorRef: { clipboard: { async writeText(value) { nativeCalls += 1; assert.equal(value, token); } } }, documentRef: undefined }), true);
assert.equal(nativeCalls, 1, "HTTPS/secure context must use Clipboard API");

const noClipboard = fakeDocument();
assert.equal(await copyTextSecurely(token, { isSecureContext: false, navigatorRef: {}, documentRef: noClipboard.documentRef }), true);
assert.deepEqual(noClipboard.state, { appended: 1, removed: 1, commands: 1 });

const rejected = fakeDocument();
assert.equal(await copyTextSecurely(token, { isSecureContext: true, navigatorRef: { clipboard: { async writeText() { throw new Error("denied"); } } }, documentRef: rejected.documentRef }), true);
assert.equal(rejected.state.commands, 1, "rejected Clipboard API must fall back");

let insecureNativeCalls = 0;
const httpLan = fakeDocument();
assert.equal(await copyTextSecurely(token, { isSecureContext: false, navigatorRef: { clipboard: { async writeText() { insecureNativeCalls += 1; } } }, documentRef: httpLan.documentRef }), true);
assert.equal(insecureNativeCalls, 0, "HTTP LAN must not call unavailable secure Clipboard API");

const blocked = fakeDocument({ copyResult: false });
assert.equal(await copyTextSecurely(token, { isSecureContext: false, navigatorRef: {}, documentRef: blocked.documentRef }), false);
assert.equal(blocked.state.removed, 1, "temporary textarea must always be removed");

const thrownFallback = fakeDocument({ throws: true });
assert.equal(await copyTextSecurely(token, { isSecureContext: false, navigatorRef: {}, documentRef: thrownFallback.documentRef }), false);
assert.equal(thrownFallback.state.removed, 1);

console.log("consent-access-runtime-tests OK: portal validation, timeout, retry gate, HTTP LAN and HTTPS clipboard fallbacks");
