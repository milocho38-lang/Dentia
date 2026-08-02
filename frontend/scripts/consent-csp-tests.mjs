import assert from "node:assert/strict";
import fs from "node:fs";
import { buildConsentPortalCsp } from "../lib/consentCsp.ts";

function directive(csp, name) {
  return csp.split(";").map((value) => value.trim()).find((value) => value.startsWith(`${name} `)) ?? "";
}

const development = buildConsentPortalCsp("development");
const production = buildConsentPortalCsp("production");
const test = buildConsentPortalCsp("test");

assert.ok(directive(development, "script-src").includes("'unsafe-eval'"));
assert.equal((development.match(/'unsafe-eval'/g) ?? []).length, 1);
assert.equal(directive(development, "script-src").includes("'unsafe-eval'"), true);
for (const current of [production, test]) assert.equal(current.includes("'unsafe-eval'"), false);
for (const current of [development, production, test]) {
  for (const expected of ["default-src 'self'", "connect-src 'self'", "frame-ancestors 'none'", "base-uri 'none'", "form-action 'self'"]) {
    assert.ok(current.includes(expected), `${expected} missing`);
  }
  assert.equal(/(^|\s)\*(\s|;|$)/.test(current), false, "CSP must not contain wildcard sources");
}

const config = fs.readFileSync("frontend/next.config.ts", "utf8");
const routeLayout = fs.readFileSync("frontend/app/(public)/consentimiento/[token]/layout.tsx", "utf8");
assert.equal((config.match(/key: "Content-Security-Policy"/g) ?? []).length, 1, "CSP header must be declared once");
assert.ok(config.includes("buildConsentPortalCsp(process.env.NODE_ENV)"));
assert.equal(routeLayout.includes("Content-Security-Policy"), false);

console.log("consent-csp-tests OK: development-only unsafe-eval and strict production CSP");
