import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { BrandingSettingsPage } from "@/components/organization/BrandingSettingsPage";

export const metadata: Metadata = { title: "Personalización" };

export default function Page() {
  return (
    <PermissionGate permission="branding.view">
      <BrandingSettingsPage />
    </PermissionGate>
  );
}
