"use client";

import { useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { ApiError } from "@/services/apiClient";
import {
  createOrthodonticRecord,
  createOrthodonticRecordVersion,
  finalizeOrthodonticRecordVersion,
  getOrthodonticRecord,
  updateOrthodonticRecordVersion,
} from "@/services/orthodonticRecordService";
import type {
  OrthodonticRecord,
  OrthodonticRecordField,
  OrthodonticRecordVersion,
} from "@/types/orthodonticRecord";

interface Props {
  caseId: string;
  caseStatus: string;
  label: string;
  accessAllowed: boolean;
  onDirtyChange?: (dirty: boolean) => void;
}

function errorMessage(error: unknown) {
  return error instanceof ApiError
    ? error.detail ?? error.message
    : "No fue posible completar la acción.";
}

function isMissing(error: unknown) {
  return error instanceof ApiError && error.status === 404 &&
    typeof error.payload === "object" && error.payload !== null &&
    "code" in error.payload && error.payload.code === "ORTHODONTIC_RECORD_NOT_FOUND";
}

function formattedDate(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value))
    : "Borrador";
}

export function OrthodonticClinicalRecordPanel({ caseId, caseStatus, label, accessAllowed, onDirtyChange }: Props) {
  const [record, setRecord] = useState<OrthodonticRecord | null>(null);
  const [missing, setMissing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [section, setSection] = useState<string>("general");
  const [content, setContent] = useState<Record<string, unknown>>({});
  const [baseline, setBaseline] = useState("{}");
  const dirty = JSON.stringify(content) !== baseline;

  function accept(next: OrthodonticRecord, success?: string) {
    setRecord(next);
    setMissing(false);
    const nextContent = next.current_version?.content ?? {};
    setContent(nextContent);
    setBaseline(JSON.stringify(nextContent));
    setMessage(success ?? null);
  }

  useEffect(() => {
    let active = true;
    setLoading(true); setError(null); setMessage(null); setMissing(false);
    void getOrthodonticRecord(caseId)
      .then((loaded) => { if (active) accept(loaded); })
      .catch((caught) => {
        if (!active) return;
        if (isMissing(caught)) { setMissing(true); setRecord(null); setContent({}); setBaseline("{}"); }
        else setError(errorMessage(caught));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [caseId]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  useEffect(() => {
    onDirtyChange?.(dirty);
    return () => onDirtyChange?.(false);
  }, [dirty, onDirtyChange]);

  const version = record?.current_version ?? null;
  const editable = Boolean(record?.can_edit && version?.status === "DRAFT");
  const fields = useMemo(
    () => record?.schema.fields.filter((field) => field.section === section) ?? [],
    [record, section],
  );

  async function run(action: () => Promise<{ message: string; record: OrthodonticRecord }>) {
    setBusy(true); setError(null); setMessage(null);
    try { const result = await action(); accept(result.record, result.message); }
    catch (caught) { setError(errorMessage(caught)); }
    finally { setBusy(false); }
  }

  async function selectVersion(versionId: string) {
    if (dirty && !window.confirm("Hay cambios sin guardar. ¿Deseas descartarlos?")) return;
    setLoading(true); setError(null);
    try { accept(await getOrthodonticRecord(caseId, versionId)); }
    catch (caught) { setError(errorMessage(caught)); }
    finally { setLoading(false); }
  }

  if (loading) return <section className="rounded-2xl border bg-white p-8" aria-busy="true"><p className="text-sm text-slate-500">Cargando {label.toLowerCase()}…</p></section>;

  if (missing) return <section className="rounded-2xl border bg-white p-8 text-center">
    <h2 className="text-xl font-black">{label}</h2>
    <p className="mt-2 text-sm text-slate-500">Este caso aún no tiene {label.toLowerCase()}.</p>
    {caseStatus === "ACTIVE" && accessAllowed
      ? <button type="button" disabled={busy} onClick={() => void run(() => createOrthodonticRecord(caseId))} className="mt-5 rounded-xl bg-green-700 px-5 py-3 font-bold text-white disabled:opacity-50">Crear ficha</button>
      : <p className="mt-4 text-sm font-semibold text-amber-700">{accessAllowed ? "Activa el caso para crearla." : "Tu acceso de Ortodoncia ya no está habilitado."}</p>}
    {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
  </section>;

  if (!record || !version) return <section className="rounded-2xl border bg-white p-8"><Alert tone="error">{error ?? "No fue posible cargar la historia."}</Alert></section>;

  return <div className="space-y-4">
    <section className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div><h2 className="text-xl font-black">{record.label}</h2><p className="mt-1 text-sm text-slate-500">Versión {version.version_number} · {version.status === "DRAFT" ? "Borrador · Versión actual" : `Finalizada ${formattedDate(version.finalized_at)}${record.versions[0]?.id === version.id ? " · Versión actual" : " · Histórica"}`}</p></div>
        <label className="text-sm font-bold">Versión
          <select value={version.id} onChange={(event) => void selectVersion(event.target.value)} className="ml-2 min-h-10 rounded-xl border bg-white px-3 font-normal">
            {record.versions.map((item) => <option key={item.id} value={item.id}>v{item.version_number} · {item.status === "DRAFT" ? "Borrador" : formattedDate(item.finalized_at)}</option>)}
          </select>
        </label>
      </div>
      {record.read_only_reason && <p className="mt-3 rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-800">{record.read_only_reason}</p>}
      {version.integrity_status === "FAIL" && <div className="mt-3"><Alert tone="error">No fue posible verificar la integridad de esta versión finalizada.</Alert></div>}
      {message && <div className="mt-4"><Alert>{message}</Alert></div>}
      {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
    </section>

    <div className="grid gap-4 lg:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="rounded-2xl border bg-white p-3">
        <label className="block text-sm font-bold lg:hidden">Sección
          <select value={section} onChange={(event) => setSection(event.target.value)} className="mt-1 min-h-11 w-full rounded-xl border bg-white px-3 font-normal">
            {record.schema.sections.map((item) => <option key={item.key} value={item.key}>{item.order}. {item.label}</option>)}
          </select>
        </label>
        <nav aria-label="Secciones de la historia de Ortodoncia" className="hidden space-y-1 lg:block">
          {record.schema.sections.map((item) => <button key={item.key} type="button" onClick={() => setSection(item.key)} className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm font-bold ${section === item.key ? "bg-green-700 text-white" : "text-slate-700 hover:bg-slate-50"}`}><span>{item.order}. {item.label}</span><ProgressDot value={version.section_progress[item.key]} /></button>)}
        </nav>
      </aside>

      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <div className="mb-5"><p className="text-xs font-bold uppercase tracking-wide text-green-700">Sección {record.schema.sections.find((item) => item.key === section)?.order}</p><h3 className="mt-1 text-lg font-black">{record.schema.sections.find((item) => item.key === section)?.label}</h3><p className="mt-1 text-sm text-slate-500">Todos los campos son opcionales. Registra únicamente lo clínicamente evaluado.</p></div>
        <div className="grid gap-5 md:grid-cols-2">
          {fields.map((field) => <Field key={field.key} field={field} value={content[field.key]} disabled={!editable || busy} onChange={(value) => setContent((current) => {
            const next = { ...current };
            if (value === null || value === "" || (Array.isArray(value) && value.length === 0)) delete next[field.key];
            else next[field.key] = value;
            return next;
          })} />)}
        </div>
        {editable && <div className="mt-6 flex flex-wrap gap-2 border-t pt-4">
          <button type="button" disabled={busy || !dirty} onClick={() => void run(() => updateOrthodonticRecordVersion(caseId, version.id, version.row_version, content))} className="rounded-xl bg-green-700 px-4 py-2 font-bold text-white disabled:opacity-40">Guardar borrador</button>
          <button type="button" disabled={busy || dirty} title={dirty ? "Guarda primero los cambios pendientes" : undefined} onClick={() => { if (window.confirm("Al finalizar, esta versión quedará inmutable. ¿Deseas continuar?")) void run(() => finalizeOrthodonticRecordVersion(caseId, version.id, version.row_version)); }} className="rounded-xl border px-4 py-2 font-bold disabled:opacity-40">Finalizar versión</button>
          {dirty && <span className="self-center text-sm font-semibold text-amber-700">Cambios sin guardar</span>}
        </div>}
        {!editable && version.status === "FINALIZED" && record.can_edit && !record.versions.some((item) => item.status === "DRAFT") && <button type="button" disabled={busy} onClick={() => void run(() => createOrthodonticRecordVersion(caseId, version.id))} className="mt-6 rounded-xl bg-green-700 px-4 py-2 font-bold text-white disabled:opacity-40">Crear nueva versión</button>}
      </section>
    </div>
  </div>;
}

function ProgressDot({ value }: { value: OrthodonticRecordVersion["section_progress"][string] | undefined }) {
  const label = value === "COMPLETED" ? "Completa" : value === "IN_PROGRESS" ? "En progreso" : "Sin iniciar";
  return <span title={label} aria-label={label} className={`h-2.5 w-2.5 rounded-full ${value === "COMPLETED" ? "bg-emerald-300" : value === "IN_PROGRESS" ? "bg-amber-300" : "bg-slate-300"}`} />;
}

function Field({ field, value, disabled, onChange }: { field: OrthodonticRecordField; value: unknown; disabled: boolean; onChange: (value: unknown) => void }) {
  const hint = field.clinical_pending_flag ? <span className="mt-1 block text-xs font-normal text-slate-500">Registro abierto; la definición clínica de este campo está pendiente de homologación.</span> : null;
  if (field.type === "text") return <label className="block text-sm font-bold md:col-span-2">{field.label}<textarea disabled={disabled} value={typeof value === "string" ? value : ""} maxLength={field.max_length ?? undefined} onChange={(event) => onChange(event.target.value)} rows={3} className="mt-1 w-full rounded-xl border p-3 font-normal disabled:bg-slate-50" />{hint}</label>;
  if (field.type === "boolean") return <label className="block text-sm font-bold">{field.label}<select disabled={disabled} value={typeof value === "boolean" ? String(value) : ""} onChange={(event) => onChange(event.target.value === "" ? null : event.target.value === "true")} className="mt-1 min-h-11 w-full rounded-xl border bg-white px-3 font-normal disabled:bg-slate-50"><option value="">Sin registrar</option><option value="true">Sí</option><option value="false">No</option></select>{hint}</label>;
  if (field.type === "single") return <label className="block text-sm font-bold">{field.label}<select disabled={disabled} value={typeof value === "string" ? value : ""} onChange={(event) => onChange(event.target.value || null)} className="mt-1 min-h-11 w-full rounded-xl border bg-white px-3 font-normal disabled:bg-slate-50"><option value="">Sin registrar</option>{field.options.map((option) => <option key={option.code} value={option.code}>{option.label}</option>)}</select>{hint}</label>;
  const selected = Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
  return <fieldset className="rounded-xl border p-3"><legend className="px-1 text-sm font-bold">{field.label}</legend><div className="space-y-2">{field.options.map((option) => <label key={option.code} className="flex items-start gap-2 text-sm"><input type="checkbox" disabled={disabled} checked={selected.includes(option.code)} onChange={(event) => onChange(event.target.checked ? [...selected, option.code] : selected.filter((item) => item !== option.code))} className="mt-0.5" /><span>{option.label}</span></label>)}</div>{hint}</fieldset>;
}
