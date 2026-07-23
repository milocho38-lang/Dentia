import type { ClinicalEventKind, ClinicalEventStatus, ToothSurface } from "./types";

export const CLASSIC_COLORS: Record<ClinicalEventKind, { fill: string; stroke: string; text: string }> = {
  CARIES: { fill: "#EF4444", stroke: "#B91C1C", text: "Caries" },
  RESTORATION: { fill: "#2563EB", stroke: "#1D4ED8", text: "Restauración" },
  ENDODONTICS: { fill: "#8B5CF6", stroke: "#6D28D9", text: "Endodoncia" },
  CROWN: { fill: "#059669", stroke: "#047857", text: "Corona" },
  IMPLANT: { fill: "#0F766E", stroke: "#115E59", text: "Implante" },
  FRACTURE: { fill: "#F97316", stroke: "#C2410C", text: "Fractura" },
  EXTRACTION: { fill: "#EF4444", stroke: "#B91C1C", text: "Extracción" },
  ABSENT: { fill: "#F8FAFC", stroke: "#94A3B8", text: "Ausente" },
  INFORMATION: { fill: "#64748B", stroke: "#475569", text: "Información clínica" },
};

export const STATUS_LABELS: Record<ClinicalEventStatus, string> = {
  DIAGNOSIS: "Diagnóstico",
  COMPLETED: "Realizado",
  PLANNED: "Planificado",
};

export const STATUS_COLORS: Record<ClinicalEventStatus, { fill: string; stroke: string; text: string }> = {
  DIAGNOSIS: { fill: "#EF4444", stroke: "#B91C1C", text: "Diagnóstico" },
  COMPLETED: { fill: "#2563EB", stroke: "#1D4ED8", text: "Realizado" },
  PLANNED: { fill: "#F97316", stroke: "#C2410C", text: "Planificado" },
};

export const LOCALIZATION_LABELS = {
  SURFACE_SPECIFIC: "Superficie específica",
  SURFACE_UNSPECIFIED: "Superficie no especificada",
  NON_SURFACE: "No superficial",
  WHOLE_TOOTH: "Pieza completa",
  PULPAL_RADICULAR: "Pulpar / radicular",
} as const;

export const SURFACE_LABELS: Record<ToothSurface, string> = {
  OCCLUSAL: "Oclusal",
  INCISAL: "Incisal",
  VESTIBULAR: "Vestibular",
  PALATAL: "Palatina",
  LINGUAL: "Lingual",
  MESIAL: "Mesial",
  DISTAL: "Distal",
  CERVICAL: "Cervical",
  PULPAL_RADICULAR: "Pulpar / radicular",
  WHOLE_TOOTH: "Pieza completa",
};

export const SURFACE_OPTIONS: ToothSurface[] = [
  "OCCLUSAL",
  "INCISAL",
  "VESTIBULAR",
  "PALATAL",
  "LINGUAL",
  "MESIAL",
  "DISTAL",
  "CERVICAL",
  "PULPAL_RADICULAR",
  "WHOLE_TOOTH",
];

export const SURFACE_EVENT_KINDS: ClinicalEventKind[] = ["CARIES", "RESTORATION", "FRACTURE"];
export const WHOLE_TOOTH_EVENT_KINDS: ClinicalEventKind[] = ["CROWN", "IMPLANT", "EXTRACTION", "ABSENT"];
