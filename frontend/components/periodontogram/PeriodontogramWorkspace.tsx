"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { RapidPeriodontalEditor } from "@/components/periodontogram/RapidPeriodontalEditor";
import { useAuth } from "@/hooks/useAuth";
import {
  findReplacingVersion,
  historicalPeriodontalExam,
  sortedPeriodontalVersions,
} from "@/lib/periodontalVersionHistory";
import { ApiError } from "@/services/apiClient";
import {
  correctPeriodontalExam,
  createPeriodontalExam,
  finalizePeriodontalExam,
  getPeriodontalExam,
  linkPeriodontalEvolution,
  listPeriodontalExams,
  listPeriodontalEvolutionCandidates,
  updatePeriodontalDraft,
} from "@/services/periodontogramService";
import type {
  PeriodontalExam,
  PeriodontalExamHistoryItem,
  PeriodontalEvolutionSummary,
} from "@/types/periodontogram";

function today(timeZone: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone,
  }).formatToParts(new Date());
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeZone: "UTC" }).format(
    new Date(`${value}T00:00:00Z`),
  );
}

function formatDateTime(value: string | null, timeZone?: string) {
  if (!value) return "No disponible";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
  }).format(new Date(value));
}

function evolutionStatus(status: PeriodontalEvolutionSummary["status"]) {
  if (status === "SIGNED") return "Firmada";
  if (status === "DRAFT") return "Borrador";
  return "Anulada";
}

function errorMessage(error: unknown) {
  return error instanceof ApiError
    ? error.detail ?? error.message
    : "No fue posible completar la acción.";
}

