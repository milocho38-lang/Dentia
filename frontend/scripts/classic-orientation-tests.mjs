import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import ts from "typescript";

const root = process.cwd();
const sourceDir = path.join(root, "frontend/components/odontogram/classic");
const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "dentia-classic-tests-"));
const files = [
  "constants.ts",
  "types.ts",
  "orientation.ts",
  "surfaceAdapter.ts",
  "clinicalCodeMapping.ts",
  "clinicalTooltip.ts",
  "dualClinicalMapper.ts",
  "fixtures.ts",
  "realClinicalAdapter.ts",
  "dualOdontogramLayout.ts",
];

for (const file of files) {
  const source = fs.readFileSync(path.join(sourceDir, file), "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
    fileName: file,
  }).outputText;
  fs.writeFileSync(path.join(tempDir, file.replace(/\.ts$/, ".js")), output);
}

const requireFromTemp = createRequire(path.join(tempDir, "runner.cjs"));
const orientation = requireFromTemp("./orientation.js");
const mapper = requireFromTemp("./dualClinicalMapper.js");
const tooltip = requireFromTemp("./clinicalTooltip.js");
const fixtures = requireFromTemp("./fixtures.js");
const realAdapter = requireFromTemp("./realClinicalAdapter.js");
const layout = requireFromTemp("./dualOdontogramLayout.js");

function expectOrientation(tooth, expected) {
  const result = orientation.getSurfaceOrientation(tooth);
  assert.equal(result.mesial, expected.mesial, `${tooth} mesial`);
  assert.equal(result.distal, expected.distal, `${tooth} distal`);
  assert.equal(result.vestibular, expected.vestibular, `${tooth} vestibular`);
  assert.equal(result.internal, expected.internal, `${tooth} internal`);
  assert.equal(result.internalSurface, expected.internalSurface, `${tooth} internalSurface`);
  assert.equal(result.centralSurface, expected.centralSurface, `${tooth} centralSurface`);
}

function model(tooth, surface) {
  return fixtures.createToothModel(tooth, [{
    id: `${tooth}-${surface}`,
    kind: "CARIES",
    surfaces: [surface],
    status: "DIAGNOSIS",
    label: `Caries ${surface}`,
  }]);
}

function expectMarkerRole(tooth, surface, role) {
  const result = mapper.mapDualClinicalTooth(model(tooth, surface));
  const marker = result.surfaceMarkers.find((item) => item.surface === surface || item.label.includes(surface));
  assert.ok(marker, `${tooth} ${surface} marker exists`);
  assert.equal(marker.role, role, `${tooth} ${surface} role`);
}

