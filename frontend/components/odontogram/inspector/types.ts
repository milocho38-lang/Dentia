import type { RefObject } from "react";
import type { OdontogramCatalogItem, OdontogramEvent, OdontogramToothState } from "@/types/odontogram";

export type DentalInspectorTab = "summary" | "history" | "register" | "drafts";

export type DentalInspectorEventOption = {
  eventType: string;
  layer: string;
  label: string;
  catalogType: string;
};

export type DentalInspectorProps = {
  toothCode: string;
  toothState?: OdontogramToothState;
  history: OdontogramEvent[];
  drafts: OdontogramEvent[];
  selectedSurfaces: string[];
  warning: string | null;
  eventOptions: readonly DentalInspectorEventOption[];
  eventType: string;
  catalogItemId: string;
  availableCatalog: OdontogramCatalogItem[];
  observation: string;
  saveAsConfirmed: boolean;
  saving: boolean;
  canEditDraft: boolean;
  canConfirm: boolean;
  closeButtonRef?: RefObject<HTMLButtonElement | null>;
  onClose: () => void;
  onToggleSurface: (surface: string) => void;
  onEventTypeChange: (value: string) => void;
  onCatalogItemChange: (value: string) => void;
  onObservationChange: (value: string) => void;
  onSaveAsConfirmedChange: (value: boolean) => void;
  onSaveEvent: () => void;
  onConfirmDraft: (event: OdontogramEvent) => void;
};
