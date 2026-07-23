import { DDS_COLORS } from "./constants";
import type { ToothRenderState } from "./types";

export function ObservationLayer({ renderState }: { renderState: ToothRenderState }) {
  const states = renderState.visualStates;

  return (
    <g data-layer="observations">
      {states.has("OBSERVATION") && (
        <circle cx="62" cy="18" r="5" fill={DDS_COLORS.observation} opacity="0.9" />
      )}
      {states.has("PLANNED_TREATMENT") && (
        <path
          d="M17 12 C30 0 48 0 61 12 L68 62 C64 82 14 82 10 62 Z"
          fill="none"
          stroke={DDS_COLORS.planned}
          strokeDasharray="4 4"
          strokeWidth="1.55"
          opacity="0.76"
        />
      )}
      {states.has("IN_PROGRESS_TREATMENT") && (
        <>
          <path
            d="M17 12 C30 0 48 0 61 12 L68 62 C64 82 14 82 10 62 Z"
            fill="none"
            stroke={DDS_COLORS.planned}
            strokeDasharray="4 4"
            strokeWidth="1.45"
            opacity="0.74"
          />
          <path
            d="M21 16 C32 7 46 7 57 16 L62 44 C51 50 27 50 16 44 Z"
            fill="none"
            stroke={DDS_COLORS.treatment}
            strokeWidth="1.65"
            opacity="0.68"
          />
        </>
      )}
    </g>
  );
}
