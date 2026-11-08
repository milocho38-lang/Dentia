import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolveClinicalCompletionCatalog } from "../lib/clinicalCompletionCatalog.mjs";

const resin = { id: "done-resin", name: "Resina realizada" };
const crown = { id: "done-crown", name: "Corona realizada" };

const configured = resolveClinicalCompletionCatalog([resin, crown], {
  default_performed_catalog_item_id: "done-resin",
});
assert.deepEqual(configured.items, [resin]);
assert.equal(configured.selectedId, "done-resin");
assert.equal(configured.error, null);

const missingDefault = resolveClinicalCompletionCatalog([resin, crown], {
  default_performed_catalog_item_id: null,
});
assert.deepEqual(missingDefault.items, []);
assert.match(missingDefault.error, /no tiene un resultado/);

const inactiveDefault = resolveClinicalCompletionCatalog([resin], {
  default_performed_catalog_item_id: "done-crown",
});
assert.deepEqual(inactiveDefault.items, []);
assert.match(inactiveDefault.error, /no está activo/);

const manual = resolveClinicalCompletionCatalog([resin, crown], null);
assert.deepEqual(manual.items, [resin, crown]);
assert.equal(manual.selectedId, "done-resin");

console.log("clinical completion UI catalog: 4 scenarios passed");

const adapter = readFileSync(
  new URL("../components/odontogram/classic/realClinicalAdapter.ts", import.meta.url),
  "utf8",
);
assert.match(
  adapter,
  /FIND_ENDO_DEFECTIVE[\s\S]{0,120}return "COMPLETED"/,
  "el marcador defectuoso debe usar color de estado realizado (azul)",
);
const anatomical = readFileSync(
  new URL("../components/odontogram/classic/AnatomicalToothView.tsx", import.meta.url),
  "utf8",
);
assert.match(
  anatomical,
  /marker\.kind === "ENDODONTICS" && marker\.variant === "DEFECTIVE_ZIGZAG"[\s\S]{0,160}\?\? structuralMarkers\.find/,
  "el zigzag activo debe ganar de forma determinista frente a una línea endodóntica previa",
);
console.log("defective endodontic UI: blue status and deterministic zigzag priority passed");
