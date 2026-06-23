import { apiRequest } from "@/services/apiClient";
import type {
  DuplicateResult,
  Patient,
  PatientAppointment,
  PatientInput,
  PatientListResponse,
  PatientSummary,
  Responsible,
  ResponsibleInput,
} from "@/types/patient";

export function listPatients(query = "") {
  return apiRequest<PatientListResponse>(`/api/patients${query}`);
}

export function searchPatients(search: string) {
  const params = new URLSearchParams({
    search,
    status: "Activo",
    page: "1",
    page_size: "15",
  });
  return listPatients(`?${params.toString()}`);
}

export function createPatient(data: PatientInput) {
  return apiRequest<Patient>("/api/patients", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getPatient(patientId: string) {
  return apiRequest<Patient>(`/api/patients/${patientId}`);
}

export function updatePatient(patientId: string, data: PatientInput) {
  const { responsibles: _responsibles, ...payload } = data;
  return apiRequest<Patient>(`/api/patients/${patientId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function checkPatientDuplicates(data: {
  first_names: string;
  last_names: string;
  document_type: string;
  document: string | null;
  mobile: string;
  birth_date?: string | null;
  exclude_patient_id?: string;
}) {
  return apiRequest<DuplicateResult>("/api/patients/check-duplicates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getPatientSummary(patientId: string) {
  return apiRequest<PatientSummary>(`/api/patients/${patientId}/summary`);
}

export async function getPatientAppointments(patientId: string) {
  const response = await apiRequest<{ items: PatientAppointment[] }>(
    `/api/patients/${patientId}/appointments?page=1&page_size=100`,
  );
  return response.items;
}

export function deactivatePatient(patientId: string) {
  return apiRequest<{ success: boolean; message: string; patient: Patient }>(
    `/api/patients/${patientId}/deactivate`,
    { method: "POST" },
  );
}

export function reactivatePatient(patientId: string) {
  return apiRequest<{ success: boolean; message: string; patient: Patient }>(
    `/api/patients/${patientId}/reactivate`,
    { method: "POST" },
  );
}

export async function getResponsibles(patientId: string) {
  const response = await apiRequest<{ items: Responsible[] }>(
    `/api/patients/${patientId}/responsibles`,
  );
  return response.items;
}

export function createResponsible(
  patientId: string,
  data: ResponsibleInput,
) {
  return apiRequest<Responsible>(`/api/patients/${patientId}/responsibles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateResponsible(
  patientId: string,
  responsibleId: string,
  data: ResponsibleInput,
) {
  return apiRequest<Responsible>(
    `/api/patients/${patientId}/responsibles/${responsibleId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function deleteResponsible(
  patientId: string,
  responsibleId: string,
) {
  return apiRequest<{ items: Responsible[] }>(
    `/api/patients/${patientId}/responsibles/${responsibleId}`,
    { method: "DELETE" },
  );
}
