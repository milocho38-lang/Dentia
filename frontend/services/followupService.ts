import { apiRequest } from "@/services/apiClient";
import type { Followup, FollowupDashboard } from "@/types/followup";

export function completeAppointment(
  appointmentId: string,
  data: {
    attention_description: string;
    prescribed_medications: string | null;
    requires_followup: boolean;
    recommended_followup_date: string | null;
    followup_reason: string | null;
  },
) {
  return apiRequest<{
    appointment_id: string;
    appointment_status: string;
    care_id: string;
    followup: Followup | null;
  }>(`/api/appointments/${appointmentId}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function listFollowups(query = "") {
  return apiRequest<{
    items: Followup[];
    page: number;
    page_size: number;
    total: number;
    pages: number;
  }>(`/api/followups${query}`);
}

export function getFollowup(id: string) {
  return apiRequest<Followup>(`/api/followups/${id}`);
}

export function getAppointmentFollowup(patientId: string, appointmentId: string) {
  return apiRequest<Followup>(
    `/api/patients/${patientId}/appointments/${appointmentId}/followup`,
  );
}

export function getFollowupDashboard(siteId?: string) {
  const query = siteId ? `?site_id=${encodeURIComponent(siteId)}` : "";
  return apiRequest<FollowupDashboard>(`/api/followups/dashboard${query}`);
}

export function registerFollowupContact(
  id: string,
  data: {
    management_type: string;
    result: string;
    observation: string | null;
    next_contact_at: string | null;
  },
) {
  return apiRequest<{ followup: Followup }>(`/api/followups/${id}/contact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function generateFollowupWhatsApp(id: string) {
  return apiRequest<{ url: string; phone: string; message: string }>(
    `/api/followups/${id}/whatsapp-link`,
    { method: "POST" },
  );
}

export function scheduleFollowupAppointment(
  id: string,
  data: {
    dentist_id: string;
    site_id: string;
    appointment_type_id: string;
    starts_at: string;
    ends_at: string;
    reason: string;
  },
) {
  return apiRequest<{ followup: Followup }>(
    `/api/followups/${id}/appointments`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function closeFollowup(id: string, reason: string, status: string) {
  return apiRequest<{ followup: Followup }>(`/api/followups/${id}/close`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason, status }),
  });
}

export function reopenFollowup(id: string) {
  return apiRequest<{ followup: Followup }>(`/api/followups/${id}/reopen`, {
    method: "POST",
  });
}
