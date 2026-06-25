import { PermissionGate } from "@/components/auth/PermissionGate";
import { PlatformCompanyListPage } from "@/components/platform/PlatformCompanyPages";

export default function Page() {
  return (
    <PermissionGate permission="platform.companies.view">
      <PlatformCompanyListPage />
    </PermissionGate>
  );
}
