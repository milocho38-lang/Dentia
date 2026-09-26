"use client";

import {
  KeyboardEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  PeriodontalArchGraph,
  PeriodontalGraphLegend,
} from "@/components/periodontogram/PeriodontalGraph";
import {
  MAXILLARY_FDI,
  MANDIBULAR_FDI,
  MOLAR_FDI,
  buildCaptureSequence,
  calculateClinicalAttachmentLevel,
  calculateDraftIndicators,
  cycleTriState,
  describeSite,
  focusKey,
  isPocket,
  siteOrderForTooth,
  type PeriodontalCaptureMode,
  type PeriodontalFocusTarget,
  type PeriodontalMeasurement,
} from "@/lib/periodontalCharting";
import {
  PERIODONTAL_SITE_COLUMNS,
  countPocketSites,
} from "@/lib/periodontalGraph";
import type {
  PeriodontalDraftBatchUpdate,
  PeriodontalExam,
  PeriodontalSite,
  PeriodontalSiteCode,
  PeriodontalTooth,
  PeriodontalToothState,
} from "@/types/periodontogram";


type DraftMap = Record<number, PeriodontalTooth>;

const cloneTooth = (tooth: PeriodontalTooth): PeriodontalTooth => ({
  ...tooth,
  sites: tooth.sites.map((site) => ({ ...site })),
});

const toDraftMap = (teeth: PeriodontalTooth[]): DraftMap =>
  Object.fromEntries(teeth.map((tooth) => [tooth.fdi_number, cloneTooth(tooth)]));

const nullableNumber = (value: string): number | null => value === "" ? null : Number(value);

const toothHasClinicalData = (tooth: PeriodontalTooth) =>
  tooth.mobility_grade !== null ||
  tooth.furcation_mesial !== null ||
  tooth.furcation_distal !== null ||
  tooth.sites.some((site) =>
    [
      site.probing_depth_mm,
      site.gingival_margin_mm,
      site.bleeding_on_probing,
      site.plaque,
      site.suppuration,
    ].some((value) => value !== null),
  );

const clearedTooth = (
  tooth: PeriodontalTooth,
  state: PeriodontalToothState,
): PeriodontalTooth => ({
  ...tooth,
  state,
  mobility_grade: null,
  furcation_mesial: null,
  furcation_distal: null,
  sites: tooth.sites.map((site) => ({
    ...site,
    probing_depth_mm: null,
    gingival_margin_mm: null,
    clinical_attachment_level_mm: null,
    is_periodontal_pocket: false,
    bleeding_on_probing: null,
    plaque: null,
    suppuration: null,
  })),
});

