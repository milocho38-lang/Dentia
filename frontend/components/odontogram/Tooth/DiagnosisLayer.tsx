import { DDS_COLORS } from "./constants";
import type { ToothFamily } from "./ToothBase";
import { isAnteriorFamily } from "./ToothBase";
import type { ToothRenderState } from "./types";

export function DiagnosisLayer({
  family,
  renderState,
}: {
  family: ToothFamily;
  renderState: ToothRenderState;
}) {
  const states = renderState.visualStates;
  const anterior = isAnteriorFamily(family);

  return (
    <g data-layer="diagnosis" fill="none" stroke={DDS_COLORS.diagnosis} strokeLinecap="round" strokeLinejoin="round">
      {states.has("CERVICAL_CARIES") && (
        <path d="M23 52 C29 55 36 56 43 55 C48 55 52 54 55 52" strokeWidth="3.8" />
      )}
      {states.has("NON_CARIOUS_CERVICAL_LESION") && (
        <>
          <path d="M24 51 C31 55 47 55 54 51" strokeWidth="2.4" />
          <path d="M27 55 C34 58 44 58 51 55" strokeWidth="1.05" strokeDasharray="3 3" opacity="0.68" />
        </>
      )}
      {states.has("WEAR") && (
        <path d={anterior ? "M29 26 C35 29 43 29 49 26" : "M28 31 C34 34 44 34 50 31"} strokeWidth="2.35" />
      )}
      {states.has("FRACTURE") && (
        <path d="M31 24 C35 28 38 29 36 35 C34 40 42 43 47 51" strokeWidth="2.1" />
      )}
      {states.has("MOBILITY") && (
        <>
          <path d="M13 34 C9 38 9 45 13 49" strokeWidth="1.8" />
          <path d="M65 34 C69 38 69 45 65 49" strokeWidth="1.8" />
          <path d="M9 34 C4 39 4 46 9 51" strokeWidth="1.1" opacity="0.62" />
          <path d="M69 34 C74 39 74 46 69 51" strokeWidth="1.1" opacity="0.62" />
        </>
      )}
    </g>
  );
}
