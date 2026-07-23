import type { ClinicalEventKind, ClinicalEventStatus, ToothSurface } from "./types";

export type ClinicalCodeMapping = {
  kind: ClinicalEventKind;
  status: ClinicalEventStatus;
  defaultSurfaces?: ToothSurface[];
  superficial: boolean;
  informational?: boolean;
};

export const REAL_CLINICAL_CODE_MAPPING: Record<string, ClinicalCodeMapping> = {
  FIND_CARIES: { kind: "CARIES", status: "DIAGNOSIS", superficial: true },
  DX_ACTIVE_CARIES: { kind: "CARIES", status: "DIAGNOSIS", superficial: true },
  FIND_FRACTURE: { kind: "FRACTURE", status: "DIAGNOSIS", superficial: true },
  DX_TRAUMA: { kind: "FRACTURE", status: "DIAGNOSIS", superficial: true },
  FIND_RESTORATION: { kind: "RESTORATION", status: "COMPLETED", superficial: true },
  DONE_RESIN: { kind: "RESTORATION", status: "COMPLETED", superficial: true },
  DONE_SEALANT: { kind: "RESTORATION", status: "COMPLETED", superficial: true },
  PLAN_RESIN: { kind: "RESTORATION", status: "PLANNED", superficial: true },
  PLAN_SEALANT: { kind: "RESTORATION", status: "PLANNED", superficial: true },
  DONE_CROWN: { kind: "CROWN", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  FIND_CROWN: { kind: "CROWN", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  PLAN_CROWN: { kind: "CROWN", status: "PLANNED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  DONE_ENDO: { kind: "ENDODONTICS", status: "COMPLETED", defaultSurfaces: ["PULPAL_RADICULAR"], superficial: false },
  PLAN_ENDO: { kind: "ENDODONTICS", status: "PLANNED", defaultSurfaces: ["PULPAL_RADICULAR"], superficial: false },
  STRUCT_IMPLANT: { kind: "IMPLANT", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  FIND_IMPLANT: { kind: "IMPLANT", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  DONE_IMPLANT: { kind: "IMPLANT", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  PLAN_IMPLANT: { kind: "IMPLANT", status: "PLANNED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  STRUCT_MISSING: { kind: "ABSENT", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  STRUCT_EXFOLIATED: { kind: "ABSENT", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  FIND_ABSENCE: { kind: "ABSENT", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  DONE_EXTRACTION: { kind: "ABSENT", status: "COMPLETED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  PLAN_EXTRACTION: { kind: "EXTRACTION", status: "PLANNED", defaultSurfaces: ["WHOLE_TOOTH"], superficial: false },
  DX_PULPITIS: { kind: "INFORMATION", status: "DIAGNOSIS", superficial: false, informational: true },
  DX_NECROSIS: { kind: "INFORMATION", status: "DIAGNOSIS", superficial: false, informational: true },
  DX_PERIAPICAL: { kind: "INFORMATION", status: "DIAGNOSIS", superficial: false, informational: true },
  OBS_GENERAL: { kind: "INFORMATION", status: "DIAGNOSIS", superficial: false, informational: true },
};

export function normalizedClinicalCode(code: string | null | undefined) {
  return String(code ?? "").trim().toUpperCase();
}

export function mappingByCode(code: string | null | undefined) {
  return REAL_CLINICAL_CODE_MAPPING[normalizedClinicalCode(code)] ?? null;
}