export function RapidPeriodontalEditor({
  exam,
  saving,
  canEdit,
  readOnlyLabel,
  onSave,
  onDirtyChange,
}: {
  exam: PeriodontalExam;
  saving: boolean;
  canEdit: boolean;
  readOnlyLabel?: string;
  onSave: (payload: PeriodontalDraftBatchUpdate) => Promise<void>;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const originals = useMemo(() => toDraftMap(exam.teeth), [exam.teeth]);
  const [drafts, setDrafts] = useState<DraftMap>(() => toDraftMap(exam.teeth));
  const [activeFdi, setActiveFdi] = useState(exam.teeth[0]?.fdi_number ?? 18);
  const [captureMode, setCaptureMode] = useState<PeriodontalCaptureMode>("PD_GM");
  const [activeTarget, setActiveTarget] = useState<PeriodontalFocusTarget | null>(null);
  const [clearFdis, setClearFdis] = useState<Set<number>>(() => new Set());
  const inputRefs = useRef(new Map<string, HTMLInputElement>());

  const teeth = useMemo(
    () => exam.teeth.map((tooth) => drafts[tooth.fdi_number] ?? tooth),
    [drafts, exam.teeth],
  );
  const dirtyFdis = useMemo(
    () => teeth
      .filter((tooth) => JSON.stringify(tooth) !== JSON.stringify(originals[tooth.fdi_number]))
      .map((tooth) => tooth.fdi_number),
    [originals, teeth],
  );
  const dirty = dirtyFdis.length > 0;
  const indicators = useMemo(() => calculateDraftIndicators(teeth), [teeth]);
  const pocketSites = useMemo(() => countPocketSites(teeth), [teeth]);
  const sequence = useMemo(
    () => buildCaptureSequence(teeth, captureMode),
    [captureMode, teeth],
  );
  const activeTooth = drafts[activeFdi] ?? teeth[0];

  useEffect(() => onDirtyChange(dirty), [dirty, onDirtyChange]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const updateTooth = (fdiNumber: number, updater: (tooth: PeriodontalTooth) => PeriodontalTooth) => {
    setDrafts((current) => ({
      ...current,
      [fdiNumber]: updater(current[fdiNumber]),
    }));
  };

  const updateSite = (
    fdiNumber: number,
    siteCode: PeriodontalSiteCode,
    changes: Partial<PeriodontalSite>,
  ) => {
    updateTooth(fdiNumber, (tooth) => ({
      ...tooth,
      sites: tooth.sites.map((site) =>
        site.site_code === siteCode ? { ...site, ...changes } : site,
      ),
    }));
  };

  const changeToothState = (state: PeriodontalToothState) => {
    if (!activeTooth || state === activeTooth.state || !canEdit) return;
    const needsClear = toothHasClinicalData(activeTooth);
    if (
      needsClear &&
      !window.confirm(
        `Cambiar la pieza ${activeTooth.fdi_number} a ${state === "ABSENT" ? "ausente" : state === "IMPLANT" ? "implante" : "presente"} limpiará sus mediciones clínicas de este borrador. ¿Deseas continuar?`,
      )
    ) {
      return;
    }
    updateTooth(activeTooth.fdi_number, (tooth) =>
      needsClear
        ? clearedTooth(tooth, state)
        : {
            ...tooth,
            state,
            mobility_grade: state === "PRESENT" ? tooth.mobility_grade : null,
            furcation_mesial: state === "PRESENT" && MOLAR_FDI.has(tooth.fdi_number) ? tooth.furcation_mesial : null,
            furcation_distal: state === "PRESENT" && MOLAR_FDI.has(tooth.fdi_number) ? tooth.furcation_distal : null,
          },
    );
    if (needsClear) {
      setClearFdis((current) => new Set(current).add(activeTooth.fdi_number));
    }
  };

  const focusSequenceTarget = (target: PeriodontalFocusTarget) => {
    setActiveFdi(target.fdiNumber);
    setActiveTarget(target);
    const input = inputRefs.current.get(target.key);
    input?.focus({ preventScroll: true });
    input?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
  };

  const moveFrom = (key: string, direction: 1 | -1) => {
    const index = sequence.findIndex((target) => target.key === key);
    if (index < 0) return;
    const next = sequence[index + direction];
    if (next) focusSequenceTarget(next);
  };

  const selectGraphTooth = (fdiNumber: number) => {
    setActiveFdi(fdiNumber);
    const firstTarget = sequence.find((target) => target.fdiNumber === fdiNumber);
    if (!firstTarget) {
      setActiveTarget(null);
      return;
    }
    if (canEdit) focusSequenceTarget(firstTarget);
    else setActiveTarget(firstTarget);
  };

  const selectGraphSite = (fdiNumber: number, siteCode: PeriodontalSiteCode) => {
    const preferredMeasurement: PeriodontalMeasurement = captureMode === "GM" ? "GM" : "PD";
    const target = sequence.find((candidate) =>
      candidate.fdiNumber === fdiNumber &&
      candidate.siteCode === siteCode &&
      candidate.measurement === preferredMeasurement,
    );
    if (!target) return;
    if (canEdit) focusSequenceTarget(target);
    else {
      setActiveFdi(fdiNumber);
      setActiveTarget(target);
    }
  };

  const selectInputTarget = (target: PeriodontalFocusTarget) => {
    setActiveFdi(target.fdiNumber);
    setActiveTarget(target);
  };

  const handleMeasurementKey = (
    event: KeyboardEvent<HTMLInputElement>,
    target: PeriodontalFocusTarget,
  ) => {
    if (event.key === "Tab" && event.shiftKey) return;
    if (event.key === "Enter") {
      if (event.currentTarget.value === "") return;
      event.preventDefault();
      moveFrom(target.key, 1);
      return;
    }
    if (event.key === "Backspace" && event.currentTarget.value === "") {
      event.preventDefault();
      moveFrom(target.key, -1);
    }
  };

  const saveBatch = async () => {
    if (!dirty || saving) return;
    const changedTeeth = teeth.filter((tooth) => dirtyFdis.includes(tooth.fdi_number));
    await onSave({
      row_version: exam.row_version,
      teeth: changedTeeth.map((tooth) => ({
        fdi_number: tooth.fdi_number,
        state: tooth.state,
        mobility_grade: tooth.state === "PRESENT" ? tooth.mobility_grade : null,
        furcation_mesial:
          tooth.state === "PRESENT" && MOLAR_FDI.has(tooth.fdi_number)
            ? tooth.furcation_mesial
            : null,
        furcation_distal:
          tooth.state === "PRESENT" && MOLAR_FDI.has(tooth.fdi_number)
            ? tooth.furcation_distal
            : null,
        clinical_note: tooth.clinical_note,
        clear_clinical_data: clearFdis.has(tooth.fdi_number),
      })),
      sites: changedTeeth.flatMap((tooth) =>
        tooth.state === "ABSENT"
          ? []
          : tooth.sites.map((site) => ({
              fdi_number: tooth.fdi_number,
              site_code: site.site_code,
              probing_depth_mm: site.probing_depth_mm,
              gingival_margin_mm: site.gingival_margin_mm,
              bleeding_on_probing: site.bleeding_on_probing,
              plaque: site.plaque,
              suppuration: tooth.state === "IMPLANT" ? site.suppuration : null,
            })),
      ),
    });
  };

  if (!activeTooth) return null;
  const context = activeTarget
    ? `Pieza ${activeTarget.fdiNumber} · ${activeTarget.face === "BUCCAL" ? "Vestibular" : activeTarget.face === "PALATAL" ? "Palatino" : "Lingual"} · ${activeTarget.siteLabel} · ${activeTarget.measurement === "PD" ? "Profundidad de sondaje" : "Margen gingival"}`
    : `Pieza ${activeTooth.fdi_number}`;

  return (
    <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50" aria-label="Captura clínica periodontal rápida">
      <div className="sticky top-2 z-20 border-b border-slate-200 bg-white/95 p-4 shadow-sm backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-green-700">Pieza activa</p>
            <p className="mt-1 font-black text-slate-950" aria-live="polite">{context}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-3 py-1.5 text-xs font-bold ${dirty ? "bg-amber-100 text-amber-900" : "bg-emerald-100 text-emerald-800"}`} aria-live="polite">
              {readOnlyLabel ?? (saving ? "Guardando…" : dirty ? "Cambios sin guardar" : "Guardado")}
            </span>
            {canEdit && (
              <button
                type="button"
                className="rounded-xl bg-green-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
                disabled={!dirty || saving}
                onClick={() => void saveBatch()}
              >
                Guardar cambios
              </button>
            )}
          </div>
        </div>

        <div className="mt-3 grid gap-3 lg:grid-cols-[auto_1fr] lg:items-end">
          <fieldset>
            <legend className="text-xs font-bold uppercase tracking-wide text-slate-500">Captura</legend>
            <div className="mt-1 inline-flex rounded-xl border border-slate-200 bg-slate-50 p-1">
              {(["PD", "GM", "PD_GM"] as PeriodontalCaptureMode[]).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  aria-pressed={captureMode === mode}
                  disabled={!canEdit}
                  onClick={() => setCaptureMode(mode)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-bold disabled:cursor-not-allowed disabled:opacity-60 ${captureMode === mode ? "bg-slate-900 text-white" : "text-slate-600"}`}
                >
                  {mode === "PD_GM"
                    ? "Profundidad + margen"
                    : mode === "PD"
                      ? "Profundidad"
                      : "Margen"}
                </button>
              ))}
            </div>
          </fieldset>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
            <Metric label="Cobertura" value={`${indicators.coverage.evaluated_sites}/${indicators.coverage.eligible_sites}`} title="Sitios con profundidad de sondaje y margen gingival / sitios elegibles" />
            <Metric label="% sangrado" value={indicators.indices.bop.percentage === null ? "—" : `${indicators.indices.bop.percentage}%`} title="Sitios con sangrado al sondaje / sitios evaluados" />
            <Metric label="% placa" value={indicators.indices.plaque.percentage === null ? "—" : `${indicators.indices.plaque.percentage}%`} title="Sitios con placa / sitios con placa evaluada" />
            <Metric label="Sitios ≥4 mm" value={String(pocketSites)} title="Ayuda visual por profundidad de sondaje; no constituye diagnóstico" />
            <Metric label="Estado" value={exam.status === "DRAFT" ? "Borrador" : "Finalizado"} />
          </div>
        </div>
      </div>

      <div className="space-y-5 p-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.16em] text-green-700">Matriz clínica</p>
              <h3 className="mt-1 text-lg font-black text-slate-950">Periodontograma</h3>
              <p className="mt-1 max-w-3xl text-xs text-slate-600">
                Mediciones y gráfico comparten el mismo eje dental. Los sitios sin medición permanecen vacíos y cortan las curvas.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {indicators.coverage.incomplete && <span className="rounded-full bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-800">Cobertura parcial</span>}
              <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700">
                {canEdit ? "Captura y gráfico sincronizados" : "Consulta de solo lectura"}
              </span>
            </div>
          </div>
          <div className="mt-3"><PeriodontalGraphLegend /></div>
        </div>

        <ToothControls
          tooth={activeTooth}
          canEdit={canEdit}
          onStateChange={changeToothState}
          onChange={(changes) => updateTooth(activeTooth.fdi_number, (tooth) => ({ ...tooth, ...changes }))}
        />

        <ArchChart
          arch="MAXILLARY"
          title="Maxilar"
          fdiNumbers={MAXILLARY_FDI}
          drafts={drafts}
          activeFdi={activeFdi}
          activeTarget={activeTarget}
          canEdit={canEdit}
          onActivate={setActiveFdi}
          onGraphSelectTooth={selectGraphTooth}
          onGraphSelectSite={selectGraphSite}
          onFocus={selectInputTarget}
          onMeasurement={(fdiNumber, siteCode, measurement, value) =>
            updateSite(
              fdiNumber,
              siteCode,
              measurement === "PD"
                ? { probing_depth_mm: value }
                : { gingival_margin_mm: value },
            )
          }
          onTriState={(fdiNumber, siteCode, field) =>
            updateSite(fdiNumber, siteCode, {
              [field]: cycleTriState(
                drafts[fdiNumber].sites.find((site) => site.site_code === siteCode)?.[field] ?? null,
              ),
            })
          }
          onKeyDown={handleMeasurementKey}
          inputRefs={inputRefs}
        />

        <ArchChart
          arch="MANDIBULAR"
          title="Mandíbula"
          fdiNumbers={MANDIBULAR_FDI}
          drafts={drafts}
          activeFdi={activeFdi}
          activeTarget={activeTarget}
          canEdit={canEdit}
          onActivate={setActiveFdi}
          onGraphSelectTooth={selectGraphTooth}
          onGraphSelectSite={selectGraphSite}
          onFocus={selectInputTarget}
          onMeasurement={(fdiNumber, siteCode, measurement, value) =>
            updateSite(
              fdiNumber,
              siteCode,
              measurement === "PD"
                ? { probing_depth_mm: value }
                : { gingival_margin_mm: value },
            )
          }
          onTriState={(fdiNumber, siteCode, field) =>
            updateSite(fdiNumber, siteCode, {
              [field]: cycleTriState(
                drafts[fdiNumber].sites.find((site) => site.site_code === siteCode)?.[field] ?? null,
              ),
            })
          }
          onKeyDown={handleMeasurementKey}
          inputRefs={inputRefs}
        />

        <p className="text-xs text-slate-500">
          Enter avanza según el modo de captura. Shift+Tab retrocede de forma nativa y Backspace sobre un campo vacío vuelve a la medición anterior. En móvil se prioriza la edición de la pieza activa mediante scroll local.
        </p>
      </div>
    </section>
  );
}