export function PeriodontogramWorkspace({ patientId }: { patientId: string }) {
  const { hasPermission, user } = useAuth();
  const activeTimezone = user?.sites.find((site) => site.id === user.active_site_id)?.timezone
    ?? "America/Bogota";
  const [items, setItems] = useState<PeriodontalExamHistoryItem[]>([]);
  const [selected, setSelected] = useState<PeriodontalExam | null>(null);
  const [clinicalDate, setClinicalDate] = useState(() => today(activeTimezone));
  const [correctionReason, setCorrectionReason] = useState("");
  const [evolutionCandidates, setEvolutionCandidates] = useState<PeriodontalEvolutionSummary[]>([]);
  const [selectedEvolutionId, setSelectedEvolutionId] = useState("");
  const [showEvolutionLink, setShowEvolutionLink] = useState(false);
  const [loadingEvolutions, setLoadingEvolutions] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [clinicalDirty, setClinicalDirty] = useState(false);
  const [historicalVersionId, setHistoricalVersionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const selectedExamId = selected?.id;
  const displayedExam = selected && historicalVersionId
    ? historicalPeriodontalExam(selected, historicalVersionId) ?? selected
    : selected;
  const isHistorical = Boolean(
    selected && displayedExam && displayedExam.current_version.id !== selected.current_version.id,
  );
  const versions = selected ? sortedPeriodontalVersions(selected) : [];
  const replacingVersion = selected && displayedExam && isHistorical
    ? findReplacingVersion(selected, displayedExam.current_version)
    : null;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listPeriodontalExams(patientId);
      setItems(response.items);
      if (selectedExamId) {
        setSelected(await getPeriodontalExam(selectedExamId));
      }
    } catch (loadError) {
      setError(errorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }, [patientId, selectedExamId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function createExam(event: FormEvent) {
    event.preventDefault();
    if (
      clinicalDirty &&
      !window.confirm("Hay cambios clínicos sin guardar. ¿Deseas crear otro examen y descartar esos cambios locales?")
    ) {
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await createPeriodontalExam(patientId, clinicalDate);
      setSelected(response.exam);
      setHistoricalVersionId(null);
      setClinicalDirty(false);
      setShowEvolutionLink(false);
      setEvolutionCandidates([]);
      setSelectedEvolutionId("");
      setMessage(response.message);
      const history = await listPeriodontalExams(patientId);
      setItems(history.items);
    } catch (createError) {
      setError(errorMessage(createError));
    } finally {
      setSaving(false);
    }
  }

  async function finalizeExam() {
    if (!selected) return;
    if (clinicalDirty) {
      setError("Guarda los cambios clínicos antes de finalizar la versión.");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await finalizePeriodontalExam(selected.id, selected.row_version);
      setSelected(response.exam);
      setHistoricalVersionId(null);
      setMessage(response.message);
      setItems((current) =>
        current.map((item) =>
          item.id === response.exam.id
            ? {
                ...item,
                status: response.exam.status,
                current_version_number: response.exam.current_version.version_number,
              }
            : item,
        ),
      );
    } catch (finalizeError) {
      setError(errorMessage(finalizeError));
    } finally {
      setSaving(false);
    }
  }

  async function startCorrection(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await correctPeriodontalExam(
        selected.id,
        selected.row_version,
        correctionReason,
      );
      setSelected(response.exam);
      setHistoricalVersionId(null);
      setClinicalDirty(false);
      setCorrectionReason("");
      setShowEvolutionLink(false);
      setEvolutionCandidates([]);
      setSelectedEvolutionId("");
      setMessage(response.message);
      setItems((current) =>
        current.map((item) =>
          item.id === response.exam.id
            ? {
                ...item,
                status: response.exam.status,
                current_version_number: response.exam.current_version.version_number,
              }
            : item,
        ),
      );
    } catch (correctionError) {
      setError(errorMessage(correctionError));
    } finally {
      setSaving(false);
    }
  }

  async function openExam(examId: string) {
    if (
      clinicalDirty &&
      !window.confirm("Hay cambios clínicos sin guardar. ¿Deseas abrir otro examen y descartar esos cambios locales?")
    ) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      setSelected(await getPeriodontalExam(examId));
      setHistoricalVersionId(null);
      setClinicalDirty(false);
      setShowEvolutionLink(false);
      setEvolutionCandidates([]);
      setSelectedEvolutionId("");
    } catch (detailError) {
      setError(errorMessage(detailError));
    }
  }

  async function showEvolutionCandidates() {
    if (!selected) return;
    setLoadingEvolutions(true);
    setError(null);
    try {
      const response = await listPeriodontalEvolutionCandidates(selected.id);
      setEvolutionCandidates(response.items);
      setSelectedEvolutionId(response.items[0]?.id ?? "");
      setShowEvolutionLink(true);
    } catch (candidateError) {
      setError(errorMessage(candidateError));
    } finally {
      setLoadingEvolutions(false);
    }
  }

  async function linkEvolution(event: FormEvent) {
    event.preventDefault();
    if (!selected || !selectedEvolutionId) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await linkPeriodontalEvolution(
        selected.id,
        selectedEvolutionId,
        selected.row_version,
      );
      setSelected(response.exam);
      setShowEvolutionLink(false);
      setEvolutionCandidates([]);
      setSelectedEvolutionId("");
      setMessage(response.message);
    } catch (linkError) {
      setError(errorMessage(linkError));
    } finally {
      setSaving(false);
    }
  }

  if (loading && items.length === 0) {
    return (
      <div className="flex items-center justify-center gap-3 rounded-3xl border border-slate-200 bg-white py-16 text-slate-500">
        <Spinner className="h-6 w-6 text-dentia-primary" />
        Cargando periodontogramas…
      </div>
    );
  }

  return (
    <section className="space-y-5" aria-labelledby="periodontogram-title">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-green-700">Salud periodontal</p>
            <h2 id="periodontogram-title" className="mt-1 text-2xl font-black text-slate-950">
              Periodontograma
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Controles independientes con versiones finalizadas inmutables y correcciones trazables.
            </p>
          </div>
          {hasPermission("periodontogram.create") && (
            <form className="flex flex-wrap items-end gap-2" onSubmit={createExam}>
              <label className="text-sm font-semibold text-slate-700">
                Fecha clínica
                <input
                  className="mt-1 block rounded-xl border border-slate-300 px-3 py-2 text-sm"
                  type="date"
                  value={clinicalDate}
                  onChange={(event) => setClinicalDate(event.target.value)}
                  required
                />
              </label>
              <button
                className="rounded-xl bg-green-700 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50"
                type="submit"
                disabled={saving}
              >
                Nuevo periodontograma
              </button>
            </form>
          )}
        </div>
      </div>

      {error && <Alert tone="error">{error}</Alert>}
      {message && <Alert tone="info">{message}</Alert>}

      {items.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center">
          <h3 className="text-lg font-bold text-slate-900">No hay periodontogramas registrados.</h3>
          <p className="mt-2 text-sm text-slate-600">
            Aún no se ha creado un periodontograma para este paciente.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h3 className="font-black text-slate-950">Historial de periodontogramas</h3>
            <p className="mt-1 text-xs text-slate-600">
              Cada fila corresponde a un examen periodontal independiente. Las correcciones se consultan como versiones dentro del examen.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3">Fecha</th>
                  <th className="px-5 py-3">Profesional</th>
                  <th className="px-5 py-3">Sede</th>
                  <th className="px-5 py-3">Estado</th>
                  <th className="px-5 py-3">Versión</th>
                  <th className="px-5 py-3 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="px-5 py-4 font-semibold text-slate-900">{formatDate(item.clinical_date)}</td>
                    <td className="px-5 py-4 text-slate-700">{item.professional_name}</td>
                    <td className="px-5 py-4 text-slate-700">{item.site_name}</td>
                    <td className="px-5 py-4">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${item.status === "FINALIZED" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                        {item.status === "FINALIZED" ? "Finalizado" : "Borrador"}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-slate-700">V{item.current_version_number}</td>
                    <td className="px-5 py-4 text-right">
                      <button
                        className="font-bold text-green-700 hover:underline"
                        type="button"
                        onClick={() => void openExam(item.id)}
                      >
                        {item.status === "DRAFT" ? "Continuar" : "Ver"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selected && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-black text-slate-950">
                Control del {formatDate(selected.clinical_date)}
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                {selected.professional_name} · {selected.site_name} · V{selected.current_version.version_number}
              </p>
            </div>
            <button
              className="text-sm font-bold text-slate-600 hover:text-slate-950"
              type="button"
              onClick={() => {
                if (
                  clinicalDirty &&
                  !window.confirm("Hay cambios clínicos sin guardar. ¿Deseas cerrar el periodontograma?")
                ) {
                  return;
                }
                setSelected(null);
                setHistoricalVersionId(null);
                setClinicalDirty(false);
              }}
            >
              Cerrar
            </button>
          </div>

          {selected.versions.length > 1 && (
            <div className="mt-5 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-end sm:justify-between">
              <label className="text-sm font-bold text-slate-800">
                Versiones del examen · Actual: {selected.current_version.version_number}
                <select
                  className="mt-2 block min-w-64 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800"
                  aria-label="Consultar versión del periodontograma"
                  value={displayedExam?.current_version.id ?? selected.current_version.id}
                  onChange={(event) => {
                    const versionId = event.target.value;
                    if (versionId === selected.current_version.id) {
                      setHistoricalVersionId(null);
                      return;
                    }
                    if (
                      clinicalDirty &&
                      !window.confirm("Hay cambios clínicos sin guardar. ¿Deseas consultar una versión histórica y descartar esos cambios locales?")
                    ) {
                      return;
                    }
                    if (!historicalPeriodontalExam(selected, versionId)) {
                      setError("No fue posible leer el snapshot clínico de esa versión.");
                      return;
                    }
                    setClinicalDirty(false);
                    setError(null);
                    setHistoricalVersionId(versionId);
                  }}
                >
                  {versions.map((version) => (
                    <option key={version.id} value={version.id}>
                      Versión {version.version_number} — {version.id === selected.current_version.id ? "Actual" : "Finalizada"}
                    </option>
                  ))}
                </select>
              </label>
              {isHistorical && (
                <button
                  className="self-start rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-800 hover:bg-slate-100 sm:self-auto"
                  type="button"
                  onClick={() => setHistoricalVersionId(null)}
                >
                  Volver a versión actual
                </button>
              )}
            </div>
          )}

          {isHistorical && displayedExam && (
            <div className="mt-5 rounded-2xl border border-sky-200 bg-sky-50 p-4" role="status">
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="font-black text-sky-950">
                  Versión histórica {displayedExam.current_version.version_number}
                </h4>
                <span className="rounded-full bg-sky-200 px-2.5 py-1 text-xs font-black uppercase tracking-wide text-sky-900">
                  Histórica
                </span>
              </div>
              <p className="mt-2 text-sm font-semibold text-sky-900">
                Consulta de solo lectura. Estás viendo una versión anterior, no el examen actual.
              </p>
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <HistoricalInfo label="Finalizada" value={formatDateTime(displayedExam.current_version.finalized_at, selected.timezone_name)} />
                <HistoricalInfo label="Profesional responsable" value={selected.professional_name} />
                <HistoricalInfo
                  label="Estado de versión"
                  value={replacingVersion ? `Reemplazada por versión ${replacingVersion.version_number}` : "Finalizada"}
                />
                <HistoricalInfo
                  label="Motivo de corrección"
                  value={replacingVersion?.correction_reason ?? "No aplica"}
                />
              </dl>
            </div>
          )}

          {displayedExam && <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <Info label="Estado" value={displayedExam.status === "FINALIZED" ? "Finalizado" : "Borrador"} />
            <Info label="Integridad" value={displayedExam.current_version.integrity_status === "PASS" ? "Verificada" : displayedExam.current_version.integrity_status === "FAIL" ? "No válida" : "Pendiente"} />
            <Info label="Versiones" value={String(selected.versions.length)} />
          </div>}

          {displayedExam && (
            <section className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4" aria-labelledby="periodontal-evolution-link-title">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h4 id="periodontal-evolution-link-title" className="font-black text-slate-950">
                    Integración con evolución clínica
                  </h4>
                  <p className="mt-1 text-sm text-slate-600">
                    El vínculo es opcional y solo referencia este examen; no copia mediciones ni genera diagnósticos.
                  </p>
                </div>
                {isHistorical && (
                  <span className="rounded-full bg-sky-100 px-2.5 py-1 text-xs font-bold text-sky-800">
                    Consulta histórica
                  </span>
                )}
              </div>

              {selected.linked_evolution ? (
                <div className="mt-4 rounded-xl border border-emerald-200 bg-white p-4">
                  <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">Periodontograma asociado</p>
                  <p className="mt-1 font-bold text-slate-950">
                    Evolución del {formatDateTime(selected.linked_evolution.attended_at, selected.linked_evolution.timezone_name)}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    {selected.linked_evolution.dentist_name} · {selected.linked_evolution.site_name} · {evolutionStatus(selected.linked_evolution.status)}
                  </p>
                  <p className="mt-2 text-xs text-slate-500">Vínculo permanente y auditable. No se modifica desde una versión histórica.</p>
                </div>
              ) : !isHistorical && selected.status === "FINALIZED" &&
                hasPermission("periodontogram.finalize") &&
                hasPermission("clinical_evolutions.view") ? (
                <div className="mt-4">
                  {!showEvolutionLink ? (
                    <button
                      className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-800 disabled:opacity-50"
                      type="button"
                      disabled={loadingEvolutions}
                      onClick={() => void showEvolutionCandidates()}
                    >
                      {loadingEvolutions ? "Consultando evoluciones…" : "Vincular a evolución"}
                    </button>
                  ) : evolutionCandidates.length === 0 ? (
                    <div className="rounded-xl bg-white p-4 text-sm text-slate-600">
                      No hay evoluciones compatibles del mismo paciente y sede.
                    </div>
                  ) : (
                    <form className="space-y-3" onSubmit={linkEvolution}>
                      <label className="block text-sm font-bold text-slate-800">
                        Evolución existente
                        <select
                          className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 font-normal"
                          value={selectedEvolutionId}
                          onChange={(event) => setSelectedEvolutionId(event.target.value)}
                        >
                          {evolutionCandidates.map((evolution) => (
                            <option key={evolution.id} value={evolution.id}>
                              {formatDateTime(evolution.attended_at, evolution.timezone_name)} · {evolution.dentist_name} · {evolutionStatus(evolution.status)}
                            </option>
                          ))}
                        </select>
                      </label>
                      <div className="flex flex-wrap gap-2">
                        <button className="rounded-xl bg-green-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-50" type="submit" disabled={saving || !selectedEvolutionId}>
                          Confirmar vínculo
                        </button>
                        <button className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-700" type="button" onClick={() => setShowEvolutionLink(false)}>
                          Cancelar
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-500">
                  Finaliza la versión actual para habilitar el vínculo opcional.
                </p>
              )}
            </section>
          )}

          {displayedExam && <RapidPeriodontalEditor
            key={`${displayedExam.current_version.id}-${displayedExam.row_version}`}
            exam={displayedExam}
            saving={saving}
            canEdit={!isHistorical && selected.status === "DRAFT" && hasPermission("periodontogram.update_draft")}
            readOnlyLabel={isHistorical ? "Versión histórica · Solo lectura" : undefined}
            onDirtyChange={setClinicalDirty}
            onSave={async (payload) => {
              setSaving(true);
              setError(null);
              setMessage(null);
              try {
                const response = await updatePeriodontalDraft(selected.id, payload);
                setSelected(response.exam);
                setHistoricalVersionId(null);
                setClinicalDirty(false);
                setMessage(response.message);
              } catch (saveError) {
                setError(errorMessage(saveError));
              } finally {
                setSaving(false);
              }
            }}
          />}

          <div className="mt-6 flex flex-wrap gap-3">
            {!isHistorical && selected.status === "DRAFT" && hasPermission("periodontogram.finalize") && (
              <button className="rounded-xl bg-green-700 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50" type="button" disabled={saving || clinicalDirty} onClick={finalizeExam}>
                Finalizar versión
              </button>
            )}
          </div>

          {!isHistorical && selected.status === "FINALIZED" && hasPermission("periodontogram.correct") && (
            <form className="mt-6 rounded-2xl bg-slate-50 p-4" onSubmit={startCorrection}>
              <label className="block text-sm font-bold text-slate-800">
                Motivo de corrección
                <textarea
                  className="mt-2 min-h-24 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 font-normal"
                  value={correctionReason}
                  onChange={(event) => setCorrectionReason(event.target.value)}
                  minLength={3}
                  maxLength={500}
                  required
                />
              </label>
              <button className="mt-3 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-800 disabled:opacity-50" type="submit" disabled={saving}>
                Crear versión correctiva
              </button>
            </form>
          )}
        </div>
      )}
    </section>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-50 px-4 py-3">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 font-bold text-slate-900">{value}</p>
    </div>
  );
}

function HistoricalInfo({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="font-bold text-sky-700">{label}</dt>
      <dd className="mt-1 text-sky-950">{value}</dd>
    </div>
  );
}
