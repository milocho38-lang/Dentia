"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Modal } from "@/components/shared/Modal";
import { Spinner } from "@/components/shared/Spinner";
import { ConfirmDialog } from "@/components/users/ConfirmDialog";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/services/apiClient";
import {
  createResponsible,
  deactivatePatient,
  deleteResponsible,
  getPatientAppointments,
  getPatientSummary,
  reactivatePatient,
  updateResponsible,
} from "@/services/patientService";
import type {
  PatientAppointment,
  PatientSummary,
  Responsible,
  ResponsibleInput,
} from "@/types/patient";

function formatDate(value: string | null, withTime = false) {
  if (!value) return "No registrado";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    ...(withTime ? { timeStyle: "short" as const } : {}),
  }).format(new Date(value));
}

export function PatientDetail({ patientId }: { patientId: string }) {
  const { hasPermission } = useAuth();
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [appointments, setAppointments] = useState<PatientAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [responsibleOpen, setResponsibleOpen] = useState(false);
  const [editingResponsible, setEditingResponsible] =
    useState<Responsible | null>(null);
  const [confirmation, setConfirmation] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [loadedSummary, loadedAppointments] = await Promise.all([
        getPatientSummary(patientId),
        getPatientAppointments(patientId),
      ]);
      setSummary(loadedSummary);
      setAppointments(loadedAppointments);
    } catch {
      setError("No fue posible cargar el paciente.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading || !summary) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 text-slate-500">
        <Spinner className="h-7 w-7 text-dentia-primary" />
        Cargando paciente…
      </div>
    );
  }

  const patient = summary.patient;

  async function changeStatus() {
    setSaving(true);
    setError(null);
    try {
      if (patient.status === "Activo") {
        await deactivatePatient(patient.id);
      } else {
        await reactivatePatient(patient.id);
      }
      setConfirmation(false);
      await load();
    } catch (statusError) {
      setError(
        statusError instanceof ApiError
          ? statusError.detail ?? statusError.message
          : "No fue posible cambiar el estado.",
      );
      setConfirmation(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <Link
        href="/pacientes"
        className="text-sm font-bold text-green-700 hover:underline"
      >
        ← Volver a pacientes
      </Link>

      <header className="mt-5 flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-bold text-slate-950">
              {patient.full_name}
            </h1>
            <span
              className={`rounded-full px-3 py-1 text-xs font-bold ${
                patient.status === "Activo"
                  ? "bg-green-50 text-green-700"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {patient.status}
            </span>
            {!patient.profile_complete && (
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
                Perfil incompleto
              </span>
            )}
            {patient.is_minor && (
              <span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-bold text-sky-800">
                Menor de edad
              </span>
            )}
          </div>
          <p className="mt-2 text-sm text-slate-500">
            {patient.document_type === "Sin documento"
              ? "Sin documento"
              : `${patient.document_type} ${patient.document ?? ""}`}{" "}
            · {patient.mobile}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {patient.status === "Activo" &&
            hasPermission("appointments.create") && (
              <Link
                href={`/agenda?patient_id=${patient.id}&new=1`}
                className="inline-flex min-h-11 items-center rounded-xl bg-dentia-primary px-4 font-bold text-white"
              >
                Nueva cita
              </Link>
            )}
          {hasPermission("patients.update") && (
            <Link
              href={`/pacientes/${patient.id}/editar`}
              className="inline-flex min-h-11 items-center rounded-xl border border-slate-300 px-4 font-bold text-slate-700"
            >
              Editar
            </Link>
          )}
          {hasPermission("patients.deactivate") && (
            <button
              type="button"
              onClick={() => setConfirmation(true)}
              className={`min-h-11 rounded-xl px-4 font-bold ${
                patient.status === "Activo"
                  ? "border border-red-200 text-red-700"
                  : "bg-green-700 text-white"
              }`}
            >
              {patient.status === "Activo" ? "Desactivar" : "Reactivar"}
            </button>
          )}
        </div>
      </header>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}

      <div className="mt-7 grid gap-5 lg:grid-cols-3">
        <SummaryCard
          label="Próxima cita"
          value={
            summary.next_appointment
              ? formatDate(summary.next_appointment.starts_at, true)
              : "Sin cita futura"
          }
        />
        <SummaryCard
          label="Última cita"
          value={
            summary.last_appointment
              ? formatDate(summary.last_appointment.starts_at, true)
              : "Sin citas anteriores"
          }
        />
        <SummaryCard
          label="Citas registradas"
          value={String(summary.appointment_count)}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.35fr_1fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">Datos personales</h2>
          <dl className="mt-5 grid gap-5 sm:grid-cols-2">
            {[
              ["Fecha de nacimiento", formatDate(patient.birth_date)],
              [
                "Edad",
                patient.age === null ? "No registrada" : `${patient.age} años`,
              ],
              ["Sexo", patient.sex ?? "No registrado"],
              ["Correo", patient.email ?? "No registrado"],
              ["Teléfono alternativo", patient.alternate_phone ?? "No registrado"],
              [
                "Ubicación",
                [patient.city, patient.department].filter(Boolean).join(", ") ||
                  "No registrada",
              ],
              ["Dirección", patient.address ?? "No registrada"],
              [
                "Contacto de emergencia",
                [patient.emergency_contact_name, patient.emergency_contact_mobile]
                  .filter(Boolean)
                  .join(" · ") || "No registrado",
              ],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs font-bold uppercase tracking-wide text-slate-400">
                  {label}
                </dt>
                <dd className="mt-1 text-sm font-semibold text-slate-800">
                  {value}
                </dd>
              </div>
            ))}
          </dl>
          <div className="mt-6 border-t border-slate-100 pt-5">
            <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Observaciones administrativas
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
              {patient.administrative_notes ?? "Sin observaciones."}
            </p>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-bold text-slate-900">Responsables</h2>
            {hasPermission("patients.update") && (
              <button
                type="button"
                onClick={() => {
                  setEditingResponsible(null);
                  setResponsibleOpen(true);
                }}
                className="text-sm font-bold text-green-700"
              >
                + Agregar
              </button>
            )}
          </div>
          <div className="mt-4 space-y-3">
            {patient.responsibles.map((responsible) => (
              <div
                key={responsible.id}
                className="rounded-xl border border-slate-200 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-bold text-slate-900">{responsible.name}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {responsible.relationship} · {responsible.mobile}
                    </p>
                    {responsible.is_primary && (
                      <span className="mt-2 inline-flex rounded-full bg-green-50 px-2 py-1 text-[11px] font-bold text-green-700">
                        Principal
                      </span>
                    )}
                  </div>
                  {hasPermission("patients.update") && (
                    <div className="flex gap-2 text-xs font-bold">
                      <button
                        type="button"
                        onClick={() => {
                          setEditingResponsible(responsible);
                          setResponsibleOpen(true);
                        }}
                        className="text-green-700"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            await deleteResponsible(
                              patient.id,
                              responsible.id,
                            );
                            await load();
                          } catch (deleteError) {
                            setError(
                              deleteError instanceof ApiError
                                ? deleteError.detail ?? deleteError.message
                                : "No fue posible retirar el responsable.",
                            );
                          }
                        }}
                        className="text-red-700"
                      >
                        Retirar
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {!patient.responsibles.length && (
              <p className="py-6 text-center text-sm text-slate-500">
                No hay responsables registrados.
              </p>
            )}
          </div>
        </section>
      </div>

      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-5">
          <h2 className="text-lg font-bold text-slate-900">
            Historial de citas
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                {["Fecha", "Tipo", "Odontólogo", "Sede", "Estado"].map(
                  (heading) => (
                    <th
                      key={heading}
                      className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500"
                    >
                      {heading}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {appointments.map((appointment) => (
                <tr key={appointment.id}>
                  <td className="px-5 py-4 text-sm text-slate-700">
                    {formatDate(appointment.starts_at, true)}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-700">
                    {appointment.appointment_type_name}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-700">
                    {appointment.dentist_name}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-700">
                    {appointment.site_name}
                  </td>
                  <td className="px-5 py-4">
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700">
                      {appointment.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!appointments.length && (
            <p className="py-12 text-center text-sm text-slate-500">
              El paciente todavía no tiene citas.
            </p>
          )}
        </div>
      </section>

      <ResponsibleDialog
        open={responsibleOpen}
        responsible={editingResponsible}
        onClose={() => setResponsibleOpen(false)}
        onSave={async (data) => {
          if (editingResponsible) {
            await updateResponsible(
              patient.id,
              editingResponsible.id,
              data,
            );
          } else {
            await createResponsible(patient.id, data);
          }
          setResponsibleOpen(false);
          await load();
        }}
      />

      <ConfirmDialog
        open={confirmation}
        title={
          patient.status === "Activo"
            ? "Desactivar paciente"
            : "Reactivar paciente"
        }
        description={
          patient.status === "Activo"
            ? "Solo podrá desactivarse si no tiene citas futuras activas."
            : "El paciente volverá a estar disponible para nuevas citas."
        }
        confirmLabel={
          patient.status === "Activo" ? "Desactivar" : "Reactivar"
        }
        busy={saving}
        tone={patient.status === "Activo" ? "danger" : "primary"}
        onClose={() => setConfirmation(false)}
        onConfirm={changeStatus}
      />
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className="mt-2 font-bold text-slate-900">{value}</p>
    </div>
  );
}

function ResponsibleDialog({
  open,
  responsible,
  onClose,
  onSave,
}: {
  open: boolean;
  responsible: Responsible | null;
  onClose: () => void;
  onSave: (data: ResponsibleInput) => Promise<void>;
}) {
  const [name, setName] = useState(responsible?.name ?? "");
  const [relationship, setRelationship] = useState(
    responsible?.relationship ?? "",
  );
  const [documentType, setDocumentType] = useState(
    responsible?.document_type ?? "CC",
  );
  const [document, setDocument] = useState(responsible?.document ?? "");
  const [mobile, setMobile] = useState(responsible?.mobile ?? "");
  const [email, setEmail] = useState(responsible?.email ?? "");
  const [primary, setPrimary] = useState(responsible?.is_primary ?? false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(responsible?.name ?? "");
    setRelationship(responsible?.relationship ?? "");
    setDocumentType(responsible?.document_type ?? "CC");
    setDocument(responsible?.document ?? "");
    setMobile(responsible?.mobile ?? "");
    setEmail(responsible?.email ?? "");
    setPrimary(responsible?.is_primary ?? false);
    setError(null);
  }, [open, responsible]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSave({
        name,
        relationship,
        document_type: documentType,
        document: documentType === "Sin documento" ? null : document || null,
        mobile,
        email: email || null,
        is_primary: primary,
      });
    } catch (submitError) {
      setError(
        submitError instanceof ApiError
          ? submitError.detail ?? submitError.message
          : "No fue posible guardar el responsable.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={open}
      title={responsible ? "Editar responsable" : "Agregar responsable"}
      onClose={onClose}
    >
      <form onSubmit={submit} className="space-y-4">
        {error && <Alert tone="error">{error}</Alert>}
        <Input label="Nombre completo" value={name} onChange={setName} />
        <Input label="Parentesco" value={relationship} onChange={setRelationship} />
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Tipo de documento
            </span>
            <select
              value={documentType}
              onChange={(event) => setDocumentType(event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
            >
              {["CC", "TI", "RC", "CE", "Pasaporte", "Otro", "Sin documento"].map(
                (type) => <option key={type}>{type}</option>,
              )}
            </select>
          </label>
          <Input
            label="Documento"
            value={document}
            onChange={setDocument}
            disabled={documentType === "Sin documento"}
          />
          <Input label="Celular" value={mobile} onChange={setMobile} />
          <Input label="Correo" value={email} onChange={setEmail} />
        </div>
        <label className="flex items-center gap-3 text-sm font-bold text-slate-700">
          <input
            type="checkbox"
            checked={primary}
            onChange={(event) => setPrimary(event.target.checked)}
            className="h-4 w-4 accent-green-600"
          />
          Responsable principal
        </label>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="min-h-11 rounded-xl border border-slate-300 px-4 font-bold"
          >
            Cancelar
          </button>
          <button
            disabled={busy}
            className="min-h-11 rounded-xl bg-dentia-primary px-5 font-bold text-white disabled:opacity-60"
          >
            Guardar
          </button>
        </div>
      </form>
    </Modal>
  );
}

function Input({
  label,
  value,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label>
      <span className="mb-2 block text-sm font-bold text-slate-700">{label}</span>
      <input
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full rounded-xl border border-slate-300 px-3 disabled:bg-slate-100"
      />
    </label>
  );
}