function Metric({ label, value, title }: { label: string; value: string; title?: string }) {
  return (
    <div className="rounded-xl bg-slate-50 px-3 py-2 text-center" title={title}>
      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="font-black text-slate-900">{value}</p>
    </div>
  );
}

function ToothControls({
  tooth,
  canEdit,
  onStateChange,
  onChange,
}: {
  tooth: PeriodontalTooth;
  canEdit: boolean;
  onStateChange: (state: PeriodontalToothState) => void;
  onChange: (changes: Partial<PeriodontalTooth>) => void;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Panel contextual</p>
          <h4 className="text-lg font-black text-slate-950">Pieza seleccionada: {tooth.fdi_number}</h4>
        </div>
        <div className="flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1" aria-label={`Estado de la pieza ${tooth.fdi_number}`}>
          {([
            ["PRESENT", "Presente"],
            ["ABSENT", "Ausente"],
            ["IMPLANT", "Implante"],
          ] as Array<[PeriodontalToothState, string]>).map(([state, label]) => (
            <button
              key={state}
              type="button"
              disabled={!canEdit}
              aria-pressed={tooth.state === state}
              className={`rounded-lg px-3 py-2 text-xs font-bold disabled:cursor-not-allowed ${tooth.state === state ? "bg-white text-green-800 shadow-sm" : "text-slate-600"}`}
              onClick={() => onStateChange(state)}
            >
              {state === "IMPLANT" && <span aria-hidden="true">◆ </span>}{label}
            </button>
          ))}
        </div>
      </div>

      {tooth.state === "PRESENT" && (
        <div className="mt-4 flex flex-wrap gap-4">
          <fieldset>
            <legend className="text-xs font-bold uppercase tracking-wide text-slate-500">Movilidad</legend>
            <div className="mt-1 flex rounded-xl border border-slate-200 p-1">
              {[null, 0, 1, 2, 3].map((value) => (
                <button
                  key={value ?? "null"}
                  type="button"
                  disabled={!canEdit}
                  aria-pressed={tooth.mobility_grade === value}
                  className={`min-h-9 min-w-10 rounded-lg px-2 text-xs font-bold ${tooth.mobility_grade === value ? "bg-slate-900 text-white" : "text-slate-600"}`}
                  onClick={() => onChange({ mobility_grade: value })}
                >
                  {value ?? "—"}
                </button>
              ))}
            </div>
          </fieldset>
          {MOLAR_FDI.has(tooth.fdi_number) && (
            <fieldset>
              <legend className="text-xs font-bold uppercase tracking-wide text-slate-500">Furcación</legend>
              <div className="mt-1 flex gap-2">
                <QuickTriState label="M" value={tooth.furcation_mesial} disabled={!canEdit} onChange={(value) => onChange({ furcation_mesial: value })} />
                <QuickTriState label="D" value={tooth.furcation_distal} disabled={!canEdit} onChange={(value) => onChange({ furcation_distal: value })} />
              </div>
            </fieldset>
          )}
        </div>
      )}

      <details className="mt-4 rounded-xl bg-slate-50 p-3">
        <summary className="cursor-pointer text-sm font-bold text-slate-700">Nota clínica de la pieza</summary>
        <textarea
          className="mt-3 min-h-20 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm disabled:bg-slate-100"
          value={tooth.clinical_note ?? ""}
          maxLength={1000}
          disabled={!canEdit}
          aria-label={`Nota clínica de la pieza ${tooth.fdi_number}`}
          onChange={(event) => onChange({ clinical_note: event.target.value || null })}
        />
      </details>
    </div>
  );
}

