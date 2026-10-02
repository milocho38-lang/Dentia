import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const page = fs.readFileSync(
  path.join(root, "frontend/components/platform/PlatformCompanyPages.tsx"),
  "utf8",
);
const service = fs.readFileSync(
  path.join(root, "frontend/services/platformService.ts"),
  "utf8",
);

for (const expected of [
  '"Desactivar clínica"',
  '"Reactivar clínica"',
  "Los usuarios de esta clínica dejarán de poder operar en Dentia.",
  "La información clínica y administrativa se conservará",
  "Usuarios activos:",
  "Odontólogos activos:",
  "cannotDeactivateOwnCompany",
  "bloquearía tu acceso actual de administración de plataforma",
  "ConfirmDialog",
]) {
  assert.ok(page.includes(expected), `missing company status UX contract: ${expected}`);
}

assert.match(page, /disabled=\{cannotDeactivateOwnCompany \|\| statusBusy\}/);
assert.match(page, /companyUser\.is_active && companyUser\.status === "Activo"/);
assert.match(page, /statusAction === "deactivate"[\s\S]*deactivatePlatformCompany/);
assert.match(page, /statusAction === "deactivate"[\s\S]*"danger" : "primary"/);

assert.match(service, /\/api\/platform\/companies\/\$\{id\}\/deactivate/);
assert.match(service, /\/api\/platform\/companies\/\$\{id\}\/reactivate/);
assert.match(service, /JSON\.stringify\(\{ reason: reason\?\.trim\(\) \|\| null \}\)/);

console.log(
  "platform-company-status-tests OK: confirmation, explicit self-lockout and status actions",
);
