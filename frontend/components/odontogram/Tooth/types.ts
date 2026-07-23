export type ToothDentition = "PERMANENT" | "PRIMARY" | "SUPERNUMERARY";

export type ToothSurface =
  | "VESTIBULAR"
  | "LINGUAL"
  | "PALATAL"
  | "MESIAL"
  | "DISTAL"
  | "OCCLUSAL"
  | "INCISAL";

export type ToothClinicalLayer =
  | "STRUCTURAL"
  | "FINDING"
  | "DIAGNOSIS"
  | "PLANNED"
  | "PERFORMED"
  | "OBSERVATION";

export type ToothVisualState =
  | "HEALTHY"
  | "OCCLUSAL_CARIES"
  | "PROXIMAL_CARIES"
  | "CERVICAL_CARIES"
  | "SIMPLE_FILLING"
  | "MULTIPLE_FILLINGS"
  | "DEFINITIVE_CROWN"
  | "TEMPORARY_CROWN"
  | "ENDODONTICS"
  | "POST"
  | "IMPLANT"
  | "FIXED_PROSTHESIS"
  | "REMOVABLE_PROSTHESIS"
  | "MISSING"
  | "TEMPORARY_RESTORATION"
  | "SEALANT"
  | "NON_CARIOUS_CERVICAL_LESION"
  | "WEAR"
  | "FRACTURE"
  | "MOBILITY"
  | "PRIMARY_TOOTH"
  | "PLANNED_TREATMENT"
  | "IN_PROGRESS_TREATMENT"
  | "OBSERVATION";

export interface ToothDetail {
  id: string;
  catalogCode: string;
  catalogName: string;
  catalogType?: string | null;
  color?: string | null;
  pattern?: string | null;
  symbol?: string | null;
  surfaces?: ToothSurface[] | null;
  layer: ToothClinicalLayer | string;
}

export interface ToothProps {
  number: string;
  dentition?: ToothDentition;
  details?: ToothDetail[];
  selected?: boolean;
  disabled?: boolean;
  eventCount?: number;
  visibleLayers?: Set<string>;
  onClick?: () => void;
  className?: string;
  compactBadges?: boolean;
}

export interface ToothRenderState {
  visualStates: Set<ToothVisualState>;
  unlocalizedStates: Set<ToothVisualState>;
  details: ToothDetail[];
  surfaceStates: Partial<Record<ToothSurface, ToothVisualState[]>>;
  primaryLabel: string;
  tooltipLines: string[];
}
