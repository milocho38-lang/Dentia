import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { PatientImport } from "@/components/patients/PatientImport";

export const metadata: Metadata = { title: "Importar pacientes" };

export default function PatientImportPage() {
  return (
    <PermissionGate permission="patients.import">
      <PatientImport />
    </PermissionGate>
  );
}
