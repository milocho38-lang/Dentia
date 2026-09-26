import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const detail = readFileSync(
  new URL("../components/patients/PatientDetail.tsx", import.meta.url),
  "utf8",
);
const workspace = readFileSync(
  new URL("../components/periodontogram/PeriodontogramWorkspace.tsx", import.meta.url),
  "utf8",
);
const editor = readFileSync(
  new URL("../components/periodontogram/RapidPeriodontalEditor.tsx", import.meta.url),
  "utf8",
);
const periodontogramUi = `${workspace}\n${editor}`;
const service = readFileSync(
  new URL("../services/periodontogramService.ts", import.meta.url),
  "utf8",
);

assert.match(detail, /id: "periodontogram"/);
assert.match(detail, /permission: "periodontogram\.view"/);
assert.match(detail, /<PeriodontogramWorkspace patientId=\{patient\.id\}/);
assert.match(workspace, /No hay periodontogramas registrados\./);
assert.match(workspace, /Nuevo periodontograma/);
assert.match(workspace, /Finalizar versión/);
assert.match(workspace, /Crear versión correctiva/);
assert.match(workspace, /hasPermission\("periodontogram\.finalize"\)/);
assert.match(workspace, /hasPermission\("periodontogram\.correct"\)/);
assert.match(periodontogramUi, /Guardar cambios/);
assert.match(periodontogramUi, /Vestibular/);
assert.match(periodontogramUi, /Palatino/);
assert.match(periodontogramUi, /Furcación/);
assert.match(periodontogramUi, /sangrado al sondaje/);
assert.match(periodontogramUi, /% placa/);
assert.match(periodontogramUi, /Nota clínica de la pieza/);
assert.match(periodontogramUi, /limpiará sus mediciones clínicas/);
assert.doesNotMatch(periodontogramUi, /Guarda los cambios de esta pieza antes de continuar/);
assert.match(periodontogramUi, /Gráfico periodontal/);
assert.match(service, /\/api\/patients\/\$\{patientId\}\/periodontograms/);
assert.match(service, /\/api\/periodontograms\/\$\{examId\}\/finalize/);
assert.match(service, /\/api\/periodontograms\/\$\{examId\}\/correct/);
assert.match(service, /\/api\/periodontograms\/\$\{examId\}\/draft/);

console.log("periodontogram-foundation-tests OK");
