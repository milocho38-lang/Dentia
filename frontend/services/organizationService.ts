import { apiRequest } from "@/services/apiClient";
import type {
  Company,
  CompanyInput,
  DentistSiteManagement,
  Site,
  SiteImpact,
  SiteInput,
} from "@/types/organization";

export function getCompany() {
  return apiRequest<Company>("/api/company");
}

export function updateCompany(data: CompanyInput) {
  return apiRequest<Company>("/api/company", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function listSites(search = "", status = "") {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (status) params.set("status", status);
  const query = params.size ? `?${params.toString()}` : "";
  return apiRequest<{ items: Site[] }>(`/api/sites${query}`);
}

export function getSite(id: string) {
  return apiRequest<Site>(`/api/sites/${id}`);
}

export function createSite(data: SiteInput) {
  return apiRequest<Site>("/api/sites", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateSite(id: string, data: SiteInput) {
  return apiRequest<Site>(`/api/sites/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getSiteImpact(id: string) {
  return apiRequest<SiteImpact>(`/api/sites/${id}/impact`);
}

export function deactivateSite(id: string, reason: string) {
  return apiRequest<{ site: Site; message: string }>(
    `/api/sites/${id}/deactivate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    },
  );
}

export function reactivateSite(id: string, reason: string) {
  return apiRequest<{ site: Site; message: string }>(
    `/api/sites/${id}/reactivate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    },
  );
}

export function listDentists() {
  return apiRequest<{ items: DentistSiteManagement[] }>("/api/dentists");
}

export function updateDentistSites(id: string, siteIds: string[]) {
  return apiRequest<DentistSiteManagement>(`/api/dentists/${id}/sites`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ site_ids: siteIds }),
  });
}
