import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { DemoRequestsPage } from "@/components/platform/DemoRequestsPage";

export const metadata: Metadata = { title: "Solicitudes de demo" };

export default function Page() {
  return (
    <PermissionGate permission="platform.demo_requests.view">
      <DemoRequestsPage />
    </PermissionGate>
  );
}
