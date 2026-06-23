import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { SiteList } from "@/components/organization/SiteList";

export const metadata: Metadata = { title: "Sedes" };

export default function Page() {
  return <PermissionGate permission="sites.view"><SiteList /></PermissionGate>;
}
