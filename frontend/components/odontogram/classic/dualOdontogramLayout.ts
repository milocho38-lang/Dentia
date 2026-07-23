import type { OdontogramToothState } from "@/types/odontogram";
import { buildDualClinicalToothModelFromState, type RealClinicalAdapterContext } from "./realClinicalAdapter";
import { dentitionFromTooth } from "./orientation";
import type { DualClinicalToothModel } from "./types";

export const PERMANENT_DUAL_ROWS = [
  ["18", "17", "16", "15", "14", "13", "12", "11"],
  ["21", "22", "23", "24", "25", "26", "27", "28"],
  ["48", "47", "46", "45", "44", "43", "42", "41"],
  ["31", "32", "33", "34", "35", "36", "37", "38"],
] as const;

export const PRIMARY_DUAL_ROWS = [
  ["55", "54", "53", "52", "51"],
  ["61", "62", "63", "64", "65"],
  ["85", "84", "83", "82", "81"],
  ["71", "72", "73", "74", "75"],
] as const;

export type DualOdontogramRows = readonly (readonly string[])[];

export function createEmptyOdontogramToothState(toothCode: string): OdontogramToothState {
  return {
    tooth_code: toothCode,
    dentition: dentitionFromTooth(toothCode),
    layers: {},
    event_count: 0,
  };
}

export function buildDualClinicalModelForTooth(
  toothCode: string,
  toothStateByCode: Map<string, OdontogramToothState>,
  context: RealClinicalAdapterContext = {},
): DualClinicalToothModel {
  const state = toothStateByCode.get(toothCode) ?? createEmptyOdontogramToothState(toothCode);
  return buildDualClinicalToothModelFromState(state, context).model;
}

export function buildDualClinicalModelsForRows(
  rows: DualOdontogramRows,
  toothStateByCode: Map<string, OdontogramToothState>,
  context: RealClinicalAdapterContext = {},
): DualClinicalToothModel[][] {
  return rows.map((row) => row.map((toothCode) => buildDualClinicalModelForTooth(toothCode, toothStateByCode, context)));
}