type TriStateField = "bleeding_on_probing" | "plaque" | "suppuration";

interface ArchChartProps {
  arch: "MAXILLARY" | "MANDIBULAR";
  title: string;
  fdiNumbers: readonly number[];
  drafts: DraftMap;
  activeFdi: number;
  activeTarget: PeriodontalFocusTarget | null;
  canEdit: boolean;
  onActivate: (fdiNumber: number) => void;
  onGraphSelectTooth: (fdiNumber: number) => void;
  onGraphSelectSite: (fdiNumber: number, siteCode: PeriodontalSiteCode) => void;
  onFocus: (target: PeriodontalFocusTarget) => void;
  onMeasurement: (
    fdiNumber: number,
    siteCode: PeriodontalSiteCode,
    measurement: PeriodontalMeasurement,
    value: number | null,
  ) => void;
  onTriState: (fdiNumber: number, siteCode: PeriodontalSiteCode, field: TriStateField) => void;
  onKeyDown: (event: KeyboardEvent<HTMLInputElement>, target: PeriodontalFocusTarget) => void;
  inputRefs: React.MutableRefObject<Map<string, HTMLInputElement>>;
}

function ArchChart(props: ArchChartProps) {
  const secondaryFace = props.arch === "MAXILLARY" ? "Palatino" : "Lingual";
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white" aria-labelledby={`arch-${props.title}`}>
      <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-2">
        <h4 id={`arch-${props.title}`} className="text-sm font-black uppercase tracking-[0.16em] text-slate-700">
          {props.title}
        </h4>
        <span className="text-xs text-slate-500">16 posiciones · seis sitios por pieza</span>
      </div>
      <div className="max-w-full overflow-x-auto overscroll-x-contain [scrollbar-gutter:stable]" tabIndex={0} data-compact-periodontal-arch={props.arch}>
        <div className="min-w-[1200px]" data-periodontal-site-columns="48">
          <ToothNumberRow {...props} />
          <ToothSummaryRow {...props} label="Movilidad" kind="MOBILITY" />
          <ToothSummaryRow {...props} label="Implante" kind="IMPLANT" />
          <ToothSummaryRow {...props} label="Furcación" kind="FURCATION" />

          <FaceMatrix {...props} face="BUCCAL" label="Vestibular" />
          <FaceGraph {...props} face="BUCCAL" label="Vestibular" />

          <FaceMatrix {...props} face="LINGUAL" label={secondaryFace} />
          <FaceGraph {...props} face="LINGUAL" label={secondaryFace} />
        </div>
      </div>
    </section>
  );
}

