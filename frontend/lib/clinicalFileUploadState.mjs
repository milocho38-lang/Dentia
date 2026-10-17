export function canApplyUploadResult(expectedGeneration, currentGeneration, expectedPatientId, currentPatientId) {
  return expectedGeneration === currentGeneration && expectedPatientId === currentPatientId;
}
