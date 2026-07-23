"use client";

import Link from "next/link";
import { useMemo, useState, type KeyboardEvent } from "react";
import { Tooth } from "@/components/odontogram/Tooth";
import type { OdontogramEvent } from "@/types/odontogram";
import { AddPlannedProcedureDialog } from "./AddPlannedProcedureDialog";
import {
  INSPECTOR_SURFACES,
  anatomicalToothName,
  buildInspectorModel,
  eventBelongsToTooth,
  eventCardBadges,
  eventCardTitle,
  eventStatusLabel,
  eventSurfaceLabel,
  formatInspectorEventDate,
  toothDentitionLabel,
} from "./dentalInspectorMapper";
import type { DentalInspectorProps, DentalInspectorTab } from "./types";

const TABS: Array<{ id: DentalInspectorTab; label: string }> = [
  { id: "summary", label: "Resumen" },
  { id: "history", label: "Historial" },
  { id: "register", label: "Registrar" },
  { id: "drafts", label: "Borradores" },
];

function layerClass(layer: string) {
  const classes: Record<string, string> = {
    STRUCTURAL: "bg-slate-100 text-slate-700",
    FINDING: "bg-red-100 text-red-700",
    DIAGNOSIS: "bg-rose-100 text-rose-800",
    PLANNED: "bg-orange-100 text-orange-800",
    PERFORMED: "bg-blue-100 text-blue-800",
    OBSERVATION: "bg-sky-100 text-sky-800",
  };
  return classes[layer] ?? "bg-slate-100 text-slate-700";
}

function statusBadgeClass(status: OdontogramEvent["status"]) {
  if (status === "CONFIRMED") return "bg-green-50 text-green-700";
  if (status === "DRAFT") return "bg-amber-50 text-amber-700";
  return "bg-slate-100 text-slate-600";
}

function statusLabel(status: OdontogramEvent["status"]) {
  if (status === "CONFIRMED") return "Confirmado";
  if (status === "DRAFT") return "Borrador";
  return "Compensado";
}

function money(value: string | number | null | undefined) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(value ?? 0));
}

function plannedProcedureCountLabel(count: number) {
  return count === 1 ? "1 procedimiento en el plan" : `${count} procedimientos en el plan`;
}

function LinkedPlannedProcedureCard({
  procedure,
  patientId,
}: {
  procedure: DentalInspectorProps["linkedProcedures"][number];
  patientId: string;
}) {
  return (
    <article className="rounded-2xl border border-green-100 bg-white p-3 shadow-sm">
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-[11px] font-black uppercase tracking-wide text-slate-500">Procedimiento</dt>
          <dd className="mt-0.5 font-black text-slate-950">{procedure.name}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-black uppercase tracking-wide text-slate-500">Tratamiento</dt>
          <dd className="mt-0.5 font-black text-slate-950">{procedure.treatment_name}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-black uppercase tracking-wide text-slate-500">Estado del tratamiento</dt>
          <dd className="mt-0.5">
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-black text-slate-700">
              {procedure.treatment_status}
            </span>
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-black uppercase tracking-wide text-slate-500">Estado del procedimiento</dt>
          <dd className="mt-0.5">
            <span className="rounded-full bg-orange-50 px-2 py-1 text-xs font-black text-orange-700">
              {procedure.status}
            </span>
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-black uppercase tracking-wide text-slate-500">Alcance</dt>
          <dd className="mt-0.5 font-bold text-slate-700">{procedure.scope_label}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-black uppercase tracking-wide text-slate-500">Valor planificado</dt>
          <dd className="mt-0.5 font-black text-slate-950">{money(procedure.total_value)}</dd>
        </div>
      </dl>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link
          href={`/tratamientos/${procedure.treatment_id}?returnPatientId=${patientId}`}
          className="inline-flex min-h-9 items-center rounded-xl bg-dentia-primary px-3 text-xs font-black text-white"
        >
          Ver tratamiento
        </Link>
      </div>
    </article>
  );
}

function handleTabKeyDown(
  event: KeyboardEvent<HTMLButtonElement>,
  currentTab: DentalInspectorTab,
  onChange: (tab: DentalInspectorTab) => void,
) {
  const currentIndex = TABS.findIndex((tab) => tab.id === currentTab);
  if (event.key === "ArrowRight") {
    event.preventDefault();
    onChange(TABS[(currentIndex + 1) % TABS.length].id);
  }
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    onChange(TABS[(currentIndex - 1 + TABS.length) % TABS.length].id);
  }
}

