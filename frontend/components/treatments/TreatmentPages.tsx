"use client";

import Link from "next/link";
import type React from "react";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/shared/Alert";
import { Modal } from "@/components/shared/Modal";
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
  createProcedureCatalogItem,
  createTreatment,
  deleteProcedure,
  downloadBudgetPdf,
  downloadPaymentReceipt,
  duplicateBudgetVersion,
  getTreatment,
  listBudgets,
  listPayments,
  listProcedureCatalog,
  listProcedures,
  listTreatments,
  markProcedureDone,
  rejectBudget,
  reversePayment,
  submitBudget,
  updateProcedure,
} from "@/services/treatmentService";
import type { AgendaOptions, PatientOption } from "@/types/agenda";
import type {
  Budget,
  Payment,
  Procedure,
  ProcedureCatalogItem,
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

const scopeOptions = [
  { value: "GENERAL", label: "General" },
  { value: "ZONE", label: "Zona" },
  { value: "TOOTH", label: "Diente" },
  { value: "TOOTH_SURFACE", label: "Cara del diente" },
];

const zoneOptions = [
  { value: "UPPER_ARCH", label: "Arcada superior" },
  { value: "LOWER_ARCH", label: "Arcada inferior" },
  { value: "FULL_MOUTH", label: "Boca completa" },
  { value: "QUADRANT_1", label: "Cuadrante 1" },
  { value: "QUADRANT_2", label: "Cuadrante 2" },
  { value: "QUADRANT_3", label: "Cuadrante 3" },
  { value: "QUADRANT_4", label: "Cuadrante 4" },
  { value: "ANTERIOR", label: "Anterior" },
  { value: "POSTERIOR", label: "Posterior" },
];

const toothOptions = [
  "11", "12", "13", "14", "15", "16", "17", "18",
  "21", "22", "23", "24", "25", "26", "27", "28",
  "31", "32", "33", "34", "35", "36", "37", "38",
  "41", "42", "43", "44", "45", "46", "47", "48",
];

const surfaceOptions = [
  { value: "VESTIBULAR", label: "Vestibular" },
  { value: "LINGUAL", label: "Lingual" },
  { value: "PALATAL", label: "Palatal" },
  { value: "MESIAL", label: "Mesial" },
  { value: "DISTAL", label: "Distal" },
  { value: "OCCLUSAL", label: "Oclusal" },
  { value: "INCISAL", label: "Incisal" },
];

type ProcedurePayload = {
  catalog_procedure_id?: string | null;
  name: string;
  category?: string | null;
  dentist_id?: string | null;
  site_id?: string | null;
  unit_value: string;
  quantity: string;
  observations?: string | null;
  scope_type: string;
  zone?: string | null;
  tooth?: string | null;
  surfaces?: string[] | null;
};

function procedureToPayload(procedure: Procedure): ProcedurePayload {
  return {
    catalog_procedure_id: procedure.catalog_procedure_id,
    name: procedure.name,
    category: procedure.category,
    dentist_id: procedure.dentist_id,
    site_id: procedure.site_id,
    unit_value: procedure.unit_value,
    quantity: procedure.quantity,
    observations: procedure.observations,
    scope_type: procedure.scope_type,
    zone: procedure.zone,
    tooth: procedure.tooth,
    surfaces: procedure.surfaces,
  };
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
  const [catalog, setCatalog] = useState<ProcedureCatalogItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingProcedure, setEditingProcedure] = useState<Procedure | null>(null);
  const [decision, setDecision] = useState<{
    type: "edit" | "delete";
    procedure: Procedure;
  } | null>(null);

  const load = useCallback(async (showSpinner = true) => {
    if (showSpinner) setLoading(true);
    setError(null);
    try {
      const [loadedTreatment, loadedProcedures, loadedBudgets, loadedPayments, loadedOptions, loadedCatalog] = await Promise.all([
        getTreatment(treatmentId),
        listProcedures(treatmentId),
        listBudgets(),
        listPayments(),
        getAgendaOptions(),
        listProcedureCatalog("?activo=true"),
      ]);
      setTreatment(loadedTreatment);
      setProcedures(loadedProcedures);
      setBudgets(loadedBudgets.filter((budget) => budget.treatment_id === treatmentId));
      setPayments(loadedPayments.filter((payment) => payment.treatment_id === treatmentId));
      setOptions(loadedOptions);
      setCatalog(loadedCatalog.items);
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

  async function handleDownloadBudgetPdf(budget: Budget) {
    const blob = await downloadBudgetPdf(budget.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `presupuesto-${budget.number ?? budget.version}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function handleDownloadPaymentReceipt(payment: Payment, print = false) {
    const blob = await downloadPaymentReceipt(payment.id);
    const url = URL.createObjectURL(blob);
    if (print) {
      const receiptWindow = window.open(url, "_blank", "noopener,noreferrer");
      receiptWindow?.addEventListener("load", () => receiptWindow.print(), { once: true });
      return;
    }
    const link = document.createElement("a");
    link.href = url;
    link.download = `comprobante-${payment.receipt_number}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  const budgetHasDiscount = latestBudget
    ? Number(latestBudget.discount_calculated_value) > 0
    : false;
  const budgetLocked = latestBudget
    ? ["Aprobado", "En ejecución", "Finalizado"].includes(latestBudget.status)
    : false;

  async function submitProcedureEdit(procedure: Procedure, data: ProcedurePayload) {
    if (budgetLocked) {
      setDecision({ type: "edit", procedure: { ...procedure, ...data } as Procedure });
      return;
    }
    await updateProcedure(treatmentId, procedure.id, data);
    setEditingProcedure(null);
    await refresh();
  }

  async function confirmApprovedEdit() {
    if (!decision || !latestBudget) return;
    await duplicateBudgetVersion(latestBudget.id);
    if (decision.type === "edit") {
      const procedure = decision.procedure;
      await updateProcedure(treatmentId, procedure.id, procedureToPayload(procedure));
    } else {
      await cancelProcedure(
        treatmentId,
        decision.procedure.id,
        "Cancelado por ajuste de presupuesto aprobado.",
      );
    }
    setDecision(null);
    setEditingProcedure(null);
    await refresh();
  }

  async function handleDeleteProcedure(procedure: Procedure) {
    if (procedure.status === "Realizado") {
      setError("No se puede eliminar un procedimiento realizado.");
      return;
    }
    if (budgetLocked) {
      setDecision({ type: "delete", procedure });
      return;
    }
    if (!window.confirm("¿Eliminar este procedimiento?")) return;
    await deleteProcedure(treatmentId, procedure.id);
    await refresh();
  }

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
          {hasPermission("treatments.update") && (
            <ProcedureForm
              options={options}
              catalog={catalog}
              submitLabel="Agregar procedimiento"
              onCreateCatalog={async (payload) => {
                const item = await createProcedureCatalogItem(payload);
                setCatalog((current) => [...current, item].sort((a, b) => a.name.localeCompare(b.name)));
                return item;
              }}
              onSubmit={async (payload) => {
                await createProcedure(treatmentId, payload);
                await refresh();
              }}
            />
          )}
          {editingProcedure && (
            <div className="mt-5 rounded-2xl border border-green-200 bg-green-50/50 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-black uppercase tracking-wide text-green-700">
                    Editar procedimiento
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    Esta acción actualiza el procedimiento y recalcula presupuestos editables.
                  </p>
                </div>
                <button onClick={() => setEditingProcedure(null)} className="text-sm font-bold text-slate-500 hover:text-slate-900">Cancelar</button>
              </div>
              <ProcedureForm
                options={options}
                catalog={catalog}
                initial={editingProcedure}
                submitLabel="Guardar cambios"
                onCreateCatalog={async (payload) => {
                  const item = await createProcedureCatalogItem(payload);
                  setCatalog((current) => [...current, item].sort((a, b) => a.name.localeCompare(b.name)));
                  return item;
                }}
                onSubmit={(payload) => submitProcedureEdit(editingProcedure, payload)}
              />
            </div>
          )}
          <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
            <table className="min-w-full table-fixed divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "Procedimiento",
                    "Alcance",
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
                      <p className="mt-1 text-xs text-slate-500">
                        {procedure.dentist_name ?? "Sin odontólogo"} · {procedure.site_name ?? "Sin sede"}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {procedure.scope_label}
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
                        <button onClick={() => setEditingProcedure(procedure)} className="text-xs font-bold text-sky-700 hover:underline">✏️ Editar</button>
                      )}
                      {hasPermission("treatments.update") && procedure.status !== "Realizado" && (
                        <button onClick={() => handleDeleteProcedure(procedure)} className="ml-3 text-xs font-bold text-red-700 hover:underline">🗑 Eliminar</button>
                      )}
                      {hasPermission("treatments.update") && procedure.status !== "Realizado" && procedure.status !== "Cancelado" && (
                        <button onClick={async () => { await markProcedureDone(treatmentId, procedure.id); await refresh(); }} className="ml-3 text-xs font-bold text-green-700 hover:underline">Realizado</button>
                      )}
                      {hasPermission("treatments.update") && procedure.status !== "Realizado" && procedure.status !== "Cancelado" && (
                        <button
                          onClick={async () => {
                            if (budgetLocked) {
                              setDecision({ type: "delete", procedure });
                              return;
                            }
                            const reason = window.prompt("Motivo de cancelación");
                            if (reason) {
                              await cancelProcedure(treatmentId, procedure.id, reason);
                              await refresh();
                            }
                          }}
                          className="ml-3 text-xs font-bold text-red-700 hover:underline"
                        >
                          Cancelar
                        </button>
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
                <div className={`grid min-w-full gap-3 sm:grid-cols-2 ${budgetHasDiscount ? "lg:min-w-[620px] lg:grid-cols-4" : "lg:min-w-[320px] lg:grid-cols-2"}`}>
                  <BudgetMetric label="Subtotal" value={money(latestBudget.gross_value)} />
                  {budgetHasDiscount && (
                    <>
                      <BudgetMetric label="Descuento" value={latestBudget.discount_type === "porcentaje" ? `${Number(latestBudget.discount_value)}%` : money(latestBudget.discount_value)} />
                      <BudgetMetric label="Valor descuento" value={money(latestBudget.discount_calculated_value)} />
                    </>
                  )}
                  <BudgetMetric label="Valor final" value={money(latestBudget.final_value)} highlight />
                </div>
              </div>
              {latestBudget.observations && (
                <p className="mt-4 text-sm text-slate-600">
                  {latestBudget.observations}
                </p>
              )}
              <div className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white">
                <table className="min-w-full divide-y divide-slate-100 text-sm">
                  <thead className="bg-white">
                    <tr>
                      {["Procedimiento", "Alcance", "Valor"].map((heading) => (
                        <th key={heading} className="px-4 py-3 text-left text-xs font-black uppercase tracking-wide text-slate-500">
                          {heading}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {latestBudget.details.map((detail) => (
                      <tr key={detail.id}>
                        <td className="px-4 py-3 font-bold text-slate-900">{detail.name}</td>
                        <td className="px-4 py-3 text-slate-600">{detail.scope_label}</td>
                        <td className="px-4 py-3 font-black text-slate-900">{money(detail.total_value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => handleDownloadBudgetPdf(latestBudget)}
                  className="min-h-10 rounded-xl border border-green-200 px-4 text-sm font-bold text-green-700 hover:bg-green-50"
                >
                  Descargar PDF
                </button>
              </div>
              {hasPermission("budgets.update") && (
                <div className="mt-3 flex flex-wrap gap-3">
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
          {hasPermission("payments.create") && <PaymentForm treatment={treatment} procedures={procedures} options={options} onDone={refresh} />}
          <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
            <table className="min-w-full table-fixed divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {["Fecha", "Comprobante", "Valor", "Medio", "Estado", "Observación", "Acciones"].map((heading) => (
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
                    <td className="px-4 py-3 font-bold text-slate-700">{payment.receipt_number}</td>
                    <td className="px-4 py-3 font-black text-slate-900">{money(payment.value)}</td>
                    <td className="px-4 py-3 text-slate-600">{payment.payment_method}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-1 text-xs font-bold ${statusBadge(payment.status)}`}>{payment.status}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{payment.observation ?? "—"}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex flex-wrap justify-end gap-2">
                        {hasPermission("payments.view") && (
                          <button onClick={() => handleDownloadPaymentReceipt(payment)} className="text-xs font-bold text-green-700 hover:underline">Descargar comprobante</button>
                        )}
                        {hasPermission("payments.reverse") && payment.status === "valido" && (
                          <button onClick={async () => { const reason = window.prompt("Motivo de reversión"); if (reason) { await reversePayment(payment.id, reason); await refresh(); } }} className="text-xs font-bold text-red-700 hover:underline">Reversar</button>
                        )}
                      </div>
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
      <Modal
        open={Boolean(decision)}
        title="Presupuesto aprobado"
        onClose={() => setDecision(null)}
      >
        <div className="space-y-4">
          <p className="text-sm leading-6 text-slate-600">
            {decision?.type === "edit"
              ? "Este procedimiento pertenece a un presupuesto aprobado. Modificarlo cambiará el plan vigente de tratamiento."
              : "Este procedimiento pertenece a un presupuesto aprobado. No se eliminará el historial del presupuesto aprobado."}
          </p>
          <p className="text-sm font-bold text-slate-900">
            ¿Qué desea hacer?
          </p>
          <div className="flex flex-wrap justify-end gap-3">
            <button
              type="button"
              onClick={() => setDecision(null)}
              className="min-h-10 rounded-xl border border-slate-200 px-4 text-sm font-bold text-slate-600 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={confirmApprovedEdit}
              className="min-h-10 rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white hover:bg-green-700"
            >
              {decision?.type === "edit"
                ? "Crear nueva versión del presupuesto"
                : "Cancelar procedimiento y crear nueva versión"}
            </button>
          </div>
        </div>
      </Modal>
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

function ProcedureForm({
  options,
  catalog,
  initial,
  submitLabel,
  onCreateCatalog,
  onSubmit,
}: {
  options: AgendaOptions | null;
  catalog: ProcedureCatalogItem[];
  initial?: Procedure;
  submitLabel: string;
  onCreateCatalog: (payload: {
    name: string;
    category?: string | null;
    suggested_value?: string | null;
    suggested_scope_type?: string | null;
    is_active?: boolean;
  }) => Promise<ProcedureCatalogItem>;
  onSubmit: (payload: ProcedurePayload) => Promise<void>;
}) {
  const [catalogProcedureId, setCatalogProcedureId] = useState(initial?.catalog_procedure_id ?? "");
  const [name, setName] = useState(initial?.name ?? "");
  const [category, setCategory] = useState(initial?.category ?? "");
  const [value, setValue] = useState(initial?.unit_value ?? "0");
  const [quantity, setQuantity] = useState(initial?.quantity ?? "1");
  const [dentistId, setDentistId] = useState(initial?.dentist_id ?? "");
  const [siteId, setSiteId] = useState(initial?.site_id ?? "");
  const [scopeType, setScopeType] = useState(initial?.scope_type ?? "GENERAL");
  const [zone, setZone] = useState(initial?.zone ?? "");
  const [tooth, setTooth] = useState(initial?.tooth ?? "");
  const [surfaces, setSurfaces] = useState<string[]>(initial?.surfaces ?? []);
  const [observations, setObservations] = useState(initial?.observations ?? "");
  const [showCatalogModal, setShowCatalogModal] = useState(false);
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [highlightedCatalogIndex, setHighlightedCatalogIndex] = useState(0);
  const [catalogForm, setCatalogForm] = useState({
    name: "",
    category: "",
    suggested_value: "",
    suggested_scope_type: "GENERAL",
  });
  const [creatingCatalog, setCreatingCatalog] = useState(false);
  const listboxId = `procedure-catalog-list-${initial?.id ?? "new"}`;

  useEffect(() => {
    setCatalogProcedureId(initial?.catalog_procedure_id ?? "");
    setName(initial?.name ?? "");
    setCategory(initial?.category ?? "");
    setValue(initial?.unit_value ?? "0");
    setQuantity(initial?.quantity ?? "1");
    setDentistId(initial?.dentist_id ?? "");
    setSiteId(initial?.site_id ?? "");
    setScopeType(initial?.scope_type ?? "GENERAL");
    setZone(initial?.zone ?? "");
    setTooth(initial?.tooth ?? "");
    setSurfaces(initial?.surfaces ?? []);
    setObservations(initial?.observations ?? "");
  }, [initial]);

  const selectedCatalog = catalog.find((item) => item.id === catalogProcedureId) ?? null;
  const exactCatalogMatch = catalog.find((item) => item.name.toLowerCase() === name.trim().toLowerCase()) ?? null;
  const visibleCatalog = catalog
    .filter((item) => item.name.toLowerCase().includes(name.trim().toLowerCase()))
    .slice(0, 8);

  function applyCatalogItem(item: ProcedureCatalogItem) {
    setCatalogProcedureId(item.id);
    setName(item.name);
    setCategory(item.category ?? "");
    if (item.suggested_value !== null) setValue(item.suggested_value);
    if (item.suggested_scope_type) {
      setScopeType(item.suggested_scope_type);
      setZone("");
      setTooth("");
      setSurfaces([]);
    }
  }

  function handleNameChange(value: string) {
    setName(value);
    setCatalogOpen(true);
    setHighlightedCatalogIndex(0);
    const match = catalog.find((item) => item.name.toLowerCase() === value.trim().toLowerCase());
    if (match) {
      applyCatalogItem(match);
    } else {
      setCatalogProcedureId("");
      setCategory("");
    }
  }

  function handleCatalogKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (!catalogOpen && ["ArrowDown", "ArrowUp"].includes(event.key)) {
      setCatalogOpen(true);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightedCatalogIndex((current) => Math.min(current + 1, Math.max(visibleCatalog.length - 1, 0)));
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightedCatalogIndex((current) => Math.max(current - 1, 0));
    }
    if (event.key === "Enter" && catalogOpen && visibleCatalog.length > 0) {
      event.preventDefault();
      applyCatalogItem(visibleCatalog[highlightedCatalogIndex] ?? visibleCatalog[0]);
      setCatalogOpen(false);
    }
    if (event.key === "Escape") {
      setCatalogOpen(false);
    }
  }

  function openCatalogModal() {
    setCatalogForm({
      name: name.trim(),
      category: "",
      suggested_value: value !== "0" ? value : "",
      suggested_scope_type: scopeType || "GENERAL",
    });
    setShowCatalogModal(true);
  }

  async function createCatalogFromModal(event: FormEvent) {
    event.preventDefault();
    setCreatingCatalog(true);
    try {
      const item = await onCreateCatalog({
        name: catalogForm.name,
        category: catalogForm.category || null,
        suggested_value: catalogForm.suggested_value || null,
        suggested_scope_type: catalogForm.suggested_scope_type || null,
        is_active: true,
      });
      applyCatalogItem(item);
      setShowCatalogModal(false);
    } finally {
      setCreatingCatalog(false);
    }
  }

  function toggleSurface(surface: string) {
    setSurfaces((current) =>
      current.includes(surface)
        ? current.filter((item) => item !== surface)
        : [...current, surface],
    );
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    await onSubmit({
      catalog_procedure_id: catalogProcedureId || null,
      name,
      category: category || null,
      unit_value: value,
      quantity,
      dentist_id: dentistId || null,
      site_id: siteId || null,
      observations: observations || null,
      scope_type: scopeType,
      zone: scopeType === "ZONE" ? zone : null,
      tooth: scopeType === "TOOTH" || scopeType === "TOOTH_SURFACE" ? tooth : null,
      surfaces: scopeType === "TOOTH_SURFACE" ? surfaces : null,
    });
    if (!initial) {
      setCatalogProcedureId("");
      setName("");
      setCategory("");
      setValue("0");
      setQuantity("1");
      setDentistId("");
      setSiteId("");
      setScopeType("GENERAL");
      setZone("");
      setTooth("");
      setSurfaces([]);
      setObservations("");
    }
  }

  return (
    <>
      <form onSubmit={submit} className="mt-5 rounded-2xl border border-slate-100 bg-slate-50 p-4">
        <div className="grid gap-4 lg:grid-cols-3">
          <label className="relative">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
              Procedimiento
            </span>
            <input
              value={name}
              onChange={(event) => handleNameChange(event.target.value)}
              onFocus={() => setCatalogOpen(true)}
              onBlur={() => window.setTimeout(() => setCatalogOpen(false), 120)}
              onKeyDown={handleCatalogKeyDown}
              role="combobox"
              aria-controls={listboxId}
              aria-expanded={catalogOpen}
              aria-autocomplete="list"
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-950 shadow-sm placeholder:text-slate-400 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-100"
              placeholder="Buscar en catálogo"
              required
            />
            {catalogOpen && (
              <div className="absolute left-0 right-0 z-30 mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white text-slate-950 shadow-xl ring-1 ring-slate-900/5">
                {visibleCatalog.length > 0 ? (
                  <ul id={listboxId} className="max-h-64 overflow-y-auto py-1" role="listbox">
                    {visibleCatalog.map((item, index) => {
                      const isHighlighted = index === highlightedCatalogIndex;
                      const isSelected = item.id === catalogProcedureId;
                      return (
                        <li key={item.id}>
                          <button
                            type="button"
                            role="option"
                            aria-selected={isSelected}
                            onMouseEnter={() => setHighlightedCatalogIndex(index)}
                            onMouseDown={(event) => {
                              event.preventDefault();
                              applyCatalogItem(item);
                              setCatalogOpen(false);
                            }}
                            className={`w-full px-3 py-2 text-left text-sm transition ${
                              isSelected
                                ? "bg-green-50 text-green-950"
                                : isHighlighted
                                  ? "bg-sky-50 text-slate-950"
                                  : "bg-white text-slate-900 hover:bg-slate-50"
                            }`}
                          >
                            <span className="block font-bold">{item.name}</span>
                            <span className="mt-0.5 block text-xs text-slate-600">
                              {[item.category, item.suggested_value ? money(item.suggested_value) : null].filter(Boolean).join(" · ") || "Sin categoría"}
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <div className="px-3 py-3 text-sm text-slate-700">
                    No hay procedimientos activos con ese nombre.
                  </div>
                )}
                {name.trim() && !exactCatalogMatch && (
                  <button
                    type="button"
                    onMouseDown={(event) => {
                      event.preventDefault();
                      openCatalogModal();
                      setCatalogOpen(false);
                    }}
                    className="w-full border-t border-slate-100 bg-emerald-50 px-3 py-2 text-left text-sm font-black text-emerald-900 hover:bg-emerald-100"
                  >
                    + Crear nuevo procedimiento
                  </button>
                )}
              </div>
            )}
            <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              {selectedCatalog ? (
                <span>{selectedCatalog.category ?? "Sin categoría"}</span>
              ) : name.trim() && !exactCatalogMatch ? (
                <button
                  type="button"
                  onClick={openCatalogModal}
                  className="font-bold text-green-700 hover:underline"
                >
                  + Crear nuevo procedimiento
                </button>
              ) : null}
            </div>
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
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-3">
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
          <label>
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
              Alcance
            </span>
            <select
              value={scopeType}
              onChange={(event) => {
                setScopeType(event.target.value);
                setZone("");
                setTooth("");
                setSurfaces([]);
              }}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
            >
              {scopeOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          {scopeType === "ZONE" && (
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Zona
              </span>
              <select
                value={zone}
                onChange={(event) => setZone(event.target.value)}
                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
                required
              >
                <option value="">Seleccionar zona</option>
                {zoneOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
          )}
          {(scopeType === "TOOTH" || scopeType === "TOOTH_SURFACE") && (
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Diente FDI
              </span>
              <select
                value={tooth}
                onChange={(event) => setTooth(event.target.value)}
                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
                required
              >
                <option value="">Seleccionar diente</option>
                {toothOptions.map((option) => (
                  <option key={option} value={option}>Diente {option}</option>
                ))}
              </select>
            </label>
          )}
          {scopeType === "TOOTH_SURFACE" && (
            <fieldset className="lg:col-span-2">
              <legend className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Caras del diente
              </legend>
              <div className="flex flex-wrap gap-2">
                {surfaceOptions.map((option) => (
                  <label
                    key={option.value}
                    className={`flex min-h-10 cursor-pointer items-center rounded-xl border px-3 text-xs font-bold ${
                      surfaces.includes(option.value)
                        ? "border-green-300 bg-green-50 text-green-800"
                        : "border-slate-200 bg-white text-slate-600"
                    }`}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={surfaces.includes(option.value)}
                      onChange={() => toggleSurface(option.value)}
                    />
                    {option.label}
                  </label>
                ))}
              </div>
            </fieldset>
          )}
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
          <label>
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
              Observaciones
            </span>
            <textarea
              value={observations}
              onChange={(event) => setObservations(event.target.value)}
              rows={2}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"
              placeholder="Notas administrativas o clínicas del procedimiento"
            />
          </label>
          <button className="min-h-11 whitespace-nowrap rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white hover:bg-green-700">
            {submitLabel}
          </button>
        </div>
      </form>

      <Modal
        open={showCatalogModal}
        title="Crear nuevo procedimiento"
        onClose={() => setShowCatalogModal(false)}
      >
        <form onSubmit={createCatalogFromModal} className="space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
              Nombre
            </span>
            <input
              value={catalogForm.name}
              onChange={(event) => setCatalogForm((current) => ({ ...current, name: event.target.value }))}
              className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm"
              required
            />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
              Categoría opcional
            </span>
            <input
              value={catalogForm.category}
              onChange={(event) => setCatalogForm((current) => ({ ...current, category: event.target.value }))}
              className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm"
            />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Valor sugerido
              </span>
              <input
                value={catalogForm.suggested_value}
                onChange={(event) => setCatalogForm((current) => ({ ...current, suggested_value: event.target.value }))}
                type="number"
                min="0"
                className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Alcance sugerido
              </span>
              <select
                value={catalogForm.suggested_scope_type}
                onChange={(event) => setCatalogForm((current) => ({ ...current, suggested_scope_type: event.target.value }))}
                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
              >
                {scopeOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setShowCatalogModal(false)}
              className="min-h-10 rounded-xl border border-slate-200 px-4 text-sm font-bold text-slate-600 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              disabled={creatingCatalog}
              className="min-h-10 rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white hover:bg-green-700 disabled:opacity-60"
            >
              {creatingCatalog ? "Creando…" : "Crear y seleccionar"}
            </button>
          </div>
        </form>
      </Modal>
    </>
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

function PaymentForm({
  treatment,
  procedures,
  options,
  onDone,
}: {
  treatment: Treatment;
  procedures: Procedure[];
  options: AgendaOptions | null;
  onDone: () => Promise<void>;
}) {
  const [value, setValue] = useState("");
  const [method, setMethod] = useState("Efectivo");
  const [siteId, setSiteId] = useState(treatment.main_site_id ?? "");
  const [dentistId, setDentistId] = useState(treatment.responsible_dentist_id ?? "");
  const [reference, setReference] = useState("");
  const [observation, setObservation] = useState("");
  const availableProcedures = procedures.filter((procedure) => procedure.status !== "Cancelado");
  const [procedureIds, setProcedureIds] = useState<string[]>(() => availableProcedures.map((procedure) => procedure.id));
  const [receiptPayment, setReceiptPayment] = useState<Payment | null>(null);

  useEffect(() => {
    if (!procedureIds.length && availableProcedures.length) {
      setProcedureIds(availableProcedures.map((procedure) => procedure.id));
    }
  }, [availableProcedures, procedureIds.length]);

  async function handleReceipt(payment: Payment, print = false) {
    const blob = await downloadPaymentReceipt(payment.id);
    const url = URL.createObjectURL(blob);
    if (print) {
      const receiptWindow = window.open(url, "_blank", "noopener,noreferrer");
      receiptWindow?.addEventListener("load", () => receiptWindow.print(), { once: true });
      return;
    }
    const link = document.createElement("a");
    link.href = url;
    link.download = `comprobante-${payment.receipt_number}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const payment = await createPayment(treatment.id, {
      value,
      payment_method: method,
      site_id: siteId,
      dentist_id: dentistId || null,
      procedure_ids: procedureIds,
      paid_at: new Date().toISOString(),
      reference: reference || null,
      observation: observation || null,
    });
    setValue("");
    setReference("");
    setObservation("");
    setReceiptPayment(payment);
    await onDone();
  }
  return (
    <>
      <form onSubmit={submit} className="mt-5 rounded-2xl border border-slate-100 bg-slate-50 p-4">
        <div className="grid gap-4 lg:grid-cols-[150px_170px_minmax(170px,1fr)_minmax(170px,1fr)] lg:items-end">
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
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label>
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
              Referencia
            </span>
            <input
              value={reference}
              onChange={(event) => setReference(event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
              placeholder="Opcional"
            />
          </label>
          <label>
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
              Observación
            </span>
            <input
              value={observation}
              onChange={(event) => setObservation(event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
              placeholder="Opcional"
            />
          </label>
        </div>
        <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                Procedimientos asociados al pago
              </p>
              <p className="mt-1 text-xs text-slate-500">
                El comprobante mostrará únicamente los procedimientos seleccionados.
              </p>
            </div>
            {availableProcedures.length > 0 && (
              <button
                type="button"
                onClick={() => setProcedureIds(availableProcedures.map((procedure) => procedure.id))}
                className="text-xs font-bold text-green-700 hover:underline"
              >
                Seleccionar todos
              </button>
            )}
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {availableProcedures.map((procedure) => (
              <label key={procedure.id} className="flex cursor-pointer items-start gap-2 rounded-xl border border-slate-200 p-3 text-sm">
                <input
                  type="checkbox"
                  checked={procedureIds.includes(procedure.id)}
                  onChange={() => {
                    setProcedureIds((current) =>
                      current.includes(procedure.id)
                        ? current.filter((id) => id !== procedure.id)
                        : [...current, procedure.id],
                    );
                  }}
                  className="mt-1"
                />
                <span>
                  <span className="font-bold text-slate-900">{procedure.name}</span>
                  <span className="mt-0.5 block text-xs text-slate-500">{procedure.scope_label} · {procedure.status}</span>
                </span>
              </label>
            ))}
            {!availableProcedures.length && (
              <p className="rounded-xl bg-slate-50 p-3 text-sm text-slate-500">
                No hay procedimientos disponibles para asociar.
              </p>
            )}
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <button className="min-h-11 whitespace-nowrap rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white hover:bg-green-700">
            Registrar pago
          </button>
        </div>
      </form>

      <Modal
        open={Boolean(receiptPayment)}
        title="Pago registrado correctamente"
        onClose={() => setReceiptPayment(null)}
      >
        <div className="space-y-4">
          <div className="rounded-2xl bg-green-50 p-4 text-green-900">
            <p className="text-lg font-black">✓ Pago registrado correctamente</p>
            <p className="mt-1 text-sm">
              Comprobante {receiptPayment?.receipt_number}. Puedes descargarlo ahora o volver a hacerlo desde el historial de pagos.
            </p>
          </div>
          <div className="flex flex-wrap justify-end gap-3">
            <button
              type="button"
              onClick={() => receiptPayment && handleReceipt(receiptPayment)}
              className="min-h-10 rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white"
            >
              Descargar comprobante
            </button>
            <button
              type="button"
              onClick={() => receiptPayment && handleReceipt(receiptPayment, true)}
              className="min-h-10 rounded-xl border border-slate-300 px-4 text-sm font-bold text-slate-700"
            >
              Imprimir
            </button>
            <button
              type="button"
              onClick={() => setReceiptPayment(null)}
              className="min-h-10 rounded-xl border border-slate-300 px-4 text-sm font-bold text-slate-700"
            >
              Cerrar
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
