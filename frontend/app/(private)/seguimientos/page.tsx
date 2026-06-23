import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { FollowupList } from "@/components/followups/FollowupList";

export const metadata: Metadata = { title: "Seguimientos" };

export default function FollowupsPage() {
  return <PermissionGate permission="followups.view"><FollowupList /></PermissionGate>;
}
