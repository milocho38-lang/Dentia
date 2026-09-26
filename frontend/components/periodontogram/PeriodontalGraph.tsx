"use client";

import { useMemo, useState } from "react";
import {
  MAXILLARY_FDI,
  MANDIBULAR_FDI,
  describeSite,
  siteOrderForTooth,
} from "@/lib/periodontalCharting";
import {
  mapGingivalMarginY,
  mapPocketBottomY,
  PERIODONTAL_ARCH_WIDTH,
  graphApicalDirection,
  periodontalToothFamily,
  periodontalSiteX,
  periodontalToothCenterX,
  siteGraphAccessibleLabel,
  siteGraphDetail,
  siteGraphMarkers,
  splitMeasuredSegments,
  toothGraphKind,
  toothGraphMarkers,
  type PeriodontalGraphArch,
  type PeriodontalGraphPoint,
  type PeriodontalToothFamily,
} from "@/lib/periodontalGraph";
import type {
  PeriodontalSite,
  PeriodontalSiteCode,
  PeriodontalTooth,
} from "@/types/periodontogram";

const SVG_HEIGHT = 148;
const TOOTH_SCALE = 1.12;
const CLINICAL_LINE_STROKE_WIDTH = 1.6;
const SINGLE_POINT_RADIUS = 1.9;
const MARKER_LANE_GAP = 5;

type GraphFace = "BUCCAL" | "LINGUAL";

interface SiteVisual {
  key: string;
  tooth: PeriodontalTooth;
  site: PeriodontalSite;
  face: GraphFace;
  x: number;
  baselineY: number;
  gm: ReturnType<typeof mapGingivalMarginY>;
  pocketBottom: ReturnType<typeof mapPocketBottomY>;
}

interface PeriodontalArchGraphProps {
  teeth: PeriodontalTooth[];
  arch: PeriodontalGraphArch;
  face: GraphFace;
  faceLabel: string;
  activeFdi: number;
  activeSiteCode: PeriodontalSiteCode | null;
  onSelectTooth: (fdiNumber: number) => void;
  onSelectSite: (fdiNumber: number, siteCode: PeriodontalSiteCode) => void;
}

const graphBaseline = (arch: PeriodontalGraphArch) =>
  arch === "MAXILLARY" ? 65 : 75;

const graphKey = (fdiNumber: number, siteCode: PeriodontalSiteCode) =>
  `${fdiNumber}:${siteCode}`;

function buildSites(
  teeth: PeriodontalTooth[],
  arch: PeriodontalGraphArch,
  face: GraphFace,
) {
  const fdiNumbers = arch === "MAXILLARY" ? MAXILLARY_FDI : MANDIBULAR_FDI;
  const toothByFdi = new Map(teeth.map((tooth) => [tooth.fdi_number, tooth]));
  const baselineY = graphBaseline(arch);
  const sites: SiteVisual[] = [];

  fdiNumbers.forEach((fdiNumber, toothIndex) => {
    const tooth = toothByFdi.get(fdiNumber);
    if (!tooth) return;
    siteOrderForTooth(fdiNumber).forEach((siteCode, siteIndex) => {
      const site = tooth.sites.find((candidate) => candidate.site_code === siteCode);
      if (!site) return;
      const siteFace: GraphFace = siteCode.startsWith("BUCCAL") ? "BUCCAL" : "LINGUAL";
      if (siteFace !== face) return;
      const x = periodontalSiteX(toothIndex, siteIndex % 3);
      sites.push({
        key: graphKey(fdiNumber, siteCode),
        tooth,
        site,
        face: siteFace,
        x,
        baselineY,
        gm: tooth.state === "ABSENT"
          ? null
          : mapGingivalMarginY(site.gingival_margin_mm, baselineY, arch),
        pocketBottom: tooth.state === "ABSENT"
          ? null
          : mapPocketBottomY(
              site.probing_depth_mm,
              site.gingival_margin_mm,
              baselineY,
              arch,
            ),
      });
    });
  });
  return { fdiNumbers, toothByFdi, baselineY, sites };
}

