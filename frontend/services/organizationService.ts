import { apiBlob, apiRequest } from "@/services/apiClient";
import type {
  Branding,
  BrandingInput,
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

export function getBranding() {
  return apiRequest<Branding>("/api/company/branding");
}

export function updateBranding(data: BrandingInput) {
  return apiRequest<Branding>("/api/company/branding", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function uploadBrandingAsset(kind: "logo" | "signature", file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiRequest<Branding>(`/api/company/branding/${kind}`, {
    method: "POST",
    body: form,
  });
}

export function deleteBrandingAsset(kind: "logo" | "signature") {
  return apiRequest<Branding>(`/api/company/branding/${kind}`, {
    method: "DELETE",
  });
}

export function fetchBrandingAsset(kind: "logo" | "signature") {
  return apiBlob(`/api/company/branding/${kind}`);
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
