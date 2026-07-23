import { LOCALIZATION_LABELS, STATUS_LABELS, SURFACE_LABELS } from "@/components/odontogram/classic/constants";
import { uniqueClinicalEvents } from "@/components/odontogram/classic/clinicalTooltip";
import { buildDualClinicalToothModelFromState } from "@/components/odontogram/classic/realClinicalAdapter";
import type { DualClinicalEvent } from "@/components/odontogram/classic/types";
import { buildToothDetailsFromState } from "@/components/odontogram/visualMapper";
import type { OdontogramEvent, OdontogramEventDetail, OdontogramToothState } from "@/types/odontogram";

export const INSPECTOR_SURFACES = [
  ["VESTIBULAR", "Vestibular"],
  ["PALATAL", "Palatina"],
  ["LINGUAL", "Lingual"],
  ["MESIAL", "Mesial"],
  ["DISTAL", "Distal"],
  ["OCCLUSAL", "Oclusal"],
  ["INCISAL", "Incisal"],
] as const;

const POSITION_NAMES: Record<string, string> = {
  "1": "Incisivo central",
  "2": "Incisivo lateral",
  "3": "Canino",
  "4": "Primer premolar",
  "5": "Segundo premolar",
  "6": "Primer molar",
  "7": "Segundo molar",
  "8": "Tercer molar",
};

const PRIMARY_POSITION_NAMES: Record<string, string> = {
  "1": "Incisivo central temporal",
  "2": "Incisivo lateral temporal",
  "3": "Canino temporal",
  "4": "Primer molar temporal",
  "5": "Segundo molar temporal",
};

const QUADRANT_NAMES: Record<string, string> = {
  "1": "superior derecho",
  "2": "superior izquierdo",
  "3": "inferior izquierdo",
  "4": "inferior derecho",
  "5": "superior derecho",
  "6": "superior izquierdo",
  "7": "inferior izquierdo",
  "8": "inferior derecho",
};

const LAYER_LABELS: Record<string, string> = {
  STRUCTURAL: "Estado estructural",
  FINDING: "Hallazgo",
  DIAGNOSIS: "Diagnóstico",
  PLANNED: "Tratamiento planificado",
  PERFORMED: "Tratamiento realizado",
  OBSERVATION: "Observación",
};

export type InspectorSummaryGroup = {
  id: "diagnosis" | "findings" | "performed" | "planned" | "informative" | "structural";
  title: string;
  tone: string;
  events: DualClinicalEvent[];
};

function eventKey(event: DualClinicalEvent) {
  return [
    event.id,
    event.sourceCode,
    event.status,
    event.sourceLayer,
    event.localization,
    event.surfaces.slice().sort().join("|"),
    event.label,
  ].filter(Boolean).join("::");
}

