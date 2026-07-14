import { apiRequest } from "@/services/apiClient";
import type {
  Allergy,
  AllergyInput,
  AllergyListResponse,
  AllergyUpdateInput,
  ClinicalEvolution,
  ClinicalEvolutionAddendum,
  ClinicalEvolutionAddendumInput,
  ClinicalEvolutionInput,
  ClinicalEvolutionListResponse,
  ClinicalEvolutionUpdateInput,
  ClinicalRecord,
  ClinicalRecordEnvelope,
  ClinicalRecordInput,
  ClinicalRecordUpdateInput,
  ClinicalSummary,
  ClinicalTimelineResponse,
  MedicalHistoryItemInput,
  MedicalHistoryResponse,
  Medication,
  MedicationInput,
  MedicationListResponse,
  MedicationUpdateInput,
} from "@/types/clinicalRecord";

export function getClinicalRecord(patientId: string) {
  return apiRequest<ClinicalRecordEnvelope>(
    `/api/patients/${patientId}/clinical-record`,
  );
}

export function createClinicalRecord(
  patientId: string,
  data: ClinicalRecordInput,
) {
  return apiRequest<ClinicalRecord>(
    `/api/patients/${patientId}/clinical-record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function updateClinicalRecordDraft(
  patientId: string,
  data: ClinicalRecordUpdateInput,
) {
  return apiRequest<ClinicalRecord>(
    `/api/patients/${patientId}/clinical-record/draft`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function listClinicalEvolutions(patientId: string) {
  return apiRequest<ClinicalEvolutionListResponse>(
    `/api/patients/${patientId}/clinical-evolutions`,
  );
}

export function createClinicalEvolution(
  patientId: string,
  data: ClinicalEvolutionInput,
) {
  return apiRequest<ClinicalEvolution>(
    `/api/patients/${patientId}/clinical-evolutions`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getClinicalEvolution(evolutionId: string) {
  return apiRequest<ClinicalEvolution>(`/api/clinical-evolutions/${evolutionId}`);
}

export function updateClinicalEvolutionDraft(
  evolutionId: string,
  data: ClinicalEvolutionUpdateInput,
) {
  return apiRequest<ClinicalEvolution>(
    `/api/clinical-evolutions/${evolutionId}/draft`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function signClinicalEvolution(evolutionId: string, version: number) {
  return apiRequest<ClinicalEvolution>(
    `/api/clinical-evolutions/${evolutionId}/sign`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version, confirm_complete: true }),
    },
  );
}

export function createClinicalEvolutionAddendum(
  evolutionId: string,
  data: ClinicalEvolutionAddendumInput,
) {
  return apiRequest<ClinicalEvolutionAddendum>(
    `/api/clinical-evolutions/${evolutionId}/addendum`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getClinicalTimeline(patientId: string) {
  return apiRequest<ClinicalTimelineResponse>(
    `/api/patients/${patientId}/clinical-timeline`,
  );
}

export function getClinicalSummary(patientId: string) {
  return apiRequest<ClinicalSummary>(
    `/api/patients/${patientId}/clinical-summary`,
  );
}

export function getMedicalHistory(patientId: string) {
  return apiRequest<MedicalHistoryResponse>(
    `/api/patients/${patientId}/medical-history`,
  );
}

export function updateMedicalHistory(
  patientId: string,
  data: {
    record_version: number;
    medical_history_state: string;
    items: MedicalHistoryItemInput[];
  },
) {
  return apiRequest<MedicalHistoryResponse>(
    `/api/patients/${patientId}/medical-history`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getAllergies(patientId: string) {
  return apiRequest<AllergyListResponse>(
    `/api/patients/${patientId}/allergies`,
  );
}

export function createAllergy(patientId: string, data: AllergyInput) {
  return apiRequest<Allergy>(`/api/patients/${patientId}/allergies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateAllergy(
  patientId: string,
  allergyId: string,
  data: AllergyUpdateInput,
) {
  return apiRequest<Allergy>(
    `/api/patients/${patientId}/allergies/${allergyId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getMedications(patientId: string) {
  return apiRequest<MedicationListResponse>(
    `/api/patients/${patientId}/medications`,
  );
}

export function createMedication(patientId: string, data: MedicationInput) {
  return apiRequest<Medication>(`/api/patients/${patientId}/medications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateMedication(
  patientId: string,
  medicationId: string,
  data: MedicationUpdateInput,
) {
  return apiRequest<Medication>(
    `/api/patients/${patientId}/medications/${medicationId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}
