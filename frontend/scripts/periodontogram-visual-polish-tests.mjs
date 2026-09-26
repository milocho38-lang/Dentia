import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

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

assert.match(graph, /CLINICAL_LINE_STROKE_WIDTH = 1\.6/);
assert.match(graph, /SINGLE_POINT_RADIUS = 1\.9/);
assert.match(graph, /strokeLinejoin="round"/);
assert.match(graph, /strokeLinecap="round"/);
assert.match(graph, /splitMeasuredSegments/);
assert.match(graph, /strokeDasharray=\{kind === "PD" \? "4 3" : undefined\}/);

assert.match(editor, /data-gm-zero-gutter-label="true"/);
assert.match(editor, /Margen gingival = 0/);
assert.match(graph, /data-gingival-margin-zero-line="true"/);
assert.doesNotMatch(graph, /<text[^>]*>\s*\{label\} · Margen gingival 0/);

assert.match(graph, /TOOTH_SCALE = 1\.12/);
assert.match(graph, /kind === "ABSENT" \? 1 : TOOTH_SCALE/);
assert.match(graph, /data-tooth-visual-scale=\{visualScale\}/);
assert.match(graph, /data-tooth-family="implant"/);
assert.match(graph, /data-tooth-family="absent" opacity=\{0\.48\}/);

assert.match(graph, /MARKER_LANE_GAP = 5/);
assert.match(graph, /data-site-marker-lanes="vertical"/);
assert.match(graph, /const bopY/);
assert.match(graph, /const plaqueY/);
assert.match(graph, /const suppurationY/);
assert.match(graph, /<circle cx=\{visual\.x\} cy=\{bopY\}/);
assert.match(graph, /<rect x=\{visual\.x - 2\.5\} y=\{plaqueY - 2\.5\}/);
assert.match(graph, /<polygon/);
assert.match(graph, /data-mobility-marker-offset="crown-side"/);
assert.match(graph, /data-furcation-marker-offset="root-side"/);

assert.match(graph, /pointerEvents="none"/);
assert.match(graph, /role="button"/);
assert.match(graph, /tabIndex=\{0\}/);
assert.match(graph, /event\.key === "Enter" \|\| event\.key === " "/);

for (const label of [
  "Margen gingival",
  "Fondo de sondaje",
  "Sangrado al sondaje",
  "Placa",
  "Supuración",
  "Bolsa ≥ 4 mm",
  "Implante",
  "Furcación",
]) {
  assert.match(graph, new RegExp(label));
}
assert.equal((editor.match(/<PeriodontalGraphLegend \/>/g) ?? []).length, 1);

assert.match(editor, /overflow-x-auto/);
assert.match(editor, /data-periodontal-graph-column-span=\{PERIODONTAL_SITE_COLUMNS\}/);
assert.match(editor, /data-periodontal-site-columns="48"/);
assert.match(
  editor,
  /teeth=\{props\.fdiNumbers\.map\(\(fdiNumber\) => props\.drafts\[fdiNumber\]\)\}/,
);
assert.match(workspace, /exam=\{displayedExam\}/);
assert.match(workspace, /historicalPeriodontalExam/);

console.log("periodontogram-visual-polish-tests OK");
