import fs from "node:fs";
import assert from "node:assert/strict";
import { resolveCatalogClinicalTargets } from "../lib/catalogClinicalTargets.mjs";

const treatment = fs.readFileSync(new URL("../components/treatments/TreatmentPages.tsx", import.meta.url), "utf8");
const mapper = fs.readFileSync(new URL("../components/odontogram/classic/dualClinicalMapper.ts", import.meta.url), "utf8");
const legacyMapper = fs.readFileSync(new URL("../components/odontogram/visualMapper.ts", import.meta.url), "utf8");
const legacyState = fs.readFileSync(new URL("../components/odontogram/Tooth/state.ts", import.meta.url), "utf8");
const legacyLayer = fs.readFileSync(new URL("../components/odontogram/Tooth/TreatmentLayer.tsx", import.meta.url), "utf8");

for (const text of [
  "Marcas gráficas fijas:",
  "El precio corresponde a un cobro único y no se multiplica",
  "setZone(targets.zone ?? \"\")",
  "disabled={isFixedSmileDesign}",
]) assert.ok(treatment.includes(text), `falta contrato UI: ${text}`);

for (const code of ["PLAN_EXTRACTION", "PLAN_VENEER", "PLAN_RESIN"]) {
  assert.ok(mapper.includes(code), `falta color planificado rojo: ${code}`);
}
assert.ok(mapper.includes('event.sourceCode === "DONE_EXTRACTION"'), "falta extracción realizada azul");
assert.ok(legacyMapper.includes('PLAN_EXTRACTION: "MISSING"'));
assert.ok(legacyMapper.includes('PLAN_VENEER: "VENEER"'));
assert.ok(legacyState.includes('includesAny(text, ["PLAN_EXTRACTION", "EXTRAC"])'));
assert.ok(legacyState.includes('includesAny(text, ["PLAN_VENEER", "CARILLA", "VENEER"])'));
assert.ok(legacyLayer.includes('M24 22 L54 72 M54 22 L24 72'));
assert.ok(legacyLayer.includes('const veneerColor = isPlanned ? "#DC2626" : "#2563EB"'));

assert.deepEqual(resolveCatalogClinicalTargets({ graphical_targets: { dentition: "PERMANENT", teeth: ["11", "12", "13", "21", "22", "23"] } }, null), {
  fixedTeeth: ["11", "12", "13", "21", "22", "23"], zone: "ANTERIOR", dentition: "PERMANENT", requiredDentition: null,
});
assert.equal(resolveCatalogClinicalTargets({ required_dentition: "PRIMARY" }, "53").dentition, "PRIMARY");
assert.equal(resolveCatalogClinicalTargets({ required_dentition: "SUPERNUMERARY" }, "16").dentition, "SUPERNUMERARY");

console.log("clear-15 UI contract: 17 assertions passed");