const compactGridStyle = {
  gridTemplateColumns: `176px repeat(${PERIODONTAL_SITE_COLUMNS}, minmax(0, 1fr))`,
};

function FaceGraph(props: ArchChartProps & { face: "BUCCAL" | "LINGUAL"; label: string }) {
  return (
    <CompactRow
      label={(
        <span>
          <span className="block">Gráfico periodontal</span>
          <span className="mt-0.5 block text-[10px] font-semibold text-slate-500">
            {props.label} · <span data-gm-zero-gutter-label="true">Margen gingival = 0</span>
          </span>
        </span>
      )}
      tone="graph"
    >
      <div
        className="min-w-0 overflow-hidden"
        style={{ gridColumn: `span ${PERIODONTAL_SITE_COLUMNS} / span ${PERIODONTAL_SITE_COLUMNS}` }}
        data-periodontal-graph-column-span={PERIODONTAL_SITE_COLUMNS}
      >
        <PeriodontalArchGraph
          teeth={props.fdiNumbers.map((fdiNumber) => props.drafts[fdiNumber])}
          arch={props.arch}
          face={props.face}
          faceLabel={props.label}
          activeFdi={props.activeFdi}
          activeSiteCode={props.activeTarget?.siteCode ?? null}
          onSelectTooth={props.onGraphSelectTooth}
          onSelectSite={props.onGraphSelectSite}
        />
      </div>
    </CompactRow>
  );
}

