"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { getOdontogramCurrent } from "@/services/odontogramService";
import { getPatient } from "@/services/patientService";
import type { OdontogramCurrentState, OdontogramToothState } from "@/types/odontogram";
import type { Patient } from "@/types/patient";
import { DualClinicalTooth } from "./DualClinicalTooth";
import { buildDualClinicalToothModelFromState } from "./realClinicalAdapter";
import { LOCALIZATION_LABELS, STATUS_LABELS } from "./constants";

const LAYER_OPTIONS = [
  ["STRUCTURAL", "Estructura"],
  ["FINDING", "Hallazgos"],
  ["DIAGNOSIS", "Diagnósticos"],
  ["PLANNED", "Planificados"],
  ["PERFORMED", "Realizados"],
  ["OBSERVATION", "Observaciones"],
] as const;

const DEFAULT_VISIBLE_LAYERS = new Set(["STRUCTURAL", "FINDING", "DIAGNOSIS", "PLANNED", "PERFORMED", "OBSERVATION"]);

export function RealDualOdontogramPreview({ patientId }: { patientId: string }) {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [current, setCurrent] = useState<OdontogramCurrentState | null>(null);
  const [selectedTooth, setSelectedTooth] = useState("");
  const [visibleLayers, setVisibleLayers] = useState<Set<string>>(DEFAULT_VISIBLE_LAYERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [loadedPatient, loadedCurrent] = await Promise.all([
        getPatient(patientId),
        getOdontogramCurrent(patientId),
      ]);
      setPatient(loadedPatient);
      setCurrent(loadedCurrent);
      setSelectedTooth((currentTooth) => currentTooth || loadedCurrent.teeth[0]?.tooth_code || "11");
    } catch {
      setError("No fue posible cargar la vista dual real del odontograma.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const toothByCode = useMemo(() => {
    const map = new Map<string, OdontogramToothState>();
    current?.teeth.forEach((tooth) => map.set(tooth.tooth_code, tooth));
    return map;
  }, [current]);
  const selectedState = toothByCode.get(selectedTooth);
  const adapted = selectedState
    ? buildDualClinicalToothModelFromState(selectedState, { visibleLayers })
    : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 text-slate-500">
        <Spinner className="h-7 w-7 text-dentia-primary" />
        Cargando vista dual real…
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <Link href={`/pacientes/${patientId}/odontograma`} className="text-sm font-bold text-green-700 hover:underline">
        ← Volver al odontograma productivo
      </Link>
      <section className="mt-5 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-black uppercase tracking-wide text-green-700">Vista previa de desarrollo</p>
        <h1 className="mt-1 text-3xl font-black text-slate-950">Dual Clinical Tooth con eventos reales</h1>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
          Esta pantalla es solo lectura, usa el estado vigente reconstruido del backend y no reemplaza el odontograma productivo.
        </p>
        <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
          <span className="font-black text-slate-950">Paciente:</span> {patient?.full_name ?? patientId}
        </div>
      </section>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}

      {current && (
        <section className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-black uppercase tracking-wide text-slate-500">Capas reales</span>
              {LAYER_OPTIONS.map(([layer, label]) => (
                <button
                  key={layer}
                  type="button"
                  onClick={() => {
                    setVisibleLayers((previous) => {
                      const next = new Set(previous);
                      if (next.has(layer)) next.delete(layer);
                      else next.add(layer);
                      return next;
                    });
                  }}
                  className={`rounded-full border px-3 py-1.5 text-xs font-black ${
                    visibleLayers.has(layer)
                      ? "border-green-100 bg-green-50 text-green-800"
                      : "border-slate-200 text-slate-500"
                  }`}
                >
                  {label}
                </button>
              ))}
              <button
                type="button"
                onClick={load}
                className="ml-auto rounded-full border border-slate-200 px-3 py-1.5 text-xs font-black text-slate-700 hover:border-green-200"
              >
                Recargar estado real
              </button>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {current.teeth.map((tooth) => {
                const preview = buildDualClinicalToothModelFromState(tooth, { visibleLayers });
                return (
                  <DualClinicalTooth
                    key={tooth.tooth_code}
                    model={preview.model}
                    selected={selectedTooth === tooth.tooth_code}
                    onSelect={() => setSelectedTooth(tooth.tooth_code)}
                    size="sm"
                  />
                );
              })}
            </div>
          </div>

          <aside className="space-y-4">
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-black uppercase tracking-wide text-slate-500">Pieza seleccionada</p>
              <h2 className="mt-1 text-4xl font-black text-slate-950">{selectedTooth}</h2>
              {adapted ? (
                <div className="mt-5 flex justify-center">
                  <DualClinicalTooth model={adapted.model} selected size="lg" />
                </div>
              ) : (
                <p className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">Sin estado real para esta pieza.</p>
              )}
            </section>

            {adapted && (
              <>
                <section className="rounded-3xl border border-blue-100 bg-blue-50 p-5 shadow-sm">
                  <h3 className="font-black text-blue-950">Modelo dual generado</h3>
                  <dl className="mt-3 space-y-2 text-sm">
                    <div className="flex justify-between gap-3"><dt className="font-bold text-blue-700">Eventos</dt><dd className="font-black text-blue-950">{adapted.model.events.length}</dd></div>
                    <div className="flex justify-between gap-3"><dt className="font-bold text-blue-700">Familia</dt><dd className="font-black text-blue-950">{adapted.model.family}</dd></div>
                    <div className="flex justify-between gap-3"><dt className="font-bold text-blue-700">Cuadrante</dt><dd className="font-black text-blue-950">{adapted.model.quadrant}</dd></div>
                    <div className="flex justify-between gap-3"><dt className="font-bold text-blue-700">Dentición</dt><dd className="font-black text-blue-950">{adapted.model.dentition}</dd></div>
                  </dl>
                </section>

                <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h3 className="font-black text-slate-950">Eventos reales activos</h3>
                  <div className="mt-3 space-y-3">
                    {adapted.sourceDetails.map((detail) => (
                      <div key={detail.id} className="rounded-2xl border border-slate-100 bg-slate-50 p-3 text-sm">
                        <p className="font-black text-slate-950">{detail.name}</p>
                        <p className="mt-1 text-xs font-semibold text-slate-500">
                          Código: {detail.code || "SIN_CÓDIGO"} · Capa: {detail.layer} · Tipo: {detail.catalogType}
                        </p>
                        <p className="mt-1 text-xs font-semibold text-slate-500">
                          Superficies reales: {detail.surfaces.length ? detail.surfaces.join(", ") : "sin superficie"}
                        </p>
                        <p className="mt-1 text-xs font-semibold text-slate-500">
                          Superficies convertidas: {detail.convertedSurfaces.length ? detail.convertedSurfaces.join(", ") : "ninguna"}
                        </p>
                        <p className="mt-1 text-xs font-semibold text-slate-500">
                          Localización: {LOCALIZATION_LABELS[detail.localization]} · Estado visual: {STATUS_LABELS[detail.visualStatus]} · Estado original: {detail.originalStatus}
                        </p>
                        {!detail.mapped && <p className="mt-2 text-xs font-black text-amber-700">{detail.reason}</p>}
                      </div>
                    ))}
                    {!adapted.sourceDetails.length && (
                      <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
                        Sin eventos reales visibles para las capas seleccionadas.
                      </p>
                    )}
                  </div>
                </section>
              </>
            )}
          </aside>
        </section>
      )}
    </main>
  );
}
