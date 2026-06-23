"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { PatientForm } from "@/components/patients/PatientForm";
import { Spinner } from "@/components/shared/Spinner";
import { getPatient, updatePatient } from "@/services/patientService";
import type { Patient } from "@/types/patient";

export default function EditPatientPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = use(params);
  const router = useRouter();
  const [patient, setPatient] = useState<Patient | null>(null);

  useEffect(() => {
    getPatient(patientId).then(setPatient);
  }, [patientId]);

  return (
    <PermissionGate permission="patients.update">
      <div className="mx-auto max-w-4xl">
        <Link
          href={`/pacientes/${patientId}`}
          className="text-sm font-bold text-green-700 hover:underline"
        >
          ← Volver al paciente
        </Link>
        <h1 className="mt-5 text-3xl font-bold text-slate-950">
          Editar paciente
        </h1>
        <div className="mt-7">
          {patient ? (
            <PatientForm
              patient={patient}
              submitLabel="Guardar cambios"
              onSubmit={async (data) => {
                await updatePatient(patientId, data);
                router.push(`/pacientes/${patientId}`);
              }}
            />
          ) : (
            <div className="flex items-center gap-3 py-16 text-slate-500">
              <Spinner className="h-6 w-6 text-dentia-primary" />
              Cargando paciente…
            </div>
          )}
        </div>
      </div>
    </PermissionGate>
  );
}
