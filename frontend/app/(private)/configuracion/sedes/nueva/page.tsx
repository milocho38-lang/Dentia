import { PermissionGate } from "@/components/auth/PermissionGate";
import { SiteForm } from "@/components/organization/SiteForm";

export default function Page() {
  return <PermissionGate permission="sites.manage"><SiteForm mode="create" /></PermissionGate>;
}