expectOrientation("15", { mesial: "RIGHT", distal: "LEFT", vestibular: "TOP", internal: "BOTTOM", internalSurface: "PALATAL", centralSurface: "OCCLUSAL" });
expectOrientation("11", { mesial: "RIGHT", distal: "LEFT", vestibular: "TOP", internal: "BOTTOM", internalSurface: "PALATAL", centralSurface: "INCISAL" });
expectOrientation("25", { mesial: "LEFT", distal: "RIGHT", vestibular: "TOP", internal: "BOTTOM", internalSurface: "PALATAL", centralSurface: "OCCLUSAL" });
expectOrientation("21", { mesial: "LEFT", distal: "RIGHT", vestibular: "TOP", internal: "BOTTOM", internalSurface: "PALATAL", centralSurface: "INCISAL" });
expectOrientation("31", { mesial: "LEFT", distal: "RIGHT", vestibular: "BOTTOM", internal: "TOP", internalSurface: "LINGUAL", centralSurface: "INCISAL" });
expectOrientation("36", { mesial: "LEFT", distal: "RIGHT", vestibular: "BOTTOM", internal: "TOP", internalSurface: "LINGUAL", centralSurface: "OCCLUSAL" });
expectOrientation("41", { mesial: "RIGHT", distal: "LEFT", vestibular: "BOTTOM", internal: "TOP", internalSurface: "LINGUAL", centralSurface: "INCISAL" });
expectOrientation("46", { mesial: "RIGHT", distal: "LEFT", vestibular: "BOTTOM", internal: "TOP", internalSurface: "LINGUAL", centralSurface: "OCCLUSAL" });
expectOrientation("51", { mesial: "RIGHT", distal: "LEFT", vestibular: "TOP", internal: "BOTTOM", internalSurface: "PALATAL", centralSurface: "INCISAL" });
expectOrientation("61", { mesial: "LEFT", distal: "RIGHT", vestibular: "TOP", internal: "BOTTOM", internalSurface: "PALATAL", centralSurface: "INCISAL" });
expectOrientation("71", { mesial: "LEFT", distal: "RIGHT", vestibular: "BOTTOM", internal: "TOP", internalSurface: "LINGUAL", centralSurface: "INCISAL" });
expectOrientation("81", { mesial: "RIGHT", distal: "LEFT", vestibular: "BOTTOM", internal: "TOP", internalSurface: "LINGUAL", centralSurface: "INCISAL" });
expectOrientation("55", { mesial: "RIGHT", distal: "LEFT", vestibular: "TOP", internal: "BOTTOM", internalSurface: "PALATAL", centralSurface: "OCCLUSAL" });
expectOrientation("65", { mesial: "LEFT", distal: "RIGHT", vestibular: "TOP", internal: "BOTTOM", internalSurface: "PALATAL", centralSurface: "OCCLUSAL" });
expectOrientation("75", { mesial: "LEFT", distal: "RIGHT", vestibular: "BOTTOM", internal: "TOP", internalSurface: "LINGUAL", centralSurface: "OCCLUSAL" });
expectOrientation("85", { mesial: "RIGHT", distal: "LEFT", vestibular: "BOTTOM", internal: "TOP", internalSurface: "LINGUAL", centralSurface: "OCCLUSAL" });

expectMarkerRole("15", "MESIAL", "RIGHT");
expectMarkerRole("15", "DISTAL", "LEFT");
expectMarkerRole("25", "MESIAL", "LEFT");
expectMarkerRole("25", "DISTAL", "RIGHT");
expectMarkerRole("31", "VESTIBULAR", "BOTTOM");
expectMarkerRole("31", "LINGUAL", "TOP");
expectMarkerRole("15", "VESTIBULAR", "TOP");
expectMarkerRole("15", "PALATAL", "BOTTOM");
expectMarkerRole("36", "OCCLUSAL", "CENTER");
expectMarkerRole("31", "INCISAL", "CENTER");

const mod36 = mapper.mapDualClinicalTooth(fixtures.DUAL_TOOTH_PRESETS.restorationMultiSurface36);
assert.deepEqual(
  mod36.surfaceMarkers.map((marker) => marker.role).sort(),
  ["CENTER", "LEFT", "RIGHT"],
  "36 MOD uses left, center, right",
);

const mod15 = mapper.mapDualClinicalTooth(fixtures.createToothModel("15", [{
  id: "restoration-mod-15",
  kind: "RESTORATION",
  surfaces: ["MESIAL", "OCCLUSAL", "DISTAL"],
  status: "COMPLETED",
  label: "Restauración MOD 15",
}]));
assert.deepEqual(
  mod15.surfaceMarkers.map((marker) => marker.role).sort(),
  ["CENTER", "LEFT", "RIGHT"],
  "15 MOD uses left, center, right with inverted mesial/distal",
);
assert.throws(() => orientation.getSurfaceOrientation("99"), /FDI inválido/);
assert.equal(orientation.isValidFdiTooth("31"), true);
assert.equal(orientation.isValidFdiTooth("59"), false);

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

function adapt(toothCode, layers, visibleLayers) {
  return realAdapter.buildDualClinicalToothModelFromState(
    toothState(toothCode, layers),
    visibleLayers ? { visibleLayers: new Set(visibleLayers) } : {},
  ).model;
}