function CompactRow({
  label,
  children,
  tone = "default",
}: {
  label: React.ReactNode;
  children: React.ReactNode;
  tone?: "default" | "heading" | "graph";
}) {
  return (
    <div
      className={`grid border-b border-slate-100 ${tone === "heading" ? "bg-slate-100" : tone === "graph" ? "bg-white" : "bg-white"}`}
      style={compactGridStyle}
    >
      <div className={`sticky left-0 z-10 flex items-center border-r border-slate-200 px-3 font-bold text-slate-700 ${tone === "graph" ? "bg-white text-xs" : tone === "heading" ? "bg-slate-100 py-2 text-xs uppercase tracking-wide" : "bg-white py-1 text-xs"}`}>
        {label}
      </div>
      {children}
    </div>
  );
}

function ToothNumberRow(props: ArchChartProps) {
  return (
    <CompactRow label="Pieza" tone="heading">
      {props.fdiNumbers.map((fdiNumber, index) => {
        const tooth = props.drafts[fdiNumber];
        return (
          <button
            key={fdiNumber}
            type="button"
            style={{ gridColumn: "span 3" }}
            className={`relative min-h-10 border-r border-slate-200 text-sm font-black focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-600 ${index === 8 ? "border-l-2 border-l-slate-400" : ""} ${props.activeFdi === fdiNumber ? "bg-green-100 text-green-900" : "bg-slate-50 text-slate-900"}`}
            aria-pressed={props.activeFdi === fdiNumber}
            aria-label={`Seleccionar pieza ${fdiNumber}`}
            onClick={() => props.onActivate(fdiNumber)}
          >
            {fdiNumber}
            {tooth.state === "ABSENT" && <span className="ml-1 text-slate-500" aria-label="Ausente">×</span>}
            {tooth.state === "IMPLANT" && <span className="ml-1 text-sky-700" aria-label="Implante">I</span>}
          </button>
        );
      })}
    </CompactRow>
  );
}

function ToothSummaryRow(props: ArchChartProps & { label: string; kind: "MOBILITY" | "IMPLANT" | "FURCATION" }) {
  return (
    <CompactRow label={props.label}>
      {props.fdiNumbers.map((fdiNumber, index) => {
        const tooth = props.drafts[fdiNumber];
        let value = "—";
        if (props.kind === "MOBILITY" && tooth.state === "PRESENT" && tooth.mobility_grade !== null) value = String(tooth.mobility_grade);
        if (props.kind === "IMPLANT" && tooth.state === "IMPLANT") value = "I";
        if (props.kind === "IMPLANT" && tooth.state === "ABSENT") value = "×";
        if (props.kind === "FURCATION" && MOLAR_FDI.has(fdiNumber) && tooth.state === "PRESENT") {
          const marker = (prefix: "M" | "D", state: boolean | null) =>
            `${prefix}${state === null ? "—" : state ? "●" : "○"}`;
          value = `${marker("M", tooth.furcation_mesial)} ${marker("D", tooth.furcation_distal)}`;
        }
        return (
          <button
            key={fdiNumber}
            type="button"
            style={{ gridColumn: "span 3" }}
            className={`min-h-7 border-r border-slate-100 px-0.5 text-[10px] font-bold focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-600 ${index === 8 ? "border-l-2 border-l-slate-400" : ""} ${props.activeFdi === fdiNumber ? "bg-green-50 text-green-900" : "text-slate-600"}`}
            onClick={() => props.onActivate(fdiNumber)}
            aria-label={`${props.label}, pieza ${fdiNumber}: ${value}`}
          >
            {value}
          </button>
        );
      })}
    </CompactRow>
  );
}

function FaceMatrix(props: ArchChartProps & { face: "BUCCAL" | "LINGUAL"; label: string }) {
  return (
    <div data-periodontal-face={props.face}>
      <CompactRow label={props.label} tone="heading">
        {props.fdiNumbers.flatMap((fdiNumber, toothIndex) =>
          faceSites(props.drafts[fdiNumber], props.face).map((site, siteIndex) => (
            <button
              key={`${fdiNumber}:${site.site_code}:label`}
              type="button"
              className={`min-h-7 border-r border-slate-200 text-[9px] font-black text-slate-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-600 ${toothIndex === 8 && siteIndex === 0 ? "border-l-2 border-l-slate-400" : ""}`}
              aria-label={`Seleccionar pieza ${fdiNumber}, ${props.label} ${describeSite(fdiNumber, site.site_code).siteLabel.toLowerCase()}`}
              onClick={() => props.onActivate(fdiNumber)}
            >
              {describeSite(fdiNumber, site.site_code).siteLabel.charAt(0)}
            </button>
          )),
        )}
      </CompactRow>
      <BooleanSiteRow {...props} label="Sangrado al sondaje" field="bleeding_on_probing" kind="BOP" />
      <BooleanSiteRow {...props} label="Placa" field="plaque" kind="PLAQUE" />
      <BooleanSiteRow {...props} label="Supuración" field="suppuration" kind="SUPPURATION" />
      <MeasurementSiteRow {...props} label="Margen gingival" measurement="GM" />
      <MeasurementSiteRow {...props} label="Profundidad de sondaje" measurement="PD" />
      <ClinicalAttachmentRow {...props} />
    </div>
  );
}

