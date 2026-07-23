import { AnatomicalClinicalMarkerLayer } from "./ClinicalMarkerLayer";
import type { DualClinicalToothViewModel, ToothFamily } from "./types";

function toothOutline(family: ToothFamily) {
  if (family === "MOLAR") {
    return "M24 18 C22 8 38 7 45 13 C53 7 69 8 67 18 L64 49 C63 64 54 82 49 66 C47 57 45 54 42 66 C36 84 27 64 26 50 Z";
  }
  if (family === "PREMOLAR") {
    return "M30 17 C27 8 44 7 50 13 C56 7 73 9 69 19 L64 49 C62 62 55 78 50 64 C47 55 45 55 42 65 C35 80 28 62 27 49 Z";
  }
  if (family === "CANINE") {
    return "M35 14 C38 6 62 6 65 14 C64 33 60 52 54 73 C50 87 39 86 36 73 C31 51 30 32 35 14 Z";
  }
  return "M36 13 C39 6 61 6 64 13 C64 34 61 54 56 75 C52 88 40 88 36 75 C31 54 31 34 36 13 Z";
}

function crownPath(family: ToothFamily) {
  if (family === "MOLAR") return "M23 18 C25 8 38 8 45 13 C53 8 66 8 68 18 L65 41 C54 46 36 46 25 41 Z";
  if (family === "PREMOLAR") return "M29 17 C29 8 44 8 50 13 C56 8 70 9 69 19 L65 40 C55 45 39 45 28 40 Z";
  return "M35 14 C39 7 61 7 65 14 L62 43 C55 47 44 47 37 43 Z";
}

export function AnatomicalToothView({ viewModel }: { viewModel: DualClinicalToothViewModel }) {
  const { model, surfaceMarkers, structuralMarkers, isAbsent } = viewModel;
  const crown = structuralMarkers.find((marker) => marker.kind === "CROWN");
  const implant = structuralMarkers.find((marker) => marker.kind === "IMPLANT");
  const endodontics = structuralMarkers.find((marker) => marker.kind === "ENDODONTICS");
  const missing = isAbsent;

  return (
    <svg
      viewBox="15 4 70 98"
      preserveAspectRatio="xMidYMid meet"
      className="block h-full max-h-full w-full max-w-full"
      role="img"
      aria-label={`Vista anatómica del diente ${model.toothNumber}`}
    >
      <defs>
        <linearGradient id={`classic-enamel-${model.toothNumber}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="100%" stopColor="#F8FAFC" />
        </linearGradient>
      </defs>
      <path
        d={toothOutline(model.family)}
        fill={missing ? "#F8FAFC" : `url(#classic-enamel-${model.toothNumber})`}
        stroke={missing ? "#94A3B8" : "#475569"}
        strokeDasharray={missing ? "4 4" : undefined}
        strokeWidth="1.8"
      />
      {!missing && <path d={crownPath(model.family)} fill="#FFFFFF" fillOpacity="0.42" stroke="#CBD5E1" strokeWidth="0.8" />}
      {!missing && <AnatomicalClinicalMarkerLayer markers={surfaceMarkers} />}
      {crown && !missing && <path d={crownPath(model.family)} fill={crown.color} fillOpacity="0.9" stroke={crown.stroke} strokeWidth="1.8" />}
      {endodontics && !missing && (
        <g stroke={endodontics.stroke} strokeLinecap="round" fill="none">
          <path d="M50 20 C49 38 49 59 50 86" strokeWidth="3.2" />
          {model.family === "MOLAR" && <path d="M42 28 C40 46 39 60 37 77" strokeWidth="2.6" />}
          {model.family !== "INCISOR" && <path d="M58 28 C60 47 61 60 63 77" strokeWidth="2.6" />}
        </g>
      )}
      {implant && !missing && (
        <g stroke={implant.stroke} fill="none" strokeLinecap="round">
          <path d="M46 58 L54 58 L58 96 L42 96 Z" fill="#ECFEFF" strokeWidth="1.8" />
          <path d="M43 68 H57 M42 76 H58 M41 84 H59" strokeWidth="1.4" />
        </g>
      )}
      {missing && <path d="M32 24 L68 72 M68 24 L32 72" stroke="#94A3B8" strokeLinecap="round" strokeWidth="2" />}
    </svg>
  );
}
