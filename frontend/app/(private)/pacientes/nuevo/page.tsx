"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { PatientForm } from "@/components/patients/PatientForm";
import { createPatient } from "@/services/patientService";

export default function NewPatientPage() {
  const router = useRouter();
  return (
    <PermissionGate permission="patients.create">
      <div className="mx-auto max-w-4xl">
        <Link
          href="/pacientes"
          className="text-sm font-bold text-green-700 hover:underline"
        >
          ← Volver a pacientes
        </Link>
        <h1 className="mt-5 text-3xl font-bold text-slate-950">
          Crear paciente
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Registra información administrativa y de contacto.
        </p>
        <div className="mt-7">
          <PatientForm
            submitLabel="Crear paciente"
            onSubmit={async (data) => {
              const patient = await createPatient(data);
              router.push(`/pacientes/${patient.id}`);
            }}
          />
        </div>
      </div>
    </PermissionGate>
  );
}
