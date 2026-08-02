import assert from "node:assert/strict";
import fs from "node:fs";

const manifest = JSON.parse(fs.readFileSync("frontend/.next/routes-manifest.json", "utf8"));
const consentHeaders = manifest.headers.filter((entry) => entry.regex?.includes("consentimiento"));
assert.equal(consentHeaders.length, 1, "production build must emit one consent header rule");
const cspHeaders = consentHeaders[0].headers.filter((entry) => entry.key.toLowerCase() === "content-security-policy");
assert.equal(cspHeaders.length, 1, "production build must emit one CSP header");
assert.equal(cspHeaders[0].value.includes("'unsafe-eval'"), false, "production build must forbid unsafe-eval");
for (const expected of ["connect-src 'self'", "frame-ancestors 'none'", "base-uri 'none'", "form-action 'self'"]) {
  assert.ok(cspHeaders[0].value.includes(expected), `${expected} missing from production build`);
}
assert.equal(/(^|\s)\*(\s|;|$)/.test(cspHeaders[0].value), false);

console.log("consent-csp-build-tests OK: generated production manifest forbids unsafe-eval");
