import type { SurfaceOrientation, SurfaceRole, ToothArch, ToothFamily, ToothQuadrant, ToothSurface } from "./types";

export function isValidFdiTooth(toothNumber: string) {
  if (!/^[1-8][1-8]$/.test(toothNumber)) return false;
  const quadrant = Number(toothNumber.slice(0, 1));
  const position = Number(toothNumber.slice(1, 2));
  if ([1, 2, 3, 4].includes(quadrant)) return position >= 1 && position <= 8;
  return position >= 1 && position <= 5;
}

export function quadrantFromTooth(toothNumber: string): ToothQuadrant {
  if (!isValidFdiTooth(toothNumber)) {
    throw new Error(`FDI inválido: ${toothNumber}`);
  }
  const quadrant = Number(toothNumber.slice(0, 1));
  return quadrant as ToothQuadrant;
}

export function archFromQuadrant(quadrant: ToothQuadrant): ToothArch {
  return [1, 2, 5, 6].includes(quadrant) ? "UPPER" : "LOWER";
}

export function familyFromTooth(toothNumber: string): ToothFamily {
  const quadrant = quadrantFromTooth(toothNumber);
  const position = Number(toothNumber.slice(1, 2));
  if ([1, 2].includes(position)) return "INCISOR";
  if (position === 3) return "CANINE";
  if ([5, 6, 7, 8].includes(quadrant) && [4, 5].includes(position)) return "MOLAR";
  if ([4, 5].includes(position)) return "PREMOLAR";
  return "MOLAR";
}

export function isAnteriorFamily(family: ToothFamily) {
  return family === "INCISOR" || family === "CANINE";
}

export function dentitionFromTooth(toothNumber: string) {
  return Number(toothNumber.slice(0, 1)) >= 5 ? "PRIMARY" : "PERMANENT";
}

export function isRightSideQuadrant(quadrant: ToothQuadrant) {
  return [1, 4, 5, 8].includes(quadrant);
}

export function getSurfaceOrientation(toothNumber: string, family = familyFromTooth(toothNumber)): SurfaceOrientation {
  const quadrant = quadrantFromTooth(toothNumber);
  const arch = archFromQuadrant(quadrant);
  const mesialRole = isRightSideQuadrant(quadrant) ? "RIGHT" : "LEFT";
  const distalRole = mesialRole === "RIGHT" ? "LEFT" : "RIGHT";
  const vestibularRole = arch === "UPPER" ? "TOP" : "BOTTOM";
  const innerRole = arch === "UPPER" ? "BOTTOM" : "TOP";
  const innerSurface = arch === "UPPER" ? "PALATAL" : "LINGUAL";
  const centralSurface = isAnteriorFamily(family) ? "INCISAL" : "OCCLUSAL";

  /*
   * Mesial = hacia línea media. Distal = lejos de línea media.
   * Superiores = vestibular arriba y palatina abajo.
   * Inferiores = lingual arriba y vestibular abajo.
   * Anteriores = centro incisal. Posteriores = centro oclusal.
   */
  return {
    toothNumber,
    arch,
    quadrant,
    maxillary: arch,
    family,
    mesial: mesialRole,
    distal: distalRole,
    vestibular: vestibularRole,
    internal: innerRole,
    internalSurface: innerSurface,
    centralSurface,
    innerSurface,
    mesialRole,
    distalRole,
    vestibularRole,
    innerRole,
  };
}

export const getToothOrientation = getSurfaceOrientation;

export function surfaceToRole(surface: ToothSurface, orientation: SurfaceOrientation): SurfaceRole {
  if (surface === "OCCLUSAL" || surface === "INCISAL") return "CENTER";
  if (surface === "MESIAL") return orientation.mesialRole;
  if (surface === "DISTAL") return orientation.distalRole;
  if (surface === "VESTIBULAR") return orientation.vestibularRole;
  if (surface === "PALATAL" || surface === "LINGUAL") return orientation.innerRole;
  if (surface === "CERVICAL") return "CERVICAL";
  if (surface === "PULPAL_RADICULAR") return "PULP";
  return "WHOLE";
}

export function normalizeSurfaceForTooth(surface: ToothSurface, orientation: SurfaceOrientation): ToothSurface {
  if (surface === "OCCLUSAL" && orientation.centralSurface === "INCISAL") return "INCISAL";
  if (surface === "INCISAL" && orientation.centralSurface === "OCCLUSAL") return "OCCLUSAL";
  if (surface === "PALATAL" && orientation.innerSurface === "LINGUAL") return "LINGUAL";
  if (surface === "LINGUAL" && orientation.innerSurface === "PALATAL") return "PALATAL";
  return surface;
}
