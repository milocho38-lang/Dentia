import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { WelcomeDashboard } from "@/components/dashboard/WelcomeDashboard";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default function DashboardPage() {
  return (
    <PermissionGate permission="dashboard.view">
      <WelcomeDashboard />
    </PermissionGate>
  );
}
