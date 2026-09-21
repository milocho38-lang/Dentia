import { apiRequest } from "@/services/apiClient";
import type {
  DemoRequestDetail,
  DemoRequestFilters,
  DemoRequestListResponse,
  DemoRequestOwner,
  DemoRequestStatus,
} from "@/types/demoRequest";

function queryString(filters: DemoRequestFilters): string {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const result = query.toString();
  return result ? `?${result}` : "";
}

export function listDemoRequests(filters: DemoRequestFilters = {}) {
  return apiRequest<DemoRequestListResponse>(
    `/api/platform/demo-requests${queryString(filters)}`,
  );
}

export function listDemoRequestOwners() {
  return apiRequest<{ items: DemoRequestOwner[] }>(
    "/api/platform/demo-requests/owners",
  );
}

export function getDemoRequest(id: string) {
  return apiRequest<DemoRequestDetail>(`/api/platform/demo-requests/${id}`);
}

export function assignDemoRequest(
  id: string,
  assignedToUserId: string | null,
  rowVersion: number,
) {
  return apiRequest<DemoRequestDetail>(
    `/api/platform/demo-requests/${id}/assignment`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assigned_to_user_id: assignedToUserId,
        row_version: rowVersion,
      }),
    },
  );
}

export function updateDemoRequestStatus(
  id: string,
  status: DemoRequestStatus,
  rowVersion: number,
  reason?: string,
) {
  return apiRequest<DemoRequestDetail>(
    `/api/platform/demo-requests/${id}/status`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, reason: reason || null, row_version: rowVersion }),
    },
  );
}

export function scheduleDemoRequest(
  id: string,
  input: {
    scheduled_at: string;
    timezone: string;
    meeting_url: string | null;
    assigned_to_user_id: string | null;
    note: string | null;
    row_version: number;
  },
) {
  return apiRequest<DemoRequestDetail>(
    `/api/platform/demo-requests/${id}/schedule`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    },
  );
}

export function addDemoRequestNote(id: string, text: string, rowVersion: number) {
  return apiRequest<DemoRequestDetail>(
    `/api/platform/demo-requests/${id}/notes`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, row_version: rowVersion }),
    },
  );
}
