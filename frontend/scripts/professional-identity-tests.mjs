import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const dentists = readFileSync(
  new URL("../components/organization/DentistSiteManagementPage.tsx", import.meta.url),
  "utf8",
);
const branding = readFileSync(
  new URL("../components/organization/BrandingSettingsPage.tsx", import.meta.url),
  "utf8",
);
const patientDetail = readFileSync(
  new URL("../components/patients/PatientDetail.tsx", import.meta.url),
  "utf8",
);

for (const label of [
  "Nombre profesional",
  "Tipo de documento",
  "Número de documento",
  "Especialidad o rol clínico",
  "Registro profesional",
  "Firma profesional actual",
  "Correo",
]) {
  assert.match(dentists, new RegExp(label));
}
assert.match(dentists, /value="RUN"/);
assert.match(dentists, /value="RUT"/);
assert.match(dentists, /fetchDentistProfessionalSignature/);
assert.match(dentists, /dentist-\$\{dentist\.id\}/);

assert.doesNotMatch(branding, /Nombre del odontólogo principal/);
assert.doesNotMatch(branding, /title="Firma digital"/);
assert.doesNotMatch(branding, /title="Información profesional"/);
assert.match(branding, /Identidad de los profesionales/);
assert.match(branding, /Configurar odontólogos/);

assert.match(patientDetail, /Completar perfil profesional/);
assert.match(patientDetail, /prescriptionProfileActionId/);
assert.match(patientDetail, /#dentist-/);

console.log("professional-identity-tests OK");
