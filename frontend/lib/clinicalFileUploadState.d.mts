export function canApplyUploadResult(expectedGeneration: number, currentGeneration: number, expectedPatientId: string, currentPatientId: string): boolean;

export interface ClinicalFileUploadAttempt {
  readonly patientId: string;
  readonly generation: number;
  readonly idempotencyKey: string;
  readonly controller: AbortController;
}

export interface ClinicalFileUploadGate {
  begin(options: {
    patientId: string;
    generation: number;
    createIdempotencyKey: () => string;
    createController: () => AbortController;
  }): ClinicalFileUploadAttempt | null;
  isOwner(attempt: ClinicalFileUploadAttempt): boolean;
  finish(attempt: ClinicalFileUploadAttempt): boolean;
  abortActive(): boolean;
  invalidate(): void;
  readonly busy: boolean;
}

export function createClinicalFileUploadGate(): ClinicalFileUploadGate;
