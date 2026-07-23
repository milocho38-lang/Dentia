"use client";

import { useMemo } from "react";
import { LOCALIZATION_LABELS, STATUS_LABELS, SURFACE_LABELS } from "./constants";
import { AnatomicalToothView } from "./AnatomicalToothView";
import { FiveSurfaceMap } from "./FiveSurfaceMap";
import { createClinicalAriaLabel, createClinicalTooltip, createIndicatorTooltip } from "./clinicalTooltip";
import { mapDualClinicalTooth } from "./dualClinicalMapper";
import type { ClinicalEventStatus, DualClinicalEvent, DualClinicalToothModel } from "./types";

function statusTone(status: ClinicalEventStatus) {
  if (status === "PLANNED") {
    return "border-orange-300 bg-orange-50 text-orange-700";
  }
  if (status === "COMPLETED") {
    return "border-blue-300 bg-blue-50 text-blue-700";
  }
  return "border-red-300 bg-red-50 text-red-700";
}

function InformativeIndicator({
  symbol,
  events,
  tone,
}: {
  symbol: "?" | "i";
  events: DualClinicalEvent[];
  tone: string;
}) {
  if (!events.length) return null;
  const title = createIndicatorTooltip(
    events,
    symbol === "?" ? "Superficie no especificada" : "Diagnóstico no superficial",
  );
  return (
    <span
      role="img"
      aria-label={title.replace(/\n/g, ". ")}
      title={title}
      className={`flex h-4 min-w-4 items-center justify-center rounded-full border px-1 text-[10px] font-black leading-none shadow-sm ${tone}`}
    >
      {symbol}
    </span>
  );
}

