import { PermissionGate } from "@/components/auth/PermissionGate";
import { PlatformCompanyCreatePage } from "@/components/platform/PlatformCompanyPages";

export default function Page() {
  return (
    <PermissionGate permission="platform.companies.manage">
      <PlatformCompanyCreatePage />
    </PermissionGate>
  );
}
