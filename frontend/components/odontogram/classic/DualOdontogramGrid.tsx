"use client";

import { useMemo } from "react";
import type { OdontogramToothState } from "@/types/odontogram";
import { DualClinicalTooth } from "./DualClinicalTooth";
import { buildDualClinicalModelsForRows, type DualOdontogramRows } from "./dualOdontogramLayout";

export function DualOdontogramGrid({
  title,
  rows,
  selectedTooth,
  toothStateByCode,
  visibleLayers,
  onSelect,
  expanded = false,
}: {
  title: string;
  rows: DualOdontogramRows;
  selectedTooth: string;
  toothStateByCode: Map<string, OdontogramToothState>;
  visibleLayers: Set<string>;
  onSelect: (tooth: string) => void;
  expanded?: boolean;
}) {
  const models = useMemo(
    () => buildDualClinicalModelsForRows(rows, toothStateByCode, { visibleLayers }),
    [rows, toothStateByCode, visibleLayers],
  );
  const upperRows = models.slice(0, 2);
  const lowerRows = models.slice(2, 4);

  return (
    <section className="rounded-[1.5rem] border border-transparent bg-transparent p-0.5 sm:p-1">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xs font-black uppercase tracking-[0.16em] text-slate-600">{title}</h3>
        <div className="hidden items-center gap-2 text-[10px] font-black uppercase tracking-wide text-slate-400 sm:flex">
          <span>Derecha paciente</span>
          <span className="h-px w-20 bg-slate-200" />
          <span>Izquierda paciente</span>
        </div>
      </div>

      <div className="mt-3 space-y-7 overflow-visible pb-1">
        <DualDentalArch rows={upperRows} selectedTooth={selectedTooth} onSelect={onSelect} arch="upper" expanded={expanded} />
        <DualDentalArch rows={lowerRows} selectedTooth={selectedTooth} onSelect={onSelect} arch="lower" expanded={expanded} />
      </div>
    </section>
  );
}

function DualDentalArch({
  rows,
  selectedTooth,
  onSelect,
  arch,
  expanded,
}: {
  rows: ReturnType<typeof buildDualClinicalModelsForRows>;
  selectedTooth: string;
  onSelect: (tooth: string) => void;
  arch: "upper" | "lower";
  expanded: boolean;
}) {
  return (
    <div className="grid w-full grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-x-2 sm:gap-x-3 2xl:gap-x-4">
      <DualQuadrant teeth={rows[0] ?? []} selectedTooth={selectedTooth} onSelect={onSelect} arch={arch} side="right" expanded={expanded} />
      <div className="h-40 w-px border-l border-dashed border-slate-300" aria-hidden="true" />
      <DualQuadrant teeth={rows[1] ?? []} selectedTooth={selectedTooth} onSelect={onSelect} arch={arch} side="left" expanded={expanded} />
    </div>
  );
}

function DualQuadrant({
  teeth,
  selectedTooth,
  onSelect,
  arch,
  side,
  expanded,
}: {
  teeth: ReturnType<typeof buildDualClinicalModelsForRows>[number];
  selectedTooth: string;
  onSelect: (tooth: string) => void;
  arch: "upper" | "lower";
  side: "right" | "left";
  expanded: boolean;
}) {
  return (
    <div className="grid min-w-0 items-center gap-x-1 sm:gap-x-1.5 2xl:gap-x-2" style={{ gridTemplateColumns: `repeat(${Math.max(teeth.length, 1)}, minmax(0, 1fr))` }}>
      {teeth.map((model, index) => (
        <DualToothSlot
          key={model.toothNumber}
          model={model}
          index={index}
          count={teeth.length}
          arch={arch}
          side={side}
          selected={selectedTooth === model.toothNumber}
          onSelect={() => onSelect(model.toothNumber)}
          expanded={expanded}
        />
      ))}
    </div>
  );
}

function DualToothSlot({
  model,
  index,
  count,
  arch,
  side,
  selected,
  onSelect,
  expanded,
}: {
  model: Parameters<typeof DualClinicalTooth>[0]["model"];
  index: number;
  count: number;
  arch: "upper" | "lower";
  side: "right" | "left";
  selected: boolean;
  onSelect: () => void;
  expanded: boolean;
}) {
  const centerIndex = side === "right" ? count - 1 : 0;
  const distanceFromCenter = Math.abs(index - centerIndex);
  const verticalOffset = arch === "upper"
    ? Math.max(0, 4 - distanceFromCenter) * 2
    : -Math.max(0, 4 - distanceFromCenter) * 2;

  return (
    <div className="flex min-w-0 justify-center overflow-visible py-1" style={{ transform: `translateY(${verticalOffset}px)` }}>
      <DualClinicalTooth
        model={model}
        selected={selected}
        onSelect={onSelect}
        size="xs"
        density="workspace"
        expanded={expanded}
      />
    </div>
  );
}
