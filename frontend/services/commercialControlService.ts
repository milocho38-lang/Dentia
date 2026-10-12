import { apiRequest } from "@/services/apiClient";
import type { CommercialAccount } from "@/types/commercialControl";

export const listCommercialAccounts = () => apiRequest<{items:CommercialAccount[]}>("/api/platform/commercial/accounts");
export const getCommercialAccount = (companyId:string) => apiRequest<CommercialAccount>(`/api/platform/commercial/accounts/${companyId}`);
export const saveCommercialAccount = (companyId:string, body:object) => apiRequest<CommercialAccount>(`/api/platform/commercial/accounts/${companyId}`, {method:"PUT", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
export const createCommercialTransfer = (companyId:string, body:object) => apiRequest<CommercialAccount>(`/api/platform/commercial/accounts/${companyId}/transfers`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
export const verifyCommercialTransfer = (companyId:string, transferId:string) => apiRequest<CommercialAccount>(`/api/platform/commercial/accounts/${companyId}/transfers/${transferId}/verify`, {method:"POST"});
export const reverseCommercialTransfer = (companyId:string, transferId:string, reason:string) => apiRequest<CommercialAccount>(`/api/platform/commercial/accounts/${companyId}/transfers/${transferId}/reverse`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({reason})});
