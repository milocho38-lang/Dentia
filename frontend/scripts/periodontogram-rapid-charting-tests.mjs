import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  MAXILLARY_FDI,
  MANDIBULAR_FDI,
  buildCaptureSequence,
  calculateClinicalAttachmentLevel,
  calculateDraftIndicators,
  cycleTriState,
  isPocket,
  siteOrderForTooth,
} from "../lib/periodontalCharting.ts";

const teeth = [...MAXILLARY_FDI, ...MANDIBULAR_FDI].map((fdi_number) => ({
  fdi_number,
  state: "PRESENT",
}));

assert.deepEqual(siteOrderForTooth(18), [
  "BUCCAL_DISTAL", "BUCCAL_MID", "BUCCAL_MESIAL",
  "LINGUAL_DISTAL", "LINGUAL_MID", "LINGUAL_MESIAL",
]);
assert.deepEqual(siteOrderForTooth(28), [
  "BUCCAL_MESIAL", "BUCCAL_MID", "BUCCAL_DISTAL",
  "LINGUAL_MESIAL", "LINGUAL_MID", "LINGUAL_DISTAL",
]);
assert.deepEqual(siteOrderForTooth(48), siteOrderForTooth(18));
assert.deepEqual(siteOrderForTooth(38), siteOrderForTooth(28));

const pdSequence = buildCaptureSequence(teeth, "PD");
assert.equal(pdSequence.length, 192);
assert.equal(pdSequence[0].key, "18:BUCCAL_DISTAL:PD");
assert.equal(pdSequence[2].key, "18:BUCCAL_MESIAL:PD");
assert.equal(pdSequence[3].key, "18:LINGUAL_DISTAL:PD");
assert.equal(pdSequence[5].key, "18:LINGUAL_MESIAL:PD");
assert.equal(pdSequence[6].key, "17:BUCCAL_DISTAL:PD");
assert.equal(pdSequence[96].key, "48:BUCCAL_DISTAL:PD");
assert.equal(pdSequence.at(-1).key, "38:LINGUAL_DISTAL:PD");

const combined = buildCaptureSequence(teeth, "PD_GM");
assert.equal(combined.length, 384);
assert.deepEqual(combined.slice(0, 4).map((target) => target.measurement), ["PD", "GM", "PD", "GM"]);
assert.equal(combined[0].fdiNumber, 18);
assert.equal(combined.at(-1).fdiNumber, 38);

const withAbsent = buildCaptureSequence(
  teeth.map((tooth) => tooth.fdi_number === 17 ? { ...tooth, state: "ABSENT" } : tooth),
  "GM",
);
assert.equal(withAbsent.length, 186);
assert.equal(withAbsent.some((target) => target.fdiNumber === 17), false);

assert.equal(calculateClinicalAttachmentLevel(4, -2), 6);
assert.equal(calculateClinicalAttachmentLevel(4, 2), 2);
assert.equal(calculateClinicalAttachmentLevel(null, 2), null);
assert.equal(calculateClinicalAttachmentLevel(4, null), null);
assert.equal(isPocket(3), false);
assert.equal(isPocket(4), true);
assert.equal(isPocket(5), true);
assert.deepEqual([cycleTriState(null), cycleTriState(false), cycleTriState(true)], [false, true, null]);

const indicatorTeeth = [
  {
    fdi_number: 18,
    state: "PRESENT",
    mobility_grade: null,
    furcation_mesial: null,
    furcation_distal: null,
    clinical_note: null,
    sites: [
      { probing_depth_mm: 0, gingival_margin_mm: 0, bleeding_on_probing: false, plaque: true },
      { probing_depth_mm: 4, gingival_margin_mm: -2, bleeding_on_probing: true, plaque: null },
    ],
  },
  {
    fdi_number: 17,
    state: "IMPLANT",
    mobility_grade: null,
    furcation_mesial: null,
    furcation_distal: null,
    clinical_note: null,
    sites: [
      { probing_depth_mm: null, gingival_margin_mm: null, bleeding_on_probing: true, plaque: false },
    ],
  },
  { fdi_number: 16, state: "ABSENT", sites: new Array(6).fill({}) },
];
const indicators = calculateDraftIndicators(indicatorTeeth);
assert.equal(indicators.coverage.evaluated_sites, 2);
assert.equal(indicators.coverage.eligible_sites, 3);
assert.equal(indicators.indices.bop.percentage, 66.67);
assert.equal(indicators.indices.plaque.percentage, 50);

const workspace = readFileSync(
  new URL("../components/periodontogram/PeriodontogramWorkspace.tsx", import.meta.url),
  "utf8",
);
const editor = readFileSync(
  new URL("../components/periodontogram/RapidPeriodontalEditor.tsx", import.meta.url),
  "utf8",
);
const ui = `${workspace}\n${editor}`;
assert.match(ui, /Cambios sin guardar/);
assert.match(ui, /Pieza activa/);
assert.match(ui, /inputMode=/);
assert.match(ui, /event\.key === "Enter"/);
assert.match(ui, /event\.shiftKey/);
assert.match(ui, /event\.key === "Backspace"/);
assert.match(ui, /aria-label=/);
assert.match(workspace, /RapidPeriodontalEditor/);
assert.match(editor, /tooth\.state === "ABSENT"/);
assert.match(editor, /tooth\.state === "IMPLANT"/);
assert.match(editor, /suppuration/);
assert.match(editor, /MOLAR_FDI\.has/);
assert.match(editor, /mobility_grade/);
assert.match(editor, /clear_clinical_data/);
assert.doesNotMatch(ui, /setTimeout\([^)]*updatePeriodontalDraft/s);

console.log("periodontogram-rapid-charting-tests OK");
