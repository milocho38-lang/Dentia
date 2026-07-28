import { apiBlob, apiRequest } from "@/services/apiClient";
import type {
  Prescription,
  PrescriptionInput,
  PrescriptionListResponse,
  PrescriptionPreviewResponse,
} from "@/types/prescription";

export function listPrescriptions(patientId: string, query = "") {
  return apiRequest<PrescriptionListResponse>(
    `/api/patients/${patientId}/prescriptions${query}`,
  );
}

export function createPrescription(patientId: string, data: PrescriptionInput) {
  return apiRequest<Prescription>(`/api/patients/${patientId}/prescriptions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updatePrescription(
  prescriptionId: string,
  data: Partial<PrescriptionInput> & { version: number },
) {
  return apiRequest<Prescription>(`/api/prescriptions/${prescriptionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function previewPrescription(prescriptionId: string) {
  return apiRequest<PrescriptionPreviewResponse>(
    `/api/prescriptions/${prescriptionId}/preview`,
    { method: "POST" },
  );
}

export function finalizePrescription(prescriptionId: string, allergiesReviewed: boolean) {
  return apiRequest<Prescription>(`/api/prescriptions/${prescriptionId}/finalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ allergies_reviewed: allergiesReviewed }),
  });
}

export function downloadPrescriptionPdf(prescriptionId: string) {
  return apiBlob(`/api/prescriptions/${prescriptionId}/pdf`);
}

export function duplicatePrescription(prescriptionId: string) {
  return apiRequest<Prescription>(`/api/prescriptions/${prescriptionId}/duplicate`, {
    method: "POST",
  });
}

export function voidPrescription(prescriptionId: string, reason: string) {
  return apiRequest<Prescription>(`/api/prescriptions/${prescriptionId}/void`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}