function faceSites(tooth: PeriodontalTooth, face: "BUCCAL" | "LINGUAL") {
  const ordered = siteOrderForTooth(tooth.fdi_number)
    .map((siteCode) => tooth.sites.find((site) => site.site_code === siteCode))
    .filter((site): site is PeriodontalSite => Boolean(site));
  return face === "BUCCAL" ? ordered.slice(0, 3) : ordered.slice(3, 6);
}

function BooleanSiteRow(props: ArchChartProps & {
  face: "BUCCAL" | "LINGUAL";
  label: string;
  field: TriStateField;
  kind: "BOP" | "PLAQUE" | "SUPPURATION";
}) {
  return (
    <CompactRow label={props.label}>
      {props.fdiNumbers.flatMap((fdiNumber, toothIndex) => {
        const tooth = props.drafts[fdiNumber];
        return faceSites(tooth, props.face).map((site, siteIndex) => {
          const disabledForState = tooth.state === "ABSENT" || (props.field === "suppuration" && tooth.state !== "IMPLANT");
          const descriptor = describeSite(fdiNumber, site.site_code);
          return (
            <SiteTriState
              key={`${fdiNumber}:${site.site_code}:${props.field}`}
              label={`Pieza ${fdiNumber}, ${descriptor.face.toLowerCase()} ${descriptor.siteLabel.toLowerCase()}, ${props.label.toLowerCase()}`}
              value={disabledForState ? null : site[props.field]}
              disabled={!props.canEdit || disabledForState}
              kind={props.kind}
              midline={toothIndex === 8 && siteIndex === 0}
              onClick={() => {
                props.onActivate(fdiNumber);
                props.onTriState(fdiNumber, site.site_code, props.field);
              }}
            />
          );
        });
      })}
    </CompactRow>
  );
}

function MeasurementSiteRow(props: ArchChartProps & {
  face: "BUCCAL" | "LINGUAL";
  label: string;
  measurement: PeriodontalMeasurement;
}) {
  return (
    <CompactRow label={props.label}>
      {props.fdiNumbers.flatMap((fdiNumber, toothIndex) => {
        const tooth = props.drafts[fdiNumber];
        return faceSites(tooth, props.face).map((site, siteIndex) =>
          tooth.state === "ABSENT" ? (
            <span
              key={`${fdiNumber}:${site.site_code}:${props.measurement}`}
              className={`flex min-h-8 items-center justify-center border-r border-slate-100 bg-slate-50 text-[10px] text-slate-300 ${toothIndex === 8 && siteIndex === 0 ? "border-l-2 border-l-slate-400" : ""}`}
              aria-label={`Pieza ${fdiNumber} ausente`}
            >
              —
            </span>
          ) : (
            <MeasurementInput
              key={`${fdiNumber}:${site.site_code}:${props.measurement}`}
              tooth={tooth}
              site={site}
              measurement={props.measurement}
              active={props.activeTarget?.key === focusKey(fdiNumber, site.site_code, props.measurement)}
              canEdit={props.canEdit}
              midline={toothIndex === 8 && siteIndex === 0}
              onFocus={props.onFocus}
              onChange={props.onMeasurement}
              onKeyDown={props.onKeyDown}
              inputRefs={props.inputRefs}
            />
          ),
        );
      })}
    </CompactRow>
  );
}

function ClinicalAttachmentRow(props: ArchChartProps & { face: "BUCCAL" | "LINGUAL" }) {
  return (
    <CompactRow label="Nivel de inserción">
      {props.fdiNumbers.flatMap((fdiNumber, toothIndex) => {
        const tooth = props.drafts[fdiNumber];
        return faceSites(tooth, props.face).map((site, siteIndex) => {
          const cal = tooth.state === "ABSENT"
            ? null
            : calculateClinicalAttachmentLevel(site.probing_depth_mm, site.gingival_margin_mm);
          return (
            <button
              key={`${fdiNumber}:${site.site_code}:CAL`}
              type="button"
              disabled={tooth.state === "ABSENT"}
              className={`relative min-h-8 border-r border-slate-100 text-[11px] font-black focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-600 ${toothIndex === 8 && siteIndex === 0 ? "border-l-2 border-l-slate-400" : ""} ${isPocket(site.probing_depth_mm) && tooth.state !== "ABSENT" ? "bg-amber-100 text-amber-950" : "text-slate-700"}`}
              title={isPocket(site.probing_depth_mm) ? "Profundidad de sondaje mayor o igual a 4 mm" : undefined}
              aria-label={`Pieza ${fdiNumber}, nivel de inserción ${cal === null ? "no disponible" : `${cal} milímetros`}`}
              onClick={() => props.onActivate(fdiNumber)}
            >
              {cal ?? "—"}
              {isPocket(site.probing_depth_mm) && tooth.state !== "ABSENT" && <span className="absolute right-0 top-0 text-amber-700" aria-label="Profundidad mayor o igual a 4 milímetros">•</span>}
            </button>
          );
        });
      })}
    </CompactRow>
  );
}

