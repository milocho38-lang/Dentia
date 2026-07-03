"use client";

import Link from "next/link";
import type React from "react";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { getAgendaOptions } from "@/services/agendaService";
import { searchPatients } from "@/services/patientService";
import {
  approveBudget,
  approveTreatment,
  cancelProcedure,
  cancelTreatment,
  closeTreatment,
  createBudget,
  createPayment,
  createProcedure,
  createTreatment,
  getTreatment,
  listBudgets,
  listPayments,
  listProcedures,
  listTreatments,
  markProcedureDone,
  rejectBudget,
  reversePayment,
  submitBudget,
} from "@/services/treatmentService";
import type { AgendaOptions, PatientOption } from "@/types/agenda";
import type {
  Budget,
  Payment,
  Procedure,
  Treatment,
  TreatmentListItem,
} from "@/types/treatment";

function money(value: string | number) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function localDate(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: value.includes("T") ? "short" : undefined,
  }).format(new Date(value));
}

function statusBadge(status: string) {
  const styles: Record<string, string> = {
    Borrador: "bg-slate-100 text-slate-700",
    Presupuestado: "bg-sky-100 text-sky-800",
    Aprobado: "bg-emerald-100 text-emerald-800",
    "En ejecución": "bg-green-100 text-green-800",
    Pausado: "bg-amber-100 text-amber-800",
    Finalizado: "bg-violet-100 text-violet-800",
    Cancelado: "bg-red-100 text-red-800",
    Realizado: "bg-violet-100 text-violet-800",
    Pendiente: "bg-slate-100 text-slate-700",
    Agendado: "bg-sky-100 text-sky-800",
    "En proceso": "bg-green-100 text-green-800",
    rechazado: "bg-red-100 text-red-800",
    reversado: "bg-red-100 text-red-800",
    valido: "bg-emerald-100 text-emerald-800",
  };
  return styles[status] ?? "bg-slate-100 text-slate-700";
}

