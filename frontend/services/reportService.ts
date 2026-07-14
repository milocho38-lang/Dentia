import { apiRequest } from "@/services/apiClient";
import type { ExecutiveSummary, ReportFilters } from "@/types/report";

function paramsFromFilters(filters: ReportFilters) {
  const params = new URLSearchParams();
  params.set("preset", filters.preset || "month_current");
  if (filters.preset === "custom") {
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
  }
  if (filters.site_id) params.set("site_id", filters.site_id);
  if (filters.dentist_id) params.set("dentist_id", filters.dentist_id);
  return params;
}

export function getExecutiveSummary(filters: ReportFilters) {
  const params = paramsFromFilters(filters);
  return apiRequest<ExecutiveSummary>(
    `/api/reports/executive-summary?${params.toString()}`,
  );
}
