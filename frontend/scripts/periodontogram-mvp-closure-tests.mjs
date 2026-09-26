import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const workspace = readFileSync(
  new URL("../components/periodontogram/PeriodontogramWorkspace.tsx", import.meta.url),
  "utf8",
);
const service = readFileSync(
  new URL("../services/periodontogramService.ts", import.meta.url),
  "utf8",
);
const types = readFileSync(
  new URL("../types/periodontogram.ts", import.meta.url),
  "utf8",
);

assert.match(workspace, /Historial de periodontogramas/);
assert.match(workspace, /Cada fila corresponde a un examen periodontal independiente/);
assert.match(workspace, /item\.status === "DRAFT" \? "Continuar" : "Ver"/);
assert.match(workspace, /Versiones del examen · Actual/);
assert.match(workspace, /Integración con evolución clínica/);
assert.match(workspace, /Vincular a evolución/);
assert.match(workspace, /no copia mediciones ni genera diagnósticos/);
assert.match(workspace, /window\.confirm\("Hay cambios clínicos sin guardar/);
assert.match(workspace, /selected\.timezone_name/);
assert.doesNotMatch(workspace, /Desvincular evolución/);

assert.match(service, /evolution-candidates/);
assert.match(service, /evolution-link/);
assert.match(service, /rowVersion: number/);

assert.match(types, /evolution_id: string \| null/);
assert.match(types, /linked_evolution: PeriodontalEvolutionSummary \| null/);
assert.match(types, /timezone_name: string/);

console.log("periodontogram-mvp-closure-tests OK");
