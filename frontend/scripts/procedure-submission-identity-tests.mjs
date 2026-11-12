import assert from "node:assert/strict";
import { resolveProcedureSubmissionIdentity } from "../lib/procedureSubmissionIdentity.mjs";

let sequence = 0;
const createKey = () => `synthetic-key-${++sequence}`;
const fingerprint = JSON.stringify({ catalog: "endo", tooth: "31", optOut: true });

let identity = resolveProcedureSubmissionIdentity(null, fingerprint, createKey);
assert.equal(identity.key, "synthetic-key-1");

// A 201 followed by a lost response/failed refresh leaves the form state intact.
// Retrying the same payload must reuse the key so the backend returns its replay.
identity = resolveProcedureSubmissionIdentity(identity, fingerprint, createKey);
assert.equal(identity.key, "synthetic-key-1");
assert.equal(sequence, 1);

// After confirmed success resetProcedureForm clears the ref. A deliberate second
// identical procedure must receive a fresh key instead of replaying the first.
identity = null;
identity = resolveProcedureSubmissionIdentity(identity, fingerprint, createKey);
assert.equal(identity.key, "synthetic-key-2");
assert.equal(sequence, 2);

// Editing the payload before retry also rotates the key.
identity = resolveProcedureSubmissionIdentity(
  identity,
  JSON.stringify({ catalog: "endo", tooth: "32", optOut: true }),
  createKey,
);
assert.equal(identity.key, "synthetic-key-3");

console.log("procedure submission identity: 4 assertions passed");
