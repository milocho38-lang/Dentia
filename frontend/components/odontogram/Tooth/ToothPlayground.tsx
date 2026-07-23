"use client";

import { useState } from "react";
import { Tooth } from "./Tooth";
import { DDS_STATE_LABELS } from "./constants";
import type { ToothDetail, ToothSurface, ToothVisualState } from "./types";

const demoSurfaces: Partial<Record<ToothVisualState, ToothSurface[]>> = {
  OCCLUSAL_CARIES: ["OCCLUSAL"],
  PROXIMAL_CARIES: ["MESIAL"],
  CERVICAL_CARIES: ["VESTIBULAR"],
  SIMPLE_FILLING: ["OCCLUSAL"],
  MULTIPLE_FILLINGS: ["OCCLUSAL", "MESIAL", "DISTAL"],
  TEMPORARY_RESTORATION: ["OCCLUSAL"],
  SEALANT: ["OCCLUSAL"],
  NON_CARIOUS_CERVICAL_LESION: ["VESTIBULAR"],
};

const demoCatalogByState: Record<ToothVisualState, Pick<ToothDetail, "catalogCode" | "catalogName" | "layer" | "catalogType">[]> = {
  HEALTHY: [],
  OCCLUSAL_CARIES: [{ catalogCode: "CARIES", catalogName: "Caries oclusal", layer: "DIAGNOSIS", catalogType: "DIAGNOSIS" }],
  PROXIMAL_CARIES: [{ catalogCode: "CARIES", catalogName: "Caries proximal", layer: "DIAGNOSIS", catalogType: "DIAGNOSIS" }],
  CERVICAL_CARIES: [{ catalogCode: "CARIES_CERVICAL", catalogName: "Caries cervical", layer: "DIAGNOSIS", catalogType: "DIAGNOSIS" }],
  SIMPLE_FILLING: [{ catalogCode: "OBTURACION", catalogName: "Obturación simple", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  MULTIPLE_FILLINGS: [{ catalogCode: "OBTURACION_MULTIPLE", catalogName: "Obturaciones múltiples", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  DEFINITIVE_CROWN: [{ catalogCode: "CORONA", catalogName: "Corona definitiva", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  TEMPORARY_CROWN: [{ catalogCode: "CORONA_TEMPORAL", catalogName: "Corona temporal", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  ENDODONTICS: [{ catalogCode: "ENDODONCIA", catalogName: "Endodoncia", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  POST: [{ catalogCode: "POSTE", catalogName: "Poste", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  IMPLANT: [{ catalogCode: "IMPLANTE", catalogName: "Implante", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  FIXED_PROSTHESIS: [{ catalogCode: "PROTESIS_FIJA", catalogName: "Prótesis fija", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  REMOVABLE_PROSTHESIS: [{ catalogCode: "PROTESIS_REMOVIBLE", catalogName: "Prótesis removible", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  MISSING: [{ catalogCode: "AUSENTE", catalogName: "Ausente", layer: "STRUCTURAL", catalogType: "STRUCTURAL_STATE" }],
  TEMPORARY_RESTORATION: [{ catalogCode: "RESTAURACION_TEMPORAL", catalogName: "Restauración temporal", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  SEALANT: [{ catalogCode: "SELLANTE", catalogName: "Sellante", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" }],
  NON_CARIOUS_CERVICAL_LESION: [{ catalogCode: "LESION_CERVICAL_NO_CARIOSA", catalogName: "Lesión cervical no cariosa", layer: "DIAGNOSIS", catalogType: "DIAGNOSIS" }],
  WEAR: [{ catalogCode: "DESGASTE", catalogName: "Desgaste", layer: "DIAGNOSIS", catalogType: "DIAGNOSIS" }],
  FRACTURE: [{ catalogCode: "FRACTURA", catalogName: "Fractura", layer: "DIAGNOSIS", catalogType: "DIAGNOSIS" }],
  MOBILITY: [{ catalogCode: "MOVILIDAD", catalogName: "Movilidad", layer: "DIAGNOSIS", catalogType: "DIAGNOSIS" }],
  PRIMARY_TOOTH: [{ catalogCode: "TEMPORAL", catalogName: "Diente temporal", layer: "STRUCTURAL", catalogType: "STRUCTURAL_STATE" }],
  PLANNED_TREATMENT: [{ catalogCode: "PLAN_RESINA", catalogName: "Tratamiento planificado", layer: "PLANNED", catalogType: "PLANNED_PROCEDURE" }],
  IN_PROGRESS_TREATMENT: [
    { catalogCode: "PLAN_CORONA", catalogName: "Tratamiento planificado", layer: "PLANNED", catalogType: "PLANNED_PROCEDURE" },
    { catalogCode: "OBTURACION", catalogName: "Obturación simple", layer: "PERFORMED", catalogType: "PERFORMED_PROCEDURE" },
  ],
  OBSERVATION: [{ catalogCode: "OBS", catalogName: "Observación", layer: "OBSERVATION", catalogType: "OBSERVATION" }],
};

const states = Object.keys(DDS_STATE_LABELS) as ToothVisualState[];

const groupedStates: Array<{ title: string; description: string; states: ToothVisualState[] }> = [
  {
    title: "Diagnósticos",
    description: "Hallazgos y condiciones que deben leerse rápido sin ocultar la anatomía.",
    states: [
      "OCCLUSAL_CARIES",
      "PROXIMAL_CARIES",
      "CERVICAL_CARIES",
      "NON_CARIOUS_CERVICAL_LESION",
      "WEAR",
      "FRACTURE",
      "MOBILITY",
    ],
  },
  {
    title: "Tratamientos realizados",
    description: "Intervenciones completadas en azul, integradas sobre el esmalte.",
    states: [
      "SIMPLE_FILLING",
      "MULTIPLE_FILLINGS",
      "DEFINITIVE_CROWN",
      "TEMPORARY_CROWN",
      "ENDODONTICS",
      "POST",
      "IMPLANT",
      "FIXED_PROSTHESIS",
      "REMOVABLE_PROSTHESIS",
      "TEMPORARY_RESTORATION",
      "SEALANT",
    ],
  },
  {
    title: "Estados especiales",
    description: "Estados estructurales, planeación, proceso y observaciones.",
    states: [
      "HEALTHY",
      "MISSING",
      "PRIMARY_TOOTH",
      "PLANNED_TREATMENT",
      "IN_PROGRESS_TREATMENT",
      "OBSERVATION",
    ],
  },
];

const combinations = [
  {
    label: "Corona + Endodoncia",
    details: [...demoDetails("DEFINITIVE_CROWN"), ...demoDetails("ENDODONTICS")],
  },
  {
    label: "Implante + Corona",
    details: [...demoDetails("IMPLANT"), ...demoDetails("DEFINITIVE_CROWN")],
  },
  {
    label: "Caries + Planificado",
    details: [...demoDetails("OCCLUSAL_CARIES"), ...demoDetails("PLANNED_TREATMENT")],
  },
  {
    label: "Obturación + Caries",
    details: [...demoDetails("SIMPLE_FILLING"), ...demoDetails("PROXIMAL_CARIES")],
  },
  {
    label: "Temporal + Lesión cervical",
    details: [...demoDetails("TEMPORARY_RESTORATION"), ...demoDetails("CERVICAL_CARIES")],
  },
];

function demoDetails(state: ToothVisualState): ToothDetail[] {
  return demoCatalogByState[state].map((detail, index) => ({
    id: `${state}-${index}`,
    color: null,
    pattern: null,
    symbol: null,
    surfaces: demoSurfaces[state] ?? null,
    ...detail,
  }));
}

export function ToothPlayground() {
  const [selected, setSelected] = useState<ToothVisualState>("HEALTHY");

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-black uppercase tracking-wide text-green-700">Dentia Design System</p>
        <h1 className="mt-1 text-3xl font-black text-slate-950">Odontograma Playground</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Pantalla temporal de desarrollo para validar DDS-001, DDS-004 y DDS-004A: anatomía, volumen, capas, estados visuales, hover, selección, tooltip y combinaciones.
        </p>
      </div>

      {groupedStates.map((group) => (
        <section
          key={group.title}
          id={group.title.toLowerCase().replace(/\s+/g, "-")}
          className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <h2 className="text-xl font-black text-slate-950">{group.title}</h2>
          <p className="mt-1 text-sm text-slate-500">{group.description}</p>
          <div className="mt-5 grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
            {group.states.map((state) => (
              <div key={state} className="rounded-2xl border border-slate-100 bg-slate-50 p-3">
                <p className="mb-2 text-center text-xs font-black uppercase text-slate-700">
                  {String(states.indexOf(state) + 1).padStart(2, "0")}. {DDS_STATE_LABELS[state]}
                </p>
                <div className="flex justify-center">
                  <Tooth
                    number={state === "PRIMARY_TOOTH" ? "55" : "36"}
                    dentition={state === "PRIMARY_TOOTH" ? "PRIMARY" : "PERMANENT"}
                    selected={selected === state}
                    details={demoDetails(state)}
                    eventCount={state === "HEALTHY" ? 0 : 1}
                    onClick={() => setSelected(state)}
                    compactBadges={false}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}

      <section id="combinaciones" className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-black text-slate-950">Combinaciones clínicas</h2>
        <p className="mt-1 text-sm text-slate-500">
          Validación de coexistencia visual sin perder prioridad clínica ni anatomía.
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {combinations.map((combo) => (
            <div key={combo.label} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
              <p className="mb-3 text-center text-xs font-black uppercase text-slate-700">{combo.label}</p>
              <div className="flex justify-center">
                <Tooth
                  number="36"
                  dentition="PERMANENT"
                  details={combo.details}
                  eventCount={combo.details.length}
                  compactBadges={false}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="interaccion" className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-black text-slate-950">Estados de interacción</h2>
        <p className="mt-1 text-sm text-slate-500">
          El hover aporta profundidad sin editar datos. La selección orienta al usuario sin ocultar la anatomía.
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p className="mb-3 text-center text-xs font-black uppercase text-slate-700">Normal</p>
            <p className="mb-3 text-center text-[11px] text-slate-500">Estado por defecto.</p>
            <div className="flex justify-center">
              <Tooth number="36" details={demoDetails("HEALTHY")} compactBadges={false} />
            </div>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p className="mb-3 text-center text-xs font-black uppercase text-slate-700">Hover</p>
            <p className="mb-3 text-center text-[11px] text-slate-500">Elevación 3% y sombra natural.</p>
            <div className="flex justify-center">
              <Tooth
                number="36"
                details={demoDetails("OCCLUSAL_CARIES")}
                compactBadges={false}
                className="-translate-y-1 scale-[1.03] border-green-300 shadow-[0_16px_34px_rgba(15,23,42,0.14)]"
              />
            </div>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p className="mb-3 text-center text-xs font-black uppercase text-slate-700">Seleccionado</p>
            <p className="mb-3 text-center text-[11px] text-slate-500">Halo verde fino y discreto.</p>
            <div className="flex justify-center">
              <Tooth number="36" details={demoDetails("ENDODONTICS")} selected compactBadges={false} />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
