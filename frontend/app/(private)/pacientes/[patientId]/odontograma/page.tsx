"use client";

import { use } from "react";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { OdontogramPage } from "@/components/patients/OdontogramPage";

export default function PatientOdontogramRoute({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = use(params);
  return (
    <PermissionGate permission="odontogram.view">
      <OdontogramPage patientId={patientId} />
    </PermissionGate>
  );
}
