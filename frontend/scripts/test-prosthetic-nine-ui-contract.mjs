import assert from "node:assert/strict";
import fs from "node:fs";

const mapping = fs.readFileSync(new URL("../components/odontogram/classic/clinicalCodeMapping.ts", import.meta.url), "utf8");
const five = fs.readFileSync(new URL("../components/odontogram/classic/FiveSurfaceMap.tsx", import.meta.url), "utf8");
const anatomical = fs.readFileSync(new URL("../components/odontogram/classic/AnatomicalToothView.tsx", import.meta.url), "utf8");
const legacy = fs.readFileSync(new URL("../components/odontogram/Tooth/TreatmentLayer.tsx", import.meta.url), "utf8");
const legacyState = fs.readFileSync(new URL("../components/odontogram/Tooth/state.ts", import.meta.url), "utf8");
const visualMapper = fs.readFileSync(new URL("../components/odontogram/visualMapper.ts", import.meta.url), "utf8");
const treatments = fs.readFileSync(new URL("../components/treatments/TreatmentPages.tsx", import.meta.url), "utf8");
const realAdapter = fs.readFileSync(new URL("../components/odontogram/classic/realClinicalAdapter.ts", import.meta.url), "utf8");

assert.match(mapping, /PLAN_POST/);
assert.match(mapping, /DONE_POST/);
assert.match(mapping, /DONE_PULPOTOMY/);
assert.match(five, /wholeMarkers\.map/);
assert.match(five, /marker\.kind === "POST"/);
assert.match(anatomical, /marker\.kind === "POST"|kind === "POST"/);
assert.doesNotMatch(legacy, /states\.has\("ENDODONTICS"\) \|\| states\.has\("POST"\)/);
assert.match(legacy, /states\.has\("PLANNED_TREATMENT"\) \? "#DC2626" : DDS_COLORS\.treatment/);
assert.match(legacyState, /layer === "PLANNED" && includesAny\(text, \["PLAN_POST", "POSTE", "POST"\]\)/);
assert.match(visualMapper, /PLAN_POST: "POST"/);
assert.match(realAdapter, /mapping\.kind === "PULPOTOMY" && mapping\.defaultSurfaces\?\.length/);
assert.match(legacy, /states\.has\("TEMPORARY_CROWN"\)\) && !states\.has\("MISSING"\)/);
assert.match(treatments, /requires_prior_code === "DONE_IMPLANT"/);
assert.match(treatments, /Implante realizado antecedente/);
assert.match(treatments, /prior_implant_event_id: requiresImplantAntecedent/);
assert.match(treatments, /No fue posible consultar los implantes realizados\. Verifique permisos/);

console.log("prosthetic nine UI contract: 16 assertions passed");
