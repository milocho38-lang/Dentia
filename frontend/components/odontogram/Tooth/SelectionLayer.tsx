import { DDS_COLORS } from "./constants";

export function SelectionLayer({ selected }: { selected?: boolean }) {
  if (!selected) return null;
  return (
    <g data-layer="selection">
      <path
        d="M14 10 C28 -3 50 -3 64 10 L72 63 C68 86 10 86 6 63 Z"
        fill="none"
        stroke={DDS_COLORS.selected}
        strokeWidth="1.25"
        opacity="0.58"
      />
    </g>
  );
}
