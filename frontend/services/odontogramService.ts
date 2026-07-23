import { apiRequest } from "@/services/apiClient";
import type {
  Odontogram,
  OdontogramCatalogItem,
  OdontogramCurrentState,
  OdontogramEnvelope,
  OdontogramEvent,
  OdontogramEventInput,
  OdontogramEventListResponse,
  OdontogramEventUpdateInput,
  OdontogramLinkedProcedureListResponse,
  OdontogramPlannedProcedureCreateInput,
  OdontogramPlannedProcedureCreateResponse,
  OdontogramToothHistoryResponse,
} from "@/types/odontogram";

export function getOdontogram(patientId: string) {
  return apiRequest<OdontogramEnvelope>(
    `/api/patients/${patientId}/odontogram`,
  );
}

export function createOdontogram(
  patientId: string,
  preferredDentition = "PERMANENT",
) {
  return apiRequest<Odontogram>(`/api/patients/${patientId}/odontogram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferred_dentition: preferredDentition }),
  });
}

export function getOdontogramCurrent(patientId: string) {
  return apiRequest<OdontogramCurrentState>(
    `/api/patients/${patientId}/odontogram/current`,
  );
}

export function getOdontogramCatalog() {
  return apiRequest<OdontogramCatalogItem[]>("/api/odontogram/catalog");
}

export function listOdontogramEvents(patientId: string, status?: string) {
  const params = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiRequest<OdontogramEventListResponse>(
    `/api/patients/${patientId}/odontogram/events${params}`,
  );
}

export function createOdontogramEvent(
  patientId: string,
  data: OdontogramEventInput,
) {
  return apiRequest<OdontogramEvent>(
    `/api/patients/${patientId}/odontogram/events`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function updateOdontogramEventDraft(
  eventId: string,
  data: OdontogramEventUpdateInput,
) {
  return apiRequest<OdontogramEvent>(`/api/odontogram/events/${eventId}/draft`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function confirmOdontogramEvent(eventId: string, version: number) {
  return apiRequest<OdontogramEvent>(
    `/api/odontogram/events/${eventId}/confirm`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version }),
    },
  );
}

export function getOdontogramToothHistory(
  patientId: string,
  toothCode: string,
) {
  return apiRequest<OdontogramToothHistoryResponse>(
    `/api/patients/${patientId}/odontogram/teeth/${toothCode}/history`,
  );
}

export function getOdontogramPlannedProcedureLinks(
  patientId: string,
  toothCode?: string,
) {
  const params = toothCode ? `?tooth_code=${encodeURIComponent(toothCode)}` : "";
  return apiRequest<OdontogramLinkedProcedureListResponse>(
    `/api/patients/${patientId}/odontogram/planned-procedure-links${params}`,
  );
}

export function createPlannedProcedureFromOdontogramEvent(
  eventId: string,
  data: OdontogramPlannedProcedureCreateInput,
) {
  return apiRequest<OdontogramPlannedProcedureCreateResponse>(
    `/api/odontogram/events/${eventId}/planned-procedures`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}
