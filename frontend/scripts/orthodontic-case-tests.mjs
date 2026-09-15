import assert from "node:assert/strict";
import fs from "node:fs";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const patient = read("components/patients/PatientDetail.tsx");
const workspace = read("components/orthodontics/OrthodonticPatientWorkspace.tsx");
const service = read("services/orthodonticCaseService.ts");
const types = read("types/orthodonticCase.ts");

assert.match(patient, /getPatientOrthodontics/);
assert.match(patient, /orthodontics\s*\?\s*\[\{ id: "orthodontics"/);
assert.match(patient, /OrthodonticPatientWorkspace/);
assert.match(workspace, /Resumen/);
assert.match(workspace, /Evolución/);
assert.match(workspace, /OrthodonticEvolutionPanel/);
assert.match(workspace, /Sin evoluciones firmadas/);
assert.match(workspace, /Sin próxima cita agendada/);
assert.match(workspace, /Cambios guardados de forma explícita/);
assert.match(workspace, /canWrite && \["DRAFT", "ACTIVE"\]\.includes\(current\.status\) && !editing/);
assert.match(workspace, /Historial de casos/);
assert.match(workspace, /Motivo obligatorio de interrupción/);
assert.match(service, /\/api\/patients\/\$\{patientId\}\/orthodontics/);
assert.match(service, /change-responsible/);
assert.match(service, /"suspend"/);
assert.match(service, /"resume"/);
assert.match(types, /DISCONTINUED/);
assert.match(types, /record_label/);

console.log("orthodontic-case-tests OK");
