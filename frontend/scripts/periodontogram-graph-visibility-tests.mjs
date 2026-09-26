import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  PERIODONTAL_ARCH_WIDTH,
  PERIODONTAL_SITE_COLUMNS,
  PERIODONTAL_TOOTH_WIDTH,
  mapGingivalMarginY,
  mapPocketBottomY,
  periodontalSiteX,
  periodontalToothCenterX,
  splitMeasuredSegments,
} from "../lib/periodontalGraph.ts";

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

// One shared coordinate model drives the 48 matrix columns and the SVG.
assert.equal(PERIODONTAL_SITE_COLUMNS, 48);
assert.equal(PERIODONTAL_ARCH_WIDTH, 1024);
assert.equal(PERIODONTAL_TOOTH_WIDTH, 64);
assert.equal(periodontalToothCenterX(0), 32);
assert.equal(periodontalToothCenterX(15), 992);
assert.equal(periodontalSiteX(0, 1), periodontalToothCenterX(0));
assert.equal(periodontalSiteX(1, 0), 64 + 64 / 6);
assert.ok(periodontalSiteX(0, 0) < periodontalSiteX(0, 1));
assert.ok(periodontalSiteX(0, 1) < periodontalSiteX(0, 2));

// The graph must occupy all site tracks. `col-span-48` is not a generated
// Tailwind utility in this project and was the original visibility defect.
assert.doesNotMatch(editor, /className="col-span-48/);
assert.match(editor, /gridColumn: `span \$\{PERIODONTAL_SITE_COLUMNS\} \/ span \$\{PERIODONTAL_SITE_COLUMNS\}`/);
assert.match(editor, /data-periodontal-graph-column-span=\{PERIODONTAL_SITE_COLUMNS\}/);
assert.match(graph, /width=\{PERIODONTAL_ARCH_WIDTH\}/);
assert.match(graph, /height=\{SVG_HEIGHT\}/);
assert.match(graph, /min-h-\[148px\]/);

// Each face is followed immediately by its own graph inside the same local
// horizontal scroller, preserving matrix/graph alignment.
assert.match(
  editor,
  /<FaceMatrix \{\.\.\.props\} face="BUCCAL" label="Vestibular" \/>\s*<FaceGraph \{\.\.\.props\} face="BUCCAL" label="Vestibular" \/>/,
);
assert.match(
  editor,
  /<FaceMatrix \{\.\.\.props\} face="LINGUAL" label=\{secondaryFace\} \/>\s*<FaceGraph \{\.\.\.props\} face="LINGUAL" label=\{secondaryFace\} \/>/,
);
assert.match(editor, /overflow-x-auto/);
assert.match(editor, /data-compact-periodontal-arch/);

// Clinical direction and depth are deterministic on both arches.
const baseline = 70;
assert.ok(mapGingivalMarginY(-2, baseline, "MAXILLARY").y < baseline);
assert.ok(mapGingivalMarginY(2, baseline, "MAXILLARY").y > baseline);
assert.ok(mapGingivalMarginY(-2, baseline, "MANDIBULAR").y > baseline);
assert.ok(mapGingivalMarginY(2, baseline, "MANDIBULAR").y < baseline);
assert.ok(
  mapPocketBottomY(6, 0, baseline, "MANDIBULAR").y >
    mapPocketBottomY(3, 0, baseline, "MANDIBULAR").y,
);
assert.ok(
  mapPocketBottomY(6, 0, baseline, "MAXILLARY").y <
    mapPocketBottomY(3, 0, baseline, "MAXILLARY").y,
);

// Null/absent measurements interrupt curves instead of inventing continuity.
assert.deepEqual(
  splitMeasuredSegments([
    { x: 1, y: 1 },
    null,
    { x: 3, y: 3 },
  ]),
  [[{ x: 1, y: 1 }], [{ x: 3, y: 3 }]],
);
assert.match(graph, /tooth\.state === "ABSENT"\s*\? null/);
assert.match(graph, /data-tooth-family="absent"/);
assert.match(graph, /data-tooth-family="implant"/);

// Curves, threshold aid and site markers remain explicit and local.
assert.match(graph, /strokeDasharray=\{kind === "PD" \? "4 3" : undefined\}/);
assert.match(graph, /markers\.pocket/);
assert.match(graph, /markers\.bop/);
assert.match(graph, /markers\.plaque/);
assert.match(graph, /markers\.suppuration/);
assert.match(graph, /markers\.furcationMesial/);
assert.match(graph, /markers\.furcationDistal/);

// Draft values are passed directly from React state; no save/request is in the
// render path. Historical versions continue to use the selected snapshot.
assert.match(editor, /teeth=\{props\.fdiNumbers\.map\(\(fdiNumber\) => props\.drafts\[fdiNumber\]\)\}/);
assert.match(editor, /setDrafts\(\(current\) =>/);
assert.match(editor, /updateSite\(/);
assert.match(workspace, /exam=\{displayedExam\}/);
assert.match(workspace, /historicalPeriodontalExam/);

console.log("periodontogram-graph-visibility-tests OK");
