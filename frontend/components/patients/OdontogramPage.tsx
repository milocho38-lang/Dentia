"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import {
  DualOdontogramGrid,
  PERMANENT_DUAL_ROWS,
  PRIMARY_DUAL_ROWS,
} from "@/components/odontogram/classic";
import { DentalInspector } from "@/components/odontogram/inspector";
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

const LAYERS = [
  ["STRUCTURAL", "Estructura"],
  ["FINDING", "Hallazgos"],
  ["DIAGNOSIS", "Diagnósticos"],
  ["PLANNED", "Planificados"],
  ["PERFORMED", "Realizados"],
  ["OBSERVATION", "Observaciones"],
] as const;

const DEFAULT_LAYERS = new Set(["STRUCTURAL", "FINDING", "DIAGNOSIS", "PLANNED", "PERFORMED"]);

const EVENT_OPTIONS = [
  { eventType: "STRUCTURAL_STATE_CHANGED", layer: "STRUCTURAL", label: "Cambiar estado estructural", catalogType: "STRUCTURAL_STATE" },
  { eventType: "FINDING_ADDED", layer: "FINDING", label: "Agregar hallazgo", catalogType: "FINDING" },
  { eventType: "DIAGNOSIS_ADDED", layer: "DIAGNOSIS", label: "Agregar diagnóstico", catalogType: "DIAGNOSIS" },
  { eventType: "PLANNED_PROCEDURE_ADDED", layer: "PLANNED", label: "Planificar procedimiento", catalogType: "PLANNED_PROCEDURE" },
  { eventType: "PROCEDURE_PERFORMED", layer: "PERFORMED", label: "Registrar realizado", catalogType: "PERFORMED_PROCEDURE" },
  { eventType: "OBSERVATION_ADDED", layer: "OBSERVATION", label: "Agregar observación", catalogType: "OBSERVATION" },
];

