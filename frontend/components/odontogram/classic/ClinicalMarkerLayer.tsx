import type { ClinicalMarker, SurfaceRole } from "./types";

type MarkerGeometry = {
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  rotate?: number;
};

const GEOMETRY_BY_ROLE: Record<SurfaceRole, MarkerGeometry> = {
  CENTER: { cx: 50, cy: 36, rx: 13, ry: 9 },
  TOP: { cx: 50, cy: 25, rx: 16, ry: 6 },
  BOTTOM: { cx: 50, cy: 51, rx: 16, ry: 6 },
  LEFT: { cx: 30, cy: 38, rx: 6, ry: 15 },
  RIGHT: { cx: 70, cy: 38, rx: 6, ry: 15 },
  CERVICAL: { cx: 50, cy: 61, rx: 22, ry: 5 },
  PULP: { cx: 50, cy: 54, rx: 5, ry: 31 },
  WHOLE: { cx: 50, cy: 39, rx: 31, ry: 30 },
};

export function AnatomicalClinicalMarkerLayer({ markers }: { markers: ClinicalMarker[] }) {
  return (
    <g aria-hidden="true">
      {markers.map((marker) => {
        const geometry = GEOMETRY_BY_ROLE[marker.role];
        if (marker.pattern === "LINE") {
          return (
            <path
              key={marker.id}
              d="M36 18 C45 25 48 31 60 35"
              fill="none"
              stroke={marker.stroke}
              strokeLinecap="round"
              strokeWidth="3"
            />
          );
        }
        if (marker.pattern === "OUTLINE") {
          return (
            <ellipse
              key={marker.id}
              cx={geometry.cx}
              cy={geometry.cy}
              rx={geometry.rx}
              ry={geometry.ry}
              fill="none"
              stroke={marker.stroke}
              strokeDasharray="4 3"
              strokeWidth="2.8"
            />
          );
        }
        return (
          <ellipse
            key={marker.id}
            cx={geometry.cx}
            cy={geometry.cy}
            rx={geometry.rx}
            ry={geometry.ry}
            fill={marker.color}
            fillOpacity={marker.pattern === "SYMBOL" ? 0.74 : 0.9}
            stroke={marker.stroke}
            strokeWidth="1.4"
          />
        );
      })}
    </g>
  );
}

export function MarkerPill({ marker }: { marker: ClinicalMarker }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-slate-100 bg-white px-2.5 py-1 text-[11px] font-black text-slate-700 shadow-sm">
      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: marker.color }} />
      {marker.label}
    </span>
  );
}