let real = adapt("31", { DIAGNOSIS: [detail("r1", "DX_ACTIVE_CARIES", "Nombre cambiado", "DIAGNOSIS", ["VESTIBULAR"])] });
assert.equal(real.events[0].kind, "CARIES", "31 caries by stable code");
assert.deepEqual(real.events[0].surfaces, ["VESTIBULAR"]);
assert.equal(mapper.mapDualClinicalTooth(real).surfaceMarkers[0].role, "BOTTOM");

real = adapt("15", { DIAGNOSIS: [detail("r2", "DX_ACTIVE_CARIES", "Cualquier texto", "DIAGNOSIS", ["MESIAL"])] });
assert.equal(mapper.mapDualClinicalTooth(real).surfaceMarkers[0].role, "RIGHT");

real = adapt("36", { PERFORMED: [detail("r3", "DONE_RESIN", "Resina", "PERFORMED", ["MESIAL", "OCCLUSAL", "DISTAL"], "PERFORMED_PROCEDURE")] });
assert.equal(real.events[0].kind, "RESTORATION");
assert.equal(real.events[0].status, "COMPLETED");
assert.deepEqual(real.events[0].surfaces, ["MESIAL", "OCCLUSAL", "DISTAL"]);

real = adapt("16", { PERFORMED: [detail("r4", "DONE_SEALANT", "Sellante", "PERFORMED", ["OCCLUSAL"], "PERFORMED_PROCEDURE")] });
assert.equal(real.events[0].kind, "RESTORATION");
assert.deepEqual(real.events[0].surfaces, ["OCCLUSAL"]);
let mapped = mapper.mapDualClinicalTooth(real);
assert.equal(mapped.surfaceMarkers[0].color.toUpperCase(), "#2563EB", "completed sealant is blue");

real = adapt("14", { PLANNED: [detail("p1", "PLAN_SEALANT", "Sellante planificado", "PLANNED", ["OCCLUSAL"], "PLANNED_PROCEDURE")] });
assert.equal(real.events[0].status, "PLANNED");
mapped = mapper.mapDualClinicalTooth(real);
assert.equal(mapped.surfaceMarkers[0].color.toUpperCase(), "#F97316", "planned sealant is orange");
assert.notEqual(mapped.surfaceMarkers[0].color.toUpperCase(), "#2563EB", "planned sealant is not completed blue");

real = adapt("36", { PLANNED: [detail("p2", "PLAN_RESIN", "Restauración planificada", "PLANNED", ["MESIAL", "OCCLUSAL", "DISTAL"], "PLANNED_PROCEDURE")] });
mapped = mapper.mapDualClinicalTooth(real);
assert.equal(real.events[0].status, "PLANNED");
assert.deepEqual(mapped.surfaceMarkers.map((marker) => marker.color.toUpperCase()), ["#F97316", "#F97316", "#F97316"]);

real = adapt("36", { PERFORMED: [detail("r5", "DONE_ENDO", "Endodoncia", "PERFORMED", null, "PERFORMED_PROCEDURE")] });
assert.equal(real.events[0].kind, "ENDODONTICS");
assert.deepEqual(real.events[0].surfaces, ["PULPAL_RADICULAR"]);

real = adapt("15", { PERFORMED: [detail("r6", "DONE_CROWN", "Corona", "PERFORMED", null, "PERFORMED_PROCEDURE")] });
assert.equal(real.events[0].kind, "CROWN");
assert.deepEqual(real.events[0].surfaces, ["WHOLE_TOOTH"]);

real = adapt("36", {
  STRUCTURAL: [detail("r7a", "STRUCT_IMPLANT", "Implante", "STRUCTURAL", null, "STRUCTURAL_STATE")],
  PERFORMED: [detail("r7b", "DONE_CROWN", "Corona sobre implante", "PERFORMED", null, "PERFORMED_PROCEDURE")],
});
assert.deepEqual(real.events.map((event) => event.kind).sort(), ["CROWN", "IMPLANT"]);