function MeasurementInput({
  tooth,
  site,
  measurement,
  active,
  canEdit,
  midline,
  onFocus,
  onChange,
  onKeyDown,
  inputRefs,
}: {
  tooth: PeriodontalTooth;
  site: PeriodontalSite;
  measurement: PeriodontalMeasurement;
  active: boolean;
  canEdit: boolean;
  midline: boolean;
  onFocus: (target: PeriodontalFocusTarget) => void;
  onChange: ArchChartProps["onMeasurement"];
  onKeyDown: ArchChartProps["onKeyDown"];
  inputRefs: ArchChartProps["inputRefs"];
}) {
  const descriptor = describeSite(tooth.fdi_number, site.site_code);
  const target: PeriodontalFocusTarget = {
    key: focusKey(tooth.fdi_number, site.site_code, measurement),
    fdiNumber: tooth.fdi_number,
    siteCode: site.site_code,
    measurement,
    ...descriptor,
  };
  const value = measurement === "PD" ? site.probing_depth_mm : site.gingival_margin_mm;
  return (
    <input
      ref={(element) => {
        if (element) inputRefs.current.set(target.key, element);
        else inputRefs.current.delete(target.key);
      }}
      className={`h-8 min-w-0 border-0 border-r border-slate-200 px-0 text-center text-[11px] font-bold outline-none [appearance:textfield] focus:relative focus:z-10 focus:ring-2 focus:ring-inset focus:ring-green-600 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none ${midline ? "border-l-2 border-l-slate-400" : ""} ${active ? "bg-green-100 text-green-950" : isPocket(site.probing_depth_mm) && measurement === "PD" ? "bg-amber-100 text-amber-950" : "bg-white text-slate-900"}`}
      type="number"
      inputMode={measurement === "GM" ? "decimal" : "numeric"}
      min={measurement === "PD" ? 0 : -50}
      max={50}
      value={value ?? ""}
      disabled={!canEdit}
      aria-label={`Pieza ${tooth.fdi_number}, ${descriptor.face === "BUCCAL" ? "vestibular" : descriptor.face === "PALATAL" ? "palatino" : "lingual"} ${descriptor.siteLabel.toLowerCase()}, ${measurement === "PD" ? "profundidad de sondaje" : "margen gingival"}`}
      onFocus={() => onFocus(target)}
      onChange={(event) => onChange(tooth.fdi_number, site.site_code, measurement, nullableNumber(event.target.value))}
      onKeyDown={(event) => onKeyDown(event, target)}
    />
  );
}

function SiteTriState({
  label,
  value,
  disabled,
  kind,
  midline,
  onClick,
}: {
  label: string;
  value: boolean | null;
  disabled: boolean;
  kind: "BOP" | "PLAQUE" | "SUPPURATION";
  midline: boolean;
  onClick: () => void;
}) {
  const symbol = value === null
    ? "—"
    : kind === "BOP"
      ? value ? "●" : "○"
      : kind === "PLAQUE"
        ? value ? "■" : "□"
        : value ? "◆" : "◇";
  const positiveClass = kind === "BOP"
    ? "text-red-700"
    : kind === "PLAQUE"
      ? "text-violet-700"
      : "text-teal-700";
  return (
    <button
      type="button"
      disabled={disabled}
      aria-label={`${label}: ${value === null ? "no evaluado" : value ? "sí" : "no"}`}
      className={`h-7 min-w-0 border-0 border-r border-slate-100 bg-white text-[11px] font-black focus:relative focus:z-10 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-600 disabled:cursor-not-allowed ${midline ? "border-l-2 border-l-slate-400" : ""} ${value === null ? "text-slate-300" : value ? positiveClass : "text-slate-400"}`}
      onClick={onClick}
    >
      {symbol}
    </button>
  );
}

function QuickTriState({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string;
  value: boolean | null;
  disabled: boolean;
  onChange: (value: boolean | null) => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      aria-label={`Furcación ${label}, ${value === null ? "no evaluada" : value ? "presente" : "ausente"}`}
      className={`min-h-10 min-w-14 rounded-xl border px-3 text-sm font-black ${value === null ? "border-dashed border-slate-300 text-slate-500" : value ? "border-rose-400 bg-rose-100 text-rose-800" : "border-emerald-300 bg-emerald-50 text-emerald-800"}`}
      onClick={() => onChange(cycleTriState(value))}
    >
      {label} · {value === null ? "—" : value ? "Sí" : "No"}
    </button>
  );
}
