"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import {
  applicableConsentTemplates,
  confirmConsentInstance,
  createConsentInstances,
  listConsentInstanceAudit,
  listConsentInstances,
  previewConsentInstance,
  updateConsentInstance,
  voidConsentInstance,
} from "@/services/consentInstanceService";
import { listProcedures } from "@/services/treatmentService";
import type { AgendaOptions } from "@/types/agenda";
import type { ApplicableConsentTemplate, ConsentContextInput, ConsentInstance, ConsentInstanceAudit } from "@/types/consentInstance";
import type { PatientAppointment } from "@/types/patient";
import type { Procedure, TreatmentListItem } from "@/types/treatment";


const statusLabel: Record<string, string> = { DRAFT: "Borrador", READY_FOR_REVIEW: "Revisado por profesional", VOIDED: "Anulado" };

function snapshotLabel(instance: ConsentInstance, section: "site" | "professional", field: string) {
  const sectionValue = instance.context_snapshot[section];
  if (!sectionValue || typeof sectionValue !== "object") return "No registrado";
  const value = (sectionValue as Record<string, unknown>)[field];
  return typeof value === "string" && value.trim() ? value : "No registrado";
}

function RestrictedDocument({ content }: { content: string }) {
  return <div className="space-y-2 text-sm leading-6 text-slate-700">{content.split("\n").map((line, index) => {
    if (line === "---") return <hr key={index} className="border-slate-200" />;
    if (line.startsWith("# ")) return <h3 key={index} className="text-xl font-black text-slate-950">{line.slice(2)}</h3>;
    if (line.startsWith("## ")) return <h4 key={index} className="text-base font-black text-slate-900">{line.slice(3)}</h4>;
    if (line.startsWith("- ")) return <p key={index} className="pl-4 before:mr-2 before:content-['•']">{line.slice(2)}</p>;
    if (/^\d+\.\s/.test(line)) return <p key={index} className="pl-4">{line}</p>;
    return line ? <p key={index}>{line.replace(/\*\*/g, "")}</p> : <div key={index} className="h-2" />;
  })}</div>;
}

interface Props {
  patientId: string;
  appointments: PatientAppointment[];
  treatments: TreatmentListItem[];
  options: AgendaOptions | null;
  canRead: boolean;
  canCreate: boolean;
  canEdit: boolean;
  canReview: boolean;
  canVoid: boolean;
  canAudit: boolean;
}

