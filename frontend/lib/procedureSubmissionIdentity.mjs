export function resolveProcedureSubmissionIdentity(current, fingerprint, createKey) {
  if (current?.fingerprint === fingerprint) return current;
  return { fingerprint, key: createKey() };
}
