import type {
  PeriodontalSiteCode,
  PeriodontalTooth,
} from "@/types/periodontogram";

export type PeriodontalCaptureMode = "PD" | "GM" | "PD_GM";
export type PeriodontalMeasurement = "PD" | "GM";

export interface PeriodontalFocusTarget {
  key: string;
  fdiNumber: number;
  siteCode: PeriodontalSiteCode;
  measurement: PeriodontalMeasurement;
  arch: "MAXILLARY" | "MANDIBULAR";
  face: "BUCCAL" | "PALATAL" | "LINGUAL";
  siteLabel: "Distal" | "Medio" | "Mesial";
}

export const MAXILLARY_FDI = [
  18, 17, 16, 15, 14, 13, 12, 11,
  21, 22, 23, 24, 25, 26, 27, 28,
] as const;

export const MANDIBULAR_FDI = [
  48, 47, 46, 45, 44, 43, 42, 41,
  31, 32, 33, 34, 35, 36, 37, 38,
] as const;

export const MOLAR_FDI = new Set([18, 17, 16, 26, 27, 28, 48, 47, 46, 36, 37, 38]);

const RIGHT_QUADRANTS = new Set([1, 4]);

const suffixOrder = (fdiNumber: number) =>
  RIGHT_QUADRANTS.has(Math.floor(fdiNumber / 10))
    ? (["DISTAL", "MID", "MESIAL"] as const)
    : (["MESIAL", "MID", "DISTAL"] as const);

export function siteOrderForTooth(fdiNumber: number): PeriodontalSiteCode[] {
  const suffixes = suffixOrder(fdiNumber);
  return [
    ...suffixes.map((suffix) => `BUCCAL_${suffix}` as PeriodontalSiteCode),
    ...suffixes.map((suffix) => `LINGUAL_${suffix}` as PeriodontalSiteCode),
  ];
}

export function describeSite(
  fdiNumber: number,
  siteCode: PeriodontalSiteCode,
): Pick<PeriodontalFocusTarget, "arch" | "face" | "siteLabel"> {
  const maxillary = Math.floor(fdiNumber / 10) <= 2;
  const suffix = siteCode.split("_").at(-1);
  return {
    arch: maxillary ? "MAXILLARY" : "MANDIBULAR",
    face: siteCode.startsWith("BUCCAL") ? "BUCCAL" : maxillary ? "PALATAL" : "LINGUAL",
    siteLabel: suffix === "DISTAL" ? "Distal" : suffix === "MESIAL" ? "Mesial" : "Medio",
  };
}

export function focusKey(
  fdiNumber: number,
  siteCode: PeriodontalSiteCode,
  measurement: PeriodontalMeasurement,
) {
  return `${fdiNumber}:${siteCode}:${measurement}`;
}

export function buildCaptureSequence(
  teeth: Pick<PeriodontalTooth, "fdi_number" | "state">[],
  mode: PeriodontalCaptureMode,
): PeriodontalFocusTarget[] {
  const toothByFdi = new Map(teeth.map((tooth) => [tooth.fdi_number, tooth]));
  const measurements: PeriodontalMeasurement[] =
    mode === "PD_GM" ? ["PD", "GM"] : [mode];
  const sequence: PeriodontalFocusTarget[] = [];
  for (const fdiNumber of [...MAXILLARY_FDI, ...MANDIBULAR_FDI]) {
    if (toothByFdi.get(fdiNumber)?.state === "ABSENT") continue;
    for (const siteCode of siteOrderForTooth(fdiNumber)) {
      const descriptor = describeSite(fdiNumber, siteCode);
      for (const measurement of measurements) {
        sequence.push({
          key: focusKey(fdiNumber, siteCode, measurement),
          fdiNumber,
          siteCode,
          measurement,
          ...descriptor,
        });
      }
    }
  }
  return sequence;
}

export function calculateClinicalAttachmentLevel(
  probingDepth: number | null,
  gingivalMargin: number | null,
) {
  return probingDepth === null || gingivalMargin === null
    ? null
    : probingDepth - gingivalMargin;
}

export function isPocket(probingDepth: number | null) {
  return probingDepth !== null && probingDepth >= 4;
}

export function cycleTriState(value: boolean | null): boolean | null {
  if (value === null) return false;
  if (value === false) return true;
  return null;
}

function index(values: Array<boolean | null>) {
  const evaluated = values.filter((value): value is boolean => value !== null);
  const positive = evaluated.filter(Boolean).length;
  return {
    positive_sites: positive,
    evaluated_sites: evaluated.length,
    percentage: evaluated.length === 0
      ? null
      : Math.round((positive * 10000) / evaluated.length) / 100,
  };
}

export function calculateDraftIndicators(teeth: PeriodontalTooth[]) {
  let eligibleSites = 0;
  let evaluatedSites = 0;
  const bop: Array<boolean | null> = [];
  const plaque: Array<boolean | null> = [];
  for (const tooth of teeth) {
    if (tooth.state === "ABSENT") continue;
    eligibleSites += tooth.sites.length;
    for (const site of tooth.sites) {
      if (site.probing_depth_mm !== null && site.gingival_margin_mm !== null) {
        evaluatedSites += 1;
      }
      bop.push(site.bleeding_on_probing);
      plaque.push(site.plaque);
    }
  }
  return {
    coverage: {
      eligible_sites: eligibleSites,
      evaluated_sites: evaluatedSites,
      incomplete: evaluatedSites < eligibleSites,
    },
    indices: { bop: index(bop), plaque: index(plaque) },
  };
}