export function PatientConsentsWorkspace({ patientId, appointments, treatments, options, canRead, canCreate, canEdit, canReview, canVoid, canAudit }: Props) {
  const [instances, setInstances] = useState<ConsentInstance[]>([]);
  const [selected, setSelected] = useState<ConsentInstance | null>(null);
  const [audit, setAudit] = useState<ConsentInstanceAudit[]>([]);
  const [creating, setCreating] = useState(false);
  const [editingInstance, setEditingInstance] = useState<ConsentInstance | null>(null);
  const [step, setStep] = useState(1);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [candidates, setCandidates] = useState<ApplicableConsentTemplate[]>([]);
  const [candidateQuery, setCandidateQuery] = useState("");
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewed, setReviewed] = useState(false);
  const [context, setContext] = useState<ConsentContextInput>({ patient_id: patientId, site_id: options?.active_site_id ?? "", appointment_id: null, treatment_id: null, treatment_procedure_ids: [], procedure_catalog_ids: [], dentist_profile_id: "", clinical_date: new Date().toISOString().slice(0, 10) });

  const load = useCallback(async () => {
    if (!canRead) return;
    setLoading(true);
    try { setInstances(await listConsentInstances(patientId)); }
    catch { setError("No fue posible cargar los consentimientos del paciente."); }
    finally { setLoading(false); }
  }, [canRead, patientId]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    setContext((current) => ({ ...current, site_id: current.site_id || options?.active_site_id || options?.sites[0]?.id || "", dentist_profile_id: current.dentist_profile_id || options?.dentists[0]?.id || "" }));
  }, [options]);
  useEffect(() => {
    if (!context.treatment_id) { setProcedures([]); setContext((current) => ({ ...current, treatment_procedure_ids: [] })); return; }
    listProcedures(context.treatment_id).then(setProcedures).catch(() => setProcedures([]));
  }, [context.treatment_id]);

  const availableDentists = useMemo(() => options?.dentists.filter((item) => !context.site_id || item.site_ids.includes(context.site_id)) ?? [], [context.site_id, options]);
  const visibleCandidates = useMemo(() => {
    const query = candidateQuery.trim().toLocaleLowerCase();
    if (!query) return candidates;
    return candidates.filter((item) => `${item.title} ${item.template_name} ${item.document_kind}`.toLocaleLowerCase().includes(query));
  }, [candidateQuery, candidates]);

  async function searchTemplates() {
    setBusy(true); setError(null);
    try { const rows = await applicableConsentTemplates(context); setCandidates(rows); setCandidateQuery(""); setSelectedVersions([]); setStep(2); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible consultar plantillas aplicables."); }
    finally { setBusy(false); }
  }

  async function createDrafts() {
    setBusy(true); setError(null);
    try {
      const created = await createConsentInstances(context, selectedVersions);
      setInstances((current) => [...created, ...current]); setCreating(false); setEditingInstance(null); setStep(1); setSelected(created[0] ?? null);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible crear los borradores."); }
    finally { setBusy(false); }
  }

  function beginCreate() {
    setEditingInstance(null); setCreating(true); setStep(1); setError(null); setCandidates([]); setCandidateQuery(""); setSelectedVersions([]);
    setContext({ patient_id: patientId, site_id: options?.active_site_id ?? options?.sites[0]?.id ?? "", appointment_id: null, treatment_id: null, treatment_procedure_ids: [], procedure_catalog_ids: [], dentist_profile_id: options?.dentists[0]?.id ?? "", clinical_date: new Date().toISOString().slice(0, 10) });
  }

  function beginEdit(instance: ConsentInstance) {
    if (instance.status !== "DRAFT") return;
    setEditingInstance(instance); setCreating(true); setStep(1); setError(null);
    setContext({ patient_id: patientId, site_id: instance.site_id, appointment_id: instance.appointment_id, treatment_id: instance.treatment_id, treatment_procedure_ids: instance.procedures.flatMap((item) => item.treatment_procedure_id ? [item.treatment_procedure_id] : []), procedure_catalog_ids: instance.procedures.flatMap((item) => item.procedure_catalog_id && !item.treatment_procedure_id ? [item.procedure_catalog_id] : []), dentist_profile_id: instance.dentist_profile_id ?? "", clinical_date: instance.clinical_date });
  }

  async function saveDraftContext() {
    if (!editingInstance) return;
    setBusy(true); setError(null);
    try {
      const updated = await updateConsentInstance(editingInstance.id, context, editingInstance.row_version);
      setInstances((rows) => rows.map((row) => row.id === updated.id ? updated : row)); setSelected(updated); setCreating(false); setEditingInstance(null);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible actualizar el borrador."); }
    finally { setBusy(false); }
  }

  async function openInstance(instance: ConsentInstance) {
    setSelected(instance); setReviewed(false); setAudit([]);
    try { setSelected((await previewConsentInstance(instance.id)).instance); } catch { /* detail remains available */ }
    if (canAudit) listConsentInstanceAudit(instance.id).then(setAudit).catch(() => setAudit([]));
  }

  async function confirm() {
    if (!selected || !reviewed) return;
    setBusy(true); setError(null);
    try { const updated = await confirmConsentInstance(selected.id, selected.row_version); setSelected(updated); setInstances((rows) => rows.map((row) => row.id === updated.id ? updated : row)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible confirmar la revisión."); }
    finally { setBusy(false); }
  }

  async function voidCurrent() {
    if (!selected) return;
    const reason = window.prompt("Motivo administrativo de anulación (mínimo 5 caracteres):")?.trim();
    if (!reason) return;
    setBusy(true);
    try { const updated = await voidConsentInstance(selected.id, reason); setSelected(updated); setInstances((rows) => rows.map((row) => row.id === updated.id ? updated : row)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible anular la instancia."); }
    finally { setBusy(false); }
  }

  if (!canRead) return <Alert tone="warning">No tienes permiso para consultar consentimientos clínicos.</Alert>;
  if (loading) return <div className="flex items-center gap-2 py-10 text-slate-500"><Spinner className="h-5 w-5" />Cargando consentimientos…</div>;

  return <div className="space-y-5">
    {error && <Alert tone="error">{error}</Alert>}
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-black text-slate-950">Consentimientos</h2><p className="text-sm text-slate-500">Preparación y revisión clínica previa. Ningún documento de esta sección ha sido enviado ni firmado.</p></div>{canCreate && <button type="button" onClick={beginCreate} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white">Crear consentimiento</button>}</div>

    {creating && <section className="rounded-2xl border border-emerald-200 bg-white p-5 shadow-sm">
      <div className="mb-5 flex gap-2 text-xs font-black text-slate-500"><span className={step === 1 ? "text-emerald-700" : ""}>1. Contexto</span>{!editingInstance && <><span>→</span><span className={step === 2 ? "text-emerald-700" : ""}>2. Plantillas</span><span>→</span><span className={step === 3 ? "text-emerald-700" : ""}>3. Vista previa</span></>}</div>
      {step === 1 && <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-bold">Sede<select value={context.site_id} onChange={(event) => setContext((current) => ({ ...current, site_id: event.target.value, dentist_profile_id: "" }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"><option value="">Seleccionar</option>{options?.sites.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label className="text-sm font-bold">Profesional<select value={context.dentist_profile_id} onChange={(event) => setContext((current) => ({ ...current, dentist_profile_id: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"><option value="">Seleccionar</option>{availableDentists.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label className="text-sm font-bold">Cita (opcional)<select value={context.appointment_id ?? ""} onChange={(event) => setContext((current) => ({ ...current, appointment_id: event.target.value || null }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"><option value="">Sin cita</option>{appointments.map((item) => <option key={item.id} value={item.id}>{new Date(item.starts_at).toLocaleDateString()} — {item.reason}</option>)}</select></label>
        <label className="text-sm font-bold">Tratamiento (opcional)<select value={context.treatment_id ?? ""} onChange={(event) => setContext((current) => ({ ...current, treatment_id: event.target.value || null }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"><option value="">Sin tratamiento</option>{treatments.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label className="text-sm font-bold">Fecha clínica<input type="date" value={context.clinical_date ?? ""} onChange={(event) => setContext((current) => ({ ...current, clinical_date: event.target.value || null }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>
        {procedures.length > 0 && <div className="md:col-span-2"><p className="text-sm font-bold">Procedimientos</p><div className="mt-2 grid gap-2 md:grid-cols-2">{procedures.map((item) => <label key={item.id} className="flex items-start gap-2 rounded-xl border border-slate-200 p-3 text-sm"><input type="checkbox" checked={context.treatment_procedure_ids.includes(item.id)} onChange={(event) => setContext((current) => ({ ...current, treatment_procedure_ids: event.target.checked ? [...current.treatment_procedure_ids, item.id] : current.treatment_procedure_ids.filter((id) => id !== item.id) }))} /><span><strong>{item.name}</strong><span className="block text-xs text-slate-500">{item.scope_label}</span></span></label>)}</div></div>}
        <div className="flex justify-end gap-2 md:col-span-2"><button type="button" onClick={() => { setCreating(false); setEditingInstance(null); }} className="rounded-xl border px-4 py-2.5 text-sm font-bold">Cancelar</button><button type="button" disabled={busy || !context.site_id || !context.dentist_profile_id} onClick={editingInstance ? saveDraftContext : searchTemplates} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">{editingInstance ? "Guardar cambios" : "Buscar plantillas"}</button></div>
      </div>}
      {step === 2 && <div className="space-y-3">{candidates.length === 0 ? <Alert tone="warning">No hay plantillas publicadas aplicables. Puedes ajustar el contexto o configurar una plantilla compatible.</Alert> : <><label className="block text-sm font-bold">Buscar entre plantillas compatibles<input type="search" value={candidateQuery} onChange={(event) => setCandidateQuery(event.target.value)} placeholder="Nombre, título o tipo" className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>{visibleCandidates.length === 0 && <Alert tone="info">No hay coincidencias para esta búsqueda. Las plantillas compatibles siguen disponibles al limpiar el filtro.</Alert>}{visibleCandidates.map((item) => <label key={item.version_id} className="flex gap-3 rounded-xl border border-slate-200 p-4"><input type="checkbox" checked={selectedVersions.includes(item.version_id)} onChange={(event) => setSelectedVersions((current) => event.target.checked ? [...current, item.version_id] : current.filter((id) => id !== item.version_id))} /><span className="min-w-0"><strong className="block text-slate-950">{item.title}</strong><span className="block text-sm text-slate-500">{item.template_name} · versión {item.version_number} · {item.country_code}</span><span className="mt-1 block text-xs font-bold text-emerald-700">{item.applicability_reason_codes.includes("GENERAL_TEMPLATE") ? "Aplica como plantilla general" : item.applicability_reasons.join(" · ")}</span>{item.missing_variable_labels.length > 0 && <span className="mt-2 block text-xs text-amber-700">Datos faltantes: {item.missing_variable_labels.join(", ")}</span>}</span></label>)}</>}<div className="flex justify-end gap-2"><button type="button" onClick={() => setStep(1)} className="rounded-xl border px-4 py-2.5 text-sm font-bold">Atrás</button><button type="button" disabled={!selectedVersions.length} onClick={() => setStep(3)} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">Revisar documentos</button></div></div>}
      {step === 3 && <div className="space-y-4"><Alert tone="warning">Documento preparado para revisión profesional. Todavía no ha sido enviado ni firmado.</Alert>{candidates.filter((item) => selectedVersions.includes(item.version_id)).map((item) => <article key={item.version_id} className="rounded-xl border border-slate-200 p-5"><h3 className="mb-3 text-lg font-black">{item.title}</h3><RestrictedDocument content={item.rendered_preview} />{item.missing_variable_labels.length > 0 && <p className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">Antes de confirmar deben completarse: {item.missing_variable_labels.join(", ")}.</p>}</article>)}<div className="flex justify-end gap-2"><button type="button" onClick={() => setStep(2)} className="rounded-xl border px-4 py-2.5 text-sm font-bold">Atrás</button><button type="button" disabled={busy} onClick={createDrafts} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">Crear {selectedVersions.length} borrador{selectedVersions.length === 1 ? "" : "es"}</button></div></div>}
    </section>}

    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white"><table className="min-w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Número</th><th className="p-3">Título</th><th className="p-3">Procedimientos</th><th className="p-3">Profesional y sede</th><th className="p-3">Estado</th><th className="p-3">Fecha</th></tr></thead><tbody>{instances.map((item) => <tr key={item.id} onClick={() => void openInstance(item)} className="cursor-pointer border-t hover:bg-emerald-50"><td className="p-3 font-black">{item.visible_number}</td><td className="p-3">{item.display_title}<span className="block text-xs text-slate-500">Plantilla v{item.template_version_number}</span></td><td className="p-3">{item.procedures.map((row) => row.name).join(", ") || "Sin procedimiento"}</td><td className="p-3">{snapshotLabel(item, "professional", "full_name")}<span className="block text-xs text-slate-500">{snapshotLabel(item, "site", "name")}</span></td><td className="p-3"><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold">{statusLabel[item.status]}</span></td><td className="p-3">{new Date(item.clinical_date + "T00:00:00").toLocaleDateString()}</td></tr>)}</tbody></table>{instances.length === 0 && <p className="p-8 text-center text-sm text-slate-500">Este paciente todavía no tiene consentimientos preparados.</p>}</div>

    {selected && <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between"><div><p className="text-xs font-black uppercase text-emerald-700">{selected.visible_number}</p><h3 className="text-xl font-black">{selected.display_title}</h3><p className="text-sm text-slate-500">{statusLabel[selected.status]} · versión {selected.template_version_number}</p></div><button type="button" onClick={() => setSelected(null)} aria-label="Cerrar detalle" className="h-9 w-9 rounded-lg border">×</button></div>{selected.missing_variable_labels.length > 0 && <Alert tone="warning">Datos faltantes: {selected.missing_variable_labels.join(", ")}. Corrige los datos maestros y actualiza el contexto del borrador.</Alert>}<div className="my-5 rounded-xl border border-slate-200 p-5"><RestrictedDocument content={selected.rendered_content ?? ""} /></div><div className="flex flex-wrap gap-2">{selected.status === "DRAFT" && canEdit && <button type="button" disabled={busy} onClick={() => beginEdit(selected)} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-black text-slate-700">Editar contexto</button>}{selected.status === "DRAFT" && canReview && <label className="mr-auto flex max-w-xl items-start gap-2 rounded-xl bg-emerald-50 p-3 text-sm"><input type="checkbox" checked={reviewed} onChange={(event) => setReviewed(event.target.checked)} /><span>Confirmo que revisé el contenido y que corresponde al procedimiento propuesto. Después de continuar, el contenido quedará inmutable.</span></label>}{selected.status === "DRAFT" && canReview && <button type="button" disabled={busy || !reviewed || selected.missing_variables.length > 0} onClick={confirm} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">Confirmar revisión profesional</button>}{selected.status !== "VOIDED" && canVoid && <button type="button" disabled={busy} onClick={voidCurrent} className="rounded-xl border border-red-200 px-4 py-2.5 text-sm font-black text-red-700">Anular administrativamente</button>}</div>{selected.status === "READY_FOR_REVIEW" && <p className="mt-4 rounded-xl bg-sky-50 p-3 text-sm text-sky-900">Consentimiento revisado y sellado. La emisión de la sesión para decisión del paciente se habilitará en C019A.3.</p>}{canAudit && audit.length > 0 && <details className="mt-5"><summary className="cursor-pointer text-sm font-black">Auditoría</summary><div className="mt-2 space-y-2">{audit.map((item) => <p key={item.id} className="rounded-lg bg-slate-50 p-2 text-xs">{new Date(item.occurred_at).toLocaleString()} · {item.action}</p>)}</div></details>}</section>}
  </div>;
}
