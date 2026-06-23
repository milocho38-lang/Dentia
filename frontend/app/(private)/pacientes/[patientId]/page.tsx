"use client";

import { use } from "react";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { PatientDetail } from "@/components/patients/PatientDetail";

export default function PatientDetailPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = use(params);
  return (
    <PermissionGate permission="patients.view">
      <PatientDetail patientId={patientId} />
    </PermissionGate>
  );
}