export function TreatmentListPage() {
  const { hasPermission } = useAuth();
  const [items, setItems] = useState<TreatmentListItem[]>([]);
  const [status, setStatus] = useState("");
  const [balance, setBalance] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (status) params.set("estado", status);
    if (balance) params.set("con_saldo", balance);
    try {
      const response = await listTreatments(params.size ? `?${params.toString()}` : "");
      setItems(response.items);
    } catch {
      setError("No fue posible cargar tratamientos.");
    } finally {
      setLoading(false);
    }
  }, [balance, status]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-7xl">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
            Gestión clínica y económica
          </p>
          <h1 className="mt-2 text-3xl font-black text-slate-950">
            Tratamientos
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Controla planes, procedimientos, presupuestos, pagos y saldos.
          </p>
        </div>
        {hasPermission("treatments.create") && (
          <Link
            href="/tratamientos/nuevo"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-dentia-primary px-5 font-bold text-white hover:bg-green-700"
          >
            Crear tratamiento
          </Link>
        )}
      </header>

      <div className="mt-7 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-[220px_180px_auto]">
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-4"
        >
          <option value="">Todos los estados</option>
          {["Borrador", "Presupuestado", "Aprobado", "En ejecución", "Pausado", "Finalizado", "Cancelado"].map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <select
          value={balance}
          onChange={(event) => setBalance(event.target.value)}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-4"
        >
          <option value="">Todos los saldos</option>
          <option value="true">Con saldo</option>
          <option value="false">Al día</option>
        </select>
        <button
          type="button"
          onClick={load}
          className="min-h-11 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50"
        >
          Filtrar
        </button>
      </div>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}

      <section className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center gap-3 py-16 text-slate-500">
            <Spinner className="h-6 w-6 text-dentia-primary" />
            Cargando tratamientos…
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  {["Paciente", "Tratamiento", "Estado", "Responsable", "Valor", "Pagado", "Saldo", ""].map((heading) => (
                    <th key={heading} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-4 font-bold text-slate-900">{item.patient_name}</td>
                    <td className="px-5 py-4 text-sm text-slate-700">
                      {item.name}
                      <p className="mt-1 text-xs text-slate-500">{item.main_site_name ?? "Sin sede principal"}</p>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${statusBadge(item.status)}`}>{item.status}</span>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">{item.responsible_dentist_name ?? "—"}</td>
                    <td className="px-5 py-4 text-sm font-bold">{money(item.final_value)}</td>
                    <td className="px-5 py-4 text-sm">{money(item.paid_value)}</td>
                    <td className="px-5 py-4 text-sm font-bold text-orange-700">{money(item.balance)}</td>
                    <td className="px-5 py-4 text-right">
                      <Link href={`/tratamientos/${item.id}`} className="text-sm font-bold text-green-700 hover:underline">
                        Ver detalle
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!items.length && (
              <p className="py-14 text-center text-sm text-slate-500">
                No hay tratamientos con los filtros seleccionados.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

export function TreatmentCreatePage() {
  const router = useRouter();
  const [options, setOptions] = useState<AgendaOptions | null>(null);
  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [patientSearch, setPatientSearch] = useState("");
  const [patientId, setPatientId] = useState("");
  const [name, setName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [dentistId, setDentistId] = useState("");
  const [siteId, setSiteId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAgendaOptions().then(setOptions).catch(() => setError("No fue posible cargar opciones."));
  }, []);

  useEffect(() => {
    if (patientSearch.trim().length < 2) return;
    const timeout = window.setTimeout(async () => {
      const response = await searchPatients(patientSearch.trim());
      setPatients(response.items.map((patient) => ({
        id: patient.id,
        full_name: patient.full_name,
        document_type: patient.document_type,
        document: patient.document,
        mobile: patient.mobile,
      })));
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [patientSearch]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!patientId || !name.trim()) {
      setError("Selecciona paciente y nombre del tratamiento.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await createTreatment({
        patient_id: patientId,
        name: name.trim(),
        specialty: specialty.trim() || null,
        responsible_dentist_id: dentistId || null,
        main_site_id: siteId || null,
      });
      router.push(`/tratamientos/${created.id}`);
    } catch {
      setError("No fue posible crear el tratamiento.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-black text-slate-950">Nuevo tratamiento</h1>
      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      <form onSubmit={submit} className="mt-6 space-y-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <label className="block">
          <span className="mb-2 block text-sm font-bold text-slate-700">Paciente</span>
          <input value={patientSearch} onChange={(event) => { setPatientSearch(event.target.value); setPatientId(""); }} className="min-h-12 w-full rounded-xl border border-slate-300 px-3" placeholder="Busca paciente" />
          {!patientId && patients.length > 0 && (
            <div className="mt-2 rounded-xl border border-slate-200 p-1">
              {patients.map((patient) => (
                <button key={patient.id} type="button" onClick={() => { setPatientId(patient.id); setPatientSearch(patient.full_name); }} className="block w-full rounded-lg px-3 py-2 text-left hover:bg-slate-50">
                  <span className="font-bold">{patient.full_name}</span>
                  <span className="ml-2 text-xs text-slate-500">{patient.mobile}</span>
                </button>
              ))}
            </div>
          )}
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-bold text-slate-700">Nombre</span>
          <input value={name} onChange={(event) => setName(event.target.value)} className="min-h-12 w-full rounded-xl border border-slate-300 px-3" placeholder="Ortodoncia, implantes, rehabilitación..." />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-bold text-slate-700">Especialidad</span>
          <input value={specialty} onChange={(event) => setSpecialty(event.target.value)} className="min-h-12 w-full rounded-xl border border-slate-300 px-3" />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">Odontólogo responsable</span>
            <select value={dentistId} onChange={(event) => setDentistId(event.target.value)} className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3">
              <option value="">Sin asignar</option>
              {options?.dentists.map((dentist) => <option key={dentist.id} value={dentist.id}>{dentist.name}</option>)}
            </select>
          </label>
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">Sede principal</span>
            <select value={siteId} onChange={(event) => setSiteId(event.target.value)} className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3">
              <option value="">Sin sede</option>
              {options?.sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
            </select>
          </label>
        </div>
        <button disabled={saving} className="min-h-12 rounded-xl bg-dentia-primary px-5 font-bold text-white hover:bg-green-700 disabled:opacity-60">
          {saving ? "Creando…" : "Crear tratamiento"}
        </button>
      </form>
    </div>
  );
}

export function TreatmentDetailPage({ treatmentId }: { treatmentId: string }) {
  const { hasPermission } = useAuth();
  const [treatment, setTreatment] = useState<Treatment | null>(null);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [options, setOptions] = useState<AgendaOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (showSpinner = true) => {
    if (showSpinner) setLoading(true);
    setError(null);
    try {
      const [loadedTreatment, loadedProcedures, loadedBudgets, loadedPayments, loadedOptions] = await Promise.all([
        getTreatment(treatmentId),
        listProcedures(treatmentId),
        listBudgets(),
        listPayments(),
        getAgendaOptions(),
      ]);
      setTreatment(loadedTreatment);
      setProcedures(loadedProcedures);
      setBudgets(loadedBudgets.filter((budget) => budget.treatment_id === treatmentId));
      setPayments(loadedPayments.filter((payment) => payment.treatment_id === treatmentId));
      setOptions(loadedOptions);
    } catch {
      setError("No fue posible cargar el tratamiento.");
    } finally {
      if (showSpinner) setLoading(false);
    }
  }, [treatmentId]);

  const refresh = useCallback(() => load(false), [load]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <div className="flex justify-center py-20"><Spinner className="h-7 w-7 text-dentia-primary" /></div>;
  }
  if (!treatment) {
    return <Alert tone="error">{error ?? "Tratamiento no encontrado."}</Alert>;
  }

  const latestBudget = budgets[0];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <Link href="/tratamientos" className="text-sm font-bold text-green-700 hover:underline">← Tratamientos</Link>
          <h1 className="mt-3 text-3xl font-black text-slate-950">{treatment.name}</h1>
          <p className="mt-2 text-sm text-slate-500">{treatment.patient_name}</p>
        </div>
        <span className={`w-fit rounded-full px-3 py-1 text-sm font-black ${statusBadge(treatment.status)}`}>{treatment.status}</span>
      </header>
      {error && <Alert tone="error">{error}</Alert>}
      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="Valor" value={money(treatment.summary.final_value)} />
        <Metric label="Pagado" value={money(treatment.summary.paid_value)} />
        <Metric label="Saldo" value={money(treatment.summary.balance)} tone="orange" />
        <Metric label="Avance" value={`${treatment.summary.procedures_done}/${treatment.summary.procedures_total}`} />
      </section>

      <Panel
        title="Procedimientos"
        description="Define el plan clínico y económico del tratamiento."
      >
          {hasPermission("treatments.update") && <ProcedureForm treatmentId={treatmentId} options={options} onDone={refresh} />}
          <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
            <table className="min-w-full table-fixed divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "Procedimiento",
                    "Odontólogo",
                    "Sede",
                    "Cantidad",
                    "Valor",
                    "Estado",
                    "Acciones",
                  ].map((heading) => (
                    <th
                      key={heading}
                      className="px-4 py-3 text-left text-xs font-black uppercase tracking-wide text-slate-500"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {procedures.map((procedure) => (
                  <tr key={procedure.id}>
                    <td className="px-4 py-3">
                      <p className="font-bold text-slate-900">{procedure.name}</p>
                      {procedure.category && (
                        <p className="text-xs text-slate-500">{procedure.category}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {procedure.dentist_name ?? "Sin odontólogo"}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {procedure.site_name ?? "Sin sede"}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {Number(procedure.quantity)}
                    </td>
                    <td className="px-4 py-3 font-bold text-slate-900">
                      {money(procedure.total_value)}
                    </td>
                    <td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-xs font-bold ${statusBadge(procedure.status)}`}>{procedure.status}</span></td>
                    <td className="px-4 py-3 text-right">
                      {hasPermission("treatments.update") && procedure.status !== "Realizado" && procedure.status !== "Cancelado" && (
                        <button onClick={async () => { await markProcedureDone(treatmentId, procedure.id); await refresh(); }} className="text-xs font-bold text-green-700 hover:underline">Realizado</button>
                      )}
                      {hasPermission("treatments.update") && procedure.status !== "Realizado" && procedure.status !== "Cancelado" && (
                        <button onClick={async () => { const reason = window.prompt("Motivo de cancelación"); if (reason) { await cancelProcedure(treatmentId, procedure.id, reason); await refresh(); } }} className="ml-3 text-xs font-bold text-red-700 hover:underline">Cancelar</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!procedures.length && <p className="py-6 text-sm text-slate-500">No hay procedimientos.</p>}
          </div>
      </Panel>

      <Panel
        title="Presupuesto"
        description="Calcula el valor bruto, descuento y valor final con espacio suficiente para revisar antes de aprobar."
      >
          {hasPermission("budgets.create") && <BudgetForm treatmentId={treatmentId} onDone={refresh} />}
          {latestBudget ? (
            <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                    Presupuesto vigente
                  </p>
                  <p className="mt-1 text-xl font-black text-slate-950">
                    Versión {latestBudget.version}
                  </p>
                  <span className={`mt-2 inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${statusBadge(latestBudget.status)}`}>
                    {latestBudget.status}
                  </span>
                </div>
                <div className="grid min-w-full gap-3 sm:grid-cols-2 lg:min-w-[620px] lg:grid-cols-4">
                  <BudgetMetric label="Valor bruto" value={money(latestBudget.gross_value)} />
                  <BudgetMetric label="Descuento" value={latestBudget.discount_type ?? "Sin descuento"} />
                  <BudgetMetric label="Valor descuento" value={money(latestBudget.discount_calculated_value)} />
                  <BudgetMetric label="Valor final" value={money(latestBudget.final_value)} highlight />
                </div>
              </div>
              {latestBudget.observations && (
                <p className="mt-4 text-sm text-slate-600">
                  {latestBudget.observations}
                </p>
              )}
              {hasPermission("budgets.update") && (
                <div className="mt-5 flex flex-wrap gap-3">
                  {latestBudget.status === "Borrador" && (
                    <button
                      onClick={async () => { await submitBudget(latestBudget.id); await refresh(); }}
                      className="min-h-10 rounded-xl border border-sky-200 px-4 text-sm font-bold text-sky-700 hover:bg-sky-50"
                    >
                      Enviar aprobación
                    </button>
                  )}
                  {latestBudget.status !== "Aprobado" && latestBudget.status !== "Rechazado" && (
                    <button
                      onClick={async () => { await approveBudget(latestBudget.id); await refresh(); }}
                      className="min-h-10 rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white hover:bg-green-700"
                    >
                      Aprobar
                    </button>
                  )}
                  {latestBudget.status !== "Aprobado" && latestBudget.status !== "Rechazado" && (
                    <button
                      onClick={async () => { await rejectBudget(latestBudget.id); await refresh(); }}
                      className="min-h-10 rounded-xl border border-red-200 px-4 text-sm font-bold text-red-700 hover:bg-red-50"
                    >
                      Rechazar
                    </button>
                  )}
                </div>
              )}
            </div>
          ) : <p className="mt-4 text-sm text-slate-500">Sin presupuesto.</p>}
      </Panel>

      <Panel
        title="Pagos"
        description={`Saldo actualizado: ${money(treatment.summary.balance)}`}
      >
          {hasPermission("payments.create") && <PaymentForm treatment={treatment} options={options} onDone={refresh} />}
          <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
            <table className="min-w-full table-fixed divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {["Fecha", "Valor", "Medio", "Estado", "Observación", "Acciones"].map((heading) => (
                    <th key={heading} className="px-4 py-3 text-left text-xs font-black uppercase tracking-wide text-slate-500">
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {payments.map((payment) => (
                  <tr key={payment.id}>
                    <td className="px-4 py-3 text-slate-600">{localDate(payment.paid_at)}</td>
                    <td className="px-4 py-3 font-black text-slate-900">{money(payment.value)}</td>
                    <td className="px-4 py-3 text-slate-600">{payment.payment_method}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-1 text-xs font-bold ${statusBadge(payment.status)}`}>{payment.status}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{payment.observation ?? "—"}</td>
                    <td className="px-4 py-3 text-right">
                      {hasPermission("payments.reverse") && payment.status === "valido" && (
                        <button onClick={async () => { const reason = window.prompt("Motivo de reversión"); if (reason) { await reversePayment(payment.id, reason); await refresh(); } }} className="text-xs font-bold text-red-700 hover:underline">Reversar</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!payments.length && <p className="py-6 text-center text-sm text-slate-500">Sin pagos registrados.</p>}
          </div>
      </Panel>

      <Panel
        title="Acciones"
        description="Cambios de estado del tratamiento y datos administrativos."
      >
          <div className="flex flex-wrap gap-3">
            {hasPermission("treatments.update") && treatment.status === "Borrador" && (
              <button onClick={async () => { await approveTreatment(treatment.id); await refresh(); }} className="min-h-10 rounded-xl border border-green-200 px-4 text-sm font-bold text-green-700">Aprobar tratamiento</button>
            )}
            {hasPermission("treatments.close") && (
              <button onClick={async () => { await closeTreatment(treatment.id); await refresh(); }} className="min-h-10 rounded-xl border border-violet-200 px-4 text-sm font-bold text-violet-700">Cerrar tratamiento</button>
            )}
            {hasPermission("treatments.cancel") && treatment.status !== "Cancelado" && (
              <button onClick={async () => { const reason = window.prompt("Motivo de cancelación"); if (reason) { await cancelTreatment(treatment.id, reason); await refresh(); } }} className="min-h-10 rounded-xl border border-red-200 px-4 text-sm font-bold text-red-700">Cancelar tratamiento</button>
            )}
          </div>
          <div className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
            <p><strong>Responsable:</strong> {treatment.responsible_dentist_name ?? "—"}</p>
            <p className="mt-1"><strong>Sede:</strong> {treatment.main_site_name ?? "—"}</p>
            <p className="mt-1"><strong>Creado:</strong> {localDate(treatment.created_at)}</p>
          </div>
      </Panel>
    </div>
  );
}

function Metric({ label, value, tone = "green" }: { label: string; value: string; tone?: "green" | "orange" }) {
  return (
    <div className={`rounded-2xl border p-5 shadow-sm ${tone === "orange" ? "border-orange-100 bg-orange-50" : "border-green-100 bg-white"}`}>
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-slate-950">{value}</p>
    </div>
  );
}

function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      {description && (
        <p className="mt-1 text-sm text-slate-500">{description}</p>
      )}
      {children}
    </section>
  );
}

function BudgetMetric({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl border p-3 ${highlight ? "border-green-200 bg-white" : "border-slate-200 bg-white/80"}`}>
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className={`mt-1 truncate text-base font-black ${highlight ? "text-green-800" : "text-slate-900"}`}>
        {value}
      </p>
    </div>
  );
}

function ProcedureForm({ treatmentId, options, onDone }: { treatmentId: string; options: AgendaOptions | null; onDone: () => Promise<void> }) {
  const [name, setName] = useState("");
  const [value, setValue] = useState("0");
  const [quantity, setQuantity] = useState("1");
  const [dentistId, setDentistId] = useState("");
  const [siteId, setSiteId] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    await createProcedure(treatmentId, {
      name,
      unit_value: value,
      quantity,
      dentist_id: dentistId || null,
      site_id: siteId || null,
    });
    setName("");
    setValue("0");
    setQuantity("1");
    await onDone();
  }

  return (
    <form onSubmit={submit} className="mt-5 rounded-2xl border border-slate-100 bg-slate-50 p-4">
      <div className="grid gap-4 lg:grid-cols-[minmax(220px,1.5fr)_minmax(170px,1fr)_minmax(160px,1fr)_120px_150px_auto] lg:items-end">
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Procedimiento
          </span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          />
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Odontólogo
          </span>
          <select
            value={dentistId}
            onChange={(event) => setDentistId(event.target.value)}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          >
            <option value="">Sin asignar</option>
            {options?.dentists.map((dentist) => <option key={dentist.id} value={dentist.id}>{dentist.name}</option>)}
          </select>
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Sede
          </span>
          <select
            value={siteId}
            onChange={(event) => setSiteId(event.target.value)}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          >
            <option value="">Sin sede</option>
            {options?.sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
          </select>
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Cantidad
          </span>
          <input
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            type="number"
            min="0.01"
            step="0.01"
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          />
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Valor unitario
          </span>
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            type="number"
            min="0"
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          />
        </label>
        <button className="min-h-11 whitespace-nowrap rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white hover:bg-green-700">
          Agregar procedimiento
        </button>
      </div>
    </form>
  );
}

function BudgetForm({ treatmentId, onDone }: { treatmentId: string; onDone: () => Promise<void> }) {
  const [discountType, setDiscountType] = useState("");
  const [discountValue, setDiscountValue] = useState("0");
  async function submit(event: FormEvent) {
    event.preventDefault();
    await createBudget(treatmentId, {
      discount_type: discountType || null,
      discount_value: discountValue,
    });
    await onDone();
  }
  return (
    <form onSubmit={submit} className="mt-5 rounded-2xl border border-slate-100 bg-slate-50 p-4">
      <div className="grid gap-4 sm:grid-cols-[minmax(180px,1fr)_minmax(160px,1fr)_auto] sm:items-end">
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Tipo de descuento
          </span>
          <select
            value={discountType}
            onChange={(event) => setDiscountType(event.target.value)}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          >
            <option value="">Sin descuento</option>
            <option value="valor">Valor fijo</option>
            <option value="porcentaje">Porcentaje</option>
          </select>
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Valor descuento
          </span>
          <input
            value={discountValue}
            onChange={(event) => setDiscountValue(event.target.value)}
            type="number"
            min="0"
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          />
        </label>
        <button className="min-h-11 whitespace-nowrap rounded-xl border border-green-200 bg-white px-4 text-sm font-bold text-green-700 hover:bg-green-50">
          Guardar presupuesto
        </button>
      </div>
    </form>
  );
}

function PaymentForm({ treatment, options, onDone }: { treatment: Treatment; options: AgendaOptions | null; onDone: () => Promise<void> }) {
  const [value, setValue] = useState("");
  const [method, setMethod] = useState("Efectivo");
  const [siteId, setSiteId] = useState(treatment.main_site_id ?? "");
  const [dentistId, setDentistId] = useState(treatment.responsible_dentist_id ?? "");
  async function submit(event: FormEvent) {
    event.preventDefault();
    await createPayment(treatment.id, {
      value,
      payment_method: method,
      site_id: siteId,
      dentist_id: dentistId || null,
      paid_at: new Date().toISOString(),
    });
    setValue("");
    await onDone();
  }
  return (
    <form onSubmit={submit} className="mt-5 rounded-2xl border border-slate-100 bg-slate-50 p-4">
      <div className="grid gap-4 lg:grid-cols-[150px_170px_minmax(170px,1fr)_minmax(170px,1fr)_auto] lg:items-end">
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Valor
          </span>
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            type="number"
            min="1"
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          />
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Medio
          </span>
          <select
            value={method}
            onChange={(event) => setMethod(event.target.value)}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          >
            {["Efectivo", "Transferencia", "Tarjeta", "Otro"].map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Sede
          </span>
          <select
            value={siteId}
            onChange={(event) => setSiteId(event.target.value)}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          >
            <option value="">Selecciona sede</option>
            {options?.sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
          </select>
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
            Odontólogo
          </span>
          <select
            value={dentistId}
            onChange={(event) => setDentistId(event.target.value)}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
          >
            <option value="">Sin odontólogo</option>
            {options?.dentists.map((dentist) => <option key={dentist.id} value={dentist.id}>{dentist.name}</option>)}
          </select>
        </label>
        <button className="min-h-11 whitespace-nowrap rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white hover:bg-green-700">
          Registrar pago
        </button>
      </div>
    </form>
  );
}
