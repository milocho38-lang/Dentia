export const responsibleRelationshipOptions = [
  ["MOTHER", "Madre"],
  ["FATHER", "Padre"],
  ["SIBLING", "Hermano/a"],
  ["GRANDPARENT", "Abuelo/a"],
  ["AUNT_UNCLE", "Tío/a"],
  ["COUSIN", "Primo/a"],
  ["CAREGIVER", "Cuidador/a"],
  ["NEIGHBOR", "Vecino/a"],
  ["LEGAL_REPRESENTATIVE", "Representante legal"],
  ["OTHER", "Otro"],
] as const;

export const minorParticipationOptions = [
  ["INFORMED_AND_AGREED", "Informado y de acuerdo"],
  ["INFORMED_NO_OBJECTION", "Informado, sin manifestar oposición"],
  ["COULD_NOT_EXPRESS_DUE_TO_AGE_OR_CONDITION", "No fue posible obtener manifestación por edad o condición"],
  ["NOT_APPLICABLE", "No aplica"],
  ["OTHER", "Otro"],
] as const;

const relationshipLabels = new Map<string, string>(responsibleRelationshipOptions);

export function responsibleRelationshipLabel(value?: string | null, other?: string | null): string | null {
  if (!value) return null;
  const label = relationshipLabels.get(value) ?? "Relación no especificada";
  return value === "OTHER" && other?.trim() ? `${label}: ${other.trim()}` : label;
}
