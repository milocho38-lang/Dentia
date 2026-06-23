"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { listPatients } from "@/services/patientService";
import type { PatientListResponse } from "@/types/patient";

function formatDate(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function PatientList() {
  const { hasPermission } = useAuth();
  const [response, setResponse] = useState<PatientListResponse | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [incomplete, setIncomplete] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({
      page: String(page),
      page_size: "20",
    });
    if (search.trim()) params.set("search", search.trim());
    if (status) params.set("status", status);
    if (incomplete) params.set("incomplete", incomplete);
    try {
      setResponse(await listPatients(`?${params.toString()}`));
    } catch {
      setError("No fue posible cargar los pacientes.");
    } finally {
      setLoading(false);
    }
  }, [incomplete, page, search, status]);

  useEffect(() => {
    load();
  }, [load]);

  function submit(event: FormEvent) {
    event.preventDefault();
    setPage(1);
    load();
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
            Gestión
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Pacientes</h1>
          <p className="mt-2 text-sm text-slate-500">
            Consulta datos administrativos, responsables e historial de citas.
          </p>
        </div>
        {hasPermission("patients.create") && (
          <Link
            href="/pacientes/nuevo"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-dentia-primary px-5 font-bold text-white hover:bg-green-700"
          >
            Crear paciente
          </Link>
        )}
      </header>

      <form
        onSubmit={submit}
        className="mt-7 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[1fr_190px_210px_auto]"
      >
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Nombre, documento, celular o correo"
          className="min-h-11 rounded-xl border border-slate-300 px-4"
        />
        <select
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-4"
        >
          <option value="">Todos los estados</option>
          <option value="Activo">Activos</option>
          <option value="Inactivo">Inactivos</option>
        </select>
        <select
          value={incomplete}
          onChange={(event) => {
            setIncomplete(event.target.value);
            setPage(1);
          }}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-4"
        >
          <option value="">Todos los perfiles</option>
          <option value="false">Perfil completo</option>
          <option value="true">Perfil incompleto</option>
        </select>
        <button className="min-h-11 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50">
          Buscar
        </button>
      </form>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}

      <section className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center gap-3 py-16 text-slate-500">
            <Spinner className="h-6 w-6 text-dentia-primary" />
            Cargando pacientes…
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "Paciente",
                    "Documento",
                    "Contacto",
                    "Próxima cita",
                    "Estado",
                    "",
                  ].map((heading) => (
                    <th
                      key={heading}
                      className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {response?.items.map((patient) => (
                  <tr key={patient.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-bold text-slate-900">
                          {patient.full_name}
                        </p>
                        {!patient.profile_complete && (
                          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-800">
                            Perfil incompleto
                          </span>
                        )}
                        {patient.is_minor && (
                          <span className="rounded-full bg-sky-100 px-2 py-0.5 text-[11px] font-bold text-sky-800">
                            Menor
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-slate-500">
                        {patient.age === null
                          ? "Edad no registrada"
                          : `${patient.age} años`}
                      </p>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">
                      {patient.document_type === "Sin documento"
                        ? "Sin documento"
                        : `${patient.document_type} ${patient.document ?? ""}`}
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">
                      {patient.mobile}
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">
                      {formatDate(patient.next_appointment_at)}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                          patient.status === "Activo"
                            ? "bg-green-50 text-green-700"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {patient.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        href={`/pacientes/${patient.id}`}
                        className="text-sm font-bold text-green-700 hover:underline"
                      >
                        Ver detalle
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!response?.items.length && (
              <p className="py-14 text-center text-sm text-slate-500">
                No se encontraron pacientes.
              </p>
            )}
          </div>
        )}
      </section>

      {response && response.pages > 1 && (
        <div className="mt-5 flex items-center justify-between text-sm">
          <span className="text-slate-500">{response.total} pacientes</span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((current) => current - 1)}
              className="rounded-xl border border-slate-300 px-4 py-2 font-bold disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={page >= response.pages}
              onClick={() => setPage((current) => current + 1)}
              className="rounded-xl border border-slate-300 px-4 py-2 font-bold disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
