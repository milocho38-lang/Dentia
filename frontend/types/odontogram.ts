export type OdontogramDentition = "PERMANENT" | "PRIMARY" | "MIXED";
export type OdontogramEventStatus =
  | "DRAFT"
  | "CONFIRMED"
  | "VOIDED_BY_COMPENSATING_EVENT";

export interface OdontogramCatalogItem {
  id: string;
  company_id: string | null;
  code: string;
  name: string;
  type: string;
  category: string | null;
  description: string | null;
  color: string | null;
  pattern: string | null;
  symbol: string | null;
  allowed_scopes: string[];
  allowed_surfaces: string[] | null;
  is_active: boolean;
}

export interface Odontogram {
  id: string;
  patient_id: string;
  clinical_record_id: string;
  status: string;
  preferred_dentition: OdontogramDentition;
  created_on: string;
  version: number;
}

export interface OdontogramEnvelope {
  exists: boolean;
  odontogram: Odontogram | null;
  clinical_record_exists: boolean;
}

export interface OdontogramEventDetailInput {
  catalog_item_id: string;
  scope_type: "GENERAL" | "ZONE" | "TOOTH" | "TOOTH_SURFACE";
  zone?: string | null;
  tooth_code?: string | null;
  dentition?: "PERMANENT" | "PRIMARY" | "SUPERNUMERARY" | null;
  surfaces?: string[] | null;
  layer: string;
  status_after?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface OdontogramEventInput {
  event_type: string;
  status?: "DRAFT" | "CONFIRMED";
  evolution_id?: string | null;
  appointment_id?: string | null;
  treatment_id?: string | null;
  procedure_id?: string | null;
  clinical_date?: string | null;
  site_id?: string | null;
  dentist_id?: string | null;
  observation?: string | null;
  details: OdontogramEventDetailInput[];
}

export interface OdontogramEventUpdateInput extends OdontogramEventInput {
  version: number;
}

export interface OdontogramEventDetail {
  id: string;
  catalog_item_id: string;
  catalog_code: string;
  catalog_name: string;
  catalog_type: string;
  color: string | null;
  pattern: string | null;
  symbol: string | null;
  scope_type: string;
  zone: string | null;
  tooth_code: string | null;
  dentition: string | null;
  surfaces: string[] | null;
  layer: string;
  status_after: string | null;
  metadata: Record<string, unknown> | null;
}

export interface OdontogramEvent {
  id: string;
  patient_id: string;
  odontogram_id: string;
  evolution_id: string | null;
  appointment_id: string | null;
  treatment_id: string | null;
  procedure_id: string | null;
  event_type: string;
  status: OdontogramEventStatus;
  clinical_date: string;
  timezone: string;
  observation: string | null;
  correction_reason: string | null;
  parent_event_id: string | null;
  version: number;
  content_hash: string | null;
  confirmed_at: string | null;
  confirmed_by: string | null;
  site_id: string;
  site_name: string | null;
  dentist_id: string;
  dentist_name: string | null;
  created_by: string;
  details: OdontogramEventDetail[];
}

export interface OdontogramEventListResponse {
  items: OdontogramEvent[];
}

export interface OdontogramToothState {
  tooth_code: string;
  dentition: string;
  layers: Record<string, OdontogramEventDetail[]>;
  event_count: number;
}

export interface OdontogramCurrentState {
  odontogram: Odontogram;
  preferred_dentition: OdontogramDentition;
  teeth: OdontogramToothState[];
  general_events: OdontogramEvent[];
  legend: OdontogramCatalogItem[];
}

export interface OdontogramToothHistoryResponse {
  tooth_code: string;
  items: OdontogramEvent[];
}
