declare module "@/lib/clinicalCompletionCatalog.mjs" {
  import type { OdontogramCatalogItem } from "@/types/odontogram";
  import type { ProcedureCatalogItem } from "@/types/treatment";

  export function resolveClinicalCompletionCatalog(
    performedItems: OdontogramCatalogItem[],
    catalogProcedure: ProcedureCatalogItem | null,
  ): {
    items: OdontogramCatalogItem[];
    selectedId: string;
    error: string | null;
  };
}
