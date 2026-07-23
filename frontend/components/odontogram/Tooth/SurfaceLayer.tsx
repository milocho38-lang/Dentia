import { DDS_COLORS } from "./constants";
import type { ToothFamily } from "./ToothBase";
import { isAnteriorFamily } from "./ToothBase";
import type { ToothRenderState, ToothSurface, ToothVisualState } from "./types";

const diagnosisStates: ToothVisualState[] = [
  "OCCLUSAL_CARIES",
  "PROXIMAL_CARIES",
  "CERVICAL_CARIES",
  "NON_CARIOUS_CERVICAL_LESION",
  "WEAR",
  "FRACTURE",
  "MOBILITY",
];

const treatmentStates: ToothVisualState[] = [
  "SIMPLE_FILLING",
  "MULTIPLE_FILLINGS",
  "TEMPORARY_RESTORATION",
  "SEALANT",
];

function surfaceColor(states: ToothVisualState[] | undefined) {
  if (!states?.length) return "transparent";
  if (states.some((state) => diagnosisStates.includes(state))) return DDS_COLORS.diagnosis;
  if (states.includes("TEMPORARY_RESTORATION")) return DDS_COLORS.temporaryRestoration;
  if (states.some((state) => treatmentStates.includes(state))) return DDS_COLORS.treatment;
  return "transparent";
}

function surfaceOpacity(states: ToothVisualState[] | undefined) {
  if (!states?.length) return 0;
  if (states.includes("SEALANT")) return 0.55;
  if (states.includes("TEMPORARY_RESTORATION")) return 0.62;
  return 0.78;
}

function hasDiagnosis(states: ToothVisualState[] | undefined) {
  return Boolean(states?.some((state) => diagnosisStates.includes(state)));
}

function hasTreatment(states: ToothVisualState[] | undefined) {
  return Boolean(states?.some((state) => treatmentStates.includes(state)));
}

function unlocalizedDiagnosisStates(renderState: ToothRenderState) {
  return [...renderState.unlocalizedStates].filter((state) => diagnosisStates.includes(state));
}

function unlocalizedTreatmentStates(renderState: ToothRenderState) {
  return [...renderState.unlocalizedStates].filter((state) => treatmentStates.includes(state));
}

function unlocalizedPath(family: ToothFamily, kind: "diagnosis" | "treatment") {
  if (kind === "treatment") {
    return family === "molar"
      ? "M30 35 C34 30 38 34 41 31 C44 34 49 31 48 36 C47 43 42 42 39 45 C35 41 29 43 30 35 Z"
      : "M31 34 C35 29 43 30 47 34 C46 40 41 43 36 41 C32 40 29 37 31 34 Z";
  }
  return family === "molar"
    ? "M31 35 C34 30 39 33 41 31 C45 32 49 36 47 40 C45 45 39 43 36 45 C31 43 28 39 31 35 Z"
    : "M31 34 C35 29 42 31 47 35 C45 40 40 42 35 40 C31 39 29 36 31 34 Z";
}

function organicSurfacePath(surface: ToothSurface, family: ToothFamily, states: ToothVisualState[] | undefined) {
  const anterior = isAnteriorFamily(family);
  if (states?.includes("SEALANT")) {
    return family === "molar"
      ? "M30 35 C33 31 37 36 39 33 C41 36 45 31 48 35 M34 40 C37 37 41 37 44 40"
      : "M32 35 C36 31 42 31 46 35";
  }
  if (states?.some((state) => state === "CERVICAL_CARIES" || state === "NON_CARIOUS_CERVICAL_LESION")) {
    return "M23 52 C31 56 47 56 55 52 C52 57 27 57 23 52 Z";
  }
  if (states?.includes("WEAR")) {
    return anterior ? "M29 27 C35 30 43 30 49 27 C46 32 32 32 29 27 Z" : "M28 31 C35 35 43 35 50 31 C47 37 31 37 28 31 Z";
  }
  if (surface === "MESIAL") return "M22 29 C27 25 31 30 29 37 C27 44 25 52 21 55 C18 47 18 34 22 29 Z";
  if (surface === "DISTAL") return "M56 29 C51 25 47 30 49 37 C51 44 53 52 57 55 C60 47 60 34 56 29 Z";
  if (surface === "VESTIBULAR") return "M29 23 C34 18 45 18 50 24 C48 31 31 32 29 23 Z";
  if (surface === "LINGUAL" || surface === "PALATAL") return "M29 49 C34 45 45 45 50 50 C47 58 31 58 29 49 Z";
  if (surface === "INCISAL") return "M31 30 C35 27 43 27 47 30 C45 36 33 36 31 30 Z";
  return family === "molar"
    ? "M29 35 C33 29 38 35 41 31 C45 31 50 35 47 40 C44 46 37 42 33 43 C28 41 27 37 29 35 Z"
    : "M31 34 C35 29 42 31 47 34 C46 39 42 42 36 41 C32 40 29 37 31 34 Z";
}

