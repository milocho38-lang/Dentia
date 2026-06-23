"use client";

import { use } from "react";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { SiteForm } from "@/components/organization/SiteForm";

export default function Page({ params }: { params: Promise<{siteId:string}> }) {
  const {siteId}=use(params);
  return <PermissionGate permission="sites.view"><SiteForm siteId={siteId} mode="detail" /></PermissionGate>;
}
