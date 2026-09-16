import assert from "node:assert/strict";
import fs from "node:fs";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const panel = read("components/orthodontics/OrthodonticEvolutionPanel.tsx");
const workspace = read("components/orthodontics/OrthodonticPatientWorkspace.tsx");
const service = read("services/orthodonticEvolutionService.ts");
const types = read("types/orthodonticEvolution.ts");

assert.match(panel, /label="Evolución"/);
assert.match(panel, /Describe la evolución clínica y los procedimientos realizados durante la sesión/);
assert.doesNotMatch(panel, /Qué se hizo/);
assert.doesNotMatch(panel, /Notas de evolución/);
assert.match(panel, /Arco superior/);
assert.match(panel, /Arco inferior/);
assert.match(panel, /Alineador superior/);
assert.match(panel, /Tipo de elásticos/);
assert.match(panel, /Agregar microtornillo/);
assert.match(panel, /Indicaciones próxima sesión/);
assert.match(panel, /Firmar/);
assert.match(panel, /Reactívalo/);
assert.match(service, /clinical_evolution_version/);
assert.match(service, /orthodontics\/evolutions/);
assert.match(types, /OptionSnapshot/);
assert.match(types, /evolution_text/);
assert.match(workspace, /summary\?\.evolution_text/);

console.log("orthodontic-evolution-tests OK");
