import { apiRequest } from "@/services/apiClient";
import type {
  PlatformCompanyCreateResponse,
  PlatformCompanyDetail,
  PlatformCompanyInput,
  PlatformCompanyListItem,
} from "@/types/platform";

export function listPlatformCompanies(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiRequest<{ items: PlatformCompanyListItem[] }>(
    `/api/platform/companies${query}`,
  );
}

export function createPlatformCompany(data: PlatformCompanyInput) {
  return apiRequest<PlatformCompanyCreateResponse>("/api/platform/companies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getPlatformCompany(id: string) {
  return apiRequest<PlatformCompanyDetail>(`/api/platform/companies/${id}`);
}

export function deactivatePlatformCompany(id: string) {
  return apiRequest<{ company: PlatformCompanyDetail; message: string }>(
    `/api/platform/companies/${id}/deactivate`,
    { method: "POST" },
  );
}

export function reactivatePlatformCompany(id: string) {
  return apiRequest<{ company: PlatformCompanyDetail; message: string }>(
    `/api/platform/companies/${id}/reactivate`,
    { method: "POST" },
  );
}
