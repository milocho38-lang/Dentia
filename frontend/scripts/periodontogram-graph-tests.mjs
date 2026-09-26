import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  countPocketSites,
  mapGingivalMarginY,
  mapPocketBottomY,
  periodontalToothFamily,
  siteGraphAccessibleLabel,
  siteGraphDetail,
  siteGraphMarkers,
  splitMeasuredSegments,
  toothGraphKind,
  toothGraphMarkers,
} from "../lib/periodontalGraph.ts";
import { historicalPeriodontalExam } from "../lib/periodontalVersionHistory.ts";

const baseline = 100;
const maxillaryApical = mapGingivalMarginY(-2, baseline, "MAXILLARY");
const maxillaryCoronal = mapGingivalMarginY(2, baseline, "MAXILLARY");
const mandibularApical = mapGingivalMarginY(-2, baseline, "MANDIBULAR");
const mandibularCoronal = mapGingivalMarginY(2, baseline, "MANDIBULAR");
assert.ok(maxillaryApical.y < baseline, "GM -2 must move toward maxillary root/apical");
assert.ok(maxillaryCoronal.y > baseline, "GM +2 must move toward maxillary crown");
assert.ok(mandibularApical.y > baseline, "GM -2 must move toward mandibular root/apical");
assert.ok(mandibularCoronal.y < baseline, "GM +2 must move toward mandibular crown");
assert.equal(mapGingivalMarginY(null, baseline, "MAXILLARY"), null);
assert.equal(mapPocketBottomY(4, null, baseline, "MAXILLARY"), null);
assert.equal(mapPocketBottomY(null, -2, baseline, "MAXILLARY"), null);

const extreme = mapPocketBottomY(50, -20, baseline, "MANDIBULAR");
assert.equal(extreme.outOfScale, true);
assert.equal(extreme.displayedOffsetMm, 12);

const site = {
  site_code: "BUCCAL_DISTAL",
  probing_depth_mm: 4,
  gingival_margin_mm: -2,
  clinical_attachment_level_mm: 6,
  is_periodontal_pocket: true,
  bleeding_on_probing: true,
  plaque: true,
  suppuration: true,
};
const natural = {
  fdi_number: 16,
  state: "PRESENT",
  mobility_grade: 2,
  furcation_mesial: true,
  furcation_distal: true,
  clinical_note: null,
  sites: [site],
};
const absent = { ...natural, state: "ABSENT", mobility_grade: null, sites: [] };
const implant = { ...natural, state: "IMPLANT", mobility_grade: null };

assert.deepEqual(siteGraphMarkers(site), {
  pocket: true,
  bop: true,
  plaque: true,
  suppuration: true,
});
assert.equal(siteGraphMarkers({ ...site, probing_depth_mm: 3 }).pocket, false);
assert.deepEqual(
  siteGraphMarkers({
    ...site,
    probing_depth_mm: null,
    bleeding_on_probing: null,
    plaque: null,
    suppuration: null,
  }),
  { pocket: false, bop: false, plaque: false, suppuration: false },
);
assert.equal(toothGraphKind(natural.state), "NATURAL");
assert.equal(toothGraphKind(absent.state), "ABSENT");
assert.equal(toothGraphKind(implant.state), "IMPLANT");
assert.deepEqual(toothGraphMarkers(natural), {
  mobility: 2,
  furcationMesial: true,
  furcationDistal: true,
});
assert.deepEqual(toothGraphMarkers(implant), {
  mobility: null,
  furcationMesial: false,
  furcationDistal: false,
});
assert.equal(countPocketSites([natural, absent, { ...implant, sites: [{ ...site, probing_depth_mm: 5 }] }]), 2);
assert.equal(siteGraphDetail(site).clinicalAttachmentLevel, 6);
assert.match(
  siteGraphAccessibleLabel(natural, site),
  /profundidad de sondaje 4 mm, margen gingival -2 mm, nivel de inserción 6 mm/,
);
assert.match(
  siteGraphAccessibleLabel(natural, {
    ...site,
    probing_depth_mm: null,
    gingival_margin_mm: null,
    bleeding_on_probing: null,
  }),
  /profundidad de sondaje no evaluada, margen gingival no evaluado, nivel de inserción no disponible, sangrado al sondaje No evaluado/,
);

