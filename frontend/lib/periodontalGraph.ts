import { calculateClinicalAttachmentLevel, describeSite, isPocket } from "./periodontalCharting.ts";
import type {
  PeriodontalSite,
  PeriodontalTooth,
  PeriodontalToothState,
} from "@/types/periodontogram";

export type PeriodontalGraphArch = "MAXILLARY" | "MANDIBULAR";
export type PeriodontalGraphPoint = { x: number; y: number };
export type PeriodontalToothFamily = "INCISOR" | "CANINE" | "PREMOLAR" | "MOLAR";

export const PERIODONTAL_TEETH_PER_ARCH = 16;
export const PERIODONTAL_SITES_PER_TOOTH_FACE = 3;
export const PERIODONTAL_SITE_COLUMNS =
  PERIODONTAL_TEETH_PER_ARCH * PERIODONTAL_SITES_PER_TOOTH_FACE;
export const PERIODONTAL_TOOTH_WIDTH = 64;
export const PERIODONTAL_ARCH_WIDTH =
  PERIODONTAL_TEETH_PER_ARCH * PERIODONTAL_TOOTH_WIDTH;

export const periodontalToothCenterX = (toothIndex: number) =>
  toothIndex * PERIODONTAL_TOOTH_WIDTH + PERIODONTAL_TOOTH_WIDTH / 2;

export const periodontalSiteX = (toothIndex: number, siteIndex: number) =>
  toothIndex * PERIODONTAL_TOOTH_WIDTH +
  PERIODONTAL_TOOTH_WIDTH * ([1 / 6, 1 / 2, 5 / 6][siteIndex] ?? 1 / 2);

export const PERIODONTAL_GRAPH_MM_SCALE = 5;
export const PERIODONTAL_GRAPH_CORONAL_LIMIT_MM = 6;
export const PERIODONTAL_GRAPH_APICAL_LIMIT_MM = 12;

export interface ScaledGraphValue {
  y: number;
  outOfScale: boolean;
  displayedOffsetMm: number;
}

const clampOffset = (offsetMm: number) =>
  Math.max(
    -PERIODONTAL_GRAPH_CORONAL_LIMIT_MM,
    Math.min(PERIODONTAL_GRAPH_APICAL_LIMIT_MM, offsetMm),
  );

export const graphApicalDirection = (arch: PeriodontalGraphArch) =>
  arch === "MAXILLARY" ? -1 : 1;

export function periodontalToothFamily(fdiNumber: number): PeriodontalToothFamily {
  const position = fdiNumber % 10;
  if (position <= 2) return "INCISOR";
  if (position === 3) return "CANINE";
  if (position <= 5) return "PREMOLAR";
  return "MOLAR";
}

export function mapGraphOffsetY(
  offsetMm: number,
  baselineY: number,
  arch: PeriodontalGraphArch,
): ScaledGraphValue {
  const displayedOffsetMm = clampOffset(offsetMm);
  return {
    y: baselineY + graphApicalDirection(arch) * displayedOffsetMm * PERIODONTAL_GRAPH_MM_SCALE,
    outOfScale: displayedOffsetMm !== offsetMm,
    displayedOffsetMm,
  };
}

export function mapGingivalMarginY(
  gingivalMarginMm: number | null,
  baselineY: number,
  arch: PeriodontalGraphArch,
): ScaledGraphValue | null {
  if (gingivalMarginMm === null) return null;
  return mapGraphOffsetY(-gingivalMarginMm, baselineY, arch);
}

export function mapPocketBottomY(
  probingDepthMm: number | null,
  gingivalMarginMm: number | null,
  baselineY: number,
  arch: PeriodontalGraphArch,
): ScaledGraphValue | null {
  if (probingDepthMm === null || gingivalMarginMm === null) return null;
  return mapGraphOffsetY(-gingivalMarginMm + probingDepthMm, baselineY, arch);
}

export function splitMeasuredSegments(
  points: Array<PeriodontalGraphPoint | null>,
): PeriodontalGraphPoint[][] {
  const segments: PeriodontalGraphPoint[][] = [];
  let current: PeriodontalGraphPoint[] = [];
  for (const point of points) {
    if (point) {
      current.push(point);
      continue;
    }
    if (current.length > 0) segments.push(current);
    current = [];
  }
  if (current.length > 0) segments.push(current);
  return segments;
}

export const toothGraphKind = (state: PeriodontalToothState) =>
  state === "ABSENT" ? "ABSENT" : state === "IMPLANT" ? "IMPLANT" : "NATURAL";

export const siteGraphMarkers = (site: PeriodontalSite) => ({
  pocket: isPocket(site.probing_depth_mm),
  bop: site.bleeding_on_probing === true,
  plaque: site.plaque === true,
  suppuration: site.suppuration === true,
});

export const toothGraphMarkers = (tooth: PeriodontalTooth) => ({
  mobility: tooth.state === "PRESENT" ? tooth.mobility_grade : null,
  furcationMesial: tooth.state === "PRESENT" && tooth.furcation_mesial === true,
  furcationDistal: tooth.state === "PRESENT" && tooth.furcation_distal === true,
});

export const countPocketSites = (teeth: PeriodontalTooth[]) =>
  teeth.reduce(
    (total, tooth) =>
      tooth.state === "ABSENT"
        ? total
        : total + tooth.sites.filter((site) => isPocket(site.probing_depth_mm)).length,
    0,
  );

const clinicalBoolean = (value: boolean | null) =>
  value === null ? "No evaluado" : value ? "Sí" : "No";

export function siteGraphAccessibleLabel(
  tooth: PeriodontalTooth,
  site: PeriodontalSite,
) {
  const descriptor = describeSite(tooth.fdi_number, site.site_code);
  const face = descriptor.face === "BUCCAL"
    ? "vestibular"
    : descriptor.face === "PALATAL"
      ? "palatino"
      : "lingual";
  const cal = calculateClinicalAttachmentLevel(
    site.probing_depth_mm,
    site.gingival_margin_mm,
  );
  return [
    `Pieza ${tooth.fdi_number}`,
    `${face} ${descriptor.siteLabel.toLowerCase()}`,
    `profundidad de sondaje ${site.probing_depth_mm === null ? "no evaluada" : `${site.probing_depth_mm} mm`}`,
    `margen gingival ${site.gingival_margin_mm === null ? "no evaluado" : `${site.gingival_margin_mm} mm`}`,
    `nivel de inserción ${cal === null ? "no disponible" : `${cal} mm`}`,
    `sangrado al sondaje ${clinicalBoolean(site.bleeding_on_probing)}`,
    `placa ${clinicalBoolean(site.plaque)}`,
    `supuración ${clinicalBoolean(site.suppuration)}`,
  ].join(", ");
}

export const siteGraphDetail = (site: PeriodontalSite) => ({
  probingDepth: site.probing_depth_mm,
  gingivalMargin: site.gingival_margin_mm,
  clinicalAttachmentLevel: calculateClinicalAttachmentLevel(
    site.probing_depth_mm,
    site.gingival_margin_mm,
  ),
  bop: site.bleeding_on_probing,
  plaque: site.plaque,
  suppuration: site.suppuration,
});
