export function canApplyUploadResult(expectedGeneration, currentGeneration, expectedPatientId, currentPatientId) {
  return expectedGeneration === currentGeneration && expectedPatientId === currentPatientId;
}

export function createClinicalFileUploadGate() {
  let active = null;

  return {
    begin({ patientId, generation, createIdempotencyKey, createController }) {
      if (active) return null;
      const attempt = Object.freeze({
        patientId,
        generation,
        idempotencyKey: createIdempotencyKey(),
        controller: createController(),
      });
      active = attempt;
      return attempt;
    },
    isOwner(attempt) {
      return active === attempt;
    },
    finish(attempt) {
      if (active !== attempt) return false;
      active = null;
      return true;
    },
    abortActive() {
      if (!active) return false;
      active.controller.abort();
      return true;
    },
    invalidate() {
      if (active) active.controller.abort();
      active = null;
    },
    get busy() {
      return active !== null;
    },
  };
}
