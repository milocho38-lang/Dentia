import { PermissionGate } from "@/components/auth/PermissionGate";
import { UsageAdoptionDashboard } from "@/components/platform/UsageAdoptionDashboard";

export default function Page() {
  return (
    <PermissionGate permission="platform.usage.view">
      <UsageAdoptionDashboard />
    </PermissionGate>
  );
}
