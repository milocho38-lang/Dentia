import { apiRequest } from "@/services/apiClient";
import type {
  PatientImportPreview,
  PatientImportResult,
  PatientImportSource,
} from "@/types/patientImport";

function form(file: File, sourceId: string, previewToken?: string) {
  const body = new FormData();
  body.append("file", file);
  body.append("source_id", sourceId);
  if (previewToken) body.append("preview_token", previewToken);
  return body;
}

export async function listDentalinkSources() {
  return (await apiRequest<{ items: PatientImportSource[] }>(
    "/api/patient-imports/dentalink/sources",
  )).items;
}

export function createDentalinkSource(label: string) {
  return apiRequest<PatientImportSource>("/api/patient-imports/dentalink/sources", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label }),
  });
}

export function previewDentalinkImport(file: File, sourceId: string) {
  return apiRequest<PatientImportPreview>("/api/patient-imports/dentalink/preview", {
    method: "POST",
    body: form(file, sourceId),
  });
}

export function confirmDentalinkImport(
  file: File,
  sourceId: string,
  previewToken: string,
) {
  return apiRequest<PatientImportResult>("/api/patient-imports/dentalink/confirm", {
    method: "POST",
    body: form(file, sourceId, previewToken),
  });
}
