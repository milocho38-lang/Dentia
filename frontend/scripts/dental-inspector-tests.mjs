import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import ts from "typescript";

const root = process.cwd();
const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "dentia-inspector-tests-"));

const sources = [
  ["frontend/components/odontogram/classic/constants.ts", "constants.js"],
  ["frontend/components/odontogram/classic/types.ts", "types.js"],
  ["frontend/components/odontogram/classic/orientation.ts", "orientation.js"],
  ["frontend/components/odontogram/classic/surfaceAdapter.ts", "surfaceAdapter.js"],
  ["frontend/components/odontogram/classic/clinicalCodeMapping.ts", "clinicalCodeMapping.js"],
  ["frontend/components/odontogram/classic/clinicalTooltip.ts", "clinicalTooltip.js"],
  ["frontend/components/odontogram/classic/realClinicalAdapter.ts", "realClinicalAdapter.js"],
  ["frontend/components/odontogram/visualMapper.ts", "visualMapper.js"],
  ["frontend/components/odontogram/inspector/dentalInspectorMapper.ts", "dentalInspectorMapper.js"],
];

const aliasReplacements = [
  ['"@/components/odontogram/classic/constants"', '"./constants.js"'],
  ['"@/components/odontogram/classic/clinicalTooltip"', '"./clinicalTooltip.js"'],
  ['"@/components/odontogram/classic/realClinicalAdapter"', '"./realClinicalAdapter.js"'],
  ['"@/components/odontogram/classic/types"', '"./types.js"'],
  ['"@/components/odontogram/visualMapper"', '"./visualMapper.js"'],
];

for (const [sourcePath, outputName] of sources) {
  const source = fs.readFileSync(path.join(root, sourcePath), "utf8");
  let output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
    fileName: path.basename(sourcePath),
  }).outputText;
  aliasReplacements.forEach(([from, to]) => {
    output = output.replaceAll(from, to);
  });
  fs.writeFileSync(path.join(tempDir, outputName), output);
}

const requireFromTemp = createRequire(path.join(tempDir, "runner.cjs"));
const inspector = requireFromTemp("./dentalInspectorMapper.js");

function detail(id, code, name, layer, surfaces = null, catalogType = "DIAGNOSIS") {
  return {
    id,
    catalog_item_id: `${id}-catalog`,
    catalog_code: code,
    catalog_name: name,
    catalog_type: catalogType,
    color: null,
    pattern: null,
    symbol: null,
    scope_type: surfaces?.length ? "TOOTH_SURFACE" : "TOOTH",
    zone: null,
    tooth_code: null,
    dentition: null,
    surfaces,
    layer,
    status_after: null,
    metadata: null,
  };
}

function toothState(toothCode, layers) {
  return {
    tooth_code: toothCode,
    dentition: Number(toothCode[0]) >= 5 ? "PRIMARY" : "PERMANENT",
    layers,
    event_count: Object.values(layers).flat().length,
  };
}

function event(id, toothCode, status = "DRAFT") {
  return {
    id,
    patient_id: "patient",
    odontogram_id: "odontogram",
    evolution_id: null,
    appointment_id: null,
    treatment_id: null,
    procedure_id: null,
    event_type: "DIAGNOSIS_ADDED",
    status,
    clinical_date: "2026-07-22T14:00:00Z",
    timezone: "America/Bogota",
    observation: null,
    correction_reason: null,
    parent_event_id: null,
    version: 1,
    content_hash: null,
    confirmed_at: null,
    confirmed_by: null,
    site_id: "site",
    site_name: "Sede",
    dentist_id: "dentist",
    dentist_name: "Dr. Dentia",
    created_by: "user",
    details: [{ ...detail(`${id}-detail`, "DX_ACTIVE_CARIES", "Caries activa", "DIAGNOSIS", ["OCCLUSAL"]), tooth_code: toothCode }],
  };
}

assert.equal(inspector.anatomicalToothName("11"), "Incisivo central superior derecho");
assert.equal(inspector.anatomicalToothName("36"), "Primer molar inferior izquierdo");
assert.equal(inspector.toothDentitionLabel("51"), "Dentición temporal");

let model = inspector.buildInspectorModel("36", toothState("36", {
  DIAGNOSIS: [detail("d1", "DX_ACTIVE_CARIES", "Caries activa", "DIAGNOSIS", ["VESTIBULAR"])],
  PERFORMED: [detail("p1", "DONE_ENDO", "Endodoncia realizada", "PERFORMED", null, "PERFORMED_PROCEDURE")],
  PLANNED: [detail("pl1", "PLAN_CROWN", "Corona planificada", "PLANNED", null, "PLANNED_PROCEDURE")],
}));
assert.equal(model.groups.find((group) => group.id === "diagnosis").events.length, 1);
assert.equal(model.groups.find((group) => group.id === "performed").events.length, 1);
assert.equal(model.groups.find((group) => group.id === "planned").events.length, 1);
assert.equal(model.toothDetails.length, 3);

model = inspector.buildInspectorModel("36", toothState("36", {
  DIAGNOSIS: [
    detail("same", "DX_ACTIVE_CARIES", "Caries activa", "DIAGNOSIS", ["OCCLUSAL"]),
    detail("same", "DX_ACTIVE_CARIES", "Caries activa", "DIAGNOSIS", ["OCCLUSAL"]),
  ],
}));
assert.equal(model.events.length, 1, "summary deduplicates repeated event by id");

model = inspector.buildInspectorModel("36", toothState("36", {
  DIAGNOSIS: [
    detail("surface-a", "DX_ACTIVE_CARIES", "Caries activa", "DIAGNOSIS", ["OCCLUSAL"]),
    detail("surface-b", "DX_ACTIVE_CARIES", "Caries activa", "DIAGNOSIS", ["MESIAL"]),
  ],
}));
assert.equal(model.events.length, 2, "different surfaces remain separate events");

model = inspector.buildInspectorModel("36", toothState("36", {
  DIAGNOSIS: [detail("info", "DX_PULPITIS", "Pulpitis", "DIAGNOSIS", null)],
}));
assert.equal(model.groups.find((group) => group.id === "informative").events.length, 1);
assert.equal(inspector.eventSurfaceLabel(model.events[0]), "Diagnóstico no superficial");

assert.equal(inspector.eventBelongsToTooth(event("e1", "36"), "36"), true);
assert.equal(inspector.eventBelongsToTooth(event("e2", "36"), "31"), false);

console.log("dental inspector tests OK");
