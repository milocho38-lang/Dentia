import { DDS_COLORS } from "./constants";
import type { ToothRenderState } from "./types";

export function TreatmentLayer({
  id,
  renderState,
}: {
  id: string;
  renderState: ToothRenderState;
}) {
  const states = renderState.visualStates;
  const crownFill = states.has("TEMPORARY_CROWN") ? `url(#${id}-crown-temp)` : `url(#${id}-crown-blue)`;

  if (states.has("MISSING")) {
    return (
      <g data-layer="treatments">
        <path
          d="M20 18 C21 6 32 7 39 16 C46 7 57 6 58 18 C63 31 63 43 56 52 C54 61 52 75 47 79 C42 82 40 62 39 55 C38 62 36 82 31 79 C26 75 24 61 22 52 C15 43 15 31 20 18 Z"
          fill="none"
          stroke={DDS_COLORS.neutral}
          strokeDasharray="5 4"
          strokeWidth="1.55"
          opacity="0.78"
        />
      </g>
    );
  }

  return (
    <g data-layer="treatments">
      {states.has("IMPLANT") && (
        <>
          <path d="M28 15 C29 7 49 7 50 15 C54 25 53 34 48 39 C43 43 35 43 30 39 C25 34 24 25 28 15 Z" fill="#FFFDF7" stroke="#CBBDA9" strokeWidth="1" />
          <path d="M34 38 C35 35 43 35 44 38 L47 78 C44 82 34 82 31 78 Z" fill={`url(#${id}-metal)`} stroke="#475569" strokeWidth="1.25" />
          <path d="M32 47 C36 45 42 45 46 47 M32 55 C36 53 42 53 46 55 M32 63 C36 61 42 61 46 63 M32 71 C36 69 42 69 46 71" stroke="#64748B" strokeWidth="1.05" fill="none" />
          <path d="M36 40 C37 52 37 66 36 78" stroke="#FFFFFF" strokeWidth="1.1" opacity="0.72" />
          <circle cx="39" cy="59" r="3" fill={DDS_COLORS.implant} opacity="0.9" />
        </>
      )}

      {(states.has("DEFINITIVE_CROWN") || states.has("TEMPORARY_CROWN")) && !states.has("IMPLANT") && !states.has("MISSING") && (
        <>
          <path d="M20 18 C22 7 32 8 39 16 C46 8 56 7 58 18 C61 28 60 40 54 48 C45 53 33 53 24 48 C18 40 17 28 20 18 Z" fill={crownFill} fillOpacity="0.9" stroke="#0F5CA8" strokeOpacity="0.55" strokeWidth="1.2" />
          <path d="M27 20 C32 15 46 15 51 20" stroke="#FFFFFF" strokeOpacity="0.7" strokeWidth="1.9" strokeLinecap="round" fill="none" />
          <path d="M26 24 C32 21 46 21 52 24" stroke="#FFFFFF" strokeOpacity="0.28" strokeWidth="1" strokeLinecap="round" fill="none" />
          <path d="M23 33 C32 39 46 39 55 33" stroke="#FFFFFF" strokeOpacity="0.34" strokeWidth="1.05" strokeLinecap="round" fill="none" />
        </>
      )}

      {states.has("FIXED_PROSTHESIS") && (
        <>
          <path d="M10 40 C20 31 29 32 38 40 C47 32 58 31 68 40" fill="none" stroke={DDS_COLORS.treatment} strokeWidth="4.2" strokeLinecap="round" opacity="0.82" />
          <path d="M17 36 C23 33 28 34 33 39 M45 39 C50 34 56 33 62 36" fill="none" stroke="#FFFFFF" strokeWidth="1.2" opacity="0.55" />
        </>
      )}

      {states.has("REMOVABLE_PROSTHESIS") && (
        <>
          <path d="M14 45 C25 36 53 36 64 45" fill="none" stroke={DDS_COLORS.implant} strokeWidth="2.4" strokeLinecap="round" />
          <path d="M22 43 C30 50 48 50 56 43" fill="none" stroke={DDS_COLORS.treatment} strokeWidth="3.2" strokeLinecap="round" strokeDasharray="5 3" opacity="0.82" />
        </>
      )}

      {(states.has("ENDODONTICS") || states.has("POST")) && !states.has("MISSING") && (
        <>
          <path d="M39 19 C38 31 38 48 39 66" stroke={DDS_COLORS.treatment} strokeWidth="1.9" strokeLinecap="round" fill="none" />
          <path d="M34 64 C36 68 42 68 44 64" stroke={DDS_COLORS.treatment} strokeWidth="1.35" strokeLinecap="round" fill="none" />
        </>
      )}

      {states.has("POST") && (
        <path d="M37.4 30 L40.6 30 L41.2 62 L36.8 62 Z" fill={DDS_COLORS.neutral} opacity="0.72" />
      )}

      {states.has("SEALANT") && (
        <path d="M30 34 C35 29 43 29 48 34 M33 38 C37 36 41 36 45 38" fill="none" stroke={DDS_COLORS.treatment} strokeWidth="2" strokeLinecap="round" />
      )}
    </g>
  );
}
