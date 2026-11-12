import assert from "node:assert/strict";
import {
  filterTeethForRequiredDentition,
  resolveCatalogClinicalTargets,
} from "../lib/catalogClinicalTargets.mjs";

const teeth = ["11", "36", "51", "55", "75", "85"];

assert.deepEqual(
  filterTeethForRequiredDentition(teeth, "PRIMARY"),
  ["51", "55", "75", "85"],
  "a temporal procedure must only offer primary teeth",
);
assert.deepEqual(
  filterTeethForRequiredDentition(teeth, "PERMANENT"),
  ["11", "36"],
  "a permanent-only procedure must not offer primary teeth",
);
assert.deepEqual(
  filterTeethForRequiredDentition(teeth, null),
  teeth,
  "catalog rows without a dentition restriction retain the current picker",
);
assert.equal(
  resolveCatalogClinicalTargets({ required_dentition: "PRIMARY" }, "11").dentition,
  "PRIMARY",
  "the authoritative catalog dentition must not be inferred from an incompatible tooth",
);

console.log("temporal endodontic procedure tests passed");
