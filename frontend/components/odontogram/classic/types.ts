export type ToothSurface =
  | "OCCLUSAL"
  | "INCISAL"
  | "VESTIBULAR"
  | "PALATAL"
  | "LINGUAL"
  | "MESIAL"
  | "DISTAL"
  | "CERVICAL"
  | "PULPAL_RADICULAR"
  | "WHOLE_TOOTH";

export type ClinicalEventKind =
  | "CARIES"
  | "RESTORATION"
  | "ENDODONTICS"
  | "CROWN"
  | "IMPLANT"
  | "FRACTURE"
  | "EXTRACTION"
  | "ABSENT"
  | "INFORMATION";

export type ClinicalEventStatus = "DIAGNOSIS" | "COMPLETED" | "PLANNED";
export type ClinicalLocalization =
  | "SURFACE_SPECIFIC"
  | "SURFACE_UNSPECIFIED"
  | "NON_SURFACE"
  | "WHOLE_TOOTH"
  | "PULPAL_RADICULAR";

export type DualClinicalEvent = {
  id: string;
  kind: ClinicalEventKind;
  surfaces: ToothSurface[];
  status: ClinicalEventStatus;
  label: string;
  localization?: ClinicalLocalization;
  sourceLayer?: string;
  sourceCode?: string;
  sourceName?: string;
  unmapped?: boolean;
};

export type ToothDentition = "PERMANENT" | "PRIMARY";
export type ToothFamily = "INCISOR" | "CANINE" | "PREMOLAR" | "MOLAR";
export type ToothArch = "UPPER" | "LOWER";
export type ToothQuadrant = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
export type SurfaceRole = "CENTER" | "TOP" | "BOTTOM" | "LEFT" | "RIGHT" | "CERVICAL" | "PULP" | "WHOLE";

export type DualClinicalToothModel = {
  toothNumber: string;
  dentition: ToothDentition;
  family: ToothFamily;
  arch: ToothArch;
  quadrant: ToothQuadrant;
  events: DualClinicalEvent[];
};

export type SurfaceOrientation = {
  toothNumber: string;
  arch: ToothArch;
  quadrant: ToothQuadrant;
  maxillary: ToothArch;
  family: ToothFamily;
  mesial: "LEFT" | "RIGHT";
  distal: "LEFT" | "RIGHT";
  vestibular: "TOP" | "BOTTOM";
  internal: "TOP" | "BOTTOM";
  internalSurface: "PALATAL" | "LINGUAL";
  centralSurface: "OCCLUSAL" | "INCISAL";
  innerSurface: "PALATAL" | "LINGUAL";
  mesialRole: "LEFT" | "RIGHT";
  distalRole: "LEFT" | "RIGHT";
  vestibularRole: "TOP" | "BOTTOM";
  innerRole: "TOP" | "BOTTOM";
};

export type ClinicalMarker = {
  id: string;
  eventId: string;
  kind: ClinicalEventKind;
  status: ClinicalEventStatus;
  label: string;
  surface: ToothSurface;
  role: SurfaceRole;
  color: string;
  stroke: string;
  pattern: "SOLID" | "OUTLINE" | "DASHED" | "LINE" | "SYMBOL";
  symbol: string;
  localization: ClinicalLocalization;
};

export type DualClinicalToothViewModel = {
  model: DualClinicalToothModel;
  orientation: SurfaceOrientation;
  surfaceMarkers: ClinicalMarker[];
  structuralMarkers: ClinicalMarker[];
  generalMarkers: ClinicalMarker[];
  tooltip: string;
  summaryLabel: string;
  eventCount: number;
  isAbsent: boolean;
};