assert.equal(periodontalToothFamily(11), "INCISOR");
assert.equal(periodontalToothFamily(23), "CANINE");
assert.equal(periodontalToothFamily(34), "PREMOLAR");
assert.equal(periodontalToothFamily(48), "MOLAR");

assert.deepEqual(
  splitMeasuredSegments([
    { x: 1, y: 1 },
    { x: 2, y: 2 },
    null,
    null,
    { x: 5, y: 5 },
  ]),
  [[{ x: 1, y: 1 }, { x: 2, y: 2 }], [{ x: 5, y: 5 }]],
  "Null sites must create real gaps instead of interpolated clinical lines",
);

const coverage = { eligible_sites: 1, evaluated_sites: 1, incomplete: false };
const indices = {
  bop: { positive_sites: 1, evaluated_sites: 1, percentage: 100 },
  plaque: { positive_sites: 1, evaluated_sites: 1, percentage: 100 },
};
const version = (number, tooth, supersedes = null) => ({
  id: `version-${number}`,
  exam_id: "exam-1",
  version_number: number,
  status: "FINALIZED",
  schema_version: "PERIODONTAL_EXAM_V2",
  row_version: number,
  content: {},
  snapshot: { teeth: [tooth], coverage, indices },
  snapshot_hash: `hash-${number}`,
  integrity_status: "PASS",
  supersedes_version_id: supersedes,
  correction_reason: supersedes ? "Corrección" : null,
  created_by_user_id: "user-1",
  finalized_by_user_id: "user-1",
  finalized_at: `2026-09-2${number}T12:00:00Z`,
  created_at: `2026-09-2${number}T11:00:00Z`,
});
const v1Tooth = { ...natural, clinical_note: "V1", sites: [{ ...site, probing_depth_mm: 4 }] };
const v2Tooth = { ...natural, clinical_note: "V2", sites: [{ ...site, probing_depth_mm: 6 }] };
const v1 = version(1, v1Tooth);
const v2 = version(2, v2Tooth, v1.id);
const exam = {
  id: "exam-1",
  company_id: "company-1",
  patient_id: "patient-1",
  site_id: "site-1",
  site_name: "Sede",
  responsible_dentist_id: "dentist-1",
  professional_name: "Dra. Demo",
  status: "FINALIZED",
  clinical_date: "2026-09-21",
  finalized_at: v2.finalized_at,
  row_version: 2,
  current_version: v2,
  versions: [v2, v1],
  teeth: [v2Tooth],
  coverage,
  indices,
  created_at: v1.created_at,
  updated_at: v2.finalized_at,
};
const historical = historicalPeriodontalExam(exam, v1.id);
assert.equal(historical.teeth[0].sites[0].probing_depth_mm, 4);
assert.equal(exam.teeth[0].sites[0].probing_depth_mm, 6);
assert.equal(countPocketSites(historical.teeth), 1);

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

assert.match(graph, /<svg/);
assert.match(graph, /viewBox=/);
assert.match(graph, /role="button"/);
assert.match(graph, /aria-label=/);
assert.match(graph, /Sangrado al sondaje/);
assert.match(graph, /Placa/);
assert.match(graph, /Supuración/);
assert.match(graph, /Bolsa ≥ 4 mm/);
assert.match(graph, /Furcación/);
assert.match(graph, /data-tooth-family="implant"/);
assert.match(graph, /data-tooth-family="absent"/);
assert.match(graph, /data-tooth-family=\{family\.toLowerCase\(\)\}/);
assert.doesNotMatch(graph, /canvas/i);
assert.doesNotMatch(graph, /periodontitis|enfermedad periodontal/i);
assert.match(editor, /<PeriodontalArchGraph/);
assert.match(editor, /data-periodontal-site-columns="48"/);
assert.match(editor, /gridTemplateColumns: `176px repeat\(\$\{PERIODONTAL_SITE_COLUMNS\}, minmax\(0, 1fr\)\)`/);
assert.match(editor, /sticky left-0/);
assert.match(editor, /Sangrado al sondaje/);
assert.match(editor, /Margen gingival/);
assert.match(editor, /Profundidad de sondaje/);
assert.match(editor, /Nivel de inserción/);
assert.doesNotMatch(editor, /w-\[246px\]/);
assert.doesNotMatch(editor, /function ToothCard/);
assert.match(editor, /updateSite/);
assert.match(workspace, /exam=\{displayedExam\}/);

console.log("periodontogram-graph-tests OK");
