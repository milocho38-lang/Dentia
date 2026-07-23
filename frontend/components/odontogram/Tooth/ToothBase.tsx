import { DDS_COLORS } from "./constants";

export type ToothFamily = "incisor" | "canine" | "premolar" | "molar";

export function getToothFamily(number: string): ToothFamily {
  const position = Number(number[1]);
  if ([1, 2].includes(position)) return "incisor";
  if (position === 3) return "canine";
  if ([4, 5].includes(position)) return "premolar";
  return "molar";
}

export function isAnteriorFamily(family: ToothFamily) {
  return family === "incisor" || family === "canine";
}

export function ToothDefs({ id }: { id: string }) {
  return (
    <defs>
      <radialGradient id={`${id}-enamel`} cx="38%" cy="22%" r="78%">
        <stop offset="0%" stopColor="#FFFFFF" />
        <stop offset="30%" stopColor="#FFFDFB" />
        <stop offset="68%" stopColor="#FAEEDB" />
        <stop offset="100%" stopColor="#D5BFA0" />
      </radialGradient>
      <radialGradient id={`${id}-primary-enamel`} cx="38%" cy="22%" r="78%">
        <stop offset="0%" stopColor="#FFF8D7" />
        <stop offset="42%" stopColor="#F8D777" />
        <stop offset="82%" stopColor="#D7A94A" />
        <stop offset="100%" stopColor="#B88934" />
      </radialGradient>
      <linearGradient id={`${id}-root-shade`} x1="0" x2="1" y1="0" y2="1">
        <stop offset="0%" stopColor="#FFFDF7" />
        <stop offset="48%" stopColor="#F3E3CF" />
        <stop offset="100%" stopColor="#C9B294" />
      </linearGradient>
      <radialGradient id={`${id}-shine`} cx="32%" cy="18%" r="42%">
        <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.98" />
        <stop offset="55%" stopColor="#FFFFFF" stopOpacity="0.32" />
        <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
      </radialGradient>
      <linearGradient id={`${id}-metal`} x1="0" x2="1">
        <stop offset="0%" stopColor="#596575" />
        <stop offset="28%" stopColor="#C8D0D8" />
        <stop offset="52%" stopColor="#F8FAFC" />
        <stop offset="74%" stopColor="#8793A2" />
        <stop offset="100%" stopColor="#475569" />
      </linearGradient>
      <linearGradient id={`${id}-crown-blue`} x1="0" x2="1" y1="0" y2="1">
        <stop offset="0%" stopColor="#B9E0FF" />
        <stop offset="24%" stopColor="#64B5F6" />
        <stop offset="58%" stopColor="#1E88E5" />
        <stop offset="100%" stopColor="#0B579F" />
      </linearGradient>
      <linearGradient id={`${id}-crown-temp`} x1="0" x2="1" y1="0" y2="1">
        <stop offset="0%" stopColor="#FFFFFF" />
        <stop offset="45%" stopColor="#CFE7F7" />
        <stop offset="100%" stopColor="#8FB4CE" />
      </linearGradient>
      <pattern id={`${id}-hatch`} patternUnits="userSpaceOnUse" width="5" height="5">
        <path d="M0 5 5 0" stroke="#64748B" strokeWidth="1" />
      </pattern>
      <filter id={`${id}-soft-shadow`} x="-35%" y="-35%" width="170%" height="170%">
        <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#0F172A" floodOpacity="0.16" />
      </filter>
    </defs>
  );
}

export function ToothBase({
  id,
  family,
  primary,
  disabled,
}: {
  id: string;
  family: ToothFamily;
  primary?: boolean;
  disabled?: boolean;
}) {
  const fill = disabled ? "#E5E7EB" : primary ? `url(#${id}-primary-enamel)` : `url(#${id}-enamel)`;
  const opacity = 1;
  const crownPath =
    family === "molar"
      ? "M20 18 C21 6 32 7 39 16 C46 7 57 6 58 18 C63 31 63 43 56 52 C54 61 52 75 47 79 C42 82 40 62 39 55 C38 62 36 82 31 79 C26 75 24 61 22 52 C15 43 15 31 20 18 Z"
      : family === "premolar"
        ? "M23 18 C24 7 34 8 39 17 C44 8 54 7 55 18 C61 31 60 43 54 52 C52 62 50 75 46 79 C42 82 40 63 39 56 C38 63 36 82 32 79 C28 75 26 62 24 52 C18 43 17 31 23 18 Z"
        : family === "canine"
          ? "M25 17 C26 7 35 7 39 18 C43 7 52 7 53 17 C58 31 57 43 50 52 C49 63 46 76 43 80 C40 84 39 61 39 54 C39 61 38 84 35 80 C32 76 29 63 28 52 C21 43 20 31 25 17 Z"
          : "M26 17 C27 7 51 7 52 17 C56 31 55 43 49 52 C48 62 45 76 42 80 C40 83 39 61 39 54 C39 61 38 83 36 80 C33 76 30 62 29 52 C23 43 22 31 26 17 Z";

  return (
    <g data-layer="tooth-base">
      <ellipse cx="39" cy="79" rx="21" ry="5" fill="#0F172A" opacity="0.08" />
      <path
        d={crownPath}
        fill={fill}
        fillOpacity={opacity}
        stroke={disabled ? "#CBD5E1" : "#CBBDA9"}
        strokeWidth="1.15"
        filter={`url(#${id}-soft-shadow)`}
      />
      <path
        d={family === "molar" ? "M25 21 C31 14 36 18 39 24 C42 18 47 14 53 21" : "M28 21 C33 16 45 16 50 21"}
        fill="none"
        stroke="#D4C3AD"
        strokeLinecap="round"
        strokeWidth="1.05"
        opacity="0.72"
      />
      <path
        d="M28 18 C31 13 37 12 40 16"
        fill="none"
        stroke="#FFFFFF"
        strokeLinecap="round"
        strokeWidth="2"
        opacity="0.55"
      />
      <ellipse cx="34" cy="27" rx="11" ry="16" fill={`url(#${id}-shine)`} opacity={disabled ? 0.2 : 0.58} />
      <path d="M24 54 C30 58 48 58 54 54" fill="none" stroke="#BFA98B" strokeWidth="0.8" opacity="0.42" />
    </g>
  );
}