real = adapt("46", { STRUCTURAL: [detail("r8", "STRUCT_MISSING", "Ausencia", "STRUCTURAL", null, "STRUCTURAL_STATE")] });
assert.equal(real.events[0].kind, "ABSENT");
assert.deepEqual(real.events[0].surfaces, ["WHOLE_TOOTH"]);

real = adapt("36", { DIAGNOSIS: [detail("r9", "DX_PULPITIS", "Pulpitis irreversible", "DIAGNOSIS", null)] });
assert.equal(real.events[0].kind, "INFORMATION");
assert.deepEqual(real.events[0].surfaces, []);
assert.equal(real.events[0].localization, "NON_SURFACE");
mapped = mapper.mapDualClinicalTooth(real);
assert.equal(mapped.surfaceMarkers.length, 0);
assert.equal(mapped.generalMarkers.length, 1);
assert.equal(mapped.generalMarkers[0].symbol, "i", "non-surface diagnosis uses informative indicator");

real = adapt("36", { DIAGNOSIS: [detail("r9b", "DX_PERIAPICAL", "Lesión periapical completa", "DIAGNOSIS", null)] });
mapped = mapper.mapDualClinicalTooth(real);
assert.equal(real.events[0].localization, "NON_SURFACE");
assert.equal(mapped.surfaceMarkers.length, 0);

real = adapt("31", { DIAGNOSIS: [detail("r9c", "DX_ACTIVE_CARIES", "Caries activa", "DIAGNOSIS", null)] });
mapped = mapper.mapDualClinicalTooth(real);
assert.equal(real.events[0].kind, "CARIES");
assert.equal(real.events[0].localization, "SURFACE_UNSPECIFIED");
assert.equal(real.events[0].surfaces.length, 0);
assert.equal(mapped.surfaceMarkers.length, 0);
assert.equal(mapped.generalMarkers.length, 1);
assert.equal(mapped.generalMarkers[0].symbol, "?", "surface-unspecified event uses question indicator");

let tooltipText = tooltip.createClinicalTooltip(real);
assert.match(tooltipText, /Caries activa/);
assert.match(tooltipText, /Diagnóstico/);
assert.match(tooltipText, /Superficie no especificada/);
assert.doesNotMatch(tooltipText, /DX_ACTIVE_CARIES|SURFACE_UNSPECIFIED|DIAGNOSIS/);

real = adapt("31", { FINDING: [detail("tooltip-restoration", "FIND_RESTORATION", "Restauración existente", "FINDING", null, "FINDING")] });
tooltipText = tooltip.createClinicalTooltip(real);
assert.match(tooltipText, /Restauración existente/);
assert.match(tooltipText, /Hallazgo/);
assert.match(tooltipText, /Superficie no especificada/);
assert.doesNotMatch(tooltipText, /FINDING|FIND_RESTORATION|SURFACE_UNSPECIFIED/);

const duplicatedById = fixtures.createToothModel("36", [
  { id: "dup-id", kind: "CARIES", surfaces: ["OCCLUSAL"], status: "DIAGNOSIS", label: "Caries activa", sourceCode: "DX_ACTIVE_CARIES", sourceLayer: "DIAGNOSIS" },
  { id: "dup-id", kind: "CARIES", surfaces: ["OCCLUSAL"], status: "DIAGNOSIS", label: "Caries activa", sourceCode: "DX_ACTIVE_CARIES", sourceLayer: "DIAGNOSIS" },
]);
assert.equal(tooltip.uniqueClinicalEvents(duplicatedById).length, 1, "duplicate events by id are shown once");

const duplicatedByFallbackKey = fixtures.createToothModel("36", [
  { id: "", kind: "CARIES", surfaces: ["OCCLUSAL"], status: "DIAGNOSIS", label: "Caries activa", sourceCode: "DX_ACTIVE_CARIES", sourceLayer: "DIAGNOSIS" },
  { id: "", kind: "CARIES", surfaces: ["OCCLUSAL"], status: "DIAGNOSIS", label: "Caries activa", sourceCode: "DX_ACTIVE_CARIES", sourceLayer: "DIAGNOSIS" },
]);
assert.equal(tooltip.uniqueClinicalEvents(duplicatedByFallbackKey).length, 1, "duplicate events by fallback key are shown once");

