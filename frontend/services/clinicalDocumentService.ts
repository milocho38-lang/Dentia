import { apiBlob, apiRequest } from "@/services/apiClient";
import type {
  ClinicalDocument,
  ClinicalDocumentInput,
  ClinicalDocumentListResponse,
  ClinicalDocumentPreviewResponse,
} from "@/types/clinicalDocument";

export function listClinicalDocuments(patientId: string, query = "") {
  return apiRequest<ClinicalDocumentListResponse>(
    `/api/patients/${patientId}/clinical-documents${query}`,
  );
}

export function createClinicalDocument(patientId: string, data: ClinicalDocumentInput) {
  return apiRequest<ClinicalDocument>(`/api/patients/${patientId}/clinical-documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateClinicalDocument(documentId: string, data: Partial<ClinicalDocumentInput> & { version: number }) {
  return apiRequest<ClinicalDocument>(`/api/clinical-documents/${documentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function previewClinicalDocument(documentId: string) {
  return apiRequest<ClinicalDocumentPreviewResponse>(`/api/clinical-documents/${documentId}/preview`, {
    method: "POST",
  });
}

export function finalizeClinicalDocument(documentId: string) {
  return apiRequest<ClinicalDocument>(`/api/clinical-documents/${documentId}/finalize`, {
    method: "POST",
  });
}

export function downloadClinicalDocumentPdf(documentId: string) {
  return apiBlob(`/api/clinical-documents/${documentId}/pdf`);
}

export function duplicateClinicalDocument(documentId: string) {
  return apiRequest<ClinicalDocument>(`/api/clinical-documents/${documentId}/duplicate`, {
    method: "POST",
  });
}

export function voidClinicalDocument(documentId: string, reason: string) {
  return apiRequest<ClinicalDocument>(`/api/clinical-documents/${documentId}/void`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}
