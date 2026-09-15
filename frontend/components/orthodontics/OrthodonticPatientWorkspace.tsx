"use client";

import { FormEvent, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { OrthodonticEvolutionPanel } from "@/components/orthodontics/OrthodonticEvolutionPanel";
import { OrthodonticClinicalRecordPanel } from "@/components/orthodontics/OrthodonticClinicalRecordPanel";
import { ApiError } from "@/services/apiClient";
import {
  activateOrthodonticCase,
  changeOrthodonticResponsible,
  completeOrthodonticCase,
  createOrthodonticCase,
  discontinueOrthodonticCase,
  getPatientOrthodontics,
  resumeOrthodonticCase,
  suspendOrthodonticCase,
  updateOrthodonticCase,
} from "@/services/orthodonticCaseService";
import type { OrthodonticCase, OrthodonticPatientWorkspace as Workspace } from "@/types/orthodonticCase";

type InternalTab = "summary" | "evolution" | "record";

const statusLabel: Record<OrthodonticCase["display_status"], string> = {
  DRAFT: "Borrador", ACTIVE: "Activo", SUSPENDED: "Suspendido",
  COMPLETED: "Completado", DISCONTINUED: "Interrumpido",
};

function date(value: string | null) {
  return value ? new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "No registrado";
}

export function OrthodonticPatientWorkspace({ patientId, initial }: { patientId: string; initial: Workspace }) {
  const [workspace, setWorkspace] = useState(initial);
  const [tab, setTab] = useState<InternalTab>("summary");
  const [editing, setEditing] = useState(false);
  const [plan, setPlan] = useState(initial.active_case?.treatment_plan ?? "");
  const [appliance, setAppliance] = useState(initial.active_case?.current_appliance_summary ?? "");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const initialRecordCaseId = initial.active_case?.id ?? initial.historical_cases[0]?.id ?? "";
  const [recordCaseId, setRecordCaseId] = useState(initialRecordCaseId);
  const [evolutionCaseId, setEvolutionCaseId] = useState(initialRecordCaseId);
  const [recordDirty, setRecordDirty] = useState(false);

  useEffect(() => {
    setWorkspace(initial);
    setPlan(initial.active_case?.treatment_plan ?? "");
    setAppliance(initial.active_case?.current_appliance_summary ?? "");
    setEditing(false);
    setMessage(null);
    setError(null);
    setRecordCaseId(initial.active_case?.id ?? initial.historical_cases[0]?.id ?? "");
    setEvolutionCaseId(initial.active_case?.id ?? initial.historical_cases[0]?.id ?? "");
  }, [initial, patientId]);

  async function refresh() {
    const loaded = await getPatientOrthodontics(patientId);
    setWorkspace(loaded);
    setPlan(loaded.active_case?.treatment_plan ?? "");
    setAppliance(loaded.active_case?.current_appliance_summary ?? "");
  }
  async function run(action: () => Promise<{ message: string }>) {
    setBusy(true); setError(null); setMessage(null);
    try { const result = await action(); setMessage(result.message); await refresh(); setEditing(false); setReason(""); }
    catch (caught) { setError(caught instanceof ApiError ? caught.detail ?? caught.message : "No fue posible completar la acción."); }
    finally { setBusy(false); }
  }
  async function save(event: FormEvent) {
    event.preventDefault();
    const current = workspace.active_case;
    if (current) await run(() => updateOrthodonticCase(current.id, current.row_version, plan, appliance));
    else await run(() => createOrthodonticCase(patientId, plan, appliance));
  }

  const current = workspace.active_case;
  const recordCases = current ? [current, ...workspace.historical_cases] : workspace.historical_cases;
  const recordCase = recordCases.find((item) => item.id === recordCaseId) ?? recordCases[0];
  const evolutionCase = recordCases.find((item) => item.id === evolutionCaseId) ?? recordCases[0];
  const canWrite = workspace.access.allowed;
  return <div>
    <div className="mb-5 flex flex-wrap gap-2" role="tablist" aria-label="Ortodoncia">
      {([{ id: "summary", label: "Resumen" }, { id: "evolution", label: "Evolución" }, { id: "record", label: workspace.record_label }] as { id: InternalTab; label: string }[]).map((item) =>
        <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} onClick={() => { if (tab === "record" && item.id !== "record" && recordDirty && !window.confirm("Hay cambios sin guardar. ¿Deseas descartarlos?")) return; setTab(item.id); }} className={`rounded-xl px-4 py-2 text-sm font-bold ${tab === item.id ? "bg-green-700 text-white" : "border bg-white text-slate-700"}`}>{item.label}</button>
      )}
    </div>
    {message && <div className="mb-4"><Alert>{message}</Alert></div>}
    {error && <div className="mb-4"><Alert tone="error">{error}</Alert></div>}
    {tab === "evolution" && evolutionCase && <div>
      {recordCases.length > 1 && <label className="mb-4 block max-w-xl text-sm font-bold">Caso de Ortodoncia
        <select value={evolutionCase.id} onChange={(event) => setEvolutionCaseId(event.target.value)} className="mt-1 min-h-11 w-full rounded-xl border bg-white px-3 font-normal">
          {recordCases.map((item) => <option key={item.id} value={item.id}>{statusLabel[item.display_status]} · {date(item.started_at)} · {item.responsible_dentist_name}</option>)}
        </select>
      </label>}
      <OrthodonticEvolutionPanel key={evolutionCase.id} orthodonticCase={evolutionCase} accessAllowed={canWrite} onChanged={refresh} />
    </div>}
    {tab === "evolution" && !evolutionCase && <section className="rounded-2xl border bg-white p-8 text-center"><h2 className="font-black">Evolución de Ortodoncia</h2><p className="mt-2 text-sm text-slate-500">Crea y activa primero un caso de Ortodoncia.</p></section>}
    {tab === "record" && recordCase && <div>
      {recordCases.length > 1 && <label className="mb-4 block max-w-xl text-sm font-bold">Caso de Ortodoncia
        <select value={recordCase.id} onChange={(event) => { if (recordDirty && !window.confirm("Hay cambios sin guardar. ¿Deseas descartarlos?")) return; setRecordCaseId(event.target.value); }} className="mt-1 min-h-11 w-full rounded-xl border bg-white px-3 font-normal">
          {recordCases.map((item) => <option key={item.id} value={item.id}>{statusLabel[item.display_status]} · {date(item.started_at)} · {item.responsible_dentist_name}</option>)}
        </select>
      </label>}
      <OrthodonticClinicalRecordPanel key={recordCase.id} caseId={recordCase.id} caseStatus={recordCase.status} label={workspace.record_label} accessAllowed={workspace.access.allowed} onDirtyChange={setRecordDirty} />
    </div>}
    {tab === "record" && !recordCase && <section className="rounded-2xl border bg-white p-8 text-center"><h2 className="font-black">{workspace.record_label}</h2><p className="mt-2 text-sm text-slate-500">Crea primero un caso de Ortodoncia.</p></section>}
    {tab === "summary" && !current && canWrite && <form onSubmit={save} className="rounded-2xl border bg-white p-6 shadow-sm"><h2 className="text-xl font-black">Iniciar caso de Ortodoncia</h2><p className="mt-2 text-sm text-slate-500">Se creará un borrador clínico asociado a la historia del paciente.</p><ClinicalFields plan={plan} appliance={appliance} onPlan={setPlan} onAppliance={setAppliance} /><button disabled={busy} className="mt-5 rounded-xl bg-green-700 px-5 py-3 font-bold text-white disabled:opacity-50">{busy ? "Guardando…" : "Crear caso en borrador"}</button></form>}
    {tab === "summary" && !current && !canWrite && <Alert tone="warning">Tu acceso de Ortodoncia ya no está habilitado. Los casos históricos permanecen disponibles en modo de solo lectura.</Alert>}
    {tab === "summary" && current && <>
      {!canWrite && <div className="mb-4"><Alert tone="warning">Tu acceso de Ortodoncia ya no está habilitado. El caso y sus borradores se conservan en modo de solo lectura.</Alert></div>}
      {current.status === "SUSPENDED" && <div className="mb-4"><Alert tone="warning">Este caso está suspendido. Reactívalo para registrar nuevas evoluciones o modificar la ficha.</Alert></div>}
      {current.status === "COMPLETED" && <div className="mb-4"><Alert tone="info">Este caso está cerrado y se conserva como historial clínico.</Alert></div>}
      {!current.responsible_dentist_available && <div className="mb-4"><Alert tone="warning">Responsable histórico no disponible. Asigna explícitamente un ortodoncista válido antes de continuar el tratamiento.</Alert></div>}
      <section className="grid gap-4 sm:grid-cols-3"><Stat label="Estado" value={statusLabel[current.display_status]} /><Stat label="Responsable" value={current.responsible_dentist_name} /><Stat label="Inicio" value={date(current.started_at)} /></section>
      <section className="mt-5 rounded-2xl border bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-black">Resumen clínico</h2><p className="text-sm text-slate-500">Cambios guardados de forma explícita.</p></div>{canWrite && ["DRAFT", "ACTIVE"].includes(current.status) && !editing && <button type="button" onClick={() => setEditing(true)} className="rounded-xl border px-4 py-2 text-sm font-bold">Editar</button>}</div>
        {editing ? <form onSubmit={save}><ClinicalFields plan={plan} appliance={appliance} onPlan={setPlan} onAppliance={setAppliance} /><div className="mt-4 flex gap-2"><button disabled={busy} className="rounded-xl bg-green-700 px-4 py-2 font-bold text-white">Guardar</button><button type="button" onClick={() => setEditing(false)} className="rounded-xl border px-4 py-2 font-bold">Cancelar</button></div></form> : <div className="mt-5 grid gap-5 md:grid-cols-2"><TextBlock title="Plan de tratamiento" value={current.treatment_plan} /><TextBlock title="Aparatología actual" value={current.current_appliance_summary} /></div>}
      </section>
      <section className="mt-5 grid gap-4 md:grid-cols-2"><div className="rounded-2xl border bg-white p-5"><h3 className="font-black">Última visita</h3><p className="mt-2 text-sm text-slate-600">{workspace.summary?.last_visit ? `${date(workspace.summary.last_visit)}${workspace.summary.last_visit_professional ? ` · ${workspace.summary.last_visit_professional}` : ""}` : "Sin evoluciones firmadas."}</p><p className="mt-2 whitespace-pre-wrap text-sm">{workspace.summary?.what_was_done || "Sin actividad firmada registrada."}</p></div><div className="rounded-2xl border bg-white p-5"><h3 className="font-black">Próxima sesión</h3><p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{workspace.summary?.next_session_instructions || "Sin indicaciones clínicas registradas."}</p><p className="mt-2 text-xs font-bold text-slate-500">{workspace.summary?.next_clinical_control ? `${workspace.summary.next_clinical_control}${workspace.summary.suggested_next_control_date ? ` · fecha sugerida ${workspace.summary.suggested_next_control_date}` : ""}` : "Sin próximo control indicado."}</p></div><div className="rounded-2xl border bg-white p-5"><h3 className="font-black">Alertas</h3>{workspace.summary?.active_alerts.length ? <ul className="mt-2 list-disc pl-5 text-sm text-red-700">{workspace.summary.active_alerts.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="mt-2 text-sm text-slate-500">Sin alertas ortodóncicas activas.</p>}</div><div className="rounded-2xl border bg-white p-5"><h3 className="font-black">Próxima cita agendada</h3><p className="mt-2 text-sm text-slate-600">{workspace.summary?.next_appointment ? `${date(workspace.summary.next_appointment.starts_at)} · ${workspace.summary.next_appointment.reason}` : "Sin próxima cita agendada."}</p></div></section>
      {canWrite && current.status !== "COMPLETED" && <section className="mt-5 rounded-2xl border bg-white p-5"><h3 className="font-black">Acciones del caso</h3><div className="mt-4 flex flex-wrap gap-2">{current.status === "DRAFT" && <button type="button" disabled={busy} onClick={() => void run(() => activateOrthodonticCase(current.id, current.row_version))} className="rounded-xl bg-green-700 px-4 py-2 font-bold text-white">Iniciar tratamiento</button>}{current.status === "ACTIVE" && <><button type="button" disabled={busy} onClick={() => void run(() => suspendOrthodonticCase(current.id, current.row_version))} className="rounded-xl border px-4 py-2 font-bold">Suspender</button><button type="button" disabled={busy} onClick={() => void run(() => completeOrthodonticCase(current.id, current.row_version))} className="rounded-xl border px-4 py-2 font-bold">Completar</button></>}{current.status === "SUSPENDED" && <button type="button" disabled={busy} onClick={() => void run(() => resumeOrthodonticCase(current.id, current.row_version))} className="rounded-xl bg-green-700 px-4 py-2 font-bold text-white">Reactivar</button>}</div>{current.status === "ACTIVE" && <div className="mt-4 flex flex-col gap-2 sm:flex-row"><input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Motivo obligatorio de interrupción" className="min-h-11 flex-1 rounded-xl border px-3" /><button type="button" disabled={busy || !reason.trim()} onClick={() => void run(() => discontinueOrthodonticCase(current.id, current.row_version, reason))} className="rounded-xl border border-red-200 px-4 py-2 font-bold text-red-700 disabled:opacity-40">Interrumpir caso</button></div>}
        <label className="mt-5 block text-sm font-bold">Cambiar responsable<select value={current.responsible_dentist_id} onChange={(event) => void run(() => changeOrthodonticResponsible(current.id, current.row_version, event.target.value))} className="mt-1 min-h-11 w-full rounded-xl border bg-white px-3 font-normal">{workspace.eligible_responsibles.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      </section>}
      {current.status === "COMPLETED" && <section className="mt-5 rounded-2xl border bg-slate-50 p-5"><h3 className="font-black">{current.display_status === "DISCONTINUED" ? "Tratamiento de Ortodoncia interrumpido" : "Tratamiento de Ortodoncia completado"}</h3><p className="mt-2 text-sm">{date(current.completed_at)}{current.closure_notes ? ` · ${current.closure_notes}` : ""}</p></section>}
    </>}
    {tab === "summary" && workspace.historical_cases.length > 0 && <section className="mt-6"><h2 className="text-lg font-black">Historial de casos</h2><div className="mt-3 space-y-3">{workspace.historical_cases.map((item) => <div key={item.id} className="rounded-2xl border bg-white p-5"><div className="flex justify-between gap-4"><div><p className="font-black">{statusLabel[item.display_status]}</p><p className="text-sm text-slate-500">{item.responsible_dentist_name}</p></div><p className="text-sm text-slate-500">{date(item.started_at)} — {date(item.completed_at)}</p></div>{item.closure_notes && <p className="mt-3 text-sm">{item.closure_notes}</p>}</div>)}</div></section>}
  </div>;
}

function ClinicalFields({ plan, appliance, onPlan, onAppliance }: { plan: string; appliance: string; onPlan: (value: string) => void; onAppliance: (value: string) => void }) { return <div className="mt-5 grid gap-4"><label className="text-sm font-bold">Plan de tratamiento<textarea value={plan} onChange={(event) => onPlan(event.target.value)} rows={5} className="mt-1 w-full rounded-xl border p-3 font-normal" /></label><label className="text-sm font-bold">Aparatología actual<textarea value={appliance} onChange={(event) => onAppliance(event.target.value)} rows={3} className="mt-1 w-full rounded-xl border p-3 font-normal" /></label></div>; }
function Stat({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border bg-white p-5"><p className="text-xs font-bold uppercase text-slate-400">{label}</p><p className="mt-2 font-black">{value}</p></div>; }
function TextBlock({ title, value }: { title: string; value: string | null }) { return <div><h3 className="font-black">{title}</h3><p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{value || "Sin información registrada."}</p></div>; }