function DentalInspectorHeader({
  toothCode,
  eventCount,
  closeButtonRef,
  onClose,
}: {
  toothCode: string;
  eventCount: number;
  closeButtonRef: DentalInspectorProps["closeButtonRef"];
  onClose: () => void;
}) {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p
            id="odontogram-clinical-drawer-title"
            className="text-xs font-bold uppercase tracking-wide text-slate-500"
          >
            Dental Inspector
          </p>
          <div className="mt-1 flex items-end gap-2">
            <h2 className="text-4xl font-black leading-none text-slate-950">{toothCode}</h2>
            <p className="pb-1 text-sm font-semibold text-slate-500">
              {toothDentitionLabel(toothCode)}
            </p>
          </div>
          <p className="mt-1 text-sm font-bold text-slate-700">{anatomicalToothName(toothCode)}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-black text-green-700">
            {eventCount} eventos
          </span>
          <button
            ref={closeButtonRef}
            type="button"
            aria-label="Cerrar Dental Inspector"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-xl font-black leading-none text-slate-500 hover:border-green-200 hover:bg-green-50 hover:text-green-700"
          >
            ×
          </button>
        </div>
      </div>
    </header>
  );
}

function DentalInspectorTabs({
  activeTab,
  onChange,
  draftCount,
}: {
  activeTab: DentalInspectorTab;
  onChange: (tab: DentalInspectorTab) => void;
  draftCount: number;
}) {
  return (
    <div className="sticky top-[5.4rem] z-[9] border-b border-slate-200 bg-slate-50/95 px-4 py-2 backdrop-blur">
      <div className="grid grid-cols-4 gap-1 rounded-2xl bg-white p-1 shadow-sm" role="tablist" aria-label="Secciones del Dental Inspector">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`dental-inspector-${tab.id}`}
            id={`dental-inspector-tab-${tab.id}`}
            onClick={() => onChange(tab.id)}
            onKeyDown={(event) => handleTabKeyDown(event, activeTab, onChange)}
            className={`rounded-xl px-2 py-2 text-[11px] font-black transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-green-600 ${
              activeTab === tab.id
                ? "bg-green-700 text-white shadow-sm"
                : "text-slate-600 hover:bg-green-50 hover:text-green-700"
            }`}
          >
            {tab.label}
            {tab.id === "drafts" && draftCount > 0 ? ` ${draftCount}` : ""}
          </button>
        ))}
      </div>
    </div>
  );
}

