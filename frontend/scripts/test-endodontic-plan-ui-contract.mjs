import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(
  new URL("../components/treatments/TreatmentPages.tsx", import.meta.url),
  "utf8",
);

assert.match(source, /default_performed_code === "DONE_ENDO"/);
assert.match(source, /diagnosis_surfaces: diagnosisMode !== "NONE" && isEndodonticPlan \? diagnosisSurfaces : null/);
assert.match(source, /isEndodonticPlan \? diagnosisSurfaces : surfaces/);
assert.match(source, /diagnosis_mode: "USE_EXISTING"/);
assert.match(source, /existing_odontogram_event_id: compatibleExisting\.eventId/);
assert.match(source, /Reutilizar diagnóstico seleccionado/);
assert.match(source, /disabled=\{reusingExisting\}/);
assert.match(source, /await onSubmit\([\s\S]{0,500}resetProcedureForm\(\)/);
assert.match(source, /"51", "52", "53", "54", "55"/);
assert.doesNotMatch(
  source,
  /odontogramBehavior === "PLANNED_RESULT" && allowedDiagnoses\.length > 0/,
  "una corona o implante no debe adquirir diagnóstico superficial por ser PLANNED_RESULT",
);

console.log("endodontic plan UI contract: 10 assertions passed");
