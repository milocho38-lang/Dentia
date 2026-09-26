import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  findReplacingVersion,
  historicalPeriodontalExam,
  sortedPeriodontalVersions,
} from "../lib/periodontalVersionHistory.ts";

const site = {
  site_code: "BUCCAL_DISTAL",
  probing_depth_mm: 4,
  gingival_margin_mm: 1,
  clinical_attachment_level_mm: 3,
  is_periodontal_pocket: true,
  bleeding_on_probing: true,
  plaque: false,
  suppuration: null,
};
const historicalTooth = {
  fdi_number: 18,
  state: "PRESENT",
  mobility_grade: null,
  furcation_mesial: null,
  furcation_distal: null,
  clinical_note: "V1",
  sites: [site],
};
const currentTooth = { ...historicalTooth, clinical_note: "V2" };
const coverage = { eligible_sites: 1, evaluated_sites: 1, incomplete: false };
const indices = {
  bop: { positive_sites: 1, evaluated_sites: 1, percentage: 100 },
  plaque: { positive_sites: 0, evaluated_sites: 1, percentage: 0 },
};
const v1 = {
  id: "version-1",
  exam_id: "exam-1",
  version_number: 1,
  status: "FINALIZED",
  schema_version: "PERIO-2",
  row_version: 3,
  content: {},
  snapshot: { teeth: [historicalTooth], coverage, indices },
  snapshot_hash: "v1-hash",
  integrity_status: "PASS",
  supersedes_version_id: null,
  correction_reason: null,
  created_by_user_id: "user-1",
  finalized_by_user_id: "user-1",
  finalized_at: "2026-09-22T14:00:00Z",
  created_at: "2026-09-22T13:00:00Z",
};
const v2 = {
  ...v1,
  id: "version-2",
  version_number: 2,
  row_version: 2,
  snapshot: { teeth: [currentTooth], coverage, indices },
  snapshot_hash: "v2-hash",
  supersedes_version_id: v1.id,
  correction_reason: "Corrección clínica trazable",
  finalized_at: "2026-09-23T14:00:00Z",
  created_at: "2026-09-23T13:00:00Z",
};
const exam = {
  id: "exam-1",
  company_id: "company-1",
  patient_id: "patient-1",
  site_id: "site-1",
  site_name: "Sede principal",
  responsible_dentist_id: "dentist-1",
  professional_name: "Dra. Demo",
  status: "FINALIZED",
  clinical_date: "2026-09-22",
  finalized_at: v2.finalized_at,
  row_version: 5,
  current_version: v2,
  versions: [v1, v2],
  teeth: [currentTooth],
  coverage,
  indices,
  created_at: "2026-09-22T13:00:00Z",
  updated_at: "2026-09-23T14:00:00Z",
};

assert.deepEqual(sortedPeriodontalVersions(exam).map((item) => item.version_number), [2, 1]);
assert.equal(findReplacingVersion(exam, v1)?.id, v2.id);
assert.equal(findReplacingVersion(exam, v2), null);

const historical = historicalPeriodontalExam(exam, v1.id);
assert.ok(historical);
assert.equal(historical.current_version.id, v1.id);
assert.equal(historical.current_version.snapshot_hash, "v1-hash");
assert.equal(historical.current_version.integrity_status, "PASS");
assert.equal(historical.teeth[0].clinical_note, "V1");
assert.deepEqual(historical.coverage, coverage);
assert.deepEqual(historical.indices, indices);
assert.equal(exam.current_version.id, v2.id);
assert.equal(exam.teeth[0].clinical_note, "V2");
assert.equal(historicalPeriodontalExam(exam, v2.id), exam);
assert.equal(historicalPeriodontalExam(exam, "foreign-version"), null);

const workspace = readFileSync(
  new URL("../components/periodontogram/PeriodontogramWorkspace.tsx", import.meta.url),
  "utf8",
);
const editor = readFileSync(
  new URL("../components/periodontogram/RapidPeriodontalEditor.tsx", import.meta.url),
  "utf8",
);

assert.match(workspace, /Versiones del examen · Actual:/);
assert.match(workspace, /Versión histórica/);
assert.match(workspace, /Histórica/);
assert.match(workspace, /Consulta de solo lectura/);
assert.match(workspace, /Volver a versión actual/);
assert.match(workspace, /Reemplazada por versión/);
assert.match(workspace, /Motivo de corrección/);
assert.match(workspace, /!isHistorical && selected\.status === "DRAFT"/);
assert.match(workspace, /!isHistorical && selected\.status === "FINALIZED"/);
assert.match(editor, /disabled=\{!canEdit\}/);
assert.match(editor, /readOnlyLabel/);

console.log("periodontogram-version-history-tests OK");