function dedupeDetails(details: OdontogramEventDetail[]) {
  const seen = new Set<string>();
  return details.filter((detail) => {
    const key = [
      detail.id,
      detail.catalog_code,
      detail.layer,
      detail.status_after,
      detail.surfaces?.slice().sort().join("|") ?? "",
      detail.catalog_name,
    ].join("::");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function toothDentitionLabel(toothCode: string) {
  return Number(toothCode[0]) >= 5 ? "Dentición temporal" : "Dentición permanente";
}

export function anatomicalToothName(toothCode: string) {
  const [quadrant, position] = toothCode.split("");
  const nameMap = Number(quadrant) >= 5 ? PRIMARY_POSITION_NAMES : POSITION_NAMES;
  const positionName = nameMap[position] ?? "Pieza dental";
  const quadrantName = QUADRANT_NAMES[quadrant] ?? "";
  return `${positionName}${quadrantName ? ` ${quadrantName}` : ""}`.trim();
}

export function clinicalLayerLabel(layer?: string | null, fallback = "Evento clínico") {
  if (!layer) return fallback;
  return LAYER_LABELS[layer] ?? fallback;
}

export function detailSurfaceLabel(detail: Pick<OdontogramEventDetail, "surfaces" | "scope_type">) {
  if (detail.surfaces?.length) {
    return detail.surfaces.map((surface) => SURFACE_LABELS[surface as keyof typeof SURFACE_LABELS] ?? surface).join(" · ");
  }
  if (detail.scope_type === "TOOTH") return "Pieza completa";
  return "Superficie no especificada";
}

export function eventSurfaceLabel(event: DualClinicalEvent) {
  if (event.surfaces.length) {
    return event.surfaces.map((surface) => SURFACE_LABELS[surface]).join(" · ");
  }
  if (event.localization === "NON_SURFACE") return "Diagnóstico no superficial";
  if (event.localization) return LOCALIZATION_LABELS[event.localization];
  return "Sin superficie";
}

function groupId(event: DualClinicalEvent): InspectorSummaryGroup["id"] {
  if (event.localization === "NON_SURFACE" || event.kind === "INFORMATION") return "informative";
  if (event.sourceLayer === "STRUCTURAL") return "structural";
  if (event.sourceLayer === "FINDING") return "findings";
  if (event.status === "PLANNED") return "planned";
  if (event.status === "COMPLETED") return "performed";
  return "diagnosis";
}

const GROUP_META: Record<InspectorSummaryGroup["id"], Omit<InspectorSummaryGroup, "events">> = {
  diagnosis: { id: "diagnosis", title: "Diagnósticos", tone: "border-red-100 bg-red-50/60 text-red-800" },
  findings: { id: "findings", title: "Hallazgos", tone: "border-rose-100 bg-rose-50/60 text-rose-800" },
  performed: { id: "performed", title: "Tratamientos realizados", tone: "border-blue-100 bg-blue-50/60 text-blue-800" },
  planned: { id: "planned", title: "Procedimientos planificados", tone: "border-orange-100 bg-orange-50/60 text-orange-800" },
  informative: { id: "informative", title: "Informativos", tone: "border-slate-100 bg-slate-50 text-slate-700" },
  structural: { id: "structural", title: "Estado estructural", tone: "border-emerald-100 bg-emerald-50/60 text-emerald-800" },
};

export function buildInspectorModel(toothCode: string, toothState?: OdontogramToothState) {
  const toothDetails = buildToothDetailsFromState(toothState);
  const dualModel = toothState
    ? buildDualClinicalToothModelFromState(toothState).model
    : {
      toothNumber: toothCode,
      dentition: Number(toothCode[0]) >= 5 ? "PRIMARY" as const : "PERMANENT" as const,
      family: "MOLAR" as const,
      arch: "UPPER" as const,
      quadrant: 1 as const,
      events: [],
    };
  const events = uniqueClinicalEvents(dualModel);
  const grouped = new Map<InspectorSummaryGroup["id"], DualClinicalEvent[]>();
  events.forEach((event) => {
    const id = groupId(event);
    grouped.set(id, [...(grouped.get(id) ?? []), event]);
  });
  const groups = (Object.keys(GROUP_META) as InspectorSummaryGroup["id"][])
    .map((id) => ({ ...GROUP_META[id], events: grouped.get(id) ?? [] }))
    .filter((group) => group.events.length > 0);
  return {
    toothDetails,
    events,
    groups,
    eventCount: toothState?.event_count ?? events.length,
  };
}

export function eventStatusLabel(event: DualClinicalEvent) {
  if (event.sourceLayer === "FINDING") return "Hallazgo";
  if (event.localization === "NON_SURFACE" && event.sourceLayer === "DIAGNOSIS") return "Diagnóstico no superficial";
  return STATUS_LABELS[event.status];
}

export function eventCardTitle(event: OdontogramEvent) {
  const details = dedupeDetails(event.details);
  return details.map((detail) => detail.catalog_name).join(", ") || "Evento clínico";
}

export function eventCardBadges(event: OdontogramEvent) {
  return dedupeDetails(event.details).map((detail) => ({
    id: detail.id,
    layer: detail.layer,
    label: [
      detail.tooth_code,
      detailSurfaceLabel(detail),
    ].filter(Boolean).join(" · "),
  }));
}

export function eventBelongsToTooth(event: OdontogramEvent, toothCode: string) {
  return event.details.some((detail) => detail.tooth_code === toothCode);
}

export function formatInspectorEventDate(value: string | null, timeZone?: string | null) {
  if (!value) return "No registrado";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
    ...(timeZone ? { timeZone } : {}),
  }).format(new Date(value));
}
