import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const workspace = fs.readFileSync(path.join(root, "frontend/components/consents/PatientConsentsWorkspace.tsx"), "utf8");
const patientDetail = fs.readFileSync(path.join(root, "frontend/components/patients/PatientDetail.tsx"), "utf8");
const service = fs.readFileSync(path.join(root, "frontend/services/consentInstanceService.ts"), "utf8");

for (const expected of [
  "Crear consentimiento",
  "1. Contexto",
  "2. Plantillas",
  "3. Vista previa",
  "Datos faltantes",
  "Buscar entre plantillas compatibles",
  "Aplica como plantilla general",
  "Documento preparado para revisión profesional. Todavía no ha sido enviado ni firmado.",
  "Confirmo que revisé el contenido y que corresponde al procedimiento propuesto.",
  "Confirmar revisión profesional",
  "Anular administrativamente",
  "Editar contexto",
  "Guardar cambios",
  "La emisión de la sesión para decisión del paciente se habilitará en C019A.3.",
  "Profesional y sede",
  "disabled={busy || !reviewed || selected.missing_variables.length > 0}",
]) {
  assert.ok(workspace.includes(expected), `missing consent-instance UI contract: ${expected}`);
}

for (const endpoint of [
  "/api/consent-instances?patient_id=",
  "/api/consent-instances/applicable-templates",
  "/api/consent-instances/batch",
  "method: \"PATCH\"",
  "/professional-confirm",
  "/preview",
  "/void",
  "/audit",
]) {
  assert.ok(service.includes(endpoint), `missing consent-instance API contract: ${endpoint}`);
}

assert.ok(patientDetail.includes('{ id: "consents", label: "Consentimientos", permission: "consent.instance.read" }'));
for (const permission of ["consent.instance.read", "consent.instance.create", "consent.instance.edit_draft", "consent.instance.review", "consent.instance.void", "consent.instance.view_audit"]) {
  assert.ok(patientDetail.includes(permission), `missing permission-aware patient integration: ${permission}`);
}
for (const forbidden of ["Generar QR", "Enviar al paciente", "Firmar consentimiento", "Código OTP", "Portal público"]) {
  assert.equal(workspace.includes(forbidden), false, `out-of-scope signing UI found: ${forbidden}`);
}

console.log("consent-instance-tests OK: patient workspace, wizard, permissions, review, void and signing guardrails");
