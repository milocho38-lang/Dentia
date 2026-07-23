import type { ClinicalMarker, DualClinicalToothViewModel, SurfaceRole } from "./types";

const ROLE_PATHS: Record<Exclude<SurfaceRole, "CERVICAL" | "PULP" | "WHOLE">, string> = {
  TOP: "M50 50 L24 24 A37 37 0 0 1 76 24 Z",
  RIGHT: "M50 50 L76 24 A37 37 0 0 1 76 76 Z",
  BOTTOM: "M50 50 L76 76 A37 37 0 0 1 24 76 Z",
  LEFT: "M50 50 L24 76 A37 37 0 0 1 24 24 Z",
  CENTER: "M50 34 A16 16 0 1 1 49.9 34 Z",
};

const MAP_ROLES: Array<keyof typeof ROLE_PATHS> = ["TOP", "RIGHT", "BOTTOM", "LEFT", "CENTER"];

function markersForRole(markers: ClinicalMarker[], role: SurfaceRole) {
  return markers.filter((marker) => marker.role === role);
}

export function FiveSurfaceMap({ viewModel }: { viewModel: DualClinicalToothViewModel }) {
  const { model, surfaceMarkers, structuralMarkers, isAbsent } = viewModel;
  const wholeMarker = structuralMarkers.find((marker) => marker.role === "WHOLE");
  const pulpMarker = structuralMarkers.find((marker) => marker.role === "PULP");

  return (
    <svg
      viewBox="5 5 90 90"
      preserveAspectRatio="xMidYMid meet"
      className="block h-full max-h-full w-full max-w-full"
      role="img"
      aria-label={`Mapa de cinco caras del diente ${model.toothNumber}`}
    >
      <circle cx="50" cy="50" r="42" fill={isAbsent ? "#F8FAFC" : "#FFFFFF"} stroke={isAbsent ? "#94A3B8" : "#94A3B8"} strokeDasharray={isAbsent ? "4 4" : undefined} strokeWidth="1.4" />
      {MAP_ROLES.map((role) => {
        const markers = markersForRole(surfaceMarkers, role);
        const baseMarker = markers.find((marker) => marker.status !== "PLANNED") ?? markers[0];
        const plannedMarkers = markers.filter((marker) => marker.status === "PLANNED");
        return (
          <g key={role}>
            <path
              d={ROLE_PATHS[role]}
              fill={baseMarker ? baseMarker.color : "#FFFFFF"}
              fillOpacity={baseMarker ? (baseMarker.status === "PLANNED" ? 0.22 : 0.9) : 0.72}
              stroke={baseMarker ? baseMarker.stroke : "#CBD5E1"}
              strokeWidth={baseMarker ? 1.8 : 1}
            />
            {plannedMarkers.map((marker) => (
              <path
                key={marker.id}
                d={ROLE_PATHS[role]}
                fill="none"
                stroke={marker.stroke}
                strokeDasharray="4 3"
                strokeWidth="3"
              />
            ))}
          </g>
        );
      })}
      {wholeMarker && !isAbsent && (
        <circle cx="50" cy="50" r="38" fill="none" stroke={wholeMarker.stroke} strokeDasharray={wholeMarker.status === "PLANNED" ? "5 4" : undefined} strokeWidth="5" />
      )}
      {pulpMarker && <circle cx="50" cy="50" r="13" fill={pulpMarker.color} fillOpacity="0.9" stroke={pulpMarker.stroke} strokeWidth="1.5" />}
      {isAbsent && (
        <g stroke="#94A3B8" strokeLinecap="round" strokeWidth="2.2">
          <path d="M31 31 L69 69" />
          <path d="M69 31 L31 69" />
        </g>
      )}
      <circle cx="50" cy="50" r="18" fill="none" stroke="#E2E8F0" strokeWidth="1" />
      <circle cx="50" cy="50" r="42" fill="none" stroke="#64748B" strokeWidth="1" />
    </svg>
  );
}