export function PeriodontalArchGraph({
  teeth,
  arch,
  face,
  faceLabel,
  activeFdi,
  activeSiteCode,
  onSelectTooth,
  onSelectSite,
}: PeriodontalArchGraphProps) {
  const model = useMemo(() => buildSites(teeth, arch, face), [arch, face, teeth]);
  const activeSiteKey = activeSiteCode ? graphKey(activeFdi, activeSiteCode) : null;
  const [selectedSiteKey, setSelectedSiteKey] = useState<string | null>(activeSiteKey);
  const selectedVisual = model.sites.find((site) => site.key === selectedSiteKey) ?? null;
  const lines = [
    ...splitMeasuredSegments(
      model.sites.map((visual) => visual.gm ? { x: visual.x, y: visual.gm.y } : null),
    ).map((points) => ({ kind: "GM" as const, points })),
    ...splitMeasuredSegments(
      model.sites.map((visual) => visual.pocketBottom
        ? { x: visual.x, y: visual.pocketBottom.y }
        : null),
    ).map((points) => ({ kind: "PD" as const, points })),
  ];

  return (
    <div
      className="min-h-[148px] bg-white"
      data-periodontal-arch-graph={arch}
      data-periodontal-graph-face={face}
      data-site-column-x-model="shared-48-columns"
    >
      <svg
        className="block h-auto w-full"
        width={PERIODONTAL_ARCH_WIDTH}
        height={SVG_HEIGHT}
        viewBox={`0 0 ${PERIODONTAL_ARCH_WIDTH} ${SVG_HEIGHT}`}
        role="img"
        aria-label={`Gráfico periodontal ${arch === "MAXILLARY" ? "maxilar" : "mandibular"}, cara ${faceLabel.toLowerCase()}`}
      >
        <rect width={PERIODONTAL_ARCH_WIDTH} height={SVG_HEIGHT} fill="#ffffff" />
        <FaceBaseline y={model.baselineY} />
        <line
          x1={PERIODONTAL_ARCH_WIDTH / 2}
          x2={PERIODONTAL_ARCH_WIDTH / 2}
          y1={8}
          y2={SVG_HEIGHT - 10}
          stroke="#cbd5e1"
          strokeDasharray="3 4"
          aria-hidden="true"
        />

        {model.fdiNumbers.map((fdiNumber, index) => {
          const tooth = model.toothByFdi.get(fdiNumber);
          if (!tooth) return null;
          return (
            <ToothGlyph
              key={fdiNumber}
              tooth={tooth}
              x={periodontalToothCenterX(index)}
              arch={arch}
              active={activeFdi === fdiNumber}
              onSelect={() => onSelectTooth(fdiNumber)}
            />
          );
        })}

        {model.sites.map((visual) => (
          <PocketDepthAid key={`pocket-${visual.key}`} visual={visual} />
        ))}
        {lines.map((line, index) => (
          <ClinicalLine key={`${line.kind}-${index}`} kind={line.kind} points={line.points} />
        ))}
        {model.sites.map((visual) => (
          <SiteMarkers key={`markers-${visual.key}`} visual={visual} arch={arch} />
        ))}
        {model.sites.map((visual) => (
          <SiteHitTarget
            key={`hit-${visual.key}`}
            visual={visual}
            active={activeSiteKey === visual.key || selectedSiteKey === visual.key}
            onSelect={() => {
              setSelectedSiteKey(visual.key);
              onSelectSite(visual.tooth.fdi_number, visual.site.site_code);
            }}
          />
        ))}
        {model.fdiNumbers.map((fdiNumber, index) => (
          <text
            key={`number-${fdiNumber}`}
            x={periodontalToothCenterX(index)}
            y={144}
            fill="#475569"
            fontSize={8}
            fontWeight={800}
            textAnchor="middle"
            aria-hidden="true"
          >
            {fdiNumber}
          </text>
        ))}
      </svg>
      {selectedVisual && <CompactSiteDetail visual={selectedVisual} />}
    </div>
  );
}

function FaceBaseline({ y }: { y: number }) {
  return (
    <g data-gingival-margin-zero-line="true" pointerEvents="none">
      <title>Margen gingival 0</title>
      <line
        x1={0}
        x2={PERIODONTAL_ARCH_WIDTH}
        y1={y}
        y2={y}
        stroke="#94a3b8"
        strokeWidth={1}
        strokeDasharray="3 4"
        vectorEffect="non-scaling-stroke"
      />
    </g>
  );
}