const differentSurfaces = fixtures.createToothModel("36", [
  { id: "surface-1", kind: "CARIES", surfaces: ["OCCLUSAL"], status: "DIAGNOSIS", label: "Caries activa", sourceCode: "DX_ACTIVE_CARIES", sourceLayer: "DIAGNOSIS" },
  { id: "surface-2", kind: "CARIES", surfaces: ["MESIAL"], status: "DIAGNOSIS", label: "Caries activa", sourceCode: "DX_ACTIVE_CARIES", sourceLayer: "DIAGNOSIS" },
]);
tooltipText = tooltip.createClinicalTooltip(differentSurfaces);
assert.match(tooltipText, /Oclusal/);
assert.match(tooltipText, /Mesial/);
assert.equal(tooltip.uniqueClinicalEvents(differentSurfaces).length, 2, "same code on different surfaces is preserved");

const differentStatuses = fixtures.createToothModel("36", [
  { id: "status-1", kind: "RESTORATION", surfaces: ["OCCLUSAL"], status: "PLANNED", label: "Restauración", sourceCode: "PLAN_RESIN", sourceLayer: "PLANNED" },
  { id: "status-2", kind: "RESTORATION", surfaces: ["OCCLUSAL"], status: "COMPLETED", label: "Restauración", sourceCode: "DONE_RESIN", sourceLayer: "PERFORMED" },
]);
assert.equal(tooltip.uniqueClinicalEvents(differentStatuses).length, 2, "planned and completed events are preserved separately");

real = adapt("36", { DIAGNOSIS: [detail("tooltip-pulpitis", "DX_PULPITIS", "Pulpitis", "DIAGNOSIS", null)] });
tooltipText = tooltip.createClinicalTooltip(real);
assert.match(tooltipText, /Pulpitis/);
assert.match(tooltipText, /Diagnóstico no superficial/);
assert.doesNotMatch(tooltipText, /DX_PULPITIS|NON_SURFACE|DIAGNOSIS/);

real = adapt("15", { PLANNED: [detail("crown-plan", "PLAN_CROWN", "Corona planificada", "PLANNED", null, "PLANNED_PROCEDURE")] });
mapped = mapper.mapDualClinicalTooth(real);
assert.equal(mapped.structuralMarkers[0].symbol, "♛");
assert.equal(mapped.structuralMarkers[0].color.toUpperCase(), "#F97316", "planned crown uses planned color");
assert.notEqual(mapped.structuralMarkers[0].color.toUpperCase(), "#059669", "planned crown is not fixed green");

real = adapt("15", { PERFORMED: [detail("crown-done", "DONE_CROWN", "Corona realizada", "PERFORMED", null, "PERFORMED_PROCEDURE")] });
mapped = mapper.mapDualClinicalTooth(real);
assert.equal(mapped.structuralMarkers[0].symbol, "♛");
assert.equal(mapped.structuralMarkers[0].color.toUpperCase(), "#2563EB", "completed crown uses completed color");

real = adapt("31", { DIAGNOSIS: [detail("r10", "DX_ACTIVE_CARIES", "Caries", "DIAGNOSIS", ["VESTIBULAR"])] }, ["PERFORMED"]);
assert.equal(real.events.length, 0, "hidden layers do not appear");

real = adapt("51", { DIAGNOSIS: [detail("r11", "DX_ACTIVE_CARIES", "Caries temporal", "DIAGNOSIS", ["INCISAL"])] });
assert.equal(real.quadrant, 5);
assert.equal(mapper.mapDualClinicalTooth(real).surfaceMarkers[0].role, "CENTER");

