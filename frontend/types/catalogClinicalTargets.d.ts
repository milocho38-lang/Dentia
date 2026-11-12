declare module "@/lib/catalogClinicalTargets.mjs" {
  export function resolveCatalogClinicalTargets(
    priceProvenance: Record<string, unknown> | null | undefined,
    tooth?: string | null,
  ): {
    fixedTeeth: string[];
    zone: "ANTERIOR" | null;
    dentition: string;
    requiredDentition: string | null;
  };

  export function filterTeethForRequiredDentition(
    teeth: string[],
    requiredDentition: string | null | undefined,
  ): string[];
}