function ClinicalLine({ kind, points }: { kind: "GM" | "PD"; points: PeriodontalGraphPoint[] }) {
  const color = kind === "GM" ? "#be3f75" : "#3374c8";
  if (points.length === 1) {
    return (
      <circle
        cx={points[0].x}
        cy={points[0].y}
        r={SINGLE_POINT_RADIUS}
        fill={color}
        pointerEvents="none"
        aria-hidden="true"
      />
    );
  }
  return (
    <polyline
      points={points.map((point) => `${point.x},${point.y}`).join(" ")}
      fill="none"
      stroke={color}
      strokeWidth={CLINICAL_LINE_STROKE_WIDTH}
      strokeDasharray={kind === "PD" ? "4 3" : undefined}
      strokeLinejoin="round"
      strokeLinecap="round"
      opacity={0.94}
      pointerEvents="none"
      vectorEffect="non-scaling-stroke"
      aria-hidden="true"
    />
  );
}

function PocketDepthAid({ visual }: { visual: SiteVisual }) {
  if (visual.tooth.state === "ABSENT") return null;
  const markers = siteGraphMarkers(visual.site);
  const markerY = visual.pocketBottom?.y ?? visual.gm?.y ?? visual.baselineY;
  const minY = Math.min(visual.gm?.y ?? markerY, visual.pocketBottom?.y ?? markerY);
  const maxY = Math.max(visual.gm?.y ?? markerY, visual.pocketBottom?.y ?? markerY);
  if (!markers.pocket || !visual.gm || !visual.pocketBottom) return null;
  return (
    <line
      x1={visual.x}
      x2={visual.x}
      y1={minY}
      y2={maxY}
      stroke="#f5b83d"
      strokeWidth={4}
      strokeLinecap="round"
      opacity={0.24}
      pointerEvents="none"
      vectorEffect="non-scaling-stroke"
      aria-hidden="true"
    />
  );
}

const clampMarkerY = (value: number) => Math.max(7, Math.min(SVG_HEIGHT - 15, value));

function SiteMarkers({ visual, arch }: { visual: SiteVisual; arch: PeriodontalGraphArch }) {
  if (visual.tooth.state === "ABSENT") return null;
  const markers = siteGraphMarkers(visual.site);
  const markerY = visual.pocketBottom?.y ?? visual.gm?.y ?? visual.baselineY;
  const direction = graphApicalDirection(arch);
  const bopY = clampMarkerY(markerY + direction * MARKER_LANE_GAP);
  const plaqueY = clampMarkerY(markerY + direction * MARKER_LANE_GAP * 2);
  const suppurationY = clampMarkerY(markerY + direction * MARKER_LANE_GAP * 3);
  return (
    <g data-site-marker-lanes="vertical" pointerEvents="none" aria-hidden="true">
      {markers.bop && (
        <circle cx={visual.x} cy={bopY} r={2.5} fill="#dc2626" stroke="#ffffff" strokeWidth={0.8} />
      )}
      {markers.plaque && (
        <rect x={visual.x - 2.5} y={plaqueY - 2.5} width={5} height={5} rx={0.7} fill="#6d4bb8" stroke="#ffffff" strokeWidth={0.7} />
      )}
      {markers.suppuration && (
        <polygon
          points={`${visual.x},${suppurationY - 3.6} ${visual.x + 3.6},${suppurationY} ${visual.x},${suppurationY + 3.6} ${visual.x - 3.6},${suppurationY}`}
          fill="#147b72"
          stroke="#ffffff"
          strokeWidth={0.7}
        />
      )}
      {(visual.gm?.outOfScale || visual.pocketBottom?.outOfScale) && (
        <text x={visual.x} y={clampMarkerY(markerY - direction * 8)} fill="#0f172a" fontSize={8} fontWeight={900} textAnchor="middle">!</text>
      )}
    </g>
  );
}

function SiteHitTarget({ visual, active, onSelect }: { visual: SiteVisual; active: boolean; onSelect: () => void }) {
  if (visual.tooth.state === "ABSENT") return null;
  const label = siteGraphAccessibleLabel(visual.tooth, visual.site);
  return (
    <g
      role="button"
      tabIndex={0}
      aria-label={label}
      className="cursor-pointer outline-none"
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
    >
      <title>{label}</title>
      <rect
        x={visual.x - 8}
        y={visual.baselineY - 44}
        width={16}
        height={88}
        rx={5}
        fill="transparent"
        stroke={active ? "#16a34a" : "transparent"}
        vectorEffect="non-scaling-stroke"
      />
    </g>
  );
}