real = adapt("14", {
  DIAGNOSIS: [detail("combo1", "DX_ACTIVE_CARIES", "Caries oclusal", "DIAGNOSIS", ["OCCLUSAL"])],
  PLANNED: [detail("combo2", "PLAN_RESIN", "Restauración planificada", "PLANNED", ["OCCLUSAL"], "PLANNED_PROCEDURE")],
});
mapped = mapper.mapDualClinicalTooth(real);
assert.equal(real.events.length, 2);
assert.deepEqual(mapped.surfaceMarkers.map((marker) => marker.status).sort(), ["DIAGNOSIS", "PLANNED"]);

const first = JSON.stringify(realAdapter.buildDualClinicalToothModelFromState(toothState("14", {
  DIAGNOSIS: [detail("persist1", "DX_ACTIVE_CARIES", "Caries oclusal", "DIAGNOSIS", ["OCCLUSAL"])],
})).model);
const second = JSON.stringify(realAdapter.buildDualClinicalToothModelFromState(toothState("14", {
  DIAGNOSIS: [detail("persist1", "DX_ACTIVE_CARIES", "Caries oclusal", "DIAGNOSIS", ["OCCLUSAL"])],
})).model);
assert.equal(first, second, "same real events produce same model");

const emptyPermanentModels = layout.buildDualClinicalModelsForRows(layout.PERMANENT_DUAL_ROWS, new Map());
assert.equal(emptyPermanentModels.flat().length, 32, "permanent layout creates 32 dual models");
assert.deepEqual(
  emptyPermanentModels.map((row) => row.map((item) => item.toothNumber)),
  [
    ["18", "17", "16", "15", "14", "13", "12", "11"],
    ["21", "22", "23", "24", "25", "26", "27", "28"],
    ["48", "47", "46", "45", "44", "43", "42", "41"],
    ["31", "32", "33", "34", "35", "36", "37", "38"],
  ],
  "permanent layout keeps mandatory FDI order",
);
assert.equal(emptyPermanentModels.flat().find((item) => item.toothNumber === "31").events.length, 0, "empty real state does not use fixtures");

const emptyPrimaryModels = layout.buildDualClinicalModelsForRows(layout.PRIMARY_DUAL_ROWS, new Map());
assert.equal(emptyPrimaryModels.flat().length, 20, "primary layout creates 20 temporal dual models");
assert.deepEqual(
  emptyPrimaryModels.map((row) => row.map((item) => item.toothNumber)),
  [
    ["55", "54", "53", "52", "51"],
    ["61", "62", "63", "64", "65"],
    ["85", "84", "83", "82", "81"],
    ["71", "72", "73", "74", "75"],
  ],
  "primary layout keeps mandatory FDI order",
);

const realStateMap = new Map([
  ["31", toothState("31", { DIAGNOSIS: [detail("layout1", "DX_ACTIVE_CARIES", "Caries vestibular", "DIAGNOSIS", ["VESTIBULAR"])] })],
  ["14", toothState("14", { PLANNED: [detail("layout2", "PLAN_SEALANT", "Sellante planificado", "PLANNED", ["OCCLUSAL"], "PLANNED_PROCEDURE")] })],
]);
const layoutModels = layout.buildDualClinicalModelsForRows(layout.PERMANENT_DUAL_ROWS, realStateMap);
assert.equal(layoutModels.flat().find((item) => item.toothNumber === "31").events[0].kind, "CARIES", "layout uses real current state");
assert.equal(layoutModels.flat().find((item) => item.toothNumber === "14").events[0].status, "PLANNED", "layout preserves planned status");
const filteredLayoutModels = layout.buildDualClinicalModelsForRows(layout.PERMANENT_DUAL_ROWS, realStateMap, { visibleLayers: new Set(["PERFORMED"]) });
assert.equal(filteredLayoutModels.flat().find((item) => item.toothNumber === "31").events.length, 0, "layout respects visible layer filters");

console.log("classic orientation and real adapter tests OK");
