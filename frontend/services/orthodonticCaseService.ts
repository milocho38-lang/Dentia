import { apiRequest } from "@/services/apiClient";
import type { OrthodonticCase, OrthodonticPatientWorkspace } from "@/types/orthodonticCase";

interface CaseAction { success: boolean; message: string; case: OrthodonticCase }

export const getPatientOrthodontics = (patientId: string) =>
  apiRequest<OrthodonticPatientWorkspace>(`/api/patients/${patientId}/orthodontics`);

export const createOrthodonticCase = (patientId: string, treatmentPlan: string, appliance: string) =>
  apiRequest<CaseAction>(`/api/patients/${patientId}/orthodontics/cases`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ treatment_plan: treatmentPlan || null, current_appliance_summary: appliance || null }),
  });

export const updateOrthodonticCase = (caseId: string, rowVersion: number, treatmentPlan: string, appliance: string) =>
  apiRequest<CaseAction>(`/api/orthodontics/cases/${caseId}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ row_version: rowVersion, treatment_plan: treatmentPlan || null, current_appliance_summary: appliance || null }),
  });

export const activateOrthodonticCase = (caseId: string, rowVersion: number) =>
  transition(caseId, "activate", rowVersion);
export const completeOrthodonticCase = (caseId: string, rowVersion: number) =>
  transition(caseId, "complete", rowVersion);
export const suspendOrthodonticCase = (caseId: string, rowVersion: number) =>
  transition(caseId, "suspend", rowVersion);
export const resumeOrthodonticCase = (caseId: string, rowVersion: number) =>
  transition(caseId, "resume", rowVersion);
export const discontinueOrthodonticCase = (caseId: string, rowVersion: number, reason: string) =>
  transition(caseId, "discontinue", rowVersion, reason);

function transition(caseId: string, action: string, rowVersion: number, reason?: string) {
  return apiRequest<CaseAction>(`/api/orthodontics/cases/${caseId}/${action}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ row_version: rowVersion, reason: reason || null }),
  });
}

export const changeOrthodonticResponsible = (caseId: string, rowVersion: number, dentistId: string) =>
  apiRequest<CaseAction>(`/api/orthodontics/cases/${caseId}/change-responsible`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ row_version: rowVersion, responsible_dentist_id: dentistId }),
  });