const DENTITION_LABELS: Record<OdontogramDentition, string> = {
  PERMANENT: "Permanente",
  PRIMARY: "Temporal",
  MIXED: "Mixta",
};

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
  const [drawerOpen, setDrawerOpen] = useState(false);
  const drawerCloseButtonRef = useRef<HTMLButtonElement | null>(null);
  const drawerReturnFocusRef = useRef<HTMLElement | null>(null);

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

  useEffect(() => {
    if (!drawerOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusTimer = window.setTimeout(() => drawerCloseButtonRef.current?.focus(), 0);
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      const hasUnsavedPanelInput = selectedSurfaces.length > 0 || observation.trim().length > 0;
      if (
        hasUnsavedPanelInput &&
        !window.confirm("Hay información del panel sin guardar. ¿Deseas descartarla?")
      ) {
        return;
      }
      setDrawerOpen(false);
      window.setTimeout(() => drawerReturnFocusRef.current?.focus(), 0);
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.clearTimeout(focusTimer);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [drawerOpen, observation, selectedSurfaces.length]);

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
  const selectedToothState = toothStateByCode.get(selectedTooth);
  const hasUnsavedPanelInput = selectedSurfaces.length > 0 || observation.trim().length > 0;

  function requestDiscardPanelInput() {
    if (!hasUnsavedPanelInput) return true;
    return window.confirm("Hay información del panel sin guardar. ¿Deseas descartarla?");
  }

  function openClinicalDrawer() {
    drawerReturnFocusRef.current = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    setDrawerOpen(true);
  }

  function closeClinicalDrawer() {
    if (!requestDiscardPanelInput()) return;
    setDrawerOpen(false);
    window.setTimeout(() => drawerReturnFocusRef.current?.focus(), 0);
  }

  function selectToothFromGrid(tooth: string) {
    if (tooth !== selectedTooth && !requestDiscardPanelInput()) return;
    if (tooth !== selectedTooth) {
      setSelectedTooth(tooth);
      setSelectedSurfaces([]);
      setObservation("");
    }
    openClinicalDrawer();
  }

  return (
    <div className={embedded ? "" : "mx-auto max-w-[96rem]"}>
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
        <section className={`${embedded ? "" : "mt-5"} rounded-[2rem] border border-slate-100 bg-slate-50/40 p-2 sm:p-2.5`}>
          <div className="rounded-[1.5rem] border border-slate-200 bg-white px-3 py-2 shadow-sm">
            <div className="flex flex-col gap-2 xl:flex-row xl:items-center xl:justify-between">
              <div className="flex flex-wrap items-center gap-2">
                <DentitionSelector value={dentition} onChange={setDentition} compact />
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-black uppercase tracking-wide text-slate-500">
                  Capas
                </span>
                {LAYERS.map(([layer, label]) => (
                  <button
                    key={layer}
                    type="button"
                    onClick={() => {
                      setVisibleLayers((prev) => {
                        const next = new Set(prev);
                        if (next.has(layer)) next.delete(layer);
                        else next.add(layer);
                        return next;
                      });
                    }}
                    aria-pressed={visibleLayers.has(layer)}
                    className={`rounded-full border px-2.5 py-1 text-[11px] font-black transition ${
                      visibleLayers.has(layer)
                        ? `${layerClass(layer)} border-transparent shadow-sm`
                        : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-3">
            <main className="min-w-0 space-y-3">
              <section className="overflow-visible rounded-[1.75rem] border border-slate-100 bg-white/80 p-2 sm:p-2.5">
                <div className="space-y-5">
                  {(dentition === "PERMANENT" || dentition === "MIXED") && (
                    <DualOdontogramGrid
                      title="Dentición permanente"
                      rows={PERMANENT_DUAL_ROWS}
                      selectedTooth={selectedTooth}
                      toothStateByCode={toothStateByCode}
                      visibleLayers={visibleLayers}
                      expanded
                      onSelect={selectToothFromGrid}
                    />
                  )}
                  {(dentition === "PRIMARY" || dentition === "MIXED") && (
                    <DualOdontogramGrid
                      title="Dentición temporal"
                      rows={PRIMARY_DUAL_ROWS}
                      selectedTooth={selectedTooth}
                      toothStateByCode={toothStateByCode}
                      visibleLayers={visibleLayers}
                      expanded
                      onSelect={selectToothFromGrid}
                    />
                  )}
                </div>
              </section>

              <CompactLegend />
            </main>

            {drawerOpen && (
              <aside
                aria-labelledby="odontogram-clinical-drawer-title"
                aria-modal="true"
                role="dialog"
                className="fixed inset-0 z-50"
              >
                <button
                  type="button"
                  aria-label="Cerrar panel clínico"
                  className="absolute inset-0 cursor-default bg-slate-950/20 backdrop-blur-[1px]"
                  onClick={closeClinicalDrawer}
                />
                <DentalInspector
                  toothCode={selectedTooth}
                  toothState={selectedToothState}
                  history={history}
                  drafts={events.filter((event) => event.status === "DRAFT")}
                  selectedSurfaces={selectedSurfaces}
                  warning={warning}
                  eventOptions={EVENT_OPTIONS}
                  eventType={eventType}
                  catalogItemId={catalogItemId}
                  availableCatalog={availableCatalog}
                  observation={observation}
                  saveAsConfirmed={saveAsConfirmed}
                  saving={saving}
                  canEditDraft={canEditDraft}
                  canConfirm={canConfirm}
                  closeButtonRef={drawerCloseButtonRef}
                  onClose={closeClinicalDrawer}
                  onToggleSurface={(value) => {
                    setSelectedSurfaces((prev) =>
                      prev.includes(value)
                        ? prev.filter((surface) => surface !== value)
                        : [...prev, value],
                    );
                  }}
                  onEventTypeChange={setEventType}
                  onCatalogItemChange={setCatalogItemId}
                  onObservationChange={setObservation}
                  onSaveAsConfirmedChange={setSaveAsConfirmed}
                  onSaveEvent={saveEvent}
                  onConfirmDraft={confirmDraft}
                />
              </aside>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

function DentitionSelector({
  value,
  onChange,
  compact = false,
}: {
  value: OdontogramDentition;
  onChange: (value: OdontogramDentition) => void;
  compact?: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`${compact ? "rounded-full px-1.5 py-1" : "rounded-2xl p-2"} border border-slate-200 bg-slate-50`}>
      <div className="flex flex-wrap items-center gap-1.5">
        <span className={`${compact ? "rounded-full px-2.5 py-1 text-xs" : "rounded-xl px-3 py-2 text-sm"} bg-white font-black text-slate-900 shadow-sm`}>
          Dentición: {DENTITION_LABELS[value]}
        </span>
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          className={`${compact ? "rounded-full px-2 py-1 text-xs" : "rounded-xl px-3 py-2 text-sm"} font-bold text-green-700 hover:bg-green-50`}
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

function CompactLegend() {
  const stateItems = [
    { label: "Diagnóstico / hallazgo", color: "bg-red-500", note: "rojo" },
    { label: "Tratamiento realizado", color: "bg-blue-500", note: "azul" },
    { label: "Tratamiento planificado", color: "bg-orange-400", note: "naranja" },
    { label: "Informativo / sin superficie", color: "bg-slate-400", note: "gris" },
    { label: "Seleccionado", color: "bg-green-600", note: "verde Dentia" },
  ];
  const symbolItems = [
    { label: "Endodoncia", symbol: "∿" },
    { label: "Corona / prótesis", symbol: "♛" },
    { label: "Implante", symbol: "⌁" },
    { label: "Ausente / extracción", symbol: "×" },
    { label: "Fractura", symbol: "Ⅱ" },
    { label: "Sin superficie", symbol: "?" },
    { label: "No superficial", symbol: "i" },
  ];
  return (
    <section className="rounded-[1.25rem] border border-slate-200 bg-white/90 px-3 py-2 shadow-sm">
      <div className="grid gap-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <h3 className="mr-1 shrink-0 text-xs font-black uppercase tracking-wide text-slate-500">Estados</h3>
            {stateItems.map((item) => (
              <span key={item.label} className="inline-flex items-center gap-1.5 rounded-full border border-slate-100 bg-slate-50 px-2.5 py-1 text-[10px] font-black text-slate-700">
              <span className={`h-2 w-2 rounded-full ${item.color}`} aria-hidden="true" />
              {item.label}
              <span className="font-semibold text-slate-400">{item.note}</span>
            </span>
            ))}
          </div>
          <p className="mt-1 text-[10px] font-semibold text-slate-500">
            El color representa el estado clínico.
          </p>
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <h3 className="mr-1 shrink-0 text-xs font-black uppercase tracking-wide text-slate-500">Símbolos clínicos</h3>
            {symbolItems.map((item) => (
              <span key={item.label} className="inline-flex items-center gap-1.5 rounded-full border border-slate-100 bg-slate-50 px-2.5 py-1 text-[10px] font-black text-slate-700">
                <span className="flex h-4 min-w-4 items-center justify-center rounded-full border border-slate-200 bg-white px-1 text-[10px] font-black text-slate-700" aria-hidden="true">
                  {item.symbol}
                </span>
                {item.label}
              </span>
            ))}
          </div>
          <p className="mt-1 text-[10px] font-semibold text-slate-500">
            La forma o símbolo representa el tipo clínico.
          </p>
        </div>
      </div>
    </section>
  );
}
