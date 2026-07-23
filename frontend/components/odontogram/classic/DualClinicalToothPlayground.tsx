"use client";

import { useMemo, useState } from "react";
import { CLASSIC_COLORS, STATUS_LABELS, SURFACE_LABELS, SURFACE_OPTIONS } from "./constants";
import { DualClinicalTooth } from "./DualClinicalTooth";
import { createToothModel, DUAL_TOOTH_PRESET_OPTIONS, DUAL_TOOTH_PRESETS, type DualToothPresetKey } from "./fixtures";
import { familyFromTooth, getSurfaceOrientation, isValidFdiTooth, surfaceToRole } from "./orientation";
import type { ClinicalEventKind, ClinicalEventStatus, ToothFamily, ToothSurface } from "./types";

const eventKinds: ClinicalEventKind[] = ["CARIES", "RESTORATION", "ENDODONTICS", "CROWN", "IMPLANT", "FRACTURE", "EXTRACTION", "ABSENT"];
const statuses: ClinicalEventStatus[] = ["DIAGNOSIS", "COMPLETED", "PLANNED"];
const families: ToothFamily[] = ["INCISOR", "CANINE", "PREMOLAR", "MOLAR"];

export function DualClinicalToothPlayground() {
  const [presetKey, setPresetKey] = useState<DualToothPresetKey>("cariesVestibular31");
  const [selected, setSelected] = useState(true);
  const preset = DUAL_TOOTH_PRESETS[presetKey];
  const [toothNumber, setToothNumber] = useState(preset.toothNumber);
  const [family, setFamily] = useState<ToothFamily>(preset.family);
  const [kind, setKind] = useState<ClinicalEventKind>(preset.events[0]?.kind ?? "CARIES");
  const [status, setStatus] = useState<ClinicalEventStatus>(preset.events[0]?.status ?? "DIAGNOSIS");
  const [surfaces, setSurfaces] = useState<ToothSurface[]>(preset.events[0]?.surfaces ?? ["VESTIBULAR"]);

  function applyPreset(key: DualToothPresetKey) {
    const next = DUAL_TOOTH_PRESETS[key];
    setPresetKey(key);
    setToothNumber(next.toothNumber);
    setFamily(next.family);
    setKind(next.events[0]?.kind ?? "CARIES");
    setStatus(next.events[0]?.status ?? "DIAGNOSIS");
    setSurfaces(next.events[0]?.surfaces ?? []);
  }

  const fdiValid = isValidFdiTooth(toothNumber);
  const safeToothNumber = fdiValid ? toothNumber : preset.toothNumber;
  const customModel = useMemo(
    () =>
      createToothModel(safeToothNumber, [
        {
          id: "custom-event",
          kind,
          status,
          surfaces,
          label: CLASSIC_COLORS[kind].text,
        },
      ], fdiValid ? family : preset.family),
    [family, fdiValid, kind, preset.family, safeToothNumber, status, surfaces],
  );
  const orientation = getSurfaceOrientation(customModel.toothNumber, customModel.family);

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-black uppercase tracking-wide text-green-700">Dentia Design System</p>
        <h1 className="mt-1 text-3xl font-black text-slate-950">Dual Clinical Tooth Playground</h1>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
          Implementación aislada de DDS-005A para validar una sola fuente clínica con dos representaciones sincronizadas:
          vista anatómica esquemática y mapa superior de cinco caras. No usa backend, no reemplaza el odontograma real y no toca Tooth Component v1.0.
        </p>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-slate-500">Componente seleccionado</p>
              <h2 className="mt-1 text-2xl font-black text-slate-950">Evento único → dos vistas sincronizadas</h2>
            </div>
            <label className="inline-flex items-center gap-2 rounded-full border border-green-100 bg-green-50 px-3 py-2 text-xs font-black text-green-800">
              <input type="checkbox" checked={selected} onChange={(event) => setSelected(event.target.checked)} />
              Seleccionado
            </label>
          </div>

          <div className="mt-8 grid gap-8 xl:grid-cols-[260px_minmax(0,1fr)]">
            <div className="flex justify-center">
              <DualClinicalTooth model={customModel} selected={selected} size="lg" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                <h3 className="text-sm font-black text-slate-950">Modelo clínico único</h3>
                <dl className="mt-3 space-y-2 text-sm">
                  <div className="flex justify-between gap-3">
                    <dt className="font-bold text-slate-500">Diente</dt>
                    <dd className="font-black text-slate-950">{customModel.toothNumber}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="font-bold text-slate-500">Familia</dt>
                    <dd className="font-black text-slate-950">{customModel.family}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="font-bold text-slate-500">Cuadrante</dt>
                    <dd className="font-black text-slate-950">{customModel.quadrant}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="font-bold text-slate-500">Estado</dt>
                    <dd className="font-black text-slate-950">{STATUS_LABELS[status]}</dd>
                  </div>
                </dl>
              </div>
              <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4">
                <h3 className="text-sm font-black text-blue-950">Orientación centralizada</h3>
                <dl className="mt-3 space-y-2 text-sm">
                  <div className="flex justify-between gap-3">
                    <dt className="font-bold text-blue-700">Mesial</dt>
                    <dd className="font-black text-blue-950">{orientation.mesialRole}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="font-bold text-blue-700">Distal</dt>
                    <dd className="font-black text-blue-950">{orientation.distalRole}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="font-bold text-blue-700">Vestibular</dt>
                    <dd className="font-black text-blue-950">{orientation.vestibularRole}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="font-bold text-blue-700">{orientation.innerSurface}</dt>
                    <dd className="font-black text-blue-950">{orientation.innerRole}</dd>
                  </div>
                </dl>
              </div>
              <div className="rounded-2xl border border-slate-100 bg-white p-4 sm:col-span-2">
                <h3 className="text-sm font-black text-slate-950">Superficies activas</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {surfaces.map((surface) => (
                    <span key={surface} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-700">
                      {SURFACE_LABELS[surface]} → {surfaceToRole(surface, orientation)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-black text-slate-950">Controles</h2>
          <div className="mt-4 space-y-4">
            <label className="block text-sm font-bold text-slate-700">
              Preset clínico
              <select value={presetKey} onChange={(event) => applyPreset(event.target.value as DualToothPresetKey)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm">
                {DUAL_TOOTH_PRESET_OPTIONS.map((option) => (
                  <option key={option.key} value={option.key}>{option.label}</option>
                ))}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm font-bold text-slate-700">
                FDI
                <input
                  value={toothNumber}
                  onChange={(event) => {
                    const next = event.target.value.replace(/\D/g, "").slice(0, 2);
                    setToothNumber(next);
                    if (isValidFdiTooth(next)) setFamily(familyFromTooth(next));
                  }}
                  className={`mt-1 w-full rounded-xl border px-3 py-2 text-sm ${fdiValid ? "border-slate-300" : "border-red-300 bg-red-50"}`}
                />
                {!fdiValid && (
                  <span className="mt-1 block text-xs font-semibold text-red-700">
                    FDI inválido. Usa permanente 11–48 o temporal 51–85.
                  </span>
                )}
              </label>
              <label className="block text-sm font-bold text-slate-700">
                Familia
                <select value={family} onChange={(event) => setFamily(event.target.value as ToothFamily)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm">
                  {families.map((item) => <option key={item}>{item}</option>)}
                </select>
              </label>
            </div>
            <label className="block text-sm font-bold text-slate-700">
              Tipo de evento
              <select value={kind} onChange={(event) => setKind(event.target.value as ClinicalEventKind)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm">
                {eventKinds.map((item) => <option key={item} value={item}>{CLASSIC_COLORS[item].text}</option>)}
              </select>
            </label>
            <label className="block text-sm font-bold text-slate-700">
              Estado
              <select value={status} onChange={(event) => setStatus(event.target.value as ClinicalEventStatus)} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm">
                {statuses.map((item) => <option key={item} value={item}>{STATUS_LABELS[item]}</option>)}
              </select>
            </label>
            <div>
              <p className="text-sm font-bold text-slate-700">Superficies</p>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {SURFACE_OPTIONS.map((surface) => (
                  <label key={surface} className="flex items-center gap-2 rounded-xl border border-slate-200 px-2 py-2 text-xs font-bold text-slate-700">
                    <input
                      type="checkbox"
                      checked={surfaces.includes(surface)}
                      onChange={() =>
                        setSurfaces((current) =>
                          current.includes(surface)
                            ? current.filter((item) => item !== surface)
                            : [...current, surface],
                        )
                      }
                    />
                    {SURFACE_LABELS[surface]}
                  </label>
                ))}
              </div>
            </div>
          </div>
        </aside>
      </section>

      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-black text-slate-950">Presets clínicos aprobados</h2>
        <p className="mt-1 text-sm text-slate-500">
          Cada tarjeta consume un único modelo clínico y renderiza simultáneamente la vista anatómica y el mapa de cinco caras.
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {DUAL_TOOTH_PRESET_OPTIONS.map((option) => (
            <div key={option.key} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
              <p className="text-sm font-black text-slate-950">{option.label}</p>
              <p className="mb-3 text-xs font-semibold text-slate-500">{option.description}</p>
              <div className="flex justify-center">
                <DualClinicalTooth
                  model={DUAL_TOOTH_PRESETS[option.key]}
                  selected={presetKey === option.key}
                  onSelect={() => applyPreset(option.key)}
                  size="sm"
                />
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