function ToothGlyph({
  tooth,
  x,
  arch,
  active,
  onSelect,
}: {
  tooth: PeriodontalTooth;
  x: number;
  arch: PeriodontalGraphArch;
  active: boolean;
  onSelect: () => void;
}) {
  const kind = toothGraphKind(tooth.state);
  const family = periodontalToothFamily(tooth.fdi_number);
  const markers = toothGraphMarkers(tooth);
  const visualScale = kind === "ABSENT" ? 1 : TOOTH_SCALE;
  const anchorY = arch === "MAXILLARY"
    ? graphBaseline(arch) + 9 * visualScale
    : graphBaseline(arch) - 9 * visualScale;
  const transform = arch === "MAXILLARY"
    ? `translate(${x} ${anchorY}) scale(${visualScale} ${-visualScale})`
    : `translate(${x} ${anchorY}) scale(${visualScale})`;
  const label = `Pieza ${tooth.fdi_number}, ${kind === "NATURAL" ? "diente natural" : kind === "IMPLANT" ? "implante" : "ausente"}`;

  return (
    <g
      role="button"
      tabIndex={0}
      aria-label={label}
      className="cursor-pointer outline-none"
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
    >
      <title>{label}</title>
      {active && <rect x={x - 29} y={8} width={58} height={126} rx={10} fill="#dcfce7" stroke="#16a34a" />}
      <g transform={transform} data-tooth-visual-scale={visualScale}>
        {kind === "ABSENT" ? (
          <AbsentGlyph />
        ) : kind === "IMPLANT" ? (
          <ImplantGlyph />
        ) : (
          <NaturalToothGlyph family={family} upper={arch === "MAXILLARY"} />
        )}
        {kind === "NATURAL" && markers.mobility !== null && (
          <g transform="translate(15 -29)" data-mobility-marker-offset="crown-side">
            <rect x={-8} y={-6.5} width={17} height={12} rx={6} fill="#fef3c7" stroke="#b76e0d" strokeWidth={0.9} />
            <text x={0.5} y={1.6} fill="#854d0e" fontSize={6.5} fontWeight={900} textAnchor="middle" transform={arch === "MAXILLARY" ? "scale(1 -1)" : undefined}>
              M{markers.mobility}
            </text>
          </g>
        )}
        {kind === "NATURAL" && family === "MOLAR" && (
          <g data-furcation-marker-offset="root-side" pointerEvents="none" aria-hidden="true">
            {markers.furcationMesial && <circle cx={-11} cy={30} r={3.2} fill="#ffffff" stroke="#be3455" strokeWidth={1.8} />}
            {markers.furcationDistal && <circle cx={11} cy={30} r={3.2} fill="#ffffff" stroke="#be3455" strokeWidth={1.8} />}
          </g>
        )}
      </g>
    </g>
  );
}

function NaturalToothGlyph({ family, upper }: { family: PeriodontalToothFamily; upper: boolean }) {
  const shape = {
    INCISOR: { width: 20, crown: "M -10 -17 Q 0 -22 10 -17 L 9 8 Q 0 13 -9 8 Z", roots: [-1] },
    CANINE: { width: 23, crown: "M -11 -13 L 0 -23 L 11 -13 L 9 9 Q 0 14 -9 9 Z", roots: [0] },
    PREMOLAR: { width: 29, crown: "M -14 -13 Q -8 -22 0 -16 Q 8 -22 14 -13 L 12 10 Q 0 15 -12 10 Z", roots: upper ? [-5, 5] : [0] },
    MOLAR: { width: 39, crown: "M -19 -11 Q -14 -21 -8 -15 Q 0 -23 8 -15 Q 14 -21 19 -11 L 17 11 Q 0 17 -17 11 Z", roots: upper ? [-10, 0, 10] : [-8, 8] },
  }[family];
  return (
    <g data-tooth-family={family.toLowerCase()}>
      <path d={shape.crown} fill="#fffaf0" stroke="#9a3412" strokeWidth={1.35} />
      {shape.roots.map((rootX, index) => (
        <path
          key={`${rootX}-${index}`}
          d={`M ${rootX - Math.max(3, shape.width / 7)} 9 Q ${rootX - 2} 31 ${rootX + (index % 2 === 0 ? -1 : 1)} 47 Q ${rootX + 1} 51 ${rootX + Math.max(3, shape.width / 7)} 9`}
          fill="#fffaf0"
          stroke="#9a3412"
          strokeWidth={1.3}
          strokeLinejoin="round"
        />
      ))}
    </g>
  );
}

