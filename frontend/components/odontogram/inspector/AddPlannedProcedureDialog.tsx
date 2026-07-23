"use client";

import { useEffect, useMemo, useState } from "react";
import { ApiError } from "@/services/apiClient";
import { createPlannedProcedureFromOdontogramEvent } from "@/services/odontogramService";
import { listProcedureCatalog, listTreatments } from "@/services/treatmentService";
import type { OdontogramEvent, OdontogramLinkedProcedure } from "@/types/odontogram";
import type { ProcedureCatalogItem, TreatmentListItem } from "@/types/treatment";
import { detailSurfaceLabel, eventCardTitle } from "./dentalInspectorMapper";

const SURFACES = ["VESTIBULAR", "PALATAL", "LINGUAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"];

function newKey() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `odontogram-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function firstEligibleDetail(event: OdontogramEvent) {
  return event.details.find((detail) => ["DIAGNOSIS", "FINDING"].includes(detail.layer));
}

function initialScope(event: OdontogramEvent) {
  const detail = firstEligibleDetail(event);
  if (!detail) return { scopeType: "GENERAL", tooth: "", surfaces: [] as string[] };
  if (detail.scope_type === "TOOTH_SURFACE" && detail.tooth_code && detail.surfaces?.length) {
    return { scopeType: "TOOTH_SURFACE", tooth: detail.tooth_code, surfaces: detail.surfaces };
  }
  if (detail.tooth_code) return { scopeType: "TOOTH", tooth: detail.tooth_code, surfaces: [] as string[] };
  return { scopeType: "GENERAL", tooth: "", surfaces: [] as string[] };
}

function decimalText(value: string | null | undefined, fallback = "0") {
  return value && Number(value) >= 0 ? value : fallback;
}

export function AddPlannedProcedureDialog({
  event,
  patientId,
  linkedProcedures,
  onClose,
  onCreated,
}: {
  event: OdontogramEvent;
  patientId: string;
  linkedProcedures: OdontogramLinkedProcedure[];
  onClose: () => void;
  onCreated: () => Promise<void> | void;
}) {
  const scope = useMemo(() => initialScope(event), [event]);
  const [treatments, setTreatments] = useState<TreatmentListItem[]>([]);
  const [catalog, setCatalog] = useState<ProcedureCatalogItem[]>([]);
  const [targetMode, setTargetMode] = useState<"existing" | "new">("existing");
  const [treatmentId, setTreatmentId] = useState("");
  const [newTreatmentName, setNewTreatmentName] = useState(`Plan diente ${scope.tooth || "odontográfico"}`);
  const [catalogId, setCatalogId] = useState("");
  const [procedureName, setProcedureName] = useState("");
  const [category, setCategory] = useState("");
  const [unitValue, setUnitValue] = useState("0");
  const [quantity, setQuantity] = useState("1");
  const [scopeType, setScopeType] = useState(scope.scopeType);
  const [tooth, setTooth] = useState(scope.tooth);
  const [surfaces, setSurfaces] = useState<string[]>(scope.surfaces);
  const [observation, setObservation] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState(newKey);
  const [warningLinks, setWarningLinks] = useState<OdontogramLinkedProcedure[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [createdNeedsRefresh, setCreatedNeedsRefresh] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    Promise.all([
      listTreatments(`?patient_id=${encodeURIComponent(patientId)}`),
      listProcedureCatalog("?active=true"),
    ])
      .then(([treatmentResponse, catalogResponse]) => {
        if (!mounted) return;
        const activeTreatments = treatmentResponse.items.filter(
          (item) => !["Finalizado", "Cancelado"].includes(item.status),
        );
        setTreatments(activeTreatments);
        setCatalog(catalogResponse.items);
        setTreatmentId(activeTreatments[0]?.id ?? "");
        setTargetMode(activeTreatments.length ? "existing" : "new");
      })
      .catch((loadError) => {
        if (!mounted) return;
        setError(loadError instanceof ApiError ? loadError.detail ?? loadError.message : "No fue posible cargar opciones comerciales.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [patientId]);

  const selectedCatalog = useMemo(() => catalog.find((item) => item.id === catalogId), [catalog, catalogId]);

  useEffect(() => {
    if (!selectedCatalog) return;
    setProcedureName(selectedCatalog.name);
    setCategory(selectedCatalog.category ?? "");
    setUnitValue(decimalText(selectedCatalog.suggested_value));
    if (selectedCatalog.suggested_scope_type && selectedCatalog.suggested_scope_type !== "ZONE") {
      setScopeType(selectedCatalog.suggested_scope_type);
    }
  }, [selectedCatalog]);

  async function submit(forceDuplicate = false) {
    setSaving(true);
    setError(null);
    try {
      const response = await createPlannedProcedureFromOdontogramEvent(event.id, {
        idempotency_key: forceDuplicate ? newKey() : idempotencyKey,
        treatment_id: targetMode === "existing" ? treatmentId : null,
        new_treatment:
          targetMode === "new"
            ? {
                name: newTreatmentName,
                responsible_dentist_id: event.dentist_id ?? null,
                main_site_id: event.site_id ?? null,
                observations: `Creado desde evento odontográfico ${event.id}`,
              }
            : null,
        catalog_procedure_id: catalogId || null,
        name: procedureName || selectedCatalog?.name || null,
        category: category || null,
        dentist_id: event.dentist_id ?? null,
        site_id: event.site_id ?? null,
        unit_value: unitValue || "0",
        quantity: quantity || "1",
        observations: observation || null,
        scope_type: scopeType,
        tooth: ["TOOTH", "TOOTH_SURFACE"].includes(scopeType) ? tooth : null,
        surfaces: scopeType === "TOOTH_SURFACE" ? surfaces : null,
        allow_similar_duplicate: forceDuplicate,
      });
      if (response.similar_duplicate_detected) {
        setWarningLinks(response.linked_procedures);
        setIdempotencyKey(newKey());
        return;
      }
      try {
        await onCreated();
        onClose();
      } catch {
        setCreatedNeedsRefresh(true);
        setError("El procedimiento fue creado, pero no fue posible actualizar la vista. Actualice la información para continuar.");
      }
    } catch (submitError) {
      setError(submitError instanceof ApiError ? submitError.detail ?? submitError.message : "No fue posible crear el procedimiento planificado.");
    } finally {
      setSaving(false);
    }
  }

  const existingLinks = linkedProcedures.filter((item) => item.source_odontogram_event_id === event.id);

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/30 p-4">
      <div className="flex max-h-[88vh] w-full max-w-2xl flex-col overflow-hidden rounded-[1.5rem] bg-white shadow-2xl">
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
          <div>
            <p className="text-xs font-black uppercase tracking-wide text-slate-500">Agregar al plan de tratamiento</p>
            <h3 className="mt-1 text-xl font-black text-slate-950">{eventCardTitle(event)}</h3>
            <p className="mt-1 text-sm font-semibold text-slate-500">
              Origen clínico confirmado · {firstEligibleDetail(event) ? detailSurfaceLabel(firstEligibleDetail(event)!) : "Sin superficie"}
            </p>
          </div>
          <button type="button" onClick={onClose} className="h-9 w-9 rounded-full border border-slate-200 text-xl font-black text-slate-500">×</button>
        </header>
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-5">
          {loading ? (
            <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">Cargando opciones…</p>
          ) : (
            <>
              {existingLinks.length > 0 && (
                <div className="rounded-2xl border border-green-200 bg-green-50 p-3 text-sm text-green-800">
                  {existingLinks.length === 1 ? "Este diagnóstico ya tiene 1 procedimiento en el plan." : `Este diagnóstico ya tiene ${existingLinks.length} procedimientos en el plan.`} Puedes agregar otro si corresponde clínicamente.
                </div>
              )}
              <section className="grid gap-3 md:grid-cols-2">
                <label className="text-sm font-bold text-slate-700">
                  Destino
                  <select value={targetMode} onChange={(item) => setTargetMode(item.target.value as "existing" | "new")} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2">
                    <option value="existing" disabled={!treatments.length}>Tratamiento existente</option>
                    <option value="new">Crear tratamiento nuevo</option>
                  </select>
                </label>
                {targetMode === "existing" ? (
                  <label className="text-sm font-bold text-slate-700">
                    Tratamiento
                    <select value={treatmentId} onChange={(item) => setTreatmentId(item.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2">
                      {treatments.map((treatment) => (
                        <option key={treatment.id} value={treatment.id}>{treatment.name}</option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <label className="text-sm font-bold text-slate-700">
                    Nombre del tratamiento
                    <input value={newTreatmentName} onChange={(item) => setNewTreatmentName(item.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
                  </label>
                )}
              </section>

              <section className="grid gap-3 md:grid-cols-2">
                <label className="text-sm font-bold text-slate-700">
                  Procedimiento
                  <select value={catalogId} onChange={(item) => setCatalogId(item.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2">
                    <option value="">Seleccionar catálogo…</option>
                    {catalog.map((item) => (
                      <option key={item.id} value={item.id}>{item.name}</option>
                    ))}
                  </select>
                </label>
                <label className="text-sm font-bold text-slate-700">
                  Nombre
                  <input value={procedureName} onChange={(item) => setProcedureName(item.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
                </label>
                <label className="text-sm font-bold text-slate-700">
                  Valor unitario
                  <input type="number" min="0" value={unitValue} onChange={(item) => setUnitValue(item.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
                </label>
                <label className="text-sm font-bold text-slate-700">
                  Cantidad
                  <input type="number" min="0.01" step="0.01" value={quantity} onChange={(item) => setQuantity(item.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
                </label>
              </section>

              <section className="grid gap-3 md:grid-cols-2">
                <label className="text-sm font-bold text-slate-700">
                  Alcance
                  <select value={scopeType} onChange={(item) => setScopeType(item.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2">
                    <option value="GENERAL">General</option>
                    <option value="TOOTH">Diente</option>
                    <option value="TOOTH_SURFACE">Diente y superficies</option>
                  </select>
                </label>
                {["TOOTH", "TOOTH_SURFACE"].includes(scopeType) && (
                  <label className="text-sm font-bold text-slate-700">
                    Diente
                    <input value={tooth} onChange={(item) => setTooth(item.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
                  </label>
                )}
              </section>
              {scopeType === "TOOTH_SURFACE" && (
                <div className="flex flex-wrap gap-2">
                  {SURFACES.map((surface) => (
                    <button key={surface} type="button" onClick={() => setSurfaces((prev) => prev.includes(surface) ? prev.filter((item) => item !== surface) : [...prev, surface])} className={`rounded-full border px-3 py-1 text-xs font-black ${surfaces.includes(surface) ? "border-green-500 bg-green-50 text-green-800" : "border-slate-200 text-slate-500"}`}>
                      {surface}
                    </button>
                  ))}
                </div>
              )}
              <label className="block text-sm font-bold text-slate-700">
                Observación comercial
                <textarea value={observation} onChange={(item) => setObservation(item.target.value)} rows={3} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2" />
              </label>
              {warningLinks.length > 0 && (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                  <p className="font-black">Posible duplicado detectado.</p>
                  {warningLinks.map((item) => (
                    <p key={item.procedure_id} className="mt-1">{item.name} · {item.treatment_name} · {item.scope_label}</p>
                  ))}
                  <button type="button" disabled={saving} onClick={() => submit(true)} className="mt-3 rounded-xl bg-amber-600 px-3 py-2 text-xs font-black text-white">
                    Crear otro de todas formas
                  </button>
                </div>
              )}
              {error && (
                <div className="rounded-2xl bg-red-50 p-3 text-sm font-semibold text-red-700">
                  <p>{error}</p>
                  {createdNeedsRefresh && (
                    <button
                      type="button"
                      className="mt-3 rounded-xl bg-red-700 px-3 py-2 text-xs font-black text-white"
                      onClick={async () => {
                        setSaving(true);
                        try {
                          await onCreated();
                          onClose();
                        } finally {
                          setSaving(false);
                        }
                      }}
                    >
                      Actualizar
                    </button>
                  )}
                </div>
              )}
            </>
          )}
        </div>
        <footer className="flex justify-end gap-2 border-t border-slate-200 p-4">
          <button type="button" onClick={onClose} className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-black text-slate-600">Cancelar</button>
          <button type="button" disabled={createdNeedsRefresh || loading || saving || !procedureName || (targetMode === "existing" && !treatmentId)} onClick={() => submit(false)} className="rounded-xl bg-dentia-primary px-4 py-2 text-sm font-black text-white disabled:opacity-50">
            {saving ? "Creando…" : "Crear procedimiento planificado"}
          </button>
        </footer>
      </div>
    </div>
  );
}
