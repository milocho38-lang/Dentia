import { archFromQuadrant, dentitionFromTooth, familyFromTooth, quadrantFromTooth } from "./orientation";
import type { ClinicalEventKind, ClinicalEventStatus, DualClinicalEvent, DualClinicalToothModel, ToothFamily, ToothSurface } from "./types";

function event(id: string, kind: ClinicalEventKind, surfaces: ToothSurface[], status: ClinicalEventStatus, label: string, sourceCode?: string): DualClinicalEvent {
  return { id, kind, surfaces, status, label, sourceCode };
}

export function createToothModel(
  toothNumber: string,
  events: DualClinicalEvent[],
  family: ToothFamily = familyFromTooth(toothNumber),
): DualClinicalToothModel {
  const quadrant = quadrantFromTooth(toothNumber);
  return {
    toothNumber,
    dentition: dentitionFromTooth(toothNumber),
    family,
    arch: archFromQuadrant(quadrant),
    quadrant,
    events,
  };
}

export const DUAL_TOOTH_PRESETS = {
  mesial15: createToothModel("15", [
    event("caries-mesial-15", "CARIES", ["MESIAL"], "DIAGNOSIS", "Caries mesial"),
  ]),
  distal15: createToothModel("15", [
    event("caries-distal-15", "CARIES", ["DISTAL"], "DIAGNOSIS", "Caries distal"),
  ]),
  palatal15: createToothModel("15", [
    event("caries-palatina-15", "CARIES", ["PALATAL"], "DIAGNOSIS", "Caries palatina"),
  ]),
  mesial25: createToothModel("25", [
    event("caries-mesial-25", "CARIES", ["MESIAL"], "DIAGNOSIS", "Caries mesial"),
  ]),
  distal25: createToothModel("25", [
    event("caries-distal-25", "CARIES", ["DISTAL"], "DIAGNOSIS", "Caries distal"),
  ]),
  cariesVestibular31: createToothModel("31", [
    event("caries-vestibular-31", "CARIES", ["VESTIBULAR"], "DIAGNOSIS", "Caries vestibular"),
  ]),
  cariesLingual31: createToothModel("31", [
    event("caries-lingual-31", "CARIES", ["LINGUAL"], "DIAGNOSIS", "Caries lingual"),
  ]),
  cariesIncisal31: createToothModel("31", [
    event("caries-incisal-31", "CARIES", ["INCISAL"], "DIAGNOSIS", "Caries incisal"),
  ]),
  cariesMesial31: createToothModel("31", [
    event("caries-mesial-31", "CARIES", ["MESIAL"], "DIAGNOSIS", "Caries mesial"),
  ]),
  restorationDistal31: createToothModel("31", [
    event("restoration-distal-31", "RESTORATION", ["DISTAL"], "COMPLETED", "Restauración distal"),
  ]),
  cariesOcclusal36: createToothModel("36", [
    event("caries-occlusal-36", "CARIES", ["OCCLUSAL"], "DIAGNOSIS", "Caries oclusal"),
  ]),
  restorationMultiSurface36: createToothModel("36", [
    event("restoration-mod-36", "RESTORATION", ["MESIAL", "OCCLUSAL", "DISTAL"], "COMPLETED", "Restauración MOD"),
  ]),
  endodontics36: createToothModel("36", [
    event("endodontics-36", "ENDODONTICS", ["PULPAL_RADICULAR"], "COMPLETED", "Endodoncia"),
  ]),
  defectiveEndodontics36: createToothModel("36", [
    event("prior-endodontics-36", "ENDODONTICS", ["PULPAL_RADICULAR"], "COMPLETED", "Endodoncia previa"),
    {
      ...event("defective-endodontics-36", "ENDODONTICS", ["PULPAL_RADICULAR"], "COMPLETED", "Endodoncia previa en mal estado"),
      variant: "DEFECTIVE_ZIGZAG",
    },
  ]),
  crown15: createToothModel("15", [
    event("crown-15", "CROWN", ["WHOLE_TOOTH"], "COMPLETED", "Corona"),
  ]),
  plannedCrown15: createToothModel("15", [
    event("planned-crown-15", "CROWN", ["WHOLE_TOOTH"], "PLANNED", "Corona planificada", "PLAN_CROWN"),
  ]),
  plannedImplant46: createToothModel("46", [
    event("planned-implant-46", "IMPLANT", ["WHOLE_TOOTH"], "PLANNED", "Implante planificado", "PLAN_IMPLANT"),
  ]),
  completedImplant46: createToothModel("46", [
    event("completed-implant-46", "IMPLANT", ["WHOLE_TOOTH"], "COMPLETED", "Implante realizado", "DONE_IMPLANT"),
  ]),
  implantCrown46: createToothModel("46", [
    event("completed-implant-crown-46", "IMPLANT", ["WHOLE_TOOTH"], "COMPLETED", "Implante realizado", "DONE_IMPLANT"),
    event("planned-crown-implant-46", "CROWN", ["WHOLE_TOOTH"], "PLANNED", "Corona sobre implante planificada", "PLAN_CROWN"),
  ]),
  completedImplantCrown46: createToothModel("46", [
    event("completed-implant-crown2-46", "IMPLANT", ["WHOLE_TOOTH"], "COMPLETED", "Implante realizado", "DONE_IMPLANT"),
    event("completed-crown-implant-46", "CROWN", ["WHOLE_TOOTH"], "COMPLETED", "Corona sobre implante realizada", "DONE_CROWN"),
  ]),
  plannedPost36: createToothModel("36", [
    event("planned-post-36", "POST", ["WHOLE_TOOTH"], "PLANNED", "Perno planificado", "PLAN_POST"),
  ]),
  completedPost36: createToothModel("36", [
    event("completed-post-36", "POST", ["WHOLE_TOOTH"], "COMPLETED", "Perno realizado", "DONE_POST"),
  ]),
  pulpotomy16: createToothModel("16", [
    event("pulpotomy-16", "PULPOTOMY", ["OCCLUSAL"], "COMPLETED", "Pulpotomía realizada", "DONE_PULPOTOMY"),
  ]),
  absent46: createToothModel("46", [
    event("absent-46", "ABSENT", ["WHOLE_TOOTH"], "COMPLETED", "Ausente"),
  ]),
  mesial46: createToothModel("46", [
    event("caries-mesial-46", "CARIES", ["MESIAL"], "DIAGNOSIS", "Caries mesial"),
  ]),
  temporal51: createToothModel("51", [
    event("caries-incisal-51", "CARIES", ["INCISAL"], "DIAGNOSIS", "Caries incisal temporal"),
  ]),
  temporal55: createToothModel("55", [
    event("restoration-occlusal-55", "RESTORATION", ["OCCLUSAL"], "COMPLETED", "Restauración oclusal temporal"),
  ]),
  combination36: createToothModel("36", [
    event("caries-vestibular-36", "CARIES", ["VESTIBULAR"], "DIAGNOSIS", "Caries vestibular"),
    event("restoration-occlusal-36", "RESTORATION", ["OCCLUSAL"], "COMPLETED", "Restauración oclusal"),
    event("endodontics-combo-36", "ENDODONTICS", ["PULPAL_RADICULAR"], "COMPLETED", "Endodoncia"),
  ]),
};

