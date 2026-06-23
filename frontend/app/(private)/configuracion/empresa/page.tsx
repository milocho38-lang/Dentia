import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { CompanySettingsPage } from "@/components/organization/CompanySettingsPage";

export const metadata: Metadata = { title: "Empresa" };

export default function Page() {
  return <PermissionGate permission="company.view"><CompanySettingsPage /></PermissionGate>;
}
