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
  source_odontogram_event_id: string | null;
  source_diagnosis_action: string | null;
  reviewed_for_evolution: boolean;
  reviewed_at: string | null;
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

export interface OdontogramLinkedProcedure {
  procedure_id: string;
  treatment_id: string;
  treatment_name: string;
  treatment_status: string;
  patient_id: string;
  source_odontogram_event_id: string;
  catalog_procedure_id: string | null;
  name: string;
  category: string | null;
  status: string;
  unit_value: string;
  quantity: string;
  total_value: string;
  scope_type: string;
  zone: string | null;
  tooth: string | null;
  surfaces: string[] | null;
  scope_label: string;
  created_at: string;
}

export interface OdontogramLinkedProcedureListResponse {
  items: OdontogramLinkedProcedure[];
  total: number;
}

export interface OdontogramPlannedProcedureCreateInput {
  idempotency_key: string;
  treatment_id?: string | null;
  new_treatment?: {
    name: string;
    description?: string | null;
    specialty?: string | null;
    responsible_dentist_id?: string | null;
    main_site_id?: string | null;
    observations?: string | null;
  } | null;
  catalog_procedure_id?: string | null;
  name?: string | null;
  category?: string | null;
  dentist_id?: string | null;
  site_id?: string | null;
  unit_value: string;
  quantity: string;
  estimated_date?: string | null;
  observations?: string | null;
  requires_tooth?: boolean;
  scope_type: string;
  zone?: string | null;
  tooth?: string | null;
  surfaces?: string[] | null;
  allow_similar_duplicate?: boolean;
}

export interface OdontogramPlannedProcedureCreateResponse {
  procedure: import("@/types/treatment").Procedure | null;
  linked_procedures: OdontogramLinkedProcedure[];
  source_odontogram_event_id: string;
  treatment_id: string | null;
  idempotency_key: string;
  idempotent_replay: boolean;
  similar_duplicate_detected: boolean;
  message: string;
}