export function surfacePath(surface: ToothSurface, family: ToothFamily) {
  const anterior = isAnteriorFamily(family);
  const center = anterior
    ? "M30 31 L48 31 L44 43 L34 43 Z"
    : family === "molar"
      ? "M28 34 C34 28 44 28 50 34 C48 43 30 43 28 34 Z"
      : "M30 33 C35 29 43 29 48 33 L45 43 L33 43 Z";

  const paths: Record<ToothSurface, string> = {
    VESTIBULAR: "M25 20 C32 15 46 15 53 20 L49 34 L29 34 Z",
    PALATAL: "M29 43 L49 43 L54 62 C46 69 32 69 24 62 Z",
    LINGUAL: "M29 43 L49 43 L54 62 C46 69 32 69 24 62 Z",
    MESIAL: "M24 22 L29 34 L24 62 C18 51 18 32 24 22 Z",
    DISTAL: "M54 22 C60 32 60 51 54 62 L49 34 Z",
    OCCLUSAL: center,
    INCISAL: anterior ? "M29 29 L49 29 L46 39 L32 39 Z" : center,
  };
  return paths[surface];
}

export function SurfaceLayer({
  family,
  renderState,
}: {
  family: ToothFamily;
  renderState: ToothRenderState;
}) {
  const surfaces: ToothSurface[] = ["VESTIBULAR", "PALATAL", "LINGUAL", "MESIAL", "DISTAL", isAnteriorFamily(family) ? "INCISAL" : "OCCLUSAL"];
  const genericDiagnosis = unlocalizedDiagnosisStates(renderState);
  const genericTreatment = unlocalizedTreatmentStates(renderState);

  return (
    <g data-layer="surfaces">
      {genericDiagnosis.length > 0 && (
        <path
          d={unlocalizedPath(family, "diagnosis")}
          fill={DDS_COLORS.diagnosis}
          fillOpacity="0.72"
          stroke="#B91C1C"
          strokeOpacity="0.78"
          strokeWidth="0.9"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      {genericTreatment.length > 0 && (
        <path
          d={unlocalizedPath(family, "treatment")}
          fill={genericTreatment.includes("TEMPORARY_RESTORATION") ? DDS_COLORS.temporaryRestoration : DDS_COLORS.treatment}
          fillOpacity={genericTreatment.includes("SEALANT") ? 0.28 : 0.62}
          stroke="#0F5CA8"
          strokeOpacity="0.56"
          strokeWidth={genericTreatment.includes("SEALANT") ? 1.8 : 1}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      {surfaces.map((surface) => {
        const states = renderState.surfaceStates[surface];
        const fill = surfaceColor(states);
        const opacity = surfaceOpacity(states);
        if (!opacity) return null;
        const treatment = hasTreatment(states);
        const diagnosis = hasDiagnosis(states);
        const sealant = states?.includes("SEALANT");
        return (
          <path
            key={surface}
            d={organicSurfacePath(surface, family, states)}
            fill={sealant ? "none" : fill}
            fillOpacity={treatment ? 0.66 : 0.74}
            stroke={diagnosis ? "#B91C1C" : treatment ? "#0F5CA8" : fill}
            strokeOpacity={treatment ? 0.5 : 0.72}
            strokeWidth={sealant ? 2.05 : treatment ? 1 : 0.75}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      })}
    </g>
  );
}
