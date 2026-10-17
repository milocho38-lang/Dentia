"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { deactivateClinicalFile, downloadClinicalFile, listClinicalFiles, reconcileClinicalFileUpload, uploadClinicalFile } from "@/services/clinicalFileService";
import type { ClinicalFile } from "@/types/clinicalFile";
import { canApplyUploadResult } from "@/lib/clinicalFileUploadState.mjs";

const labels: Record<string, string> = { RADIOGRAPH: "Radiografía", EXAM: "Examen", PHOTOGRAPH: "Fotografía", DOCUMENT: "Documento", OTHER: "Otro" };

export function PatientFilesWorkspace({ patientId, canView, canCreate, canManage }: { patientId: string; canView: boolean; canCreate: boolean; canManage: boolean }) {
  const [items, setItems] = useState<ClinicalFile[]>([]);
  const [selected, setSelected] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [type, setType] = useState("RADIOGRAPH");
  const input = useRef<HTMLInputElement>(null);
  const upload = useRef<AbortController | null>(null);
  const generation = useRef(0);

  async function refresh() {
    if (!canView) return;
    const currentGeneration = generation.current;
    try { const result = await listClinicalFiles(patientId); if (currentGeneration === generation.current) setItems(result.items); }
    catch { if (currentGeneration === generation.current) setMessage("No fue posible cargar los archivos clínicos."); }
  }
  useEffect(() => {
    generation.current += 1;
    const currentGeneration = generation.current;
    let current = true;
    upload.current?.abort(); upload.current = null;
    setItems([]); setSelected(null); setMessage(null); setBusy(false);
    if (input.current) input.current.value = "";
    if (canView) listClinicalFiles(patientId).then((r) => current && currentGeneration === generation.current && setItems(r.items)).catch(() => current && currentGeneration === generation.current && setMessage("No fue posible cargar los archivos clínicos."));
    return () => { current = false; upload.current?.abort(); };
  }, [patientId, canView]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selected || busy) return;
    const controller = new AbortController();
    const currentGeneration = generation.current;
    const uploadPatientId = patientId;
    const idempotencyKey = crypto.randomUUID();
    upload.current = controller;
    setBusy(true); setMessage(null);
    const data = new FormData(); data.set("archivo", selected); data.set("tipo", type); data.set("categoria", "GENERAL"); data.set("idempotency_key", idempotencyKey);
    try {
      await uploadClinicalFile(patientId, data, controller.signal);
      if (!canApplyUploadResult(currentGeneration, generation.current, uploadPatientId, patientId)) return;
      setSelected(null); if (input.current) input.current.value = "";
      setMessage("Archivo cargado de forma segura."); await refresh();
    } catch (error) {
      if (!canApplyUploadResult(currentGeneration, generation.current, uploadPatientId, patientId)) return;
      if (controller.signal.aborted) {
        try {
          await reconcileClinicalFileUpload(patientId, idempotencyKey);
          const result = await listClinicalFiles(patientId);
          if (!canApplyUploadResult(currentGeneration, generation.current, uploadPatientId, patientId)) return;
          setItems(result.items); setMessage("La carga terminó en el servidor antes de cancelarse y fue reconciliada.");
        } catch { if (canApplyUploadResult(currentGeneration, generation.current, uploadPatientId, patientId)) setMessage("No existe una carga confirmada para la solicitud cancelada."); }
      } else setMessage(error instanceof Error ? error.message : "No fue posible cargar el archivo.");
    } finally { if (currentGeneration === generation.current) { if (upload.current === controller) upload.current = null; setBusy(false); } }
  }

  async function download(item: ClinicalFile) {
    try {
      const blob = await downloadClinicalFile(item.id); const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = item.original_name; anchor.click(); URL.revokeObjectURL(url);
    } catch { setMessage("No fue posible descargar el archivo."); }
  }

  async function deactivate(item: ClinicalFile) {
    const reason = window.prompt("Motivo para retirar este archivo del expediente visible:");
    if (!reason || reason.trim().length < 5) return;
    try { await deactivateClinicalFile(item.id, reason); setMessage("Archivo retirado. Se conservó para auditoría."); await refresh(); }
    catch { setMessage("No fue posible retirar el archivo."); }
  }

  if (!canView) return <p className="text-sm text-slate-600">No tienes permiso para consultar archivos clínicos.</p>;
  return <section className="space-y-5">
    <div><h2 className="text-xl font-semibold text-slate-900">Archivos clínicos</h2><p className="text-sm text-slate-600">Radiografías, exámenes y documentos privados del paciente.</p></div>
    {message && <div role="status" className="rounded-lg bg-slate-100 px-4 py-3 text-sm">{message}</div>}
    {canCreate && <form onSubmit={submit} className="grid gap-3 rounded-xl border border-slate-200 p-4 md:grid-cols-[180px_1fr_auto]">
      <select value={type} onChange={(e) => setType(e.target.value)} disabled={busy} className="rounded-lg border p-2"><option value="RADIOGRAPH">Radiografía</option><option value="EXAM">Examen</option><option value="PHOTOGRAPH">Fotografía</option><option value="DOCUMENT">Documento</option><option value="OTHER">Otro</option></select>
      <input ref={input} type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" disabled={busy} onChange={(e) => setSelected(e.target.files?.[0] ?? null)} className="rounded-lg border p-2" />
      <div className="flex gap-2"><button type="submit" disabled={!selected || busy} className="rounded-lg bg-dentia-primary px-4 py-2 text-white disabled:opacity-50">{busy ? "Cargando…" : "Cargar"}</button>{busy && <button type="button" onClick={() => upload.current?.abort()} className="rounded-lg border px-3 py-2">Cancelar</button>}</div>
      <p className="text-xs text-slate-500 md:col-span-3">Máximo 25 MB. Formatos: PDF, JPEG, PNG y WebP. Se valida estructura y contenido; esto no sustituye un análisis antimalware.</p>
    </form>}
    <div className="divide-y rounded-xl border border-slate-200">{items.length === 0 ? <p className="p-5 text-sm text-slate-500">No hay archivos clínicos cargados.</p> : items.map((item) => <div key={item.id} className="flex items-center justify-between gap-3 p-4"><div><p className="font-medium text-slate-900">{item.original_name}</p><p className="text-xs text-slate-500">{labels[item.file_type] ?? item.file_type} · {(item.size_bytes / 1024 / 1024).toFixed(2)} MB · {new Date(item.uploaded_at).toLocaleDateString("es-CO")}</p></div><div className="flex gap-2"><button type="button" onClick={() => download(item)} className="rounded-lg border px-3 py-2 text-sm">Descargar</button>{canManage && <button type="button" onClick={() => deactivate(item)} className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700">Retirar</button>}</div></div>)}</div>
  </section>;
}
