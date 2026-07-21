"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/services/apiClient";
import {
  confirmOdontogramEvent,
  createOdontogram,
  createOdontogramEvent,
  getOdontogram,
  getOdontogramCatalog,
  getOdontogramCurrent,
  getOdontogramToothHistory,
  listOdontogramEvents,
} from "@/services/odontogramService";
import { getPatient } from "@/services/patientService";
import type {
  OdontogramCatalogItem,
  OdontogramCurrentState,
  OdontogramDentition,
  OdontogramEvent,
  OdontogramEventInput,
  OdontogramToothState,
} from "@/types/odontogram";
import type { Patient } from "@/types/patient";

const PERMANENT_ROWS = [
  ["18", "17", "16", "15", "14", "13", "12", "11", "21", "22", "23", "24", "25", "26", "27", "28"],
  ["48", "47", "46", "45", "44", "43", "42", "41", "31", "32", "33", "34", "35", "36", "37", "38"],
];

const PRIMARY_ROWS = [
  ["55", "54", "53", "52", "51", "61", "62", "63", "64", "65"],
  ["85", "84", "83", "82", "81", "71", "72", "73", "74", "75"],
];

const LAYERS = [
  ["STRUCTURAL", "Estructura"],
  ["FINDING", "Hallazgos"],
  ["DIAGNOSIS", "Diagnósticos"],
  ["PLANNED", "Planificados"],
  ["PERFORMED", "Realizados"],
  ["OBSERVATION", "Observaciones"],
] as const;

const DEFAULT_LAYERS = new Set(["STRUCTURAL", "FINDING", "PLANNED", "PERFORMED"]);

const EVENT_OPTIONS = [
  { eventType: "STRUCTURAL_STATE_CHANGED", layer: "STRUCTURAL", label: "Cambiar estado estructural", catalogType: "STRUCTURAL_STATE" },
  { eventType: "FINDING_ADDED", layer: "FINDING", label: "Agregar hallazgo", catalogType: "FINDING" },
  { eventType: "DIAGNOSIS_ADDED", layer: "DIAGNOSIS", label: "Agregar diagnóstico", catalogType: "DIAGNOSIS" },
  { eventType: "PLANNED_PROCEDURE_ADDED", layer: "PLANNED", label: "Planificar procedimiento", catalogType: "PLANNED_PROCEDURE" },
  { eventType: "PROCEDURE_PERFORMED", layer: "PERFORMED", label: "Registrar realizado", catalogType: "PERFORMED_PROCEDURE" },
  { eventType: "OBSERVATION_ADDED", layer: "OBSERVATION", label: "Agregar observación", catalogType: "OBSERVATION" },
];

const SURFACES = [
  ["VESTIBULAR", "Vestibular"],
  ["PALATAL", "Palatina"],
  ["LINGUAL", "Lingual"],
  ["MESIAL", "Mesial"],
  ["DISTAL", "Distal"],
  ["OCCLUSAL", "Oclusal"],
  ["INCISAL", "Incisal"],
] as const;

const DENTITION_LABELS: Record<OdontogramDentition, string> = {
  PERMANENT: "Permanente",
  PRIMARY: "Temporal",
  MIXED: "Mixta",
};

function formatDate(value: string | null, withTime = true, timeZone?: string | null) {
  if (!value) return "No registrado";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    ...(withTime ? { timeStyle: "short" as const } : {}),
    ...(timeZone ? { timeZone } : {}),
  }).format(new Date(value));
}

function layerClass(layer: string) {
  const classes: Record<string, string> = {
    STRUCTURAL: "bg-slate-100 text-slate-700",
    FINDING: "bg-red-100 text-red-700",
    DIAGNOSIS: "bg-rose-100 text-rose-800",
    PLANNED: "bg-orange-100 text-orange-800",
    PERFORMED: "bg-green-100 text-green-800",
    OBSERVATION: "bg-sky-100 text-sky-800",
  };
  return classes[layer] ?? "bg-slate-100 text-slate-700";
}

function toothDentition(tooth: string): "PERMANENT" | "PRIMARY" {
  return tooth.startsWith("5") || tooth.startsWith("6") || tooth.startsWith("7") || tooth.startsWith("8")
    ? "PRIMARY"
    : "PERMANENT";
}

function selectedSurfaceWarning(tooth: string, surfaces: string[]) {
  const isAnterior = ["1", "2", "3"].includes(tooth[1]);
  const isUpper = tooth.startsWith("1") || tooth.startsWith("2") || tooth.startsWith("5") || tooth.startsWith("6");
  if (!isAnterior && surfaces.includes("INCISAL")) return "Incisal suele aplicar a dientes anteriores.";
  if (isAnterior && surfaces.includes("OCCLUSAL")) return "Oclusal suele aplicar a dientes posteriores.";
  if (!isUpper && surfaces.includes("PALATAL")) return "Palatina suele aplicar a dientes superiores.";
  return null;
}

