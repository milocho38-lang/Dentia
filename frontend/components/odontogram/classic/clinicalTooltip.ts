import { LOCALIZATION_LABELS, STATUS_LABELS, SURFACE_LABELS } from "./constants";
import type { DualClinicalEvent, DualClinicalToothModel, ToothSurface } from "./types";

const CLINICAL_LAYER_LABELS: Record<string, string> = {
  FINDING: "Hallazgo",
  DIAGNOSIS: "Diagnóstico",
  PLANNED: "Tratamiento planificado",
  PERFORMED: "Tratamiento realizado",
  OBSERVATION: "Observación",
  STRUCTURAL: "Estado estructural",
};

const EVENT_ORDER = {
  DIAGNOSIS: 1,
  COMPLETED: 2,
  PLANNED: 3,
} as const;

function clinicalCategory(event: DualClinicalEvent) {
  if (event.localization === "NON_SURFACE" && event.sourceLayer === "DIAGNOSIS") {
    return "Diagnóstico no superficial";
  }
  if (event.localization === "NON_SURFACE") {
    return "Información clínica no superficial";
  }
  if (event.sourceLayer && CLINICAL_LAYER_LABELS[event.sourceLayer]) {
    return CLINICAL_LAYER_LABELS[event.sourceLayer];
  }
  return STATUS_LABELS[event.status];
}

function surfaceLabel(surface: ToothSurface) {
  return SURFACE_LABELS[surface] ?? surface;
}

function clinicalLocalization(event: DualClinicalEvent) {
  if (event.surfaces.length) {
    return event.surfaces.map(surfaceLabel).join(" · ");
  }
  if (event.localization === "NON_SURFACE") {
    return null;
  }
  if (event.localization) {
    return LOCALIZATION_LABELS[event.localization];
  }
  return null;
}

function fallbackEventKey(toothNumber: string, event: DualClinicalEvent) {
  return [
    toothNumber,
    event.sourceCode ?? event.kind,
    event.status,
    event.sourceLayer ?? "",
    event.localization ?? "",
    event.surfaces.slice().sort().join("|"),
    event.label,
  ].join("::");
}

export function uniqueClinicalEvents(model: DualClinicalToothModel) {
  const seen = new Set<string>();
  return model.events.filter((event) => {
    const key = event.id || fallbackEventKey(model.toothNumber, event);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function sortClinicalEvents(events: DualClinicalEvent[]) {
  return [...events].sort((a, b) => {
    const byStatus = (EVENT_ORDER[a.status] ?? 9) - (EVENT_ORDER[b.status] ?? 9);
    if (byStatus !== 0) return byStatus;
    return a.label.localeCompare(b.label, "es");
  });
}

export function clinicalEventTooltipLines(event: DualClinicalEvent) {
  return [
    event.label,
    clinicalCategory(event),
    clinicalLocalization(event),
  ].filter(Boolean) as string[];
}

function compactEventLine(event: DualClinicalEvent) {
  const localization = clinicalLocalization(event);
  const category = clinicalCategory(event);
  if (localization) return `${event.label} — ${localization}`;
  return `${event.label} — ${category}`;
}

export function createClinicalTooltip(model: DualClinicalToothModel) {
  const events = sortClinicalEvents(uniqueClinicalEvents(model));
  if (!events.length) {
    return `Diente ${model.toothNumber}\nSin eventos clínicos visibles`;
  }
  if (events.length === 1) {
    return [`Diente ${model.toothNumber}`, ...clinicalEventTooltipLines(events[0])].join("\n");
  }
  return [
    `Diente ${model.toothNumber} · ${events.length} eventos`,
    "",
    ...events.map((event) => `• ${compactEventLine(event)}`),
  ].join("\n");
}

export function createClinicalAriaLabel(model: DualClinicalToothModel) {
  const events = sortClinicalEvents(uniqueClinicalEvents(model));
  if (!events.length) return `Diente ${model.toothNumber}, sin eventos clínicos visibles.`;
  if (events.length === 1) {
    return `Diente ${model.toothNumber}, ${clinicalEventTooltipLines(events[0]).join(", ")}.`;
  }
  return `Diente ${model.toothNumber}, ${events.length} eventos: ${events.map(compactEventLine).join("; ")}.`;
}

export function createIndicatorTooltip(events: DualClinicalEvent[], emptyLabel: string) {
  const model: DualClinicalToothModel = {
    toothNumber: "indicador",
    dentition: "PERMANENT",
    family: "MOLAR",
    arch: "UPPER",
    quadrant: 1,
    events,
  };
  const uniqueEvents = sortClinicalEvents(uniqueClinicalEvents(model));
  if (!uniqueEvents.length) return emptyLabel;
  if (uniqueEvents.length === 1) {
    return clinicalEventTooltipLines(uniqueEvents[0]).join("\n");
  }
  return [
    `${uniqueEvents.length} eventos clínicos informativos`,
    "",
    ...uniqueEvents.map((event) => `• ${compactEventLine(event)}`),
  ].join("\n");
}
