import type { MedicalHistoryItemInput } from "@/types/clinicalRecord";

export const LEGACY_MEDICAL_HISTORY_TYPES = new Set([
  "hipertensión",
  "enfermedad cardiovascular",
  "diabetes",
  "trastorno de coagulación",
  "enfermedad respiratoria",
  "enfermedad renal",
  "enfermedad hepática",
  "enfermedad neurológica",
  "inmunosupresión",
  "cáncer",
  "hospitalización",
  "cirugía",
  "transfusión",
  "prótesis o dispositivo",
  "embarazo",
  "lactancia",
  "otro",
]);

function normalized(value: string | null | undefined) {
  return (value ?? "").trim().toLocaleLowerCase("es");
}

export function isCurrentPositiveMedicalHistory(
  item: Pick<MedicalHistoryItemInput, "present" | "status">,
) {
  return normalized(item.present) === "si" && normalized(item.status) === "activo";
}

export function hasLegacyMedicalHistoryQuestionnaire(
  items: MedicalHistoryItemInput[],
) {
  if (items.some((item) => normalized(item.source).startsWith("legacy"))) {
    return true;
  }
  const types = new Set(items.map((item) => normalized(item.type)));
  return [...LEGACY_MEDICAL_HISTORY_TYPES].every((type) => types.has(type));
}

export function isLegacyMedicalHistoryItem(
  item: MedicalHistoryItemInput,
  items: MedicalHistoryItemInput[],
) {
  return (
    hasLegacyMedicalHistoryQuestionnaire(items) &&
    LEGACY_MEDICAL_HISTORY_TYPES.has(normalized(item.type))
  );
}

export function medicalHistoryResponseLabel(item: MedicalHistoryItemInput) {
  const present = normalized(item.present);
  if (present === "si") {
    return normalized(item.status) === "activo" ? "Sí" : "Sí · Registro inactivo";
  }
  if (present === "no") return "No";
  return "Información no confirmada";
}
