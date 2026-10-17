import { apiBlob, apiRequest } from "@/services/apiClient";
import type { ClinicalFile, ClinicalFileListResponse } from "@/types/clinicalFile";

export function listClinicalFiles(patientId: string) {
  return apiRequest<ClinicalFileListResponse>(`/api/patients/${patientId}/clinical-files`);
}
export function uploadClinicalFile(patientId: string, form: FormData, signal?: AbortSignal) {
  return apiRequest<ClinicalFile>(`/api/patients/${patientId}/clinical-files`, { method: "POST", body: form, signal });
}
export function downloadClinicalFile(id: string) { return apiBlob(`/api/clinical-files/${id}/download`); }
export function deactivateClinicalFile(id: string, reason: string) {
  return apiRequest<void>(`/api/clinical-files/${id}/deactivate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }) });
}
