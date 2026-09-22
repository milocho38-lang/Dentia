import { apiRequest } from "@/services/apiClient";
import type {
  UsageAdoptionResponse,
  UsageContextResponse,
  UsageQueryFilters,
} from "@/types/usageAdoption";

export function getUsageContext(companyId?: string, signal?: AbortSignal) {
  const query = companyId ? `?company_id=${encodeURIComponent(companyId)}` : "";
  return apiRequest<UsageContextResponse>(`/api/platform/usage/context${query}`, {
    cache: "no-store",
    signal,
  });
}

export function getUserUsageAdoption(
  filters: UsageQueryFilters,
  signal?: AbortSignal,
) {
  const query = new URLSearchParams({ company_id: filters.companyId });
  if (filters.dentistId) query.set("dentist_id", filters.dentistId);
  if (filters.siteId) query.set("site_id", filters.siteId);
  if (filters.periodMode === "custom") {
    if (filters.startDate) query.set("start_date", filters.startDate);
    if (filters.endDate) query.set("end_date", filters.endDate);
  } else {
    query.set("preset", filters.periodMode);
    if (filters.periodMode === "pilot_to_date") {
      if (filters.startDate) query.set("start_date", filters.startDate);
      if (filters.endDate) query.set("end_date", filters.endDate);
    }
  }
  return apiRequest<UsageAdoptionResponse>(
    `/api/platform/usage/users/${filters.userId}?${query.toString()}`,
    { cache: "no-store", signal },
  );
}
