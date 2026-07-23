import type { OdontogramEventDetail, OdontogramToothState } from "@/types/odontogram";
import { mappingByCode, normalizedClinicalCode } from "./clinicalCodeMapping";
import { adaptRealSurfaces } from "./surfaceAdapter";
import { archFromQuadrant, dentitionFromTooth, familyFromTooth, quadrantFromTooth } from "./orientation";
import type { ClinicalEventStatus, ClinicalLocalization, DualClinicalEvent, DualClinicalToothModel } from "./types";

export type RealClinicalAdapterContext = {
  visibleLayers?: Set<string>;
};

export type AdaptedRealClinicalModel = {
  model: DualClinicalToothModel;
  sourceDetails: Array<{
    id: string;
    code: string;
    name: string;
    layer: string;
    catalogType: string;
    surfaces: string[];
    convertedSurfaces: string[];
    localization: ClinicalLocalization;
    visualStatus: ClinicalEventStatus;
    originalStatus: string;
    mapped: boolean;
    reason?: string;
  }>;
};

function fallbackKind(detail: OdontogramEventDetail) {
  const haystack = `${detail.catalog_code} ${detail.catalog_name} ${detail.catalog_type} ${detail.layer}`.toUpperCase();
  if (haystack.includes("CARIES")) return mappingByCode("FIND_CARIES");
  if (haystack.includes("RESIN") || haystack.includes("RESTAUR") || haystack.includes("OBTUR") || haystack.includes("SELLANTE")) {
    return detail.layer === "PLANNED" ? mappingByCode("PLAN_RESIN") : mappingByCode("DONE_RESIN");
  }
  if (haystack.includes("ENDO")) return detail.layer === "PLANNED" ? mappingByCode("PLAN_ENDO") : mappingByCode("DONE_ENDO");
  if (haystack.includes("CORONA")) return detail.layer === "PLANNED" ? mappingByCode("PLAN_CROWN") : mappingByCode("DONE_CROWN");
  if (haystack.includes("IMPLANT")) return detail.layer === "PLANNED" ? mappingByCode("PLAN_IMPLANT") : mappingByCode("DONE_IMPLANT");
  if (haystack.includes("AUSEN") || haystack.includes("EXTRAC")) return detail.layer === "PLANNED" ? mappingByCode("PLAN_EXTRACTION") : mappingByCode("DONE_EXTRACTION");
  if (haystack.includes("FRACT")) return mappingByCode("FIND_FRACTURE");
  if (["DIAGNOSIS", "OBSERVATION"].includes(detail.layer)) return mappingByCode("OBS_GENERAL");
  return null;
}

function localizationForDetail(
  mapping: NonNullable<ReturnType<typeof mappingByCode>>,
  realSurfaces: ReturnType<typeof adaptRealSurfaces>,
): ClinicalLocalization {
  if (mapping.informational) return "NON_SURFACE";
  if (realSurfaces.some((surface) => surface === "PULPAL_RADICULAR")) return "PULPAL_RADICULAR";
  if (realSurfaces.some((surface) => surface === "WHOLE_TOOTH")) return "WHOLE_TOOTH";
  if (realSurfaces.length) return "SURFACE_SPECIFIC";
  if (mapping.defaultSurfaces?.some((surface) => surface === "PULPAL_RADICULAR")) return "PULPAL_RADICULAR";
  if (mapping.defaultSurfaces?.some((surface) => surface === "WHOLE_TOOTH")) return "WHOLE_TOOTH";
  if (mapping.superficial) return "SURFACE_UNSPECIFIED";
  return "NON_SURFACE";
}

function statusFromLayer(detail: OdontogramEventDetail, fallback: ClinicalEventStatus): ClinicalEventStatus {
  if (detail.layer === "PLANNED") return "PLANNED";
  if (detail.layer === "PERFORMED") return "COMPLETED";
  if (detail.layer === "DIAGNOSIS" || detail.layer === "FINDING") return "DIAGNOSIS";
  return fallback;
}

function adaptDetail(detail: OdontogramEventDetail): DualClinicalEvent | null {
  const mapping = mappingByCode(detail.catalog_code) ?? fallbackKind(detail);
  if (!mapping) return null;
  const realSurfaces = adaptRealSurfaces(detail.surfaces);
  const localization = localizationForDetail(mapping, realSurfaces);
  const surfaces = localization === "SURFACE_UNSPECIFIED" || localization === "NON_SURFACE"
    ? []
    : realSurfaces.length ? realSurfaces : mapping.defaultSurfaces ?? [];
  const status = statusFromLayer(detail, mapping.status);
  return {
    id: detail.id,
    kind: localization === "NON_SURFACE" ? "INFORMATION" : mapping.kind,
    status,
    surfaces,
    label: detail.catalog_name,
    localization,
    sourceLayer: detail.layer,
    sourceCode: normalizedClinicalCode(detail.catalog_code),
    sourceName: detail.catalog_name,
    unmapped: false,
  };
}

export function buildDualClinicalToothModelFromState(
  realToothState: OdontogramToothState,
  context: RealClinicalAdapterContext = {},
): AdaptedRealClinicalModel {
  const toothNumber = realToothState.tooth_code;
  const quadrant = quadrantFromTooth(toothNumber);
  const visibleLayers = context.visibleLayers;
  const details = Object.entries(realToothState.layers ?? {}).flatMap(([layer, layerDetails]) =>
    visibleLayers && !visibleLayers.has(layer) ? [] : layerDetails,
  );
  const events = details.map(adaptDetail).filter(Boolean) as DualClinicalEvent[];
  const model: DualClinicalToothModel = {
    toothNumber,
    dentition: realToothState.dentition === "PRIMARY" ? "PRIMARY" : dentitionFromTooth(toothNumber),
    family: familyFromTooth(toothNumber),
    arch: archFromQuadrant(quadrant),
    quadrant,
    events,
  };
  return {
    model,
    sourceDetails: details.map((detail) => {
      const adapted = adaptDetail(detail);
      const mapped = Boolean(adapted);
      return {
        id: detail.id,
        code: normalizedClinicalCode(detail.catalog_code),
        name: detail.catalog_name,
        layer: detail.layer,
        catalogType: detail.catalog_type,
        surfaces: detail.surfaces ?? [],
        convertedSurfaces: adapted?.surfaces ?? [],
        localization: adapted?.localization ?? "NON_SURFACE",
        visualStatus: adapted?.status ?? "DIAGNOSIS",
        originalStatus: detail.status_after ?? detail.layer,
        mapped,
        reason: mapped ? undefined : "Código clínico sin correspondencia aprobada",
      };
    }),
  };
}
