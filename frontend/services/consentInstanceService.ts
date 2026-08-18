import { apiBlob, apiRequest } from "@/services/apiClient";
import type { ApplicableConsentTemplate, ConsentAccessAudit, ConsentAccessSession, ConsentClarification, ConsentContextInput, ConsentInstance, ConsentInstanceAudit, ConsentPaperPacket } from "@/types/consentInstance";

export async function listConsentInstances(patientId: string): Promise<ConsentInstance[]> {
  return (await apiRequest<{ items: ConsentInstance[] }>(`/api/consent-instances?patient_id=${encodeURIComponent(patientId)}`)).items;
}

export async function getConsentInstance(id: string): Promise<ConsentInstance> {
  return apiRequest(`/api/consent-instances/${id}`);
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
export type ConsentAcceptanceSummary = { acceptance_id:string; status:string; accepted_at:string; actor_type:string; patient_name:string; declarations_version:string; declaration_set_code:string; declarations_country_code:string; declarations_locale:string; declarations_legal_status:string; declarations_set_sha256:string; test_document:boolean; test_notice:string|null; final_document_sha256:string; copy_delivery_status:string|null };
export const getConsentAcceptance = (id:string) => apiRequest<ConsentAcceptanceSummary>(`/api/consent-instances/${id}/acceptance`);
export const downloadConsentFinalDocument = (id:string) => apiBlob(`/api/consent-instances/${id}/final-document`);
export const resendConsentCopy = (id:string) => apiRequest<{status:string;recipient_masked:string;attempted_at:string}>(`/api/consent-instances/${id}/copy-deliveries/resend`,{method:"POST"});
export const getConsentPaperPacket = (id:string) => apiRequest<ConsentPaperPacket>(`/api/consent-instances/${id}/paper`);
export const prepareConsentPaperPacket = (id:string) => apiRequest<ConsentPaperPacket>(`/api/consent-instances/${id}/paper`,{method:"POST"});
export const downloadConsentPaperPrint = (id:string) => apiBlob(`/api/consent-instances/${id}/paper/print-document`);
export const recordConsentPaperSigned = (id:string) => apiRequest<ConsentPaperPacket>(`/api/consent-instances/${id}/paper/record-signed`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({confirmed:true})});
export async function uploadConsentPaperPages(id:string,file:File){const form=new FormData();form.append("file",file);return apiRequest<ConsentPaperPacket>(`/api/consent-instances/${id}/paper/pages`,{method:"POST",body:form});}
export const removeConsentPaperPage = (id:string,pageId:string) => apiRequest<ConsentPaperPacket>(`/api/consent-instances/${id}/paper/pages/${pageId}`,{method:"DELETE"});
export const reorderConsentPaperPages = (id:string,pageIds:string[]) => apiRequest<ConsentPaperPacket>(`/api/consent-instances/${id}/paper/pages/order`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({page_ids:pageIds})});
export const finalizeConsentPaper = (id:string,verification:Record<string,boolean>) => apiRequest<ConsentPaperPacket>(`/api/consent-instances/${id}/paper/finalize`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(verification)});
export const downloadConsentPaperFinal = (id:string) => apiBlob(`/api/consent-instances/${id}/paper/final-document?download=true`);
export const viewConsentPaperFinal = (id:string) => apiBlob(`/api/consent-instances/${id}/paper/final-document`);
export const previewConsentPaperPage = (id:string,pageId:string) => apiBlob(`/api/consent-instances/${id}/paper/pages/${pageId}/preview`);
