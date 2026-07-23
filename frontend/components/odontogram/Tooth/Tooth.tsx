"use client";

import { memo, useMemo } from "react";
import { DiagnosisLayer } from "./DiagnosisLayer";
import { ObservationLayer } from "./ObservationLayer";
import { SelectionLayer } from "./SelectionLayer";
import { SurfaceLayer } from "./SurfaceLayer";
import { ToothBase, ToothDefs, getToothFamily } from "./ToothBase";
import { TreatmentLayer } from "./TreatmentLayer";
import { buildToothRenderState } from "./state";
import type { ToothProps } from "./types";

function ToothComponent({
  number,
  dentition,
  details = [],
  selected = false,
  disabled = false,
  eventCount = 0,
  visibleLayers,
  onClick,
  className = "",
}: ToothProps) {
  const family = getToothFamily(number);
  const id = `dds-tooth-${number}`;
  const renderState = useMemo(
    () => buildToothRenderState({ number, dentition, details, visibleLayers, eventCount }),
    [number, dentition, details, visibleLayers, eventCount],
  );
  const missing = renderState.visualStates.has("MISSING");
  const primary = dentition === "PRIMARY" || renderState.visualStates.has("PRIMARY_TOOTH");
  const tooltip = renderState.tooltipLines.join("\n");

  return (
    <button
      type="button"
      onClick={onClick}
      title={tooltip}
      disabled={disabled}
      aria-label={`Diente ${number}. ${renderState.primaryLabel}`}
      className={`group relative flex h-[6.9rem] w-[5.1rem] flex-col items-center justify-center rounded-3xl border bg-white text-sm font-black shadow-sm transition duration-200 hover:-translate-y-1 hover:scale-[1.03] hover:border-green-300 hover:shadow-[0_16px_34px_rgba(15,23,42,0.14)] disabled:cursor-not-allowed disabled:opacity-60 ${
        selected ? "border-green-400 shadow-[0_12px_28px_rgba(46,125,50,0.16)] ring-1 ring-green-100" : "border-slate-200"
      } ${className}`}
    >
      <span className="absolute left-2 top-1.5 z-10 rounded-full bg-white/95 px-1.5 text-[12px] font-black text-slate-800 shadow-sm">
        {number}
      </span>
      {eventCount > 0 && (
        <span
          className="absolute right-2 top-2 z-10 rounded-full bg-slate-900/90 px-[0.3125rem] py-0 text-[9px] font-black leading-4 text-white shadow-sm"
          title="Tiene histórico"
        >
          {eventCount}
        </span>
      )}
      <span className="pointer-events-none absolute bottom-[6.55rem] left-1/2 z-20 hidden w-48 -translate-x-1/2 whitespace-pre-line rounded-xl bg-slate-950 px-3 py-2 text-left text-[11px] font-semibold leading-4 text-white shadow-xl group-hover:block">
        {tooltip}
      </span>
      <svg viewBox="0 0 78 86" className={`mt-5 h-[4.95rem] w-[4.4rem] ${primary ? "scale-[0.92]" : ""}`} aria-hidden="true">
        <ToothDefs id={id} />
        {!missing && (
          <ToothBase id={id} family={family} primary={primary} disabled={disabled} />
        )}
        {!missing && <SurfaceLayer family={family} renderState={renderState} />}
        {!missing && <DiagnosisLayer family={family} renderState={renderState} />}
        <TreatmentLayer id={id} renderState={renderState} />
        <ObservationLayer renderState={renderState} />
        <SelectionLayer selected={selected} />
      </svg>
    </button>
  );
}

export const Tooth = memo(ToothComponent);