function ImplantGlyph() {
  return (
    <g data-tooth-family="implant">
      <path d="M -15 -13 Q 0 -21 15 -13 L 12 9 Q 0 14 -12 9 Z" fill="#e0f2fe" stroke="#0369a1" strokeWidth={1.4} />
      <path d="M -6 9 L 6 9 L 4 45 L 0 51 L -4 45 Z" fill="#bae6fd" stroke="#0369a1" strokeWidth={1.5} />
      {[16, 23, 30, 37, 44].map((y) => <line key={y} x1={-5} x2={5} y1={y} y2={y} stroke="#0369a1" strokeWidth={1.2} />)}
      <text x={0} y={1} fill="#075985" fontSize={8} fontWeight={900} textAnchor="middle">I</text>
    </g>
  );
}

function AbsentGlyph() {
  return (
    <g data-tooth-family="absent" opacity={0.48}>
      <rect x={-15} y={-17} width={30} height={31} rx={9} fill="none" stroke="#64748b" strokeDasharray="3 3" />
      <line x1={-11} x2={11} y1={-13} y2={10} stroke="#475569" strokeWidth={1.6} />
      <line x1={11} x2={-11} y1={-13} y2={10} stroke="#475569" strokeWidth={1.6} />
    </g>
  );
}

function CompactSiteDetail({ visual }: { visual: SiteVisual }) {
  const descriptor = describeSite(visual.tooth.fdi_number, visual.site.site_code);
  const detail = siteGraphDetail(visual.site);
  const face = descriptor.face === "BUCCAL" ? "Vestibular" : descriptor.face === "PALATAL" ? "Palatino" : "Lingual";
  const value = (measurement: number | null) => measurement === null ? "—" : `${measurement} mm`;
  return (
    <p className="border-t border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700" aria-live="polite">
      <strong className="text-slate-950">Pieza {visual.tooth.fdi_number} · {face} {descriptor.siteLabel.toLowerCase()}:</strong>{" "}
      Profundidad de sondaje {value(detail.probingDepth)} · Margen gingival {value(detail.gingivalMargin)} · Nivel de inserción {value(detail.clinicalAttachmentLevel)}
    </p>
  );
}

export function PeriodontalGraphLegend() {
  const items = [
    ["Margen gingival", <span key="gm" className="inline-block h-0.5 w-5" style={{ backgroundColor: "#be3f75" }} />],
    ["Fondo de sondaje", <span key="pd" className="inline-block w-5 border-t-2 border-dashed" style={{ borderColor: "#3374c8" }} />],
    ["Sangrado al sondaje", <span key="bop" className="inline-block h-2.5 w-2.5 rounded-full bg-red-600" />],
    ["Placa", <span key="plaque" className="inline-block h-2.5 w-2.5 rounded-sm bg-violet-600" />],
    ["Supuración", <span key="suppuration" className="inline-block h-2.5 w-2.5 rotate-45 rounded-sm bg-teal-700" />],
    ["Bolsa ≥ 4 mm", <span key="pocket" className="inline-block h-3 w-1.5 rounded bg-amber-400/60" />],
    ["Implante", <span key="implant" className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-sky-700 bg-sky-100 text-[8px] font-black text-sky-800">I</span>],
    ["Furcación", <span key="furcation" className="inline-block h-2.5 w-2.5 rounded-full border-2 border-rose-600 bg-white" />],
  ] as const;
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs font-semibold text-slate-700" aria-label="Leyenda del periodontograma">
      {items.map(([label, symbol]) => <span key={label} className="inline-flex items-center gap-1.5">{symbol}{label}</span>)}
    </div>
  );
}
