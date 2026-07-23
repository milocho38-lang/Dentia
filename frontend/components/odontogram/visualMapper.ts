"use client";

import type { ToothDetail, ToothSurface } from "@/components/odontogram/Tooth";
import type { OdontogramEventDetail, OdontogramToothState } from "@/types/odontogram";

type VisualLayer =
  | "STRUCTURAL"
  | "FINDING"
  | "DIAGNOSIS"
  | "PLANNED"
  | "PERFORMED"
  | "OBSERVATION";

const KNOWN_LAYERS = new Set<VisualLayer>([
  "STRUCTURAL",
  "FINDING",
  "DIAGNOSIS",
  "PLANNED",
  "PERFORMED",
  "OBSERVATION",
]);

const CODE_TO_VISUAL_HINT: Record<string, string> = {
  STRUCT_HEALTHY: "HEALTHY",
  STRUCT_MISSING: "MISSING",
  STRUCT_IMPLANT: "IMPLANT",
  STRUCT_PRIMARY: "PRIMARY_TOOTH",
  STRUCT_UNERUPTED: "OBSERVATION",
  STRUCT_ERUPTING: "OBSERVATION",
  STRUCT_EXFOLIATED: "MISSING",
  STRUCT_RETAINED: "OBSERVATION",
  FIND_CARIES: "CARIES",
  FIND_FRACTURE: "FRACTURE",
  FIND_WEAR: "WEAR",
  FIND_PIGMENT: "OBSERVATION",
  FIND_RESTORATION: "RESTORATION",
  FIND_CROWN: "DEFINITIVE_CROWN",
  FIND_IMPLANT: "IMPLANT",
  FIND_ABSENCE: "MISSING",
  DX_ACTIVE_CARIES: "CARIES",
  DX_PULPITIS: "DIAGNOSIS_GENERAL",
  DX_NECROSIS: "DIAGNOSIS_GENERAL",
  DX_PERIAPICAL: "DIAGNOSIS_GENERAL",
  DX_TRAUMA: "FRACTURE",
  PLAN_RESIN: "PLANNED_TREATMENT",
  PLAN_ENDO: "PLANNED_TREATMENT",
  PLAN_CROWN: "PLANNED_TREATMENT",
  PLAN_EXTRACTION: "PLANNED_TREATMENT",
  PLAN_IMPLANT: "PLANNED_TREATMENT",
  PLAN_SEALANT: "PLANNED_TREATMENT",
  DONE_RESIN: "RESTORATION",
  DONE_ENDO: "ENDODONTICS",
  DONE_CROWN: "DEFINITIVE_CROWN",
  DONE_EXTRACTION: "MISSING",
  DONE_IMPLANT: "IMPLANT",
  DONE_SEALANT: "SEALANT",
  OBS_GENERAL: "OBSERVATION",
};

function safeLayer(layer: string): VisualLayer {
  return KNOWN_LAYERS.has(layer as VisualLayer) ? (layer as VisualLayer) : "OBSERVATION";
}

function normalizedCode(detail: OdontogramEventDetail) {
  return (detail.catalog_code ?? "").trim().toUpperCase();
}

function normalizeSurfaces(surfaces: string[] | null): ToothSurface[] | null {
  if (!surfaces?.length) return null;
  return surfaces.filter(Boolean).map((surface) => surface as ToothSurface);
}

function surfaceAwareCatalogName(detail: OdontogramEventDetail) {
  const code = normalizedCode(detail);
  const hint = CODE_TO_VISUAL_HINT[code];
  const surfaces = detail.surfaces ?? [];

  if (hint === "CARIES") {
    if (surfaces.includes("MESIAL") || surfaces.includes("DISTAL")) return "Caries proximal";
    if (surfaces.includes("OCCLUSAL") || surfaces.includes("INCISAL")) return "Caries oclusal";
    if (surfaces.includes("VESTIBULAR") || surfaces.includes("LINGUAL") || surfaces.includes("PALATAL")) {
      return "Caries en superficie";
    }
    return "Caries sin superficie específica";
  }

  if (hint === "RESTORATION") {
    return surfaces.length > 1 ? "Obturaciones múltiples" : "Obturación";
  }

  if (hint === "DIAGNOSIS_GENERAL") {
    return `${detail.catalog_name} · diagnóstico`;
  }

  return detail.catalog_name;
}

function visualCatalogCode(detail: OdontogramEventDetail) {
  const code = normalizedCode(detail);
  return CODE_TO_VISUAL_HINT[code] ?? code;
}

export function mapOdontogramDetailToToothDetail(detail: OdontogramEventDetail): ToothDetail {
  return {
    id: detail.id,
    catalogCode: visualCatalogCode(detail),
    catalogName: surfaceAwareCatalogName(detail),
    catalogType: detail.catalog_type,
    color: detail.color,
    pattern: detail.pattern,
    symbol: detail.symbol,
    surfaces: normalizeSurfaces(detail.surfaces),
    layer: safeLayer(detail.layer),
  };
}

export function buildToothDetailsFromState(state: OdontogramToothState | undefined): ToothDetail[] {
  return Object.entries(state?.layers ?? {}).flatMap(([, details]) =>
    details.map(mapOdontogramDetailToToothDetail),
  );
}
