import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { PatientList } from "@/components/patients/PatientList";

export const metadata: Metadata = { title: "Pacientes" };

export default function PatientsPage() {
  return (
    <PermissionGate permission="patients.view">
      <PatientList />
    </PermissionGate>
  );
}