export type DualToothPresetKey = keyof typeof DUAL_TOOTH_PRESETS;

export const DUAL_TOOTH_PRESET_OPTIONS: Array<{ key: DualToothPresetKey; label: string; description: string }> = [
  { key: "mesial15", label: "Mesial 15", description: "15 · Mesial hacia línea media" },
  { key: "distal15", label: "Distal 15", description: "15 · Distal alejado de línea media" },
  { key: "palatal15", label: "Palatina 15", description: "15 · Palatina inferior visual" },
  { key: "mesial25", label: "Mesial 25", description: "25 · Mesial hacia línea media" },
  { key: "distal25", label: "Distal 25", description: "25 · Distal alejado de línea media" },
  { key: "cariesVestibular31", label: "Caries vestibular", description: "31 · Vestibular" },
  { key: "cariesLingual31", label: "Caries lingual", description: "31 · Lingual" },
  { key: "cariesIncisal31", label: "Caries incisal", description: "31 · Incisal" },
  { key: "cariesMesial31", label: "Caries mesial", description: "31 · Mesial" },
  { key: "restorationDistal31", label: "Restauración distal", description: "31 · Distal" },
  { key: "cariesOcclusal36", label: "Caries oclusal", description: "36 · Oclusal" },
  { key: "restorationMultiSurface36", label: "Restauración mult superficie", description: "36 · Mesial + Oclusal + Distal" },
  { key: "endodontics36", label: "Endodoncia", description: "36 · Pulpar / radicular" },
  { key: "defectiveEndodontics36", label: "Retratamiento pendiente", description: "36 · Zigzag azul sobre endodoncia previa" },
  { key: "crown15", label: "Corona", description: "15 · Pieza completa" },
  { key: "plannedCrown15", label: "Corona planificada", description: "15 · Contorno rojo" },
  { key: "plannedImplant46", label: "Implante planificado", description: "46 · Símbolo rojo" },
  { key: "completedImplant46", label: "Implante realizado", description: "46 · Símbolo azul" },
  { key: "implantCrown46", label: "Implante + corona pendiente", description: "46 · Implante azul + aro rojo" },
  { key: "completedImplantCrown46", label: "Implante + corona realizada", description: "46 · Implante azul + aro azul" },
  { key: "plannedPost36", label: "Perno planificado", description: "36 · Perno rojo sin conducto inventado" },
  { key: "completedPost36", label: "Perno realizado", description: "36 · Perno azul" },
  { key: "pulpotomy16", label: "Pulpotomía realizada", description: "16 · Círculo oclusal azul sin raíz" },
  { key: "absent46", label: "Ausente", description: "46 · Pieza completa" },
  { key: "mesial46", label: "Mesial 46", description: "46 · Mesial hacia línea media" },
  { key: "temporal51", label: "Temporal 51", description: "51 · Incisal temporal" },
  { key: "temporal55", label: "Temporal 55", description: "55 · Oclusal temporal" },
  { key: "combination36", label: "Combinación clínica", description: "36 · Caries + restauración + endodoncia" },
];
