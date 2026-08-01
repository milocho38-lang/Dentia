import { PermissionGate } from "@/components/auth/PermissionGate";
import { ConsentTemplatesPage } from "@/components/consents/ConsentTemplatesPage";

export default function ConsentTemplatesRoute() {
  return (
    <PermissionGate permission="consent.template.read">
      <ConsentTemplatesPage />
    </PermissionGate>
  );
}
