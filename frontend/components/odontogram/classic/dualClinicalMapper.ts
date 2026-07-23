import { CLASSIC_COLORS, LOCALIZATION_LABELS, STATUS_COLORS, STATUS_LABELS, SURFACE_LABELS, WHOLE_TOOTH_EVENT_KINDS } from "./constants";
import { getSurfaceOrientation, normalizeSurfaceForTooth, surfaceToRole } from "./orientation";
import type { ClinicalLocalization, ClinicalMarker, DualClinicalEvent, DualClinicalToothModel, DualClinicalToothViewModel, ToothSurface } from "./types";

function markerPattern(event: DualClinicalEvent): ClinicalMarker["pattern"] {
  if (event.kind === "ABSENT") return "DASHED";
  if (event.kind === "FRACTURE") return "LINE";
  if (event.kind === "INFORMATION") return "SYMBOL";
  if (event.status === "PLANNED") return "OUTLINE";
  if (event.kind === "ENDODONTICS" || event.kind === "IMPLANT") return "SYMBOL";
  return "SOLID";
}

function markerSymbol(event: DualClinicalEvent) {
  if (event.kind === "ENDODONTICS") return "∿";
  if (event.kind === "IMPLANT") return "⌁";
  if (event.kind === "FRACTURE") return "Ⅱ";
  if (event.kind === "ABSENT" || event.kind === "EXTRACTION") return "×";
  if (event.kind === "CROWN") return "♛";
  if (event.kind === "INFORMATION") return "i";
  return "●";
}

function eventLocalization(event: DualClinicalEvent): ClinicalLocalization {
  if (event.localization) return event.localization;
  if (event.surfaces.some((surface) => surface === "PULPAL_RADICULAR")) return "PULPAL_RADICULAR";
  if (event.surfaces.some((surface) => surface === "WHOLE_TOOTH")) return "WHOLE_TOOTH";
  if (event.surfaces.length) return "SURFACE_SPECIFIC";
  if (event.kind === "INFORMATION") return "NON_SURFACE";
  return "SURFACE_UNSPECIFIED";
}

function eventColors(event: DualClinicalEvent) {
  const localization = eventLocalization(event);
  if (event.kind === "ABSENT") return CLASSIC_COLORS.ABSENT;
  if (event.kind === "INFORMATION" || localization === "NON_SURFACE") return CLASSIC_COLORS.INFORMATION;
  return STATUS_COLORS[event.status] ?? CLASSIC_COLORS[event.kind];
}

function eventSurfaces(event: DualClinicalEvent, model: DualClinicalToothModel): ToothSurface[] {
  const orientation = getSurfaceOrientation(model.toothNumber, model.family);
  const localization = eventLocalization(event);
  if (localization === "SURFACE_UNSPECIFIED" || localization === "NON_SURFACE") return [];
  if (event.surfaces.length) {
    return event.surfaces.map((surface) => normalizeSurfaceForTooth(surface, orientation));
  }
  if (event.kind === "ENDODONTICS") return ["PULPAL_RADICULAR"];
  if (WHOLE_TOOTH_EVENT_KINDS.includes(event.kind)) return ["WHOLE_TOOTH"];
  return [];
}

function createMarker(event: DualClinicalEvent, model: DualClinicalToothModel, surface: ToothSurface): ClinicalMarker {
  const orientation = getSurfaceOrientation(model.toothNumber, model.family);
  const colors = eventColors(event);
  return {
    id: `${event.id}-${surface}`,
    eventId: event.id,
    kind: event.kind,
    status: event.status,
    label: event.label,
    surface,
    role: surfaceToRole(surface, orientation),
    color: colors.fill,
    stroke: colors.stroke,
    pattern: markerPattern(event),
    symbol: markerSymbol(event),
    localization: eventLocalization(event),
  };
}

function createGeneralMarker(event: DualClinicalEvent): ClinicalMarker {
  const colors = eventColors(event);
  return {
    id: `${event.id}-general`,
    eventId: event.id,
    kind: event.kind,
    status: event.status,
    label: event.label,
    surface: "WHOLE_TOOTH",
    role: "WHOLE",
    color: colors.fill,
    stroke: colors.stroke,
    pattern: markerPattern(event),
    symbol: event.localization === "SURFACE_UNSPECIFIED" ? "?" : markerSymbol(event),
    localization: eventLocalization(event),
  };
}

export function mapDualClinicalTooth(model: DualClinicalToothModel): DualClinicalToothViewModel {
  const orientation = getSurfaceOrientation(model.toothNumber, model.family);
  const allMarkers = model.events.flatMap((event) =>
    eventSurfaces(event, model).map((surface) => createMarker(event, model, surface)),
  );
  const surfaceMarkers = allMarkers.filter((marker) => marker.role !== "WHOLE" && marker.role !== "PULP");
  const structuralMarkers = allMarkers.filter((marker) => marker.role === "WHOLE" || marker.role === "PULP");
  const generalMarkers = model.events
    .filter((event) => ["SURFACE_UNSPECIFIED", "NON_SURFACE"].includes(eventLocalization(event)))
    .map(createGeneralMarker);
  const isAbsent = model.events.some((event) => event.kind === "ABSENT" || event.kind === "EXTRACTION");
  const summaryLabel = model.events.length
    ? model.events.map((event) => event.label).slice(0, 2).join(" + ")
    : "Sin eventos clínicos";
  const tooltip = [
    `Diente ${model.toothNumber}`,
    summaryLabel,
    ...model.events.slice(0, 4).map((event) => {
      const surfaces = eventSurfaces(event, model)
        .map((surface) => SURFACE_LABELS[surface])
        .join(", ");
      return `${event.label} · ${surfaces || LOCALIZATION_LABELS[eventLocalization(event)]} · ${STATUS_LABELS[event.status]}`;
    }),
    `${model.events.length} evento${model.events.length === 1 ? "" : "s"}`,
  ].join("\n");

  return {
    model,
    orientation,
    surfaceMarkers,
    structuralMarkers,
    generalMarkers,
    tooltip,
    summaryLabel,
    eventCount: model.events.length,
    isAbsent,
  };
}
