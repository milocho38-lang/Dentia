"use client";

import { use } from "react";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { ClinicalRecordPage } from "@/components/patients/ClinicalRecordPage";

export default function PatientClinicalRecordRoute({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = use(params);
  return (
    <PermissionGate permission="clinical_records.view_sensitive">
      <ClinicalRecordPage patientId={patientId} />
    </PermissionGate>
  );
}