function suggestedDentition(age: number | null | undefined): OdontogramDentition {
  if (age === null || age === undefined) return "PERMANENT";
  if (age < 6) return "PRIMARY";
  if (age <= 12) return "MIXED";
  return "PERMANENT";
}

function toothFamily(tooth: string) {
  const position = Number(tooth[1]);
  if ([1, 2].includes(position)) return "incisor";
  if (position === 3) return "canine";
  if ([4, 5].includes(position)) return "premolar";
  return "molar";
}

function isAnteriorTooth(tooth: string) {
  return ["incisor", "canine"].includes(toothFamily(tooth));
}

function detailMatches(detail: { catalog_code: string; catalog_name: string }, ...terms: string[]) {
  const value = `${detail.catalog_code} ${detail.catalog_name}`.toUpperCase();
  return terms.some((term) => value.includes(term.toUpperCase()));
}

function firstLayerDetails(state: OdontogramToothState | undefined, visibleLayers: Set<string>) {
  return Object.entries(state?.layers ?? {})
    .filter(([layer]) => visibleLayers.has(layer))
    .flatMap(([, details]) => details);
}

function tooltipForTooth(tooth: string, state: OdontogramToothState | undefined, visibleLayers: Set<string>) {
  const details = firstLayerDetails(state, visibleLayers);
  if (!details.length) return `${tooth} · Sin eventos visibles`;
  const summary = details
    .slice(0, 5)
    .map((detail) => {
      const scope = detail.surfaces?.length
        ? ` ${detail.surfaces.join(", ").toLowerCase()}`
        : "";
      return `${detail.catalog_name}${scope}`;
    })
    .join(". ");
  return `${tooth} · ${summary}${details.length > 5 ? ". Más eventos…" : ""}`;
}

function surfaceStyles(
  state: OdontogramToothState | undefined,
  visibleLayers: Set<string>,
): Record<string, { fill?: string; stroke?: string; strokeWidth?: number; opacity?: number }> {
  const styles: Record<string, { fill?: string; stroke?: string; strokeWidth?: number; opacity?: number }> = {};
  const details = firstLayerDetails(state, visibleLayers);
  details.forEach((detail) => {
    const surfaces = detail.surfaces?.length
      ? detail.surfaces
      : ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"];
    surfaces.forEach((surface) => {
      if (detail.layer === "FINDING") {
        styles[surface] = { fill: detail.color ?? "#ef4444", stroke: "#991b1b", strokeWidth: 1.6 };
      }
      if (detail.layer === "DIAGNOSIS") {
        styles[surface] = { fill: detail.color ?? "#be123c", stroke: "#7f1d1d", strokeWidth: 1.6 };
      }
      if (detailMatches(detail, "RESTAUR")) {
        styles[surface] = { fill: detail.color ?? "#3b82f6", stroke: "#1d4ed8", strokeWidth: 1.6 };
      }
      if (detail.layer === "PLANNED") {
        styles[surface] = { ...styles[surface], stroke: detail.color ?? "#f97316", strokeWidth: 2.2 };
      }
      if (detail.layer === "PERFORMED" && !detailMatches(detail, "CORONA", "IMPLANTE", "ENDO")) {
        styles[surface] = { fill: detail.color ?? "#22c55e", stroke: "#15803d", strokeWidth: 1.8 };
      }
    });
  });
  return styles;
}

