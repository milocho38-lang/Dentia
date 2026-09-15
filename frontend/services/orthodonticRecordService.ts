import { apiRequest } from "@/services/apiClient";
import type { OrthodonticRecord, OrthodonticRecordAction } from "@/types/orthodonticRecord";

export const getOrthodonticRecord = (caseId: string, versionId?: string) =>
  apiRequest<OrthodonticRecord>(`/api/orthodontics/cases/${caseId}/record${versionId ? `?version_id=${versionId}` : ""}`);

export const createOrthodonticRecord = (caseId: string) =>
  apiRequest<OrthodonticRecordAction>(`/api/orthodontics/cases/${caseId}/record`, { method: "POST" });

export const updateOrthodonticRecordVersion = (
  caseId: string, versionId: string, rowVersion: number, content: Record<string, unknown>,
) => apiRequest<OrthodonticRecordAction>(`/api/orthodontics/cases/${caseId}/record/versions/${versionId}`, {
  method: "PATCH", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ row_version: rowVersion, content }),
});

export const finalizeOrthodonticRecordVersion = (
  caseId: string, versionId: string, rowVersion: number,
) => apiRequest<OrthodonticRecordAction>(`/api/orthodontics/cases/${caseId}/record/versions/${versionId}/finalize`, {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ row_version: rowVersion }),
});

export const createOrthodonticRecordVersion = (caseId: string, basedOnVersionId?: string) =>
  apiRequest<OrthodonticRecordAction>(`/api/orthodontics/cases/${caseId}/record/versions`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ based_on_version_id: basedOnVersionId ?? null }),
  });
