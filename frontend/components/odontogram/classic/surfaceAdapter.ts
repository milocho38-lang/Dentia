import type { ToothSurface } from "./types";

const SURFACE_ALIASES: Record<string, ToothSurface> = {
  OCCLUSAL: "OCCLUSAL",
  OCLUSAL: "OCCLUSAL",
  INCISAL: "INCISAL",
  VESTIBULAR: "VESTIBULAR",
  LABIAL: "VESTIBULAR",
  PALATAL: "PALATAL",
  PALATINA: "PALATAL",
  LINGUAL: "LINGUAL",
  MESIAL: "MESIAL",
  DISTAL: "DISTAL",
  CERVICAL: "CERVICAL",
  PULPAL: "PULPAL_RADICULAR",
  RADICULAR: "PULPAL_RADICULAR",
  PULPAR: "PULPAL_RADICULAR",
  PULPAL_RADICULAR: "PULPAL_RADICULAR",
  WHOLE_TOOTH: "WHOLE_TOOTH",
  PIEZA_COMPLETA: "WHOLE_TOOTH",
  DIENTE_COMPLETO: "WHOLE_TOOTH",
};

export function adaptRealSurfaces(surfaces: string[] | null | undefined): ToothSurface[] {
  if (!surfaces?.length) return [];
  return [...new Set(
    surfaces
      .map((surface) => SURFACE_ALIASES[String(surface).trim().toUpperCase()])
      .filter(Boolean),
  )];
}
