import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  PERIODONTAL_ARCH_WIDTH,
  PERIODONTAL_SITE_COLUMNS,
  PERIODONTAL_TOOTH_WIDTH,
  mapGingivalMarginY,
  mapPocketBottomY,
  periodontalToothFamily,
} from "../lib/periodontalGraph.ts";
import {
  MAXILLARY_FDI,
  MANDIBULAR_FDI,
  calculateClinicalAttachmentLevel,
} from "../lib/periodontalCharting.ts";

assert.equal(MAXILLARY_FDI.length, 16);
assert.equal(MANDIBULAR_FDI.length, 16);
assert.equal(PERIODONTAL_SITE_COLUMNS, 48);
assert.equal(PERIODONTAL_TOOTH_WIDTH, 64);
assert.equal(PERIODONTAL_ARCH_WIDTH, 1024);
assert.deepEqual(MAXILLARY_FDI, [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]);
assert.deepEqual(MANDIBULAR_FDI, [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]);

assert.equal(periodontalToothFamily(21), "INCISOR");
assert.equal(periodontalToothFamily(13), "CANINE");
assert.equal(periodontalToothFamily(25), "PREMOLAR");
assert.equal(periodontalToothFamily(36), "MOLAR");

const baseline = 100;
assert.ok(mapGingivalMarginY(-2, baseline, "MAXILLARY").y < baseline);
assert.ok(mapGingivalMarginY(2, baseline, "MAXILLARY").y > baseline);
assert.ok(mapGingivalMarginY(-2, baseline, "MANDIBULAR").y > baseline);
assert.ok(mapGingivalMarginY(2, baseline, "MANDIBULAR").y < baseline);

const shallowPocket = mapPocketBottomY(3, 0, baseline, "MANDIBULAR");
const deepPocket = mapPocketBottomY(6, 0, baseline, "MANDIBULAR");
assert.ok(deepPocket.y > shallowPocket.y, "A deeper mandibular probing depth must move the pocket bottom apically");
assert.equal(calculateClinicalAttachmentLevel(6, -2), 8);
assert.equal(calculateClinicalAttachmentLevel(4, 2), 2);

const graph = readFileSync(
  new URL("../components/periodontogram/PeriodontalGraph.tsx", import.meta.url),
  "utf8",
);
const editor = readFileSync(
  new URL("../components/periodontogram/RapidPeriodontalEditor.tsx", import.meta.url),
  "utf8",
);
const workspace = readFileSync(
  new URL("../components/periodontogram/PeriodontogramWorkspace.tsx", import.meta.url),
  "utf8",
);

assert.match(editor, /data-compact-periodontal-arch/);
assert.match(editor, /data-periodontal-site-columns="48"/);
assert.match(editor, /repeat\(\$\{PERIODONTAL_SITE_COLUMNS\}, minmax\(0, 1fr\)\)/);
assert.match(editor, /min-w-\[1200px\]/);
assert.match(editor, /sticky left-0/);
assert.match(editor, /border-l-2 border-l-slate-400/);
assert.match(editor, /overflow-x-auto/);
assert.match(editor, /16 posiciones · seis sitios por pieza/);

for (const label of [
  "Movilidad",
  "Implante",
  "Furcación",
  "Sangrado al sondaje",
  "Placa",
  "Supuración",
  "Margen gingival",
  "Profundidad de sondaje",
  "Nivel de inserción",
]) {
  assert.match(editor, new RegExp(label));
}

assert.doesNotMatch(editor, /function ToothCard/);
assert.doesNotMatch(editor, /w-\[246px\]/);
assert.match(editor, /Pieza seleccionada:/);
assert.match(editor, /tooth\.state === "ABSENT"/);
assert.match(editor, /tooth\.state === "IMPLANT"/);
assert.match(editor, /event\.key === "Enter"/);
assert.match(editor, /event\.shiftKey/);
assert.match(editor, /event\.key === "Backspace"/);
assert.match(editor, /props\.onFocus/);
assert.match(editor, /props\.onActivate/);

assert.match(editor, /gridColumn: `span \$\{PERIODONTAL_SITE_COLUMNS\} \/ span \$\{PERIODONTAL_SITE_COLUMNS\}`/);
assert.match(editor, /data-periodontal-graph-column-span=\{PERIODONTAL_SITE_COLUMNS\}/);
assert.match(graph, /data-tooth-family=\{family\.toLowerCase\(\)\}/);
assert.match(graph, /data-tooth-family="implant"/);
assert.match(graph, /data-tooth-family="absent"/);
assert.match(graph, /Margen gingival 0/);
assert.match(graph, /Sangrado al sondaje/);
assert.match(graph, /Fondo de sondaje/);
assert.match(graph, /siteGraphMarkers/);
assert.match(graph, /splitMeasuredSegments/);
assert.doesNotMatch(graph, /canvas/i);

assert.match(workspace, /exam=\{displayedExam\}/);
assert.match(workspace, /historicalPeriodontalExam/);

console.log("periodontogram-compact-layout-tests OK");
