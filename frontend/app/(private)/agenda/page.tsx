import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { AgendaView } from "@/components/agenda/AgendaView";

export const metadata: Metadata = { title: "Agenda" };

export default function AgendaPage() {
  return (
    <PermissionGate permission="appointments.view">
      <AgendaView />
    </PermissionGate>
  );
}
