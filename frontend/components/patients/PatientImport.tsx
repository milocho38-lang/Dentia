"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { ApiError } from "@/services/apiClient";
import {
  confirmDentalinkImport,
  createDentalinkSource,
  listDentalinkSources,
  previewDentalinkImport,
} from "@/services/patientImportService";
import { buildPatientImportCsv } from "@/lib/patientImportCsv.mjs";
import type {
  PatientImportPreview,
  PatientImportResult,
  PatientImportSource,
  PatientImportStatus,
} from "@/types/patientImport";


const STATUS_LABELS: Record<PatientImportStatus, string> = {
  READY: "Listo",
  INCOMPLETE: "Incompleto importable",
  REVIEW: "Requiere revisión",
  REJECTED: "Rechazado",
  ALREADY_IMPORTED: "Ya importado",
};

function downloadMinimizedReport(result: PatientImportResult) {
  const csv = buildPatientImportCsv([
    ["fila", "id_origen", "estado", "motivos", "campos_pendientes"],
    ...result.rows.map((row) => [
      String(row.row_number),
      row.source_patient_id,
      row.status,
      row.issues.join(" | "),
      row.pending_fields.join(" | "),
    ]),
  ]);
  const url = URL.createObjectURL(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `resultado-importacion-${result.batch_id}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function PatientImport() {
  const [file, setFile] = useState<File | null>(null);
  const [sources, setSources] = useState<PatientImportSource[]>([]);
  const [sourceId, setSourceId] = useState("");
  const [creatingSource, setCreatingSource] = useState(false);
  const [sourceLabel, setSourceLabel] = useState("");
  const [preview, setPreview] = useState<PatientImportPreview | null>(null);
  const [result, setResult] = useState<PatientImportResult | null>(null);
  const [filter, setFilter] = useState<PatientImportStatus | "">("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDentalinkSources()
      .then((items) => {
        setSources(items);
        if (items.length === 1) setSourceId(items[0].id);
      })
      .catch(() => setError("No fue posible cargar los orígenes Dentalink."));
  }, []);

  const visibleRows = useMemo(
    () => preview?.rows.filter((row) => !filter || row.status === filter) ?? [],
    [filter, preview],
  );
  const importable = (preview?.counts.ready ?? 0) + (preview?.counts.incomplete ?? 0);

  async function runPreview(event: FormEvent) {
    event.preventDefault();
    if (!file || !sourceId) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setPreview(await previewDentalinkImport(file, sourceId));
    } catch (caught) {
      setPreview(null);
      setError(
        caught instanceof ApiError
          ? caught.detail ?? caught.message
          : "No fue posible analizar el Excel.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!file || !preview) return;
    setBusy(true);
    setError(null);
    try {
      const response = await confirmDentalinkImport(
        file,
        preview.source.id,
        preview.preview_token,
      );
      setResult(response);
      setPreview(null);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.detail ?? caught.message
          : "No fue posible confirmar la importación.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function createSource() {
    if (sourceLabel.trim().length < 3) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createDentalinkSource(sourceLabel.trim());
      setSources((current) => [...current, created]);
      setSourceId(created.id);
      setSourceLabel("");
      setCreatingSource(false);
      setPreview(null);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.detail ?? caught.message
          : "No fue posible crear el origen Dentalink.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <Link href="/pacientes" className="text-sm font-bold text-green-700 hover:underline">
        ← Volver a pacientes
      </Link>
      <h1 className="mt-5 text-3xl font-bold text-slate-950">Importar pacientes de Dentalink</h1>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
        Revisa el archivo antes de confirmar. Dentia no sobrescribe pacientes existentes,
        no importa observaciones sensibles y separa los conflictos para revisión.
      </p>

      <form onSubmit={runPreview} className="mt-7 grid gap-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:grid-cols-2">
        <div>
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">Origen Dentalink registrado</span>
            <select
              value={sourceId}
              onChange={(event) => {
                setSourceId(event.target.value);
                setPreview(null);
              }}
              required
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4"
            >
              <option value="">Selecciona un origen</option>
              {sources.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.label} · {source.code}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => setCreatingSource((current) => !current)}
            className="mt-2 text-sm font-bold text-green-700 underline"
          >
            {creatingSource ? "Cancelar alta" : "Registrar otra instancia Dentalink"}
          </button>
          {creatingSource && (
            <div className="mt-3 rounded-xl border border-amber-300 bg-amber-50 p-4">
              <p className="text-sm font-bold text-amber-950">Crea otro origen solo si es una instalación Dentalink distinta.</p>
              <p className="mt-1 text-xs leading-5 text-amber-900">Una etiqueta equivocada crea una identidad separada y puede impedir detectar recargas sin RUT.</p>
              <input
                value={sourceLabel}
                onChange={(event) => setSourceLabel(event.target.value)}
                placeholder="Etiqueta humana, ej. Dentalink sede adquirida"
                minLength={3}
                maxLength={100}
                className="mt-3 min-h-11 w-full rounded-lg border border-amber-300 px-3"
              />
              <button type="button" disabled={busy || sourceLabel.trim().length < 3} onClick={createSource} className="mt-3 rounded-lg bg-amber-800 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">
                Registrar origen separado
              </button>
            </div>
          )}
        </div>
        <label>
          <span className="mb-2 block text-sm font-bold text-slate-700">Archivo XLSX</span>
          <input
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            required
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setPreview(null);
            }}
            className="block min-h-12 w-full rounded-xl border border-slate-300 px-3 py-2"
          />
        </label>
        <button disabled={busy || !file || !sourceId} className="min-h-12 rounded-xl bg-dentia-primary px-5 font-bold text-white disabled:opacity-50 md:col-span-2">
          {busy ? "Analizando…" : "Generar vista previa"}
        </button>
      </form>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      {busy && <div className="mt-6 flex items-center gap-3 text-slate-500"><Spinner className="h-5 w-5" />Procesando localmente en Dentia…</div>}

      {result && (
        <section className="mt-7 rounded-2xl border border-green-200 bg-green-50 p-6">
          <h2 className="text-xl font-bold text-green-950">Importación terminada</h2>
          <p className="mt-2 text-sm text-green-900">
            {result.imported} importados · {result.skipped_already_imported} ya importados · {result.skipped_review} para revisión · {result.rejected} rechazados.
          </p>
          <button onClick={() => downloadMinimizedReport(result)} className="mt-4 rounded-xl border border-green-700 px-4 py-2 text-sm font-bold text-green-800">
            Descargar reporte minimizado
          </button>
        </section>
      )}

      {preview && (
        <section className="mt-7 space-y-5">
          <div className="grid gap-3 sm:grid-cols-5">
            {(
              [
                ["READY", preview.counts.ready],
                ["INCOMPLETE", preview.counts.incomplete],
                ["REVIEW", preview.counts.review],
                ["REJECTED", preview.counts.rejected],
                ["ALREADY_IMPORTED", preview.counts.already_imported],
              ] as [PatientImportStatus, number][]
            ).map(([status, count]) => (
              <button key={status} type="button" onClick={() => setFilter(filter === status ? "" : status)} className="rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm">
                <span className="block text-2xl font-black text-slate-900">{count}</span>
                <span className="text-xs font-bold text-slate-500">{STATUS_LABELS[status]}</span>
              </button>
            ))}
          </div>

          {(preview.extra_headers.length > 0 || preview.missing_headers.length > 0) && (
            <Alert tone="warning">
              {preview.extra_headers.length > 0 && <p>Columnas adicionales no importadas: {preview.extra_headers.join(", ")}.</p>}
              {preview.missing_headers.length > 0 && <p>Columnas opcionales ausentes: {preview.missing_headers.join(", ")}.</p>}
            </Alert>
          )}

          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50"><tr>{["Fila", "# Paciente", "Paciente", "Estado", "Detalle", "Pendientes"].map((item) => <th key={item} className="px-4 py-3 text-left text-xs font-bold uppercase text-slate-500">{item}</th>)}</tr></thead>
              <tbody className="divide-y divide-slate-100">
                {visibleRows.slice(0, 500).map((row) => (
                  <tr key={`${row.row_number}-${row.source_patient_id}`}>
                    <td className="px-4 py-3">{row.row_number}</td>
                    <td className="px-4 py-3 font-mono text-xs">{row.source_patient_id}</td>
                    <td className="px-4 py-3 font-semibold">{row.display_name}</td>
                    <td className="px-4 py-3">{STATUS_LABELS[row.status]}</td>
                    <td className="max-w-md px-4 py-3 text-slate-600">{row.issues.join(" ") || "—"}</td>
                    <td className="px-4 py-3 text-slate-500">{row.pending_fields.join(", ") || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {visibleRows.length > 500 && <p className="text-sm text-slate-500">Se muestran las primeras 500 filas del filtro.</p>}

          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6">
            <h2 className="font-bold text-amber-950">Confirmar importación</h2>
            <p className="mt-2 text-sm leading-6 text-amber-900">
              Se importarán {importable} filas listas o incompletas. Las filas en revisión,
              rechazadas o ya importadas se conservarán únicamente en el resultado.
            </p>
            <button type="button" disabled={busy || importable === 0} onClick={confirm} className="mt-4 min-h-11 rounded-xl bg-amber-800 px-5 font-bold text-white disabled:opacity-50">
              Confirmar {importable} pacientes
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
