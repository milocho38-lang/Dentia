"use client";

import { use } from "react";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { DemoRequestDetailPage } from "@/components/platform/DemoRequestDetailPage";

export default function Page({ params }: { params: Promise<{ demoRequestId: string }> }) {
  const { demoRequestId } = use(params);
  return (
    <PermissionGate permission="platform.demo_requests.view">
      <DemoRequestDetailPage demoRequestId={demoRequestId} />
    </PermissionGate>
  );
}
