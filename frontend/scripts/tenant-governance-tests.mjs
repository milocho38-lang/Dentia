import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const userForm = fs.readFileSync(
  path.join(root, "frontend/components/users/UserForm.tsx"),
  "utf8",
);
const platform = fs.readFileSync(
  path.join(root, "frontend/components/platform/PlatformCompanyPages.tsx"),
  "utf8",
);
const platformService = fs.readFileSync(
  path.join(root, "frontend/services/platformService.ts"),
  "utf8",
);

for (const removed of ["Usuarios que consumen cupo:", "options.active_users", "options.max_active_users"]) {
  assert.ok(!userForm.includes(removed), `user quota must not be marketed in tenant UI: ${removed}`);
}

for (const expected of [
  "Límite de odontólogos",
  "Odontólogos activos",
  "updatePlatformCompanyDentistLimit",
]) {
  assert.ok(platform.includes(expected), `missing platform dentist quota UI: ${expected}`);
}

assert.ok(
  platformService.includes("/dentist-limit"),
  "platform service must use the dedicated dentist-limit endpoint",
);

console.log("tenant-governance-tests OK: dentist seats and platform-only limit management");
