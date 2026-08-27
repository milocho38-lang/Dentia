import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const page = readFileSync(new URL("../components/patients/ClinicalRecordPage.tsx", import.meta.url), "utf8");
const branding = readFileSync(new URL("../components/organization/BrandingSettingsPage.tsx", import.meta.url), "utf8");
const service = readFileSync(new URL("../services/clinicalRecordService.ts", import.meta.url), "utf8");
const medicalHistory = readFileSync(new URL("../lib/medicalHistory.ts", import.meta.url), "utf8");

assert.match(page, /label="Anamnesis"/);
assert.match(page, /Hábitos relevantes/);
assert.match(page, /Antecedentes odontológicos relevantes/);
assert.match(page, /Agregar antecedente médico/);
assert.match(page, /Información histórica preservada/);
assert.match(page, /Respuestas históricas de antecedentes médicos/);
assert.match(page, /Sin antecedentes médicos vigentes registrados/);
assert.match(page, /medicalHistoryResponseLabel/);
assert.doesNotMatch(page, /const MEDICAL_TYPES/);
assert.match(medicalHistory, /isCurrentPositiveMedicalHistory/);
assert.match(medicalHistory, /present.*=== "si".*status.*=== "activo"/s);
assert.match(medicalHistory, /LEGACY_MEDICAL_HISTORY_TYPES/);
assert.match(medicalHistory, /Información no confirmada/);
assert.match(service, /clinical-record\/pdf/);
assert.match(branding, /Tipografía de documentos/);
assert.match(branding, /TIMES_COMPATIBLE/);
console.log("clinical-history-improvements-tests OK");
