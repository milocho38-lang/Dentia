import assert from "node:assert/strict";
import fs from "node:fs";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const workspace = read("components/orthodontics/OrthodonticPatientWorkspace.tsx");
const evolution = read("components/orthodontics/OrthodonticEvolutionPanel.tsx");
const record = read("components/orthodontics/OrthodonticClinicalRecordPanel.tsx");
const caseTypes = read("types/orthodonticCase.ts");
const evolutionTypes = read("types/orthodonticEvolution.ts");
const recordTypes = read("types/orthodonticRecord.ts");

assert.match(workspace, /Este caso está suspendido\. Reactívalo/);
assert.match(workspace, /Este caso está cerrado y se conserva como historial clínico/);
assert.match(workspace, /Tu acceso de Ortodoncia ya no está habilitado/);
assert.match(workspace, /Responsable histórico no disponible/);
assert.match(workspace, /evolutionCaseId/);
assert.match(workspace, /accessAllowed=\{canWrite\}/);
assert.match(evolution, /historial permanece disponible en modo de solo lectura/);
assert.match(evolution, /integrity_status === "FAIL"/);
assert.match(record, /Versión actual/);
assert.match(record, /Histórica/);
assert.match(record, /integrity_status === "FAIL"/);
assert.match(caseTypes, /responsible_dentist_available/);
assert.match(evolutionTypes, /integrity_status/);
assert.match(recordTypes, /integrity_status/);

console.log("orthodontic-governance-tests OK");
