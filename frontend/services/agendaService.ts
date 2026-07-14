import { apiRequest } from "@/services/apiClient";
export { completeAppointment } from "@/services/followupService";
import type {
  AgendaOptions,
  Appointment,
  AppointmentClinicalContext,
  AppointmentCreateInput,
  ClinicalCareCompletionInput,
  ClinicalCareCompletionResult,
  AppointmentRescheduleInput,
  AppointmentTimeAdjustInput,
  PatientOption,
} from "@/types/agenda";

export async function getAgendaOptions() {
  return apiRequest<AgendaOptions>("/api/agenda/options");
}

export async function getAgendaEvents(
  startsAt: string,
  endsAt: string,
  dentistId?: string,
  siteId?: string,
) {
  const params = new URLSearchParams({
    starts_at: startsAt,
    ends_at: endsAt,
  });
  if (dentistId) params.set("dentist_id", dentistId);
  if (siteId) params.set("site_id", siteId);
  const response = await apiRequest<{ items: Appointment[] }>(
    `/api/agenda/events?${params.toString()}`,
  );
  return response.items;
}

export function createQuickPatient(data: {
  first_names: string;
  last_names: string;
  document_type: string;
  document: string | null;
  mobile: string;
}) {
  return apiRequest<PatientOption>("/api/patients/quick", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function createAppointment(data: AppointmentCreateInput) {
  return apiRequest<Appointment>("/api/appointments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function confirmAppointment(appointmentId: string, method: string) {
  return apiRequest<Appointment>(
    `/api/appointments/${appointmentId}/confirm`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method }),
    },
  );
}

export function generateAppointmentWhatsApp(appointmentId: string) {
  return apiRequest<{ url: string; phone: string; message: string }>(
    `/api/appointments/${appointmentId}/whatsapp-link`,
    { method: "POST" },
  );
}

export function getAppointmentClinicalContext(appointmentId: string) {
  return apiRequest<AppointmentClinicalContext>(
    `/api/appointments/${appointmentId}/clinical-context`,
  );
}

export function completeClinicalCare(
  appointmentId: string,
  data: ClinicalCareCompletionInput,
) {
  return apiRequest<ClinicalCareCompletionResult>(
    `/api/appointments/${appointmentId}/complete-clinical-care`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function cancelAppointment(appointmentId: string, reason: string) {
  return apiRequest<Appointment>(
    `/api/appointments/${appointmentId}/cancel`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    },
  );
}

export function rescheduleAppointment(
  appointmentId: string,
  data: AppointmentRescheduleInput,
) {
  return apiRequest<Appointment>(
    `/api/appointments/${appointmentId}/reschedule`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function adjustAppointmentTime(
  appointmentId: string,
  data: AppointmentTimeAdjustInput,
) {
  return apiRequest<Appointment>(
    `/api/appointments/${appointmentId}/adjust-time`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}
