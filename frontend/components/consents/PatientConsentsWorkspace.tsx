"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { ConsentAccessPanel } from "@/components/consents/ConsentAccessPanel";
import { ConsentAcceptancePanel } from "@/components/consents/ConsentAcceptancePanel";
import { ConsentPaperPanel } from "@/components/consents/ConsentPaperPanel";
import { ConsentRestrictedMarkdown } from "@/components/consents/ConsentRestrictedMarkdown";
import { minorParticipationOptions, responsibleRelationshipLabel, responsibleRelationshipOptions } from "@/lib/consentSignerLabels";
import { subscribeConsentSigned } from "@/lib/consentStatusEvents.mjs";
import {
  applicableConsentTemplates,
  confirmConsentInstance,
  createConsentInstances,
  getConsentInstance,
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

function emptyResponsibleAdult() {
  return { relationship_type: "MOTHER", identity_verified: false, full_name: "", document_type: "CC", document_number: "", email: "", phone: "", relationship_other: "" };
}

const statusLabel: Record<string, string> = { DRAFT: "Borrador", READY_FOR_REVIEW: "Revisado por profesional", PENDING_SIGNATURE: "Pendiente de revisión del paciente", SIGNED: "Aceptado y firmado", VOIDED: "Anulado" };

function instanceStatusLabel(instance: ConsentInstance) {
  if (instance.completion_channel === "PAPER" && instance.paper_status === "FINALIZED") return "Firmado en papel — copia digitalizada";
  if (instance.completion_channel === "PAPER" && ["SIGNED_PENDING_DIGITIZATION", "DIGITIZING"].includes(instance.paper_status ?? "")) return "Firmado en papel — pendiente de digitalización";
  if (instance.completion_channel === "PAPER") return "Preparado para firma en papel";
  if (instance.status === "SIGNED") return "Firmado electrónicamente";
  if (instance.completion_channel === "ELECTRONIC" && instance.status === "PENDING_SIGNATURE") return "Pendiente de firma electrónica";
  return statusLabel[instance.status];
}

function snapshotLabel(instance: ConsentInstance, section: "site" | "professional", field: string) {
  const sectionValue = instance.context_snapshot[section];
  if (!sectionValue || typeof sectionValue !== "object") return "No registrado";
  const value = (sectionValue as Record<string, unknown>)[field];
  return typeof value === "string" && value.trim() ? value : "No registrado";
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
  canIssueAccess: boolean; canReadAccess: boolean; canRevokeAccess: boolean; canReissueAccess: boolean; canManageClarifications: boolean; canViewAccessAudit: boolean;
  canReadAcceptance:boolean; canDownloadFinal:boolean; canResendCopy:boolean;
  canReadPaper:boolean; canPreparePaper:boolean; canRecordPaper:boolean; canUploadPaper:boolean; canFinalizePaper:boolean;
}

export function PatientConsentsWorkspace({ patientId, appointments, treatments, options, canRead, canCreate, canEdit, canReview, canVoid, canAudit, canIssueAccess, canReadAccess, canRevokeAccess, canReissueAccess, canManageClarifications, canViewAccessAudit, canReadAcceptance, canDownloadFinal, canResendCopy, canReadPaper, canPreparePaper, canRecordPaper, canUploadPaper, canFinalizePaper }: Props) {
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
  const handledAcceptances = useRef(new Set<string>());
  const pollingInFlight = useRef(false);
  const selectedPollingId = selected?.id;
  const selectedPollingStatus = selected?.status;
  const [context, setContext] = useState<ConsentContextInput>({ patient_id: patientId, site_id: options?.active_site_id ?? "", appointment_id: null, treatment_id: null, treatment_procedure_ids: [], procedure_catalog_ids: [], dentist_profile_id: "", clinical_date: new Date().toISOString().slice(0, 10), signer_actor_type: "PATIENT_SELF", responsible_adult: null, minor_participation_status: "NOT_APPLICABLE", minor_participation_observation: null });

  const load = useCallback(async () => {
    if (!canRead) return;
    setLoading(true);
    try { setInstances(await listConsentInstances(patientId)); }
    catch { setError("No fue posible cargar los consentimientos del paciente."); }
    finally { setLoading(false); }
  }, [canRead, patientId]);

  const refreshConsentState = useCallback(async () => {
    const rows = await listConsentInstances(patientId);
    setInstances(rows);
    setSelected((current) => current ? rows.find((row) => row.id === current.id) ?? current : null);
  }, [patientId]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => subscribeConsentSigned(({ acceptanceId }) => {
    if (!canRead || handledAcceptances.current.has(acceptanceId)) return;
    handledAcceptances.current.add(acceptanceId);
    void listConsentInstances(patientId).then((rows) => {
      setInstances(rows);
      setSelected((current) => current ? rows.find((row) => row.id === current.id) ?? current : null);
    }).catch(() => {
      handledAcceptances.current.delete(acceptanceId);
      setError("La firma fue registrada, pero no fue posible actualizar la vista. Intenta nuevamente.");
    });
  }), [canRead, patientId]);
  useEffect(() => {
    if (!canRead || !selectedPollingId || !selectedPollingStatus || !["READY_FOR_REVIEW", "PENDING_SIGNATURE"].includes(selectedPollingStatus)) return;
    let cancelled = false;
    const pollSelectedInstance = async () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return;
      if (pollingInFlight.current) return;
      pollingInFlight.current = true;
      try {
        const updated = await getConsentInstance(selectedPollingId);
        if (cancelled) return;
        setInstances((rows) => rows.map((row) => row.id === updated.id ? updated : row));
        setSelected((current) => current?.id === updated.id ? updated : current);
      } catch {
        if (!cancelled) setError("No fue posible actualizar el estado del consentimiento. Se reintentará automáticamente.");
      } finally {
        pollingInFlight.current = false;
      }
    };
    const timer = window.setInterval(() => void pollSelectedInstance(), 5000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [canRead, selectedPollingId, selectedPollingStatus]);
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
    setContext({ patient_id: patientId, site_id: options?.active_site_id ?? options?.sites[0]?.id ?? "", appointment_id: null, treatment_id: null, treatment_procedure_ids: [], procedure_catalog_ids: [], dentist_profile_id: options?.dentists[0]?.id ?? "", clinical_date: new Date().toISOString().slice(0, 10), signer_actor_type: "PATIENT_SELF", responsible_adult: null, minor_participation_status: "NOT_APPLICABLE", minor_participation_observation: null });
  }

  function beginEdit(instance: ConsentInstance) {
    if (instance.status !== "DRAFT") return;
    setEditingInstance(instance); setCreating(true); setStep(1); setError(null);
    setContext({ patient_id: patientId, site_id: instance.site_id, appointment_id: instance.appointment_id, treatment_id: instance.treatment_id, treatment_procedure_ids: instance.procedures.flatMap((item) => item.treatment_procedure_id ? [item.treatment_procedure_id] : []), procedure_catalog_ids: instance.procedures.flatMap((item) => item.procedure_catalog_id && !item.treatment_procedure_id ? [item.procedure_catalog_id] : []), dentist_profile_id: instance.dentist_profile_id ?? "", clinical_date: instance.clinical_date, signer_actor_type: instance.signer_actor_type, responsible_adult: instance.signer_actor_type === "RESPONSIBLE_ADULT" ? { patient_responsible_id: instance.responsible_adult?.patient_responsible_id ?? null, full_name: instance.responsible_adult?.full_name ?? instance.signer_name ?? "", document_type: instance.responsible_adult?.document_type ?? "CC", document_number: instance.responsible_adult?.document_number ?? "", relationship_type: instance.responsible_adult?.relationship_type ?? "MOTHER", relationship_other: instance.responsible_adult?.relationship_other ?? "", email: "", phone: instance.responsible_adult?.phone ?? "", identity_verified: false } : null, minor_participation_status: instance.minor_participation_status ?? "NOT_APPLICABLE", minor_participation_observation: instance.minor_participation_observation });
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
        <section className="space-y-4 rounded-2xl border border-emerald-100 bg-emerald-50/40 p-4 md:col-span-2">
          <div><p className="text-sm font-black text-slate-950">Firmante del consentimiento</p><p className="text-xs text-slate-500">Selecciona si firmará el paciente adulto o un adulto responsable. Esta información queda congelada al emitir el acceso.</p></div>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="rounded-xl border border-slate-200 bg-white p-3 text-sm font-bold"><input type="radio" className="mr-2" checked={(context.signer_actor_type ?? "PATIENT_SELF") === "PATIENT_SELF"} onChange={() => setContext((current) => ({ ...current, signer_actor_type: "PATIENT_SELF", responsible_adult: null, minor_participation_status: "NOT_APPLICABLE" }))} />Paciente adulto</label>
            <label className="rounded-xl border border-slate-200 bg-white p-3 text-sm font-bold"><input type="radio" className="mr-2" checked={context.signer_actor_type === "RESPONSIBLE_ADULT"} onChange={() => setContext((current) => ({ ...current, signer_actor_type: "RESPONSIBLE_ADULT", responsible_adult: current.responsible_adult ?? emptyResponsibleAdult(), minor_participation_status: current.minor_participation_status === "NOT_APPLICABLE" ? "COULD_NOT_EXPRESS_DUE_TO_AGE_OR_CONDITION" : current.minor_participation_status }))} />Adulto responsable</label>
          </div>
          {context.signer_actor_type === "RESPONSIBLE_ADULT" && <div className="grid gap-3 md:grid-cols-2">
            <label className="text-sm font-bold">Nombre completo<input value={context.responsible_adult?.full_name ?? ""} onChange={(event) => setContext((current) => ({ ...current, responsible_adult: { ...(current.responsible_adult ?? emptyResponsibleAdult()), full_name: event.target.value } }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>
            <label className="text-sm font-bold">Tipo documento<input value={context.responsible_adult?.document_type ?? ""} onChange={(event) => setContext((current) => ({ ...current, responsible_adult: { ...(current.responsible_adult ?? emptyResponsibleAdult()), document_type: event.target.value } }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>
            <label className="text-sm font-bold">Número documento<input value={context.responsible_adult?.document_number ?? ""} onChange={(event) => setContext((current) => ({ ...current, responsible_adult: { ...(current.responsible_adult ?? emptyResponsibleAdult()), document_number: event.target.value } }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>
            <label className="text-sm font-bold">Relación<select value={context.responsible_adult?.relationship_type ?? "MOTHER"} onChange={(event) => setContext((current) => ({ ...current, responsible_adult: { ...(current.responsible_adult ?? emptyResponsibleAdult()), relationship_type: event.target.value } }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal">{responsibleRelationshipOptions.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            {context.responsible_adult?.relationship_type === "OTHER" && <label className="text-sm font-bold md:col-span-2">Describe la relación<input value={context.responsible_adult?.relationship_other ?? ""} onChange={(event) => setContext((current) => ({ ...current, responsible_adult: { ...(current.responsible_adult ?? emptyResponsibleAdult()), relationship_other: event.target.value } }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>}
            <label className="text-sm font-bold">Correo<input type="email" value={context.responsible_adult?.email ?? ""} onChange={(event) => setContext((current) => ({ ...current, responsible_adult: { ...(current.responsible_adult ?? emptyResponsibleAdult()), email: event.target.value } }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>
            <label className="text-sm font-bold">Teléfono<input value={context.responsible_adult?.phone ?? ""} onChange={(event) => setContext((current) => ({ ...current, responsible_adult: { ...(current.responsible_adult ?? emptyResponsibleAdult()), phone: event.target.value } }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>
            <label className="text-sm font-bold">Participación del menor<select value={context.minor_participation_status ?? "NOT_APPLICABLE"} onChange={(event) => setContext((current) => ({ ...current, minor_participation_status: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal">{minorParticipationOptions.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <label className="text-sm font-bold">Observación<input value={context.minor_participation_observation ?? ""} onChange={(event) => setContext((current) => ({ ...current, minor_participation_observation: event.target.value || null }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>
            <label className="flex items-start gap-2 rounded-xl bg-white p-3 text-sm font-bold md:col-span-2"><input type="checkbox" checked={Boolean(context.responsible_adult?.identity_verified)} onChange={(event) => setContext((current) => ({ ...current, responsible_adult: { ...(current.responsible_adult ?? emptyResponsibleAdult()), identity_verified: event.target.checked } }))} />La clínica verificó la identidad del adulto responsable antes de preparar el consentimiento.</label>
          </div>}
        </section>
        <div className="flex justify-end gap-2 md:col-span-2"><button type="button" onClick={() => { setCreating(false); setEditingInstance(null); }} className="rounded-xl border px-4 py-2.5 text-sm font-bold">Cancelar</button><button type="button" disabled={busy || !context.site_id || !context.dentist_profile_id} onClick={editingInstance ? saveDraftContext : searchTemplates} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">{editingInstance ? "Guardar cambios" : "Buscar plantillas"}</button></div>
      </div>}
      {step === 2 && <div className="space-y-3">{candidates.length === 0 ? <Alert tone="warning">No hay plantillas publicadas aplicables. Puedes ajustar el contexto o configurar una plantilla compatible.</Alert> : <><label className="block text-sm font-bold">Buscar entre plantillas compatibles<input type="search" value={candidateQuery} onChange={(event) => setCandidateQuery(event.target.value)} placeholder="Nombre, título o tipo" className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label>{visibleCandidates.length === 0 && <Alert tone="info">No hay coincidencias para esta búsqueda. Las plantillas compatibles siguen disponibles al limpiar el filtro.</Alert>}{visibleCandidates.map((item) => <label key={item.version_id} className="flex gap-3 rounded-xl border border-slate-200 p-4"><input type="checkbox" checked={selectedVersions.includes(item.version_id)} onChange={(event) => setSelectedVersions((current) => event.target.checked ? [...current, item.version_id] : current.filter((id) => id !== item.version_id))} /><span className="min-w-0"><strong className="block text-slate-950">{item.title}</strong><span className="block text-sm text-slate-500">{item.template_name} · versión {item.version_number} · {item.country_code} · {item.signer_policy}</span><span className="mt-1 block text-xs font-bold text-emerald-700">{item.applicability_reason_codes.includes("GENERAL_TEMPLATE") ? "Aplica como plantilla general" : item.applicability_reasons.join(" · ")}</span>{item.missing_variable_labels.length > 0 && <span className="mt-2 block text-xs text-amber-700">Datos faltantes: {item.missing_variable_labels.join(", ")}</span>}</span></label>)}</>}<div className="flex justify-end gap-2"><button type="button" onClick={() => setStep(1)} className="rounded-xl border px-4 py-2.5 text-sm font-bold">Atrás</button><button type="button" disabled={!selectedVersions.length} onClick={() => setStep(3)} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">Revisar documentos</button></div></div>}
      {step === 3 && <div className="space-y-4"><Alert tone="warning">Documento preparado para revisión profesional. Todavía no ha sido enviado ni firmado.</Alert>{candidates.filter((item) => selectedVersions.includes(item.version_id)).map((item) => <article key={item.version_id} className="rounded-xl border border-slate-200 p-5"><h3 className="mb-3 text-lg font-black">{item.title}</h3><ConsentRestrictedMarkdown content={item.rendered_preview} />{item.missing_variable_labels.length > 0 && <p className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">Antes de confirmar deben completarse: {item.missing_variable_labels.join(", ")}.</p>}</article>)}<div className="flex justify-end gap-2"><button type="button" onClick={() => setStep(2)} className="rounded-xl border px-4 py-2.5 text-sm font-bold">Atrás</button><button type="button" disabled={busy} onClick={createDrafts} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">Crear {selectedVersions.length} borrador{selectedVersions.length === 1 ? "" : "es"}</button></div></div>}
    </section>}

    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white"><table className="min-w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Número</th><th className="p-3">Título</th><th className="p-3">Procedimientos</th><th className="p-3">Profesional y sede</th><th className="p-3">Estado</th><th className="p-3">Fecha</th></tr></thead><tbody>{instances.map((item) => <tr key={item.id} onClick={() => void openInstance(item)} className="cursor-pointer border-t hover:bg-emerald-50"><td className="p-3 font-black">{item.visible_number}</td><td className="p-3">{item.display_title}<span className="block text-xs text-slate-500">Plantilla v{item.template_version_number}</span></td><td className="p-3">{item.procedures.map((row) => row.name).join(", ") || "Sin procedimiento"}</td><td className="p-3">{snapshotLabel(item, "professional", "full_name")}<span className="block text-xs text-slate-500">{snapshotLabel(item, "site", "name")}</span></td><td className="p-3"><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold">{instanceStatusLabel(item)}</span></td><td className="p-3">{new Date(item.clinical_date + "T00:00:00").toLocaleDateString()}</td></tr>)}</tbody></table>{instances.length === 0 && <p className="p-8 text-center text-sm text-slate-500">Este paciente todavía no tiene consentimientos preparados.</p>}</div>

    {selected && <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between"><div><p className="text-xs font-black uppercase text-emerald-700">{selected.visible_number}</p><h3 className="text-xl font-black">{selected.display_title}</h3><p className="text-sm text-slate-500">{instanceStatusLabel(selected)} · versión {selected.template_version_number}</p></div><button type="button" onClick={() => setSelected(null)} aria-label="Cerrar detalle" className="h-9 w-9 rounded-lg border">×</button></div>{selected.is_test_document&&selected.test_notice&&<p role="alert" className="mt-4 rounded-xl border-2 border-red-700 bg-red-50 p-3 text-center text-sm font-black text-red-800">{selected.test_notice}</p>}{!selected.acceptance_compatible&&<Alert tone="warning">{selected.acceptance_block_message} <button type="button" onClick={beginCreate} className="mt-2 block font-black underline">Crear nueva instancia de consentimiento</button></Alert>}{selected.missing_variable_labels.length > 0 && <Alert tone="warning">Datos faltantes: {selected.missing_variable_labels.join(", ")}. Corrige los datos maestros y actualiza el contexto del borrador.</Alert>}{selected.status === "PENDING_SIGNATURE" && selected.completion_channel !== "PAPER" && <Alert tone="info">Esperando la firma del paciente. Dentia actualizará este estado automáticamente mientras mantengas esta ficha abierta.</Alert>}<div className="mt-4 grid gap-3 rounded-xl border border-emerald-100 bg-emerald-50 p-4 text-sm md:grid-cols-3"><div><span className="block text-xs font-black uppercase text-emerald-700">Firmante</span><strong>{selected.signer_actor_type === "RESPONSIBLE_ADULT" ? "Adulto responsable" : "Paciente adulto"}</strong></div><div><span className="block text-xs font-black uppercase text-emerald-700">Nombre</span><strong>{selected.signer_name ?? "No registrado"}</strong></div><div><span className="block text-xs font-black uppercase text-emerald-700">Correo</span><strong>{selected.signer_email_masked ?? "No registrado"}</strong></div>{selected.responsible_adult && <div className="md:col-span-3 text-xs text-slate-600">Relación: {selected.responsible_adult.relationship_label ?? responsibleRelationshipLabel(selected.responsible_adult.relationship_type, selected.responsible_adult.relationship_other)}. Teléfono: {selected.responsible_adult.phone ?? "No registrado"}.</div>}</div><div className="my-5 rounded-xl border border-slate-200 p-5"><ConsentRestrictedMarkdown content={selected.rendered_content ?? ""} /></div><div className="flex flex-wrap gap-2">{selected.status === "DRAFT" && canEdit && <button type="button" disabled={busy} onClick={() => beginEdit(selected)} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-black text-slate-700">Editar contexto</button>}{selected.status === "DRAFT" && canReview && <label className="mr-auto flex max-w-xl items-start gap-2 rounded-xl bg-emerald-50 p-3 text-sm"><input type="checkbox" checked={reviewed} onChange={(event) => setReviewed(event.target.checked)} /><span>Confirmo que revisé el contenido y que corresponde al procedimiento propuesto. Después de continuar, el contenido quedará inmutable.</span></label>}{selected.status === "DRAFT" && canReview && <button type="button" disabled={busy || !reviewed || selected.missing_variables.length > 0} onClick={confirm} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">Confirmar revisión profesional</button>}{!["VOIDED","SIGNED"].includes(selected.status) && canVoid && <button type="button" disabled={busy} onClick={voidCurrent} className="rounded-xl border border-red-200 px-4 py-2.5 text-sm font-black text-red-700">Anular administrativamente</button>}</div>{["READY_FOR_REVIEW","PENDING_SIGNATURE"].includes(selected.status) && selected.completion_channel !== "PAPER" && <ConsentAccessPanel instanceId={selected.id} canIssue={canIssueAccess} canRead={canReadAccess} canRevoke={canRevokeAccess} canReissue={canReissueAccess} canManageClarifications={canManageClarifications} canViewAudit={canViewAccessAudit} />}{(["READY_FOR_REVIEW","PENDING_SIGNATURE"].includes(selected.status) || (selected.status === "SIGNED" && selected.completion_channel === "PAPER")) && <ConsentPaperPanel instanceId={selected.id} channel={selected.completion_channel} canRead={canReadPaper} canPrepare={canPreparePaper} canRecord={canRecordPaper} canUpload={canUploadPaper} canFinalize={canFinalizePaper} onChanged={refreshConsentState} />}{selected.status==="SIGNED"&&selected.completion_channel!=="PAPER"&&<ConsentAcceptancePanel instanceId={selected.id} canRead={canReadAcceptance} canDownload={canDownloadFinal} canResend={canResendCopy}/>} {canAudit && audit.length > 0 && <details className="mt-5"><summary className="cursor-pointer text-sm font-black">Auditoría</summary><div className="mt-2 space-y-2">{audit.map((item) => <p key={item.id} className="rounded-lg bg-slate-50 p-2 text-xs">{new Date(item.occurred_at).toLocaleString()} · {item.action}</p>)}</div></details>}</section>}
  </div>;
}