export function DualClinicalTooth({
  model,
  selected = false,
  onSelect,
  size = "md",
  density = "card",
  expanded = false,
}: {
  model: DualClinicalToothModel;
  selected?: boolean;
  onSelect?: (model: DualClinicalToothModel) => void;
  size?: "xs" | "sm" | "md" | "lg";
  density?: "card" | "workspace";
  expanded?: boolean;
}) {
  const viewModel = useMemo(() => mapDualClinicalTooth(model), [model]);
  const clinicalTooltip = useMemo(() => createClinicalTooltip(model), [model]);
  const clinicalAriaLabel = useMemo(() => createClinicalAriaLabel(model), [model]);
  const dimensions = density === "workspace"
    ? expanded
      ? "w-full max-w-[5.65rem] sm:max-w-[6.1rem] xl:max-w-[6.65rem] 2xl:max-w-[7rem]"
      : "w-full max-w-[5.15rem] sm:max-w-[5.55rem] xl:max-w-[5.95rem] 2xl:max-w-[6.35rem]"
    : size === "lg" ? "w-56" : size === "xs" ? "w-24" : size === "sm" ? "w-28" : "w-40";
  const anatomicalHeight = density === "workspace"
    ? expanded
      ? "h-[4.05rem] sm:h-[4.25rem] xl:h-[4.45rem] 2xl:h-[4.65rem]"
      : "h-[3.6rem] sm:h-[3.8rem] xl:h-[4rem] 2xl:h-[4.15rem]"
    : size === "lg" ? "h-40" : size === "xs" ? "h-20" : size === "sm" ? "h-24" : "h-32";
  const mapSize = density === "workspace"
    ? expanded
      ? "max-h-[50px]"
      : "max-h-[42px]"
    : size === "lg" ? "h-28 w-28" : size === "xs" ? "h-14 w-14" : size === "sm" ? "h-16 w-16" : "h-20 w-20";
  const isWorkspace = density === "workspace";
  const workspaceAnatomyStyle = {
    width: expanded ? "min(40px, calc(100% - 8px))" : "min(34px, calc(100% - 8px))",
    maxWidth: "100%",
  };
  const workspaceMapStyle = {
    width: expanded ? "min(50px, calc(100% - 8px))" : "min(42px, calc(100% - 8px))",
    maxWidth: "100%",
    aspectRatio: "1 / 1",
  };

  if (isWorkspace) {
    const unspecifiedSurfaceEvents = viewModel.model.events.filter((event) => event.localization === "SURFACE_UNSPECIFIED");
    const nonSurfaceEvents = viewModel.model.events.filter((event) => event.localization === "NON_SURFACE");
    const accessibleContext = [
      unspecifiedSurfaceEvents.length
        ? `${unspecifiedSurfaceEvents.length} evento${unspecifiedSurfaceEvents.length === 1 ? "" : "s"} con superficie no especificada`
        : null,
      nonSurfaceEvents.length
        ? `${nonSurfaceEvents.length} evento${nonSurfaceEvents.length === 1 ? "" : "s"} clínico${nonSurfaceEvents.length === 1 ? "" : "s"} informativo${nonSurfaceEvents.length === 1 ? "" : "s"}`
        : null,
    ].filter(Boolean).join(". ");
    return (
      <button
        type="button"
        title={clinicalTooltip}
        aria-label={accessibleContext ? `${clinicalAriaLabel} ${accessibleContext}.` : clinicalAriaLabel}
        onClick={() => onSelect?.(model)}
        className={`${dimensions} group relative z-0 box-border grid max-w-full justify-items-center rounded-2xl border px-1 py-1 text-left transition duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-green-600 hover:z-10 hover:border-green-100 hover:bg-white/75 hover:shadow-md ${
          expanded
            ? "grid-rows-[1rem_4.25rem_4rem_1rem] sm:grid-rows-[1rem_4.45rem_4.15rem_1rem] xl:grid-rows-[1rem_4.65rem_4.35rem_1rem]"
            : "grid-rows-[1rem_3.8rem_3.5rem_1rem] sm:grid-rows-[1rem_4rem_3.7rem_1rem] xl:grid-rows-[1rem_4.2rem_3.85rem_1rem]"
        } ${
          selected
            ? "border-green-500 bg-green-50/55 shadow-[inset_0_0_0_1px_rgba(34,197,94,0.18),0_4px_12px_rgba(15,23,42,0.06)]"
            : "border-transparent bg-transparent"
        }`}
      >
        <p className="self-center text-center text-[12px] font-semibold leading-none text-slate-950 sm:text-[13px]">
          {model.toothNumber}
        </p>
        <div className={`${anatomicalHeight} max-w-full self-end`} style={workspaceAnatomyStyle}>
          <AnatomicalToothView viewModel={viewModel} />
        </div>
        <div className={`${mapSize} box-border max-w-full self-center`} style={workspaceMapStyle}>
          <FiveSurfaceMap viewModel={viewModel} />
        </div>
        <div className="flex h-4 items-center justify-center gap-1 self-center">
          <InformativeIndicator
            symbol="?"
            events={unspecifiedSurfaceEvents}
            tone={statusTone(unspecifiedSurfaceEvents[0]?.status ?? "DIAGNOSIS")}
          />
          <InformativeIndicator
            symbol="i"
            events={nonSurfaceEvents}
            tone="border-slate-300 bg-slate-50 text-slate-700"
          />
        </div>
      </button>
    );
  }

  return (
    <button
      type="button"
      title={viewModel.tooltip}
      aria-label={`Diente ${model.toothNumber}. ${viewModel.summaryLabel}. ${viewModel.eventCount} eventos.`}
      onClick={() => onSelect?.(model)}
      className={`${dimensions} group text-left transition duration-200 hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600 ${
        `rounded-3xl border bg-white p-3 shadow-sm hover:border-green-300 hover:shadow-lg ${selected ? "border-green-500 ring-2 ring-green-100" : "border-slate-200"}`
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-black uppercase tracking-wide text-slate-400">FDI</p>
          <p className="text-2xl font-black leading-none text-slate-950">
            {model.toothNumber}
          </p>
        </div>
        {viewModel.eventCount > 0 && (
          <span className="rounded-full bg-slate-900 px-2 py-1 text-[10px] font-black leading-none text-white shadow-sm ring-1 ring-white/80">
            {viewModel.eventCount}
          </span>
        )}
      </div>
      <div className={`mt-2 ${anatomicalHeight}`}>
        <AnatomicalToothView viewModel={viewModel} />
      </div>
      <div className="mt-2 flex justify-center">
        <div className={mapSize}>
          <FiveSurfaceMap viewModel={viewModel} />
        </div>
      </div>
      <div className="mt-3 space-y-1">
        {model.events.slice(0, 3).map((event) => (
          <p
            key={event.id}
            title={`${event.label} · ${event.surfaces.map((surface) => SURFACE_LABELS[surface]).join(", ") || LOCALIZATION_LABELS[event.localization ?? "NON_SURFACE"]} · ${STATUS_LABELS[event.status]} · ${event.sourceCode ?? "sin código"}`}
            className="truncate text-[11px] font-bold text-slate-600"
          >
            {event.label}
            <span className="font-semibold text-slate-400">
              {" · "}
              {event.surfaces.map((surface) => SURFACE_LABELS[surface]).join(", ") || LOCALIZATION_LABELS[event.localization ?? "NON_SURFACE"]}
              {" · "}
              {STATUS_LABELS[event.status]}
            </span>
          </p>
        ))}
        {!model.events.length && <p className="text-[11px] font-semibold text-slate-400">Sin eventos clínicos</p>}
      </div>
      {viewModel.generalMarkers.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {viewModel.generalMarkers.slice(0, 2).map((marker) => (
            <span
              key={marker.id}
              title={`${marker.label} · ${LOCALIZATION_LABELS[marker.localization]}`}
              className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-black text-slate-600"
            >
              {marker.symbol} {LOCALIZATION_LABELS[marker.localization]}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