function SummaryTab({
  toothCode,
  toothState,
  history,
  linkedProcedures,
  onRegisterFirst,
  onAddToPlan,
  patientId,
}: {
  toothCode: string;
  toothState: DentalInspectorProps["toothState"];
  history: OdontogramEvent[];
  linkedProcedures: DentalInspectorProps["linkedProcedures"];
  onRegisterFirst: () => void;
  onAddToPlan: (event: OdontogramEvent) => void;
  patientId: string;
}) {
  const model = useMemo(() => buildInspectorModel(toothCode, toothState), [toothCode, toothState]);
  const dentition = Number(toothCode[0]) >= 5 ? "PRIMARY" : "PERMANENT";
  const eligibleEvents = useMemo(
    () =>
      history.filter(
        (event) =>
          event.status === "CONFIRMED" &&
          eventBelongsToTooth(event, toothCode) &&
          event.details.some((detail) => ["DIAGNOSIS", "FINDING"].includes(detail.layer)),
      ),
    [history, toothCode],
  );

  return (
    <div className="space-y-4" role="tabpanel" id="dental-inspector-summary" aria-labelledby="dental-inspector-tab-summary">
      <section className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-black uppercase tracking-wide text-slate-500">Tooth Component</p>
        <div className="mt-4 flex justify-center rounded-3xl bg-gradient-to-b from-slate-50 to-white p-5">
          <Tooth
            number={toothCode}
            dentition={dentition}
            details={model.toothDetails}
            eventCount={model.eventCount}
            selected
            className="scale-125"
          />
        </div>
      </section>

      <section className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-wide text-slate-500">Estado vigente actual</p>
            <h3 className="mt-1 text-lg font-black text-slate-950">Resumen clínico</h3>
          </div>
          {model.events.length === 0 && (
            <button
              type="button"
              onClick={onRegisterFirst}
              className="rounded-full bg-dentia-primary px-3 py-1.5 text-xs font-black text-white"
            >
              Registrar primer evento
            </button>
          )}
        </div>

        {!model.groups.length ? (
          <p className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
            Pieza sin eventos clínicos confirmados.
          </p>
        ) : (
          <div className="mt-4 space-y-3">
            {model.groups.map((group) => (
              <div key={group.id} className={`rounded-2xl border p-3 ${group.tone}`}>
                <p className="text-xs font-black uppercase tracking-wide">{group.title}</p>
                <div className="mt-2 space-y-2">
                  {group.events.map((event) => (
                    <div key={`${event.id}-${event.sourceCode}-${event.status}`} className="rounded-xl bg-white/75 px-3 py-2 text-sm">
                      <p className="font-black text-slate-900">{event.label}</p>
                      <p className="mt-0.5 text-xs font-semibold text-slate-600">
                        {eventStatusLabel(event)} · {eventSurfaceLabel(event)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {eligibleEvents.length > 0 && (
        <section className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">Plan de tratamiento</p>
          <h3 className="mt-1 text-lg font-black text-slate-950">Convertir diagnóstico en procedimiento</h3>
          <p className="mt-1 text-sm text-slate-500">
            Crea procedimientos planificados desde eventos confirmados sin modificar el odontograma.
          </p>
          <div className="mt-4 space-y-3">
            {eligibleEvents.map((event) => {
              const linked = linkedProcedures.filter((procedure) => procedure.source_odontogram_event_id === event.id);
              return (
                <div key={event.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-black text-slate-900">{eventCardTitle(event)}</p>
                      <p className="mt-1 text-xs font-semibold text-slate-500">
                        {linked.length ? plannedProcedureCountLabel(linked.length) : "Sin procedimientos en el plan"}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => onAddToPlan(event)}
                      className="rounded-xl bg-dentia-primary px-3 py-2 text-xs font-black text-white"
                    >
                      {linked.length ? "Agregar otro procedimiento" : "Agregar al plan"}
                    </button>
                  </div>
                  {linked.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {linked.map((procedure) => (
                        <LinkedPlannedProcedureCard
                          key={procedure.procedure_id}
                          procedure={procedure}
                          patientId={patientId}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}

function HistoryEventCard({
  event,
  onConfirm,
}: {
  event: OdontogramEvent;
  onConfirm?: () => void;
}) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-black text-slate-900">{eventCardTitle(event)}</p>
          <p className="mt-1 text-xs text-slate-500">
            {formatInspectorEventDate(event.clinical_date, event.timezone)} · {event.dentist_name ?? "Odontólogo"} · {event.site_name ?? "Sede"}
          </p>
        </div>
        <span className={`rounded-full px-2 py-1 text-[11px] font-black ${statusBadgeClass(event.status)}`}>
          {statusLabel(event.status)}
        </span>
      </div>
      {event.observation && (
        <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{event.observation}</p>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        {eventCardBadges(event).map((badge) => (
          <span key={badge.id} className={`rounded-full px-2.5 py-1 text-xs font-bold ${layerClass(badge.layer)}`}>
            {badge.label}
          </span>
        ))}
      </div>
      {onConfirm && (
        <button
          type="button"
          onClick={onConfirm}
          className="mt-3 rounded-xl bg-green-700 px-3 py-2 text-xs font-black text-white"
        >
          Confirmar
        </button>
      )}
    </article>
  );
}

function HistoryTab({
  history,
  canConfirm,
  onConfirmDraft,
}: {
  history: OdontogramEvent[];
  canConfirm: boolean;
  onConfirmDraft: (event: OdontogramEvent) => void;
}) {
  return (
    <div className="space-y-3" role="tabpanel" id="dental-inspector-history" aria-labelledby="dental-inspector-tab-history">
      <section className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-lg font-black text-slate-950">Historial cronológico</h3>
        <p className="mt-1 text-sm text-slate-500">Todo lo ocurrido con esta pieza, más reciente primero.</p>
      </section>
      {history.map((item) => (
        <HistoryEventCard key={item.id} event={item} onConfirm={canConfirm && item.status === "DRAFT" ? () => onConfirmDraft(item) : undefined} />
      ))}
      {!history.length && (
        <p className="rounded-2xl bg-white p-4 text-sm text-slate-500 shadow-sm">
          Sin eventos para este diente.
        </p>
      )}
    </div>
  );
}

function RegisterTab(props: DentalInspectorProps) {
  const {
    selectedSurfaces,
    warning,
    canEditDraft,
    canConfirm,
    eventOptions,
    eventType,
    catalogItemId,
    availableCatalog,
    observation,
    saveAsConfirmed,
    saving,
    onToggleSurface,
    onEventTypeChange,
    onCatalogItemChange,
    onObservationChange,
    onSaveAsConfirmedChange,
    onSaveEvent,
  } = props;

  return (
    <div className="space-y-4" role="tabpanel" id="dental-inspector-register" aria-labelledby="dental-inspector-tab-register">
      <section className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Superficies</p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {INSPECTOR_SURFACES.map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => onToggleSurface(value)}
              className={`rounded-xl border px-3 py-2 text-sm font-bold ${
                selectedSurfaces.includes(value)
                  ? "border-green-500 bg-green-50 text-green-800 shadow-sm"
                  : "border-slate-200 text-slate-600 hover:border-green-200 hover:bg-green-50/40"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {warning && <p className="mt-2 text-xs font-semibold text-amber-700">{warning}</p>}
      </section>

      <section className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-lg font-black text-slate-950">Registrar evento</h3>
        {!canEditDraft ? (
          <p className="mt-3 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
            No tienes permiso para registrar eventos en este odontograma.
          </p>
        ) : (
          <div className="mt-4 space-y-4">
            <label className="block text-sm font-bold text-slate-700">
              Acción
              <select
                value={eventType}
                onChange={(event) => onEventTypeChange(event.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              >
                {eventOptions.map((option) => (
                  <option key={option.eventType} value={option.eventType}>{option.label}</option>
                ))}
              </select>
            </label>
            <label className="block text-sm font-bold text-slate-700">
              Catálogo
              <select
                value={catalogItemId}
                onChange={(event) => onCatalogItemChange(event.target.value)}
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
                onChange={(event) => onObservationChange(event.target.value)}
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
                  onChange={(event) => onSaveAsConfirmedChange(event.target.checked)}
                />
                Guardar confirmado
              </label>
            )}
            <button
              type="button"
              disabled={saving || !catalogItemId}
              onClick={onSaveEvent}
              className="min-h-11 w-full rounded-xl bg-dentia-primary px-4 font-bold text-white disabled:opacity-60"
            >
              {saving ? "Guardando…" : saveAsConfirmed ? "Registrar y confirmar" : "Guardar borrador"}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function DraftsTab({
  drafts,
  canConfirm,
  onConfirmDraft,
}: {
  drafts: OdontogramEvent[];
  canConfirm: boolean;
  onConfirmDraft: (event: OdontogramEvent) => void;
}) {
  return (
    <div className="space-y-3" role="tabpanel" id="dental-inspector-drafts" aria-labelledby="dental-inspector-tab-drafts">
      <section className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-lg font-black text-slate-950">Borradores</h3>
        <p className="mt-1 text-sm text-slate-500">Eventos pendientes de confirmar para esta pieza.</p>
      </section>
      {drafts.map((event) => (
        <HistoryEventCard key={event.id} event={event} onConfirm={canConfirm ? () => onConfirmDraft(event) : undefined} />
      ))}
      {!drafts.length && (
        <p className="rounded-2xl bg-white p-4 text-sm text-slate-500 shadow-sm">
          No hay eventos odontográficos en borrador para esta pieza.
        </p>
      )}
    </div>
  );
}

export function DentalInspector(props: DentalInspectorProps) {
  const [activeTab, setActiveTab] = useState<DentalInspectorTab>("summary");
  const [planEvent, setPlanEvent] = useState<OdontogramEvent | null>(null);
  const inspectorModel = useMemo(() => buildInspectorModel(props.toothCode, props.toothState), [props.toothCode, props.toothState]);
  const draftsForTooth = useMemo(
    () => props.drafts.filter((event) => eventBelongsToTooth(event, props.toothCode)),
    [props.drafts, props.toothCode],
  );

  return (
    <div className="absolute right-0 top-0 flex h-full w-[min(100vw,clamp(350px,40vw,430px))] flex-col border-l border-slate-200 bg-slate-50 shadow-2xl">
      <DentalInspectorHeader
        toothCode={props.toothCode}
        eventCount={inspectorModel.eventCount}
        closeButtonRef={props.closeButtonRef}
        onClose={props.onClose}
      />
      <DentalInspectorTabs activeTab={activeTab} onChange={setActiveTab} draftCount={draftsForTooth.length} />
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {activeTab === "summary" && (
          <SummaryTab
            toothCode={props.toothCode}
            toothState={props.toothState}
            history={props.history}
            linkedProcedures={props.linkedProcedures}
            patientId={props.patientId}
            onRegisterFirst={() => setActiveTab("register")}
            onAddToPlan={setPlanEvent}
          />
        )}
        {activeTab === "history" && (
          <HistoryTab history={props.history} canConfirm={props.canConfirm} onConfirmDraft={props.onConfirmDraft} />
        )}
        {activeTab === "register" && <RegisterTab {...props} />}
        {activeTab === "drafts" && (
          <DraftsTab drafts={draftsForTooth} canConfirm={props.canConfirm} onConfirmDraft={props.onConfirmDraft} />
        )}
      </div>
      {planEvent && (
        <AddPlannedProcedureDialog
          event={planEvent}
          patientId={props.patientId}
          linkedProcedures={props.linkedProcedures}
          onClose={() => setPlanEvent(null)}
          onCreated={props.onPlannedProcedureCreated}
        />
      )}
    </div>
  );
}
