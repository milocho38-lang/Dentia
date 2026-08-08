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
  "ConsentAccessPanel",
  "Crear nueva instancia de consentimiento",
  "acceptance_compatible",
  "ConsentRestrictedMarkdown",
  "Profesional y sede",
  "disabled={busy || !reviewed || selected.missing_variables.length > 0}",
  "handledAcceptances.current.has(acceptanceId)",
  "subscribeConsentSigned",
  "getConsentInstance",
  "pollingInFlight",
  "window.setInterval",
  "5000",
  "document.visibilityState !== \"visible\"",
  "Esperando la firma del paciente",
]) {
  assert.ok(workspace.includes(expected), `missing consent-instance UI contract: ${expected}`);
}

for (const endpoint of [
  "/api/consent-instances?patient_id=",
  "/api/consent-instances/${id}",
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
for (const forbidden of ["Firmar consentimiento", "Aceptar consentimiento", "Consentimiento firmado"]) {
  assert.equal(workspace.includes(forbidden), false, `out-of-scope signing UI found: ${forbidden}`);
}

console.log("consent-instance-tests OK: patient workspace, wizard, permissions, review, void and signing guardrails");
