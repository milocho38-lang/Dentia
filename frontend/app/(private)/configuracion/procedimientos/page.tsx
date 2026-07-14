import { PermissionGate } from "@/components/auth/PermissionGate";
import { ProcedureCatalogPage } from "@/components/treatments/ProcedureCatalogPage";

export default function ProceduresCatalogRoute() {
  return (
    <PermissionGate permission="procedure_catalog.view">
      <ProcedureCatalogPage />
    </PermissionGate>
  );
}
