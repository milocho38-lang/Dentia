import { apiRequest } from "@/services/apiClient";
import type {
  ConsentCatalogItem,
  ConsentPreview,
  ConsentTemplate,
  ConsentTemplateCreateInput,
  ConsentValidation,
  ConsentVersion,
  ConsentVersionInput,
} from "@/types/consentTemplate";

export function listConsentTemplates(query = "") {
  return apiRequest<{ items: ConsentTemplate[]; total: number }>(`/api/consent-templates${query}`);
}

export function getConsentTemplate(id: string) {
  return apiRequest<ConsentTemplate>(`/api/consent-templates/${id}`);
}

export function createConsentTemplate(data: ConsentTemplateCreateInput) {
  return apiRequest<ConsentTemplate>("/api/consent-templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateConsentTemplate(id: string, data: Partial<Pick<ConsentTemplate, "code" | "name" | "description" | "document_kind" | "country_code" | "language_code" | "is_active">>) {
  return apiRequest<ConsentTemplate>(`/api/consent-templates/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function listConsentVersions(templateId: string) {
  return apiRequest<ConsentVersion[]>(`/api/consent-templates/${templateId}/versions`);
}

export function createConsentVersion(templateId: string, data: ConsentVersionInput) {
  return apiRequest<ConsentVersion>(`/api/consent-templates/${templateId}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateConsentVersion(templateId: string, version: ConsentVersion, data: ConsentVersionInput) {
  return apiRequest<ConsentVersion>(`/api/consent-templates/${templateId}/versions/${version.id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...data, row_version: version.row_version }),
  });
}

export function previewConsentVersion(templateId: string, versionId: string) {
  return apiRequest<ConsentPreview>(`/api/consent-templates/${templateId}/versions/${versionId}/preview`, { method: "POST" });
}

export function validateConsentVersion(templateId: string, versionId: string) {
  return apiRequest<ConsentValidation>(`/api/consent-templates/${templateId}/versions/${versionId}/validate`, { method: "POST" });
}

export function publishConsentVersion(templateId: string, versionId: string) {
  return apiRequest<ConsentVersion>(`/api/consent-templates/${templateId}/versions/${versionId}/publish`, { method: "POST" });
}

export function retireConsentVersion(templateId: string, versionId: string, reason: string) {
  return apiRequest<ConsentVersion>(`/api/consent-templates/${templateId}/versions/${versionId}/retire`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }),
  });
}

export function voidConsentDraft(templateId: string, versionId: string, reason: string) {
  return apiRequest<ConsentVersion>(`/api/consent-templates/${templateId}/versions/${versionId}/void`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }),
  });
}

export function createDraftFromConsentVersion(templateId: string, versionId: string, changeSummary: string) {
  return apiRequest<ConsentVersion>(`/api/consent-templates/${templateId}/versions/${versionId}/create-draft`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ change_summary: changeSummary }),
  });
}

export function getConsentDocumentKinds() {
  return apiRequest<ConsentCatalogItem[]>("/api/consent-template-catalog/document-kinds");
}

export function getConsentVariables() {
  return apiRequest<ConsentCatalogItem[]>("/api/consent-template-catalog/variables");
}
