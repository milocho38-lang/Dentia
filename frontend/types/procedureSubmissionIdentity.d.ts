declare module "@/lib/procedureSubmissionIdentity.mjs" {
  export type ProcedureSubmissionIdentity = {
    fingerprint: string;
    key: string;
  };

  export function resolveProcedureSubmissionIdentity(
    current: ProcedureSubmissionIdentity | null,
    fingerprint: string,
    createKey: () => string,
  ): ProcedureSubmissionIdentity;
}
