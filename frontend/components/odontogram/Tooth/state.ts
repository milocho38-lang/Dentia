import { DDS_STATE_LABELS, DDS_VISUAL_PRIORITY } from "./constants";
import type { ToothDetail, ToothRenderState, ToothSurface, ToothVisualState } from "./types";

function normalized(value: string | null | undefined) {
  return (value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase();
}

function includesAny(value: string, terms: string[]) {
  return terms.some((term) => value.includes(normalized(term)));
}

function isProximalSurface(surface: ToothSurface) {
  return surface === "MESIAL" || surface === "DISTAL";
}

function normalizeSurfaces(detail: ToothDetail): ToothSurface[] {
  return detail.surfaces?.length ? detail.surfaces : [];
}

function requiresLocalizedVisualFallback(state: ToothVisualState) {
  return [
    "OCCLUSAL_CARIES",
    "PROXIMAL_CARIES",
    "SIMPLE_FILLING",
    "MULTIPLE_FILLINGS",
    "TEMPORARY_RESTORATION",
    "SEALANT",
  ].includes(state);
}

function isDiagnosisVisualState(state: ToothVisualState) {
  return [
    "OCCLUSAL_CARIES",
    "PROXIMAL_CARIES",
    "CERVICAL_CARIES",
    "NON_CARIOUS_CERVICAL_LESION",
    "WEAR",
    "FRACTURE",
    "MOBILITY",
  ].includes(state);
}

function isPerformedTreatmentVisualState(state: ToothVisualState) {
  return [
    "SIMPLE_FILLING",
    "MULTIPLE_FILLINGS",
    "DEFINITIVE_CROWN",
    "TEMPORARY_CROWN",
    "ENDODONTICS",
    "POST",
    "IMPLANT",
    "FIXED_PROSTHESIS",
    "REMOVABLE_PROSTHESIS",
    "TEMPORARY_RESTORATION",
    "SEALANT",
  ].includes(state);
}

function clinicalSummaryLabel({
  primary,
  hasDetails,
  hasVisibleDiagnosis,
  hasPerformedTreatment,
  hasPlannedTreatment,
  unlocalizedStates,
}: {
  primary: ToothVisualState;
  hasDetails: boolean;
  hasVisibleDiagnosis: boolean;
  hasPerformedTreatment: boolean;
  hasPlannedTreatment: boolean;
  unlocalizedStates: Set<ToothVisualState>;
}) {
  if (unlocalizedStates.has("OCCLUSAL_CARIES") || unlocalizedStates.has("PROXIMAL_CARIES")) {
    return "Diagnóstico sin superficie específica";
  }
  if (hasVisibleDiagnosis) return "Diagnóstico activo";
  if (hasPerformedTreatment) return "Tratamiento realizado";
  if (hasPlannedTreatment) return "Tratamiento planificado";
  if (primary === "HEALTHY" && hasDetails) return "Sin representación anatómica";
  return DDS_STATE_LABELS[primary];
}

export function classifyToothDetail(detail: ToothDetail): ToothVisualState {
  const text = normalized(`${detail.catalogCode} ${detail.catalogName} ${detail.catalogType ?? ""}`);
  const layer = normalized(detail.layer);

  if (layer === "PLANNED") return "PLANNED_TREATMENT";
  if (includesAny(text, ["AUSENTE", "EXTRAC", "EXFOLIADO", "MISSING"])) return "MISSING";
  if (includesAny(text, ["IMPLANTE", "IMPLANT"])) return "IMPLANT";
  if (includesAny(text, ["PROTESIS FIJA", "PRÓTESIS FIJA", "PUENTE", "FIXED"])) return "FIXED_PROSTHESIS";
  if (includesAny(text, ["PROTESIS REMOVIBLE", "PRÓTESIS REMOVIBLE", "REMOVIBLE"])) return "REMOVABLE_PROSTHESIS";
  if (includesAny(text, ["CORONA TEMPORAL"])) return "TEMPORARY_CROWN";
  if (includesAny(text, ["CORONA", "CROWN"])) return "DEFINITIVE_CROWN";
  if (includesAny(text, ["POSTE", "POST"])) return "POST";
  if (includesAny(text, ["ENDODONCIA", "ENDO", "CONDUCTO"])) return "ENDODONTICS";
  if (includesAny(text, ["RESTAURACION TEMPORAL", "RESTAURACIÓN TEMPORAL", "OBTURACION TEMPORAL", "OBTURACIÓN TEMPORAL"])) {
    return "TEMPORARY_RESTORATION";
  }
  if (includesAny(text, ["SELLANTE", "SEALANT"])) return "SEALANT";
  if (includesAny(text, ["OBTURACION", "OBTURACIÓN", "RESINA", "RESTAURACION", "RESTAURACIÓN"])) {
    return normalizeSurfaces(detail).length > 1 ? "MULTIPLE_FILLINGS" : "SIMPLE_FILLING";
  }
  if (includesAny(text, ["LESION CERVICAL NO CARIOSA", "LESIÓN CERVICAL NO CARIOSA", "ABRASION", "ABRASIÓN", "EROSION", "EROSIÓN"])) {
    return "NON_CARIOUS_CERVICAL_LESION";
  }
  if (includesAny(text, ["LESION CERVICAL", "LESIÓN CERVICAL", "CARIES CERVICAL"])) return "CERVICAL_CARIES";
  if (includesAny(text, ["DESGASTE", "WEAR"])) return "WEAR";
  if (includesAny(text, ["FRACTURA", "FRACTURE"])) return "FRACTURE";
  if (includesAny(text, ["MOVILIDAD", "MOBILITY"])) return "MOBILITY";
  if (includesAny(text, ["CARIES"])) {
    const surfaces = normalizeSurfaces(detail);
    if (surfaces.some(isProximalSurface)) return "PROXIMAL_CARIES";
    if (surfaces.includes("OCCLUSAL") || surfaces.includes("INCISAL")) return "OCCLUSAL_CARIES";
    return "OCCLUSAL_CARIES";
  }
  if (includesAny(text, ["DIAGNOSIS_GENERAL", "PULPITIS", "NECROSIS", "PERIAPICAL"])) return "HEALTHY";
  if (layer === "PERFORMED") return "SIMPLE_FILLING";
  if (layer === "OBSERVATION") return "OBSERVATION";
  if (includesAny(text, ["TEMPORAL", "PRIMARY", "INFANTIL"])) return "PRIMARY_TOOTH";
  return "HEALTHY";
}

export function getPrimaryVisualState(states: Set<ToothVisualState>): ToothVisualState {
  return DDS_VISUAL_PRIORITY.find((state) => states.has(state)) ?? "HEALTHY";
}

export function buildToothRenderState({
  number,
  dentition,
  details,
  visibleLayers,
  eventCount,
}: {
  number: string;
  dentition?: string;
  details: ToothDetail[];
  visibleLayers?: Set<string>;
  eventCount?: number;
}): ToothRenderState {
  const filteredDetails = visibleLayers
    ? details.filter((detail) => visibleLayers.has(detail.layer))
    : details;
  const visualStates = new Set<ToothVisualState>();
  const unlocalizedStates = new Set<ToothVisualState>();
  const surfaceStates: ToothRenderState["surfaceStates"] = {};

  if (dentition === "PRIMARY") visualStates.add("PRIMARY_TOOTH");

  filteredDetails.forEach((detail) => {
    const visualState = classifyToothDetail(detail);
    visualStates.add(visualState);
    const surfaces = normalizeSurfaces(detail);
    if (!surfaces.length && requiresLocalizedVisualFallback(visualState)) {
      unlocalizedStates.add(visualState);
    }
    surfaces.forEach((surface) => {
      surfaceStates[surface] = [...(surfaceStates[surface] ?? []), visualState];
    });
  });

  if (filteredDetails.some((detail) => detail.layer === "PLANNED") && filteredDetails.some((detail) => detail.layer === "PERFORMED")) {
    visualStates.add("IN_PROGRESS_TREATMENT");
  } else if (filteredDetails.some((detail) => detail.layer === "PLANNED")) {
    visualStates.add("PLANNED_TREATMENT");
  }

  if (!visualStates.size) visualStates.add("HEALTHY");

  const primary = getPrimaryVisualState(visualStates);
  const hasDetails = filteredDetails.length > 0;
  const hasVisibleDiagnosis = [...visualStates].some(isDiagnosisVisualState);
  const hasPerformedTreatment = [...visualStates].some(isPerformedTreatmentVisualState);
  const hasPlannedTreatment = visualStates.has("PLANNED_TREATMENT");
  const primaryLabel = clinicalSummaryLabel({
    primary,
    hasDetails,
    hasVisibleDiagnosis,
    hasPerformedTreatment,
    hasPlannedTreatment,
    unlocalizedStates,
  });
  const tooltipLines = [
    number,
    primaryLabel,
    ...filteredDetails.slice(0, 3).map((detail) => {
      const surface = detail.surfaces?.length ? ` · ${detail.surfaces.join(", ").toLowerCase()}` : "";
      return `${detail.catalogName}${surface}`;
    }),
  ];
  if (eventCount && eventCount > filteredDetails.length) tooltipLines.push(`${eventCount} eventos históricos`);

  return {
    visualStates,
    unlocalizedStates,
    details: filteredDetails,
    surfaceStates,
    primaryLabel,
    tooltipLines: tooltipLines.slice(0, 5),
  };
}
