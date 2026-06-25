"use client";

import { use } from "react";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { PlatformCompanyDetailPage } from "@/components/platform/PlatformCompanyPages";

export default function Page({
  params,
}: {
  params: Promise<{ companyId: string }>;
}) {
  const { companyId } = use(params);
  return (
    <PermissionGate permission="platform.companies.view">
      <PlatformCompanyDetailPage companyId={companyId} />
    </PermissionGate>
  );
}
