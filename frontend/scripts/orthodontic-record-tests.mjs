import assert from "node:assert/strict";
import fs from "node:fs";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const workspace = read("components/orthodontics/OrthodonticPatientWorkspace.tsx");
const panel = read("components/orthodontics/OrthodonticClinicalRecordPanel.tsx");
const service = read("services/orthodonticRecordService.ts");
const types = read("types/orthodonticRecord.ts");

assert.match(workspace, /OrthodonticClinicalRecordPanel/);
assert.doesNotMatch(workspace, /Disponible en ORT-4/);
assert.match(panel, /Todos los campos son opcionales/);
assert.match(panel, /Guardar borrador/);
assert.match(panel, /Finalizar versión/);
assert.match(panel, /Crear nueva versión/);
assert.match(panel, /Hay cambios sin guardar/);
assert.match(panel, /beforeunload/);
assert.match(panel, /record\.schema\.sections/);
assert.match(service, /record\/versions\/\$\{versionId\}\/finalize/);
assert.match(service, /based_on_version_id/);
assert.match(types, /"DRAFT" \| "FINALIZED"/);
assert.match(types, /content_snapshot/);

console.log("orthodontic-record-tests OK");
