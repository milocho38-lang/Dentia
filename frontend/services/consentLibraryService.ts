import { apiRequest } from "@/services/apiClient";
import type { ConsentLibraryDocument, ConsentLibraryEquivalenceApprovalInput, ConsentLibraryInstallResponse, ConsentLibrarySourceReview, ConsentLibraryVersion } from "@/types/consentLibrary";

export function listConsentLibrary(query = "") {
  return apiRequest<{ items: ConsentLibraryDocument[]; total: number }>(`/api/consent-library${query}`);
}

export function installConsentLibraryVersion(versionId: string) {
  return apiRequest<ConsentLibraryInstallResponse>(`/api/consent-library/versions/${versionId}/install`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ change_summary: "Instalación desde biblioteca oficial Dentia." }),
  });
}

export function cloneConsentLibraryVersion(versionId: string) {
  return apiRequest<ConsentLibraryInstallResponse>(`/api/consent-library/versions/${versionId}/clone`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ change_summary: "Copia editable creada desde biblioteca oficial Dentia." }),
  });
}

export function approveConsentLibraryEquivalence(versionId: string, payload: ConsentLibraryEquivalenceApprovalInput) {
  return apiRequest<ConsentLibraryVersion>(`/api/consent-library/versions/${versionId}/approve-equivalence`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getConsentLibrarySourceReview(versionId: string) {
  return apiRequest<ConsentLibrarySourceReview>(`/api/consent-library/versions/${versionId}/source`);
}
