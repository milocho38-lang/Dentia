import assert from "node:assert/strict";
import fs from "node:fs";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const form = read("components/DemoForm.tsx");
const styles = read("app/globals.css");
const config = read("next.config.ts");

for (const name of [
  "firstName",
  "lastName",
  "email",
  "phone",
  "country",
  "city",
  "practiceType",
  "dentistCount",
  "message",
  "privacyConsent",
]) {
  assert.ok(form.includes(`name=\"${name}\"`), `Missing demo field ${name}`);
}
assert.match(form, /privacyConsent\" type=\"checkbox\" required/);
assert.match(form, /href="\/privacidad"/);
assert.match(form, /companyWebsite/);
assert.match(styles, /\.demo-honeypot/);
assert.match(form, /submittingRef\.current/);
assert.match(form, /disabled=\{state === "submitting"\}/);
assert.match(form, /No pudimos enviar tu solicitud\. Intenta nuevamente\./);
assert.match(form, /Solicitud recibida\./);
assert.match(form, /type="tel" required/);
assert.match(form, /type="email" required/);
assert.match(form, /min="1" max="10000" type="number" required/);
assert.match(config, /API_PROXY_TARGET/);
assert.match(config, /\/api\/public\/demo-requests/);
assert.match(styles, /@media \(max-width: 680px\)/);
assert.match(styles, /\.form-grid[\s\S]*grid-template-columns: 1fr/);

console.log("demo-request-form-tests OK");