export function OdontogramPage({
  patientId,
  embedded = false,
}: {
  patientId: string;
  embedded?: boolean;
}) {
  const { hasPermission } = useAuth();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [envelope, setEnvelope] = useState<{ exists: boolean; clinical_record_exists: boolean } | null>(null);
  const [current, setCurrent] = useState<OdontogramCurrentState | null>(null);
  const [catalog, setCatalog] = useState<OdontogramCatalogItem[]>([]);
  const [events, setEvents] = useState<OdontogramEvent[]>([]);
  const [history, setHistory] = useState<OdontogramEvent[]>([]);
  const [selectedTooth, setSelectedTooth] = useState("11");
  const [selectedSurfaces, setSelectedSurfaces] = useState<string[]>([]);
  const [dentition, setDentition] = useState<OdontogramDentition>("PERMANENT");
  const [visibleLayers, setVisibleLayers] = useState<Set<string>>(DEFAULT_LAYERS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [eventType, setEventType] = useState(EVENT_OPTIONS[1].eventType);
  const [catalogItemId, setCatalogItemId] = useState("");
  const [observation, setObservation] = useState("");
  const [saveAsConfirmed, setSaveAsConfirmed] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [loadedPatient, loadedEnvelope, loadedCatalog] = await Promise.all([
        getPatient(patientId),
        getOdontogram(patientId),
        getOdontogramCatalog(),
      ]);
      setPatient(loadedPatient);
      setEnvelope({
        exists: loadedEnvelope.exists,
        clinical_record_exists: loadedEnvelope.clinical_record_exists,
      });
      setCatalog(loadedCatalog);
      const ageBasedDentition = suggestedDentition(loadedPatient.age);
      if (loadedEnvelope.exists) {
        const [loadedCurrent, loadedEvents] = await Promise.all([
          getOdontogramCurrent(patientId),
          listOdontogramEvents(patientId),
        ]);
        setCurrent(loadedCurrent);
        setEvents(loadedEvents.items);
        setDentition(ageBasedDentition ?? loadedCurrent.preferred_dentition);
      } else {
        setCurrent(null);
        setEvents([]);
        setDentition(ageBasedDentition);
      }
    } catch (loadError) {
      setError(
        loadError instanceof ApiError
          ? loadError.detail ?? loadError.message
          : "No fue posible cargar el odontograma.",
      );
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  const loadHistory = useCallback(async () => {
    if (!envelope?.exists || !selectedTooth || !hasPermission("odontogram.history")) {
      setHistory([]);
      return;
    }
    try {
      const response = await getOdontogramToothHistory(patientId, selectedTooth);
      setHistory(response.items);
    } catch {
      setHistory([]);
    }
  }, [envelope?.exists, hasPermission, patientId, selectedTooth]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const selectedOption = EVENT_OPTIONS.find((option) => option.eventType === eventType) ?? EVENT_OPTIONS[1];
  const availableCatalog = useMemo(
    () => catalog.filter((item) => item.type === selectedOption.catalogType),
    [catalog, selectedOption.catalogType],
  );

  useEffect(() => {
    if (!availableCatalog.some((item) => item.id === catalogItemId)) {
      setCatalogItemId(availableCatalog[0]?.id ?? "");
    }
  }, [availableCatalog, catalogItemId]);

  const toothStateByCode = useMemo(() => {
    const map = new Map<string, OdontogramToothState>();
    current?.teeth.forEach((tooth) => map.set(tooth.tooth_code, tooth));
    return map;
  }, [current?.teeth]);

  async function createPatientOdontogram() {
    setSaving(true);
    setError(null);
    try {
      await createOdontogram(patientId, dentition);
      setMessage("Odontograma creado.");
      await load();
    } catch (createError) {
      setError(
        createError instanceof ApiError
          ? createError.detail ?? createError.message
          : "No fue posible crear el odontograma.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function saveEvent() {
    if (!catalogItemId) {
      setError("Selecciona un elemento del catálogo.");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    const useSurfaces = selectedSurfaces.length > 0;
    const payload: OdontogramEventInput = {
      event_type: eventType,
      status: saveAsConfirmed ? "CONFIRMED" : "DRAFT",
      observation: observation.trim() || null,
      details: [
        {
          catalog_item_id: catalogItemId,
          scope_type: useSurfaces ? "TOOTH_SURFACE" : "TOOTH",
          tooth_code: selectedTooth,
          dentition: toothDentition(selectedTooth),
          surfaces: useSurfaces ? selectedSurfaces : null,
          layer: selectedOption.layer,
        },
      ],
    };
    try {
      await createOdontogramEvent(patientId, payload);
      setObservation("");
      setSelectedSurfaces([]);
      setMessage(saveAsConfirmed ? "Evento confirmado." : "Borrador guardado.");
      await load();
      await loadHistory();
    } catch (saveError) {
      setError(
        saveError instanceof ApiError
          ? saveError.detail ?? saveError.message
          : "No fue posible registrar el evento.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function confirmDraft(event: OdontogramEvent) {
    setSaving(true);
    setError(null);
    try {
      await confirmOdontogramEvent(event.id, event.version);
      setMessage("Evento confirmado.");
      await load();
      await loadHistory();
    } catch (confirmError) {
      setError(
        confirmError instanceof ApiError
          ? confirmError.detail ?? confirmError.message
          : "No fue posible confirmar el evento.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 text-slate-500">
        <Spinner className="h-7 w-7 text-dentia-primary" />
        Cargando odontograma…
      </div>
    );
  }

  const canCreate = hasPermission("odontogram.create");
  const canEditDraft = hasPermission("odontogram.update_draft");
  const canConfirm = hasPermission("odontogram.confirm");
  const warning = selectedSurfaceWarning(selectedTooth, selectedSurfaces);

  return (
    <div className={embedded ? "" : "mx-auto max-w-7xl"}>
      {!embedded && (
        <>
          <Link href={`/pacientes/${patientId}`} className="text-sm font-bold text-green-700 hover:underline">
            ← Volver al paciente
          </Link>

          <header className="mt-5 flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-green-700">
                Odontograma histórico
              </p>
              <h1 className="mt-1 text-3xl font-black text-slate-950">
                {patient?.full_name ?? "Paciente"}
              </h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">
                Registra hallazgos, diagnósticos y procedimientos como eventos. El estado actual se calcula desde el historial confirmado.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm">
              <span className="font-bold text-slate-900">Fuente de verdad:</span>{" "}
              eventos odontográficos
            </div>
          </header>
        </>
      )}

      {error && <div className={embedded ? "mb-5" : "mt-5"}><Alert tone="error">{error}</Alert></div>}
      {message && <div className={embedded ? "mb-5" : "mt-5"}><Alert tone="info">{message}</Alert></div>}

      {!envelope?.exists && (
        <section className={`${embedded ? "" : "mt-6"} rounded-2xl border border-slate-200 bg-white p-7 shadow-sm`}>
          <h2 className="text-xl font-black text-slate-950">
            Este paciente aún no tiene odontograma.
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            El odontograma es opcional y permite registrar el estado dental de forma histórica. No bloquea urgencias, agenda ni tratamientos.
          </p>
          {!envelope?.clinical_record_exists ? (
            <div className="mt-5">
              <Alert tone="warning">
                Primero debe existir Historia Clínica / Ficha Clínica activa para crear el odontograma.
              </Alert>
            </div>
          ) : (
            <div className="mt-5 flex flex-wrap items-center gap-3">
              <DentitionSelector value={dentition} onChange={setDentition} />
              {canCreate && (
                <button
                  type="button"
                  disabled={saving}
                  onClick={createPatientOdontogram}
                  className="min-h-11 rounded-xl bg-dentia-primary px-5 font-bold text-white disabled:opacity-60"
                >
                  {saving ? "Creando…" : "Crear odontograma"}
                </button>
              )}
            </div>
          )}
        </section>
      )}

      {envelope?.exists && current && (
        <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_390px]">
          <main className="space-y-5">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <DentitionSelector value={dentition} onChange={setDentition} />
                <div className="flex flex-wrap gap-2">
                  <span className="mr-1 self-center text-xs font-black uppercase tracking-wide text-slate-500">
                    Capas visibles
                  </span>
                  {LAYERS.map(([layer, label]) => (
                    <label
                      key={layer}
                      className={`inline-flex cursor-pointer items-center gap-2 rounded-full border px-3 py-2 text-xs font-bold ${
                        visibleLayers.has(layer)
                          ? `${layerClass(layer)} border-transparent shadow-sm`
                          : "border-slate-200 bg-white text-slate-500"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={visibleLayers.has(layer)}
                        onChange={() => {
                          setVisibleLayers((prev) => {
                            const next = new Set(prev);
                            if (next.has(layer)) next.delete(layer);
                            else next.add(layer);
                            return next;
                          });
                        }}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>
            </section>

            {(dentition === "PERMANENT" || dentition === "MIXED") && (
              <OdontogramGrid
                title="Dentición permanente"
                rows={PERMANENT_ROWS}
                selectedTooth={selectedTooth}
                toothStateByCode={toothStateByCode}
                visibleLayers={visibleLayers}
                onSelect={(tooth) => {
                  setSelectedTooth(tooth);
                  setSelectedSurfaces([]);
                }}
              />
            )}
            {(dentition === "PRIMARY" || dentition === "MIXED") && (
              <OdontogramGrid
                title="Dentición temporal"
                rows={PRIMARY_ROWS}
                selectedTooth={selectedTooth}
                toothStateByCode={toothStateByCode}
                visibleLayers={visibleLayers}
                onSelect={(tooth) => {
                  setSelectedTooth(tooth);
                  setSelectedSurfaces([]);
                }}
              />
            )}

            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-black text-slate-950">Leyenda</h2>
              <p className="mt-1 text-sm text-slate-500">
                Los colores son apoyo; la forma, el patrón y el símbolo ayudan a distinguir hallazgos y tratamientos.
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {current.legend.slice(0, 24).map((item) => (
                  <div key={item.id} className="flex items-center gap-3 rounded-xl border border-slate-100 p-3">
                    <LegendExample item={item} />
                    <div>
                      <p className="text-sm font-bold text-slate-900">{item.name}</p>
                      <p className="text-xs text-slate-500">{item.category ?? item.type}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </main>

          <aside className="space-y-5">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Diente seleccionado</p>
                  <h2 className="mt-1 text-3xl font-black text-slate-950">{selectedTooth}</h2>
                  <p className="text-sm text-slate-500">{toothDentition(selectedTooth) === "PRIMARY" ? "Temporal" : "Permanente"}</p>
                </div>
                <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-bold text-green-700">
                  {toothStateByCode.get(selectedTooth)?.event_count ?? 0} eventos
                </span>
              </div>

              <div className="mt-5">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Superficies</p>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {SURFACES.map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => {
                        setSelectedSurfaces((prev) =>
                          prev.includes(value)
                            ? prev.filter((surface) => surface !== value)
                            : [...prev, value],
                        );
                      }}
                      className={`rounded-xl border px-3 py-2 text-sm font-bold ${
                        selectedSurfaces.includes(value)
                          ? "border-green-500 bg-green-50 text-green-800"
                          : "border-slate-200 text-slate-600 hover:border-green-200"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                {warning && <p className="mt-2 text-xs font-semibold text-amber-700">{warning}</p>}
              </div>
            </section>

            {canEditDraft && (
              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-black text-slate-950">Registrar evento</h2>
                <div className="mt-4 space-y-4">
                  <label className="block text-sm font-bold text-slate-700">
                    Acción
                    <select
                      value={eventType}
                      onChange={(event) => setEventType(event.target.value)}
                      className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                    >
                      {EVENT_OPTIONS.map((option) => (
                        <option key={option.eventType} value={option.eventType}>{option.label}</option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-sm font-bold text-slate-700">
                    Catálogo
                    <select
                      value={catalogItemId}
                      onChange={(event) => setCatalogItemId(event.target.value)}
                      className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                    >
                      {availableCatalog.map((item) => (
                        <option key={item.id} value={item.id}>{item.name}</option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-sm font-bold text-slate-700">
                    Observación
                    <textarea
                      value={observation}
                      onChange={(event) => setObservation(event.target.value)}
                      rows={3}
                      className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                      placeholder="Detalle clínico breve del evento."
                    />
                  </label>
                  {canConfirm && (
                    <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm font-bold text-slate-700">
                      <input
                        type="checkbox"
                        checked={saveAsConfirmed}
                        onChange={(event) => setSaveAsConfirmed(event.target.checked)}
                      />
                      Guardar confirmado
                    </label>
                  )}
                  <button
                    type="button"
                    disabled={saving || !catalogItemId}
                    onClick={saveEvent}
                    className="min-h-11 w-full rounded-xl bg-dentia-primary px-4 font-bold text-white disabled:opacity-60"
                  >
                    {saving ? "Guardando…" : saveAsConfirmed ? "Registrar y confirmar" : "Guardar borrador"}
                  </button>
                </div>
              </section>
            )}

            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-black text-slate-950">Estado actual del diente</h2>
              <ToothLayerSummary tooth={toothStateByCode.get(selectedTooth)} />
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-black text-slate-950">Histórico</h2>
                <span className="text-xs font-bold text-slate-400">{history.length} registros</span>
              </div>
              <div className="mt-4 space-y-3">
                {history.map((item) => (
                  <EventCard key={item.id} event={item} onConfirm={canConfirm && item.status === "DRAFT" ? () => confirmDraft(item) : undefined} />
                ))}
                {!history.length && (
                  <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                    Sin eventos para este diente.
                  </p>
                )}
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-black text-slate-950">Borradores</h2>
              <div className="mt-4 space-y-3">
                {events.filter((event) => event.status === "DRAFT").map((event) => (
                  <EventCard key={event.id} event={event} onConfirm={canConfirm ? () => confirmDraft(event) : undefined} />
                ))}
                {!events.some((event) => event.status === "DRAFT") && (
                  <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                    No hay eventos odontográficos en borrador.
                  </p>
                )}
              </div>
            </section>
          </aside>
        </div>
      )}
    </div>
  );
}

function DentitionSelector({
  value,
  onChange,
}: {
  value: OdontogramDentition;
  onChange: (value: OdontogramDentition) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-xl bg-white px-3 py-2 text-sm font-black text-slate-900 shadow-sm">
          Dentición: {DENTITION_LABELS[value]}
        </span>
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          className="rounded-xl px-3 py-2 text-sm font-bold text-green-700 hover:bg-green-50"
        >
          Cambiar
        </button>
      </div>
      {open && (
        <div className="mt-2 flex flex-wrap gap-2 border-t border-slate-200 pt-2">
          {[
            ["PERMANENT", "Permanente"],
            ["PRIMARY", "Temporal"],
            ["MIXED", "Mixta"],
          ].map(([option, label]) => (
            <button
              key={option}
              type="button"
              onClick={() => {
                onChange(option as OdontogramDentition);
                setOpen(false);
              }}
              className={`rounded-xl px-4 py-2 text-sm font-bold ${
                value === option
                  ? "bg-green-700 text-white"
                  : "border border-slate-200 bg-white text-slate-700 hover:border-green-200"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function OdontogramGrid({
  title,
  rows,
  selectedTooth,
  toothStateByCode,
  visibleLayers,
  onSelect,
}: {
  title: string;
  rows: string[][];
  selectedTooth: string;
  toothStateByCode: Map<string, OdontogramToothState>;
  visibleLayers: Set<string>;
  onSelect: (tooth: string) => void;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <div className="mt-5 space-y-5 overflow-x-auto pb-2">
        {rows.map((row, index) => (
          <div key={index} className="flex min-w-max justify-center gap-2">
            {row.map((tooth) => (
              <ToothButton
                key={tooth}
                tooth={tooth}
                selected={selectedTooth === tooth}
                state={toothStateByCode.get(tooth)}
                visibleLayers={visibleLayers}
                onClick={() => onSelect(tooth)}
              />
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}

function ToothButton({
  tooth,
  selected,
  state,
  visibleLayers,
  onClick,
}: {
  tooth: string;
  selected: boolean;
  state?: OdontogramToothState;
  visibleLayers: Set<string>;
  onClick: () => void;
}) {
  const activeDetails = firstLayerDetails(state, visibleLayers);
  const absent = activeDetails.some((detail) => detailMatches(detail, "AUSENTE", "EXTRACCIÓN", "EXFOLIADO"));
  const hasHistory = Boolean(state?.event_count);
  const hasCrown = activeDetails.some((detail) => detailMatches(detail, "CORONA", "CROWN"));
  const hasImplant = activeDetails.some((detail) => detailMatches(detail, "IMPLANTE", "IMPLANT"));
  const hasEndo = activeDetails.some((detail) => detailMatches(detail, "ENDODONCIA", "ENDO"));
  const planned = activeDetails.some((detail) => detail.layer === "PLANNED");
  const performed = activeDetails.some((detail) => detail.layer === "PERFORMED");
  return (
    <button
      type="button"
      onClick={onClick}
      title={tooltipForTooth(tooth, state, visibleLayers)}
      className={`relative flex h-[6.75rem] w-[4.75rem] flex-col items-center justify-center rounded-3xl border-2 bg-white text-sm font-black shadow-sm transition ${
        selected
          ? "border-green-500 ring-4 ring-green-100"
          : "border-slate-200 hover:border-green-300"
      } ${absent ? "opacity-45" : ""}`}
    >
      <span className="absolute left-2 top-1.5 rounded-full bg-white/90 px-1.5 text-[11px] text-slate-500 shadow-sm">{tooth}</span>
      {hasHistory && (
        <span className="absolute right-1.5 top-1.5 rounded-full bg-slate-900 px-1.5 py-0.5 text-[10px] font-black text-white" title="Tiene histórico">
          ◷ {state?.event_count}
        </span>
      )}
      <ClinicalToothSvg
        tooth={tooth}
        styles={surfaceStyles(state, visibleLayers)}
        hasCrown={hasCrown}
        hasImplant={hasImplant}
        hasEndo={hasEndo}
        absent={absent}
        planned={planned}
        performed={performed}
      />
      <div className="mt-1 flex h-4 max-w-[4rem] items-center justify-center gap-1">
        {[...new Set(activeDetails.map((detail) => detail.layer))].slice(0, 3).map((layer) => (
          <span key={layer} className={`rounded-full px-1.5 py-0.5 text-[9px] font-black ${layerClass(layer)}`}>
            {LAYERS.find(([value]) => value === layer)?.[1].slice(0, 3)}
          </span>
        ))}
      </div>
    </button>
  );
}

function ClinicalToothSvg({
  tooth,
  styles,
  hasCrown,
  hasImplant,
  hasEndo,
  absent,
  planned,
  performed,
}: {
  tooth: string;
  styles: Record<string, { fill?: string; stroke?: string; strokeWidth?: number; opacity?: number }>;
  hasCrown: boolean;
  hasImplant: boolean;
  hasEndo: boolean;
  absent: boolean;
  planned: boolean;
  performed: boolean;
}) {
  const family = toothFamily(tooth);
  const anterior = isAnteriorTooth(tooth);
  const defaultSurface = { fill: "#ffffff", stroke: "#cbd5e1", strokeWidth: 1.2 };
  const surface = (key: string) => ({ ...defaultSurface, ...(styles[key] ?? {}) });
  const mainSurface = anterior ? "INCISAL" : "OCCLUSAL";
  const outlineStroke = planned ? "#f97316" : performed ? "#16a34a" : "#94a3b8";
  const outlineWidth = planned || performed ? 2.8 : 1.4;

  return (
    <svg viewBox="0 0 78 86" className="mt-4 h-[4.6rem] w-[4.1rem]" aria-hidden="true">
      <defs>
        <linearGradient id={`metal-${tooth}`} x1="0" x2="1">
          <stop offset="0%" stopColor="#94a3b8" />
          <stop offset="45%" stopColor="#e2e8f0" />
          <stop offset="100%" stopColor="#64748b" />
        </linearGradient>
        <pattern id={`hatch-${tooth}`} patternUnits="userSpaceOnUse" width="5" height="5">
          <path d="M0 5 5 0" stroke="#64748b" strokeWidth="1" />
        </pattern>
      </defs>

      {absent ? (
        <>
          <path d="M24 18 C24 8 54 8 54 18 L61 58 C63 72 15 72 17 58 Z" fill="#f8fafc" stroke="#94a3b8" strokeDasharray="5 3" strokeWidth="2.2" />
          <path d="M22 22 L58 64 M58 22 L22 64" stroke="#94a3b8" strokeWidth="2.4" strokeLinecap="round" />
        </>
      ) : hasImplant ? (
        <>
          <path d="M28 14 C28 6 50 6 50 14 L56 34 C58 44 20 44 22 34 Z" fill={`url(#metal-${tooth})`} stroke="#475569" strokeWidth="1.6" />
          <path d="M34 39 L44 39 L48 78 L30 78 Z" fill={`url(#hatch-${tooth})`} stroke="#475569" strokeWidth="1.8" />
          <path d="M32 49 H46 M31 58 H47 M30 67 H48" stroke="#475569" strokeWidth="1.5" />
        </>
      ) : (
        <>
          <path d="M23 15 C23 7 55 7 55 15 L63 57 C66 75 12 75 15 57 Z" fill="#fff" stroke={outlineStroke} strokeWidth={outlineWidth} />
          <path d="M24 17 C31 12 47 12 54 17 L48 36 L30 36 Z" {...surface("VESTIBULAR")} />
          <path d="M30 36 L48 36 L55 59 C47 65 31 65 23 59 Z" {...surface(anterior ? "LINGUAL" : "PALATAL")} />
          <path d="M23 18 L30 36 L23 59 C18 50 18 27 23 18 Z" {...surface("MESIAL")} />
          <path d="M55 18 C60 27 60 50 55 59 L48 36 Z" {...surface("DISTAL")} />
          <path
            d={family === "molar"
              ? "M30 33 C35 28 43 28 48 33 C46 41 32 41 30 33 Z"
              : family === "premolar"
                ? "M31 32 C36 29 42 29 47 32 L45 40 L33 40 Z"
                : family === "canine"
                  ? "M30 31 L39 23 L48 31 L43 42 L35 42 Z"
                  : "M29 30 L49 30 L44 42 L34 42 Z"}
            {...surface(mainSurface)}
          />
          {hasCrown && (
            <>
              <path d="M21 16 C29 5 49 5 57 16 L62 43 C50 49 28 49 16 43 Z" fill="#22c55e" fillOpacity="0.32" stroke="#15803d" strokeWidth="2.4" />
              <path d="M25 18 L53 18 M21 30 C31 35 47 35 57 30" stroke="#15803d" strokeWidth="1.7" strokeLinecap="round" />
            </>
          )}
          {hasEndo && (
            <>
              <path d="M39 18 C38 30 37 43 39 62" stroke="#7e22ce" strokeWidth="4" strokeLinecap="round" fill="none" />
              <path d="M31 61 C35 66 43 66 47 61" stroke="#7e22ce" strokeWidth="2.4" strokeLinecap="round" fill="none" />
            </>
          )}
        </>
      )}
      {planned && !absent && (
        <path d="M18 12 C30 0 48 0 60 12 L68 62 C64 82 14 82 10 62 Z" fill="none" stroke="#f97316" strokeDasharray="5 4" strokeWidth="2" />
      )}
      {performed && !absent && !hasImplant && !hasCrown && (
        <circle cx="61" cy="65" r="8" fill="#16a34a" stroke="#ffffff" strokeWidth="2" />
      )}
    </svg>
  );
}

function LegendExample({ item }: { item: OdontogramCatalogItem }) {
  const code = `${item.code} ${item.name}`.toUpperCase();
  const color = item.color ?? "#64748b";
  const isCrown = code.includes("CORONA") || code.includes("CROWN");
  const isImplant = code.includes("IMPLANTE") || code.includes("IMPLANT");
  const isEndo = code.includes("ENDO");
  const isAbsent = code.includes("AUSENTE") || code.includes("EXTRAC");
  const isPlanned = item.type === "PLANNED_PROCEDURE";
  const isPerformed = item.type === "PERFORMED_PROCEDURE";

  return (
    <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-slate-50">
      <svg viewBox="0 0 54 58" className="h-10 w-10" aria-hidden="true">
        <path
          d="M15 10 C15 4 39 4 39 10 L45 38 C48 51 6 51 9 38 Z"
          fill={isAbsent ? "#f8fafc" : isImplant ? "#cbd5e1" : "#ffffff"}
          stroke={isPlanned ? "#f97316" : isPerformed ? "#16a34a" : "#94a3b8"}
          strokeWidth={isPlanned || isPerformed ? 2.3 : 1.4}
          strokeDasharray={isAbsent || isPlanned ? "4 3" : undefined}
        />
        {!isCrown && !isImplant && !isEndo && !isAbsent && (
          <path d="M18 24 L36 24 L32 37 L22 37 Z" fill={color} fillOpacity="0.72" stroke={color} strokeWidth="1.3" />
        )}
        {isCrown && (
          <path d="M13 11 C20 2 34 2 41 11 L45 30 C35 35 19 35 9 30 Z" fill="#22c55e" fillOpacity="0.36" stroke="#15803d" strokeWidth="2" />
        )}
        {isImplant && (
          <>
            <path d="M22 28 L32 28 L35 52 L19 52 Z" fill="#e2e8f0" stroke="#475569" strokeWidth="1.6" />
            <path d="M21 36 H33 M20 43 H34" stroke="#475569" strokeWidth="1.3" />
          </>
        )}
        {isEndo && (
          <path d="M27 12 C26 24 26 36 28 47" stroke="#7e22ce" strokeWidth="3.6" strokeLinecap="round" fill="none" />
        )}
        {isAbsent && (
          <path d="M14 14 L40 44 M40 14 L14 44" stroke="#94a3b8" strokeWidth="2.2" strokeLinecap="round" />
        )}
      </svg>
      <span
        className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-[9px] font-black text-white shadow"
        style={{ backgroundColor: color }}
      >
        {item.symbol ?? "•"}
      </span>
    </div>
  );
}

function ToothLayerSummary({ tooth }: { tooth?: OdontogramToothState }) {
  if (!tooth) {
    return (
      <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
        Sin eventos confirmados en capas visibles.
      </p>
    );
  }
  return (
    <div className="mt-4 space-y-3">
      {Object.entries(tooth.layers).map(([layer, details]) => (
        <div key={layer} className="rounded-xl border border-slate-100 p-3">
          <p className={`inline-flex rounded-full px-2 py-1 text-xs font-black ${layerClass(layer)}`}>
            {LAYERS.find(([value]) => value === layer)?.[1] ?? layer}
          </p>
          <div className="mt-2 space-y-1">
            {details.map((detail) => (
              <p key={detail.id} className="text-sm text-slate-700">
                {detail.catalog_name}
                {detail.surfaces?.length ? ` · ${detail.surfaces.join(", ")}` : ""}
              </p>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function EventCard({
  event,
  onConfirm,
}: {
  event: OdontogramEvent;
  onConfirm?: () => void;
}) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-black text-slate-900">
            {event.details.map((detail) => detail.catalog_name).join(", ") || event.event_type}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {formatDate(event.clinical_date, true, event.timezone)} · {event.dentist_name ?? "Odontólogo"} · {event.site_name ?? "Sede"}
          </p>
        </div>
        <span className={`rounded-full px-2 py-1 text-[11px] font-black ${
          event.status === "CONFIRMED"
            ? "bg-green-50 text-green-700"
            : event.status === "DRAFT"
              ? "bg-amber-50 text-amber-700"
              : "bg-slate-100 text-slate-600"
        }`}>
          {event.status === "CONFIRMED" ? "Confirmado" : event.status === "DRAFT" ? "Borrador" : "Compensado"}
        </span>
      </div>
      {event.observation && (
        <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{event.observation}</p>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        {event.details.map((detail) => (
          <span key={detail.id} className={`rounded-full px-2.5 py-1 text-xs font-bold ${layerClass(detail.layer)}`}>
            {detail.tooth_code ? `${detail.tooth_code} · ` : ""}
            {detail.surfaces?.length ? detail.surfaces.join(", ") : detail.scope_type}
          </span>
        ))}
      </div>
      {event.content_hash && (
        <p className="mt-2 truncate text-[11px] text-slate-400">
          Hash: {event.content_hash}
        </p>
      )}
      {onConfirm && (
        <button
          type="button"
          onClick={onConfirm}
          className="mt-3 rounded-xl bg-green-700 px-3 py-2 text-xs font-black text-white"
        >
          Confirmar
        </button>
      )}
    </div>
  );
}
