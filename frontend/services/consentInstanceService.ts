import { apiRequest } from "@/services/apiClient";
import type { ApplicableConsentTemplate, ConsentAccessAudit, ConsentAccessSession, ConsentClarification, ConsentContextInput, ConsentInstance, ConsentInstanceAudit } from "@/types/consentInstance";

export async function listConsentInstances(patientId: string): Promise<ConsentInstance[]> {
  return (await apiRequest<{ items: ConsentInstance[] }>(`/api/consent-instances?patient_id=${encodeURIComponent(patientId)}`)).items;
}

export async function applicableConsentTemplates(context: ConsentContextInput): Promise<ApplicableConsentTemplate[]> {
  return (await apiRequest<{ items: ApplicableConsentTemplate[] }>("/api/consent-instances/applicable-templates", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(context) })).items;
}

export async function createConsentInstances(context: ConsentContextInput, templateVersionIds: string[]): Promise<ConsentInstance[]> {
  return apiRequest<ConsentInstance[]>("/api/consent-instances/batch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ context, template_version_ids: templateVersionIds }) });
}

export async function updateConsentInstance(id: string, context: ConsentContextInput, rowVersion: number): Promise<ConsentInstance> {
  return apiRequest(`/api/consent-instances/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...context, row_version: rowVersion }) });
}

export async function previewConsentInstance(id: string): Promise<{ warning: string; instance: ConsentInstance }> {
  return apiRequest(`/api/consent-instances/${id}/preview`, { method: "POST" });
}

export async function confirmConsentInstance(id: string, rowVersion: number): Promise<ConsentInstance> {
  return apiRequest(`/api/consent-instances/${id}/professional-confirm`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmed: true, row_version: rowVersion }) });
}

export async function voidConsentInstance(id: string, reason: string): Promise<ConsentInstance> {
  return apiRequest(`/api/consent-instances/${id}/void`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }) });
}

export async function listConsentInstanceAudit(id: string): Promise<ConsentInstanceAudit[]> {
  return apiRequest(`/api/consent-instances/${id}/audit`);
}

export const listConsentAccess = (id: string) => apiRequest<ConsentAccessSession[]>(`/api/consent-instances/${id}/access-sessions`);
export const listConsentAccessAudit = (id: string) => apiRequest<ConsentAccessAudit[]>(`/api/consent-instances/${id}/access-sessions/audit`);
export const issueConsentAccess = (id: string) => apiRequest<ConsentAccessSession>(`/api/consent-instances/${id}/access-sessions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
export const reissueConsentAccess = (id: string) => apiRequest<ConsentAccessSession>(`/api/consent-instances/${id}/access-sessions/reissue`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
export const revokeConsentAccess = (instanceId: string, accessId: string, reason: string) => apiRequest<ConsentAccessSession>(`/api/consent-instances/${instanceId}/access-sessions/${accessId}/revoke`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }) });
export const listConsentClarifications = (id: string) => apiRequest<ConsentClarification[]>(`/api/consent-instances/${id}/clarifications`);
export const resolveConsentClarification = (instanceId: string, clarificationId: string) => apiRequest<ConsentClarification>(`/api/consent-instances/${instanceId}/clarifications/${clarificationId}/resolve`, { method: "POST" });
