import { PermissionGate } from "@/components/auth/PermissionGate";
import { DentistSiteManagementPage } from "@/components/organization/DentistSiteManagementPage";

export default function DentistsPage() {
  return (
    <PermissionGate permission="sites.view">
      <DentistSiteManagementPage />
    </PermissionGate>
  );
}
