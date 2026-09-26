import { apiRequest } from "@/services/apiClient";
import type {
  PeriodontalExam,
  PeriodontalExamAction,
  PeriodontalDraftBatchUpdate,
  PeriodontalExamList,
  PeriodontalEvolutionCandidateList,
} from "@/types/periodontogram";

export const listPeriodontalExams = (patientId: string) =>
  apiRequest<PeriodontalExamList>(`/api/patients/${patientId}/periodontograms`);

export const getPeriodontalExam = (examId: string) =>
  apiRequest<PeriodontalExam>(`/api/periodontograms/${examId}`);

export const createPeriodontalExam = (patientId: string, clinicalDate: string) =>
  apiRequest<PeriodontalExamAction>(`/api/patients/${patientId}/periodontograms`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ clinical_date: clinicalDate }),
  });

export const finalizePeriodontalExam = (examId: string, rowVersion: number) =>
  apiRequest<PeriodontalExamAction>(`/api/periodontograms/${examId}/finalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ row_version: rowVersion }),
  });

export const updatePeriodontalDraft = (
  examId: string,
  payload: PeriodontalDraftBatchUpdate,
) =>
  apiRequest<PeriodontalExamAction>(`/api/periodontograms/${examId}/draft`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

export const correctPeriodontalExam = (
  examId: string,
  rowVersion: number,
  reason: string,
) =>
  apiRequest<PeriodontalExamAction>(`/api/periodontograms/${examId}/correct`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ row_version: rowVersion, reason }),
  });

export const listPeriodontalEvolutionCandidates = (examId: string) =>
  apiRequest<PeriodontalEvolutionCandidateList>(
    `/api/periodontograms/${examId}/evolution-candidates`,
  );

export const linkPeriodontalEvolution = (
  examId: string,
  evolutionId: string,
  rowVersion: number,
) =>
  apiRequest<PeriodontalExamAction>(
    `/api/periodontograms/${examId}/evolution-link`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ evolution_id: evolutionId, row_version: rowVersion }),
    },
  );
