export interface ClinicalTerminology {
  record: string;
  open_record: string;
  summary: string;
}

export interface HabitsInput {
  tobacco?: string | null;
  alcohol?: string | null;
  substances?: string | null;
  bruxism?: string | null;
  oral_hygiene?: string | null;
  brushing_frequency?: string | null;
  dental_floss?: string | null;
  sugary_diet?: string | null;
  others?: string | null;
}

export interface DentalHistoryInput {
  last_visit?: string | null;
  previous_treatments?: string | null;
  orthodontics?: string | null;
  implants?: string | null;
  surgeries?: string | null;
  trauma?: string | null;
  bleeding?: string | null;
  sensitivity?: string | null;
  pain?: string | null;
  oral_habits?: string | null;
  previous_experiences?: string | null;
  observations?: string | null;
}

export interface ClinicalRecordInput {
  opening_site_id?: string | null;
  opening_dentist_id?: string | null;
  chief_complaint?: string | null;
  current_situation?: string | null;
  situation_start?: string | null;
  situation_evolution?: string | null;
  symptoms?: string | null;
  previous_treatments?: string | null;
  informant_type?: string | null;
  informant_responsible_id?: string | null;
  informant_name?: string | null;
  informant_relationship?: string | null;
  informant_document?: string | null;
  observations?: string | null;
  habits: HabitsInput;
  dental_history: DentalHistoryInput;
  allergies_state: string;
  medical_history_state: string;
}

export interface ClinicalRecordUpdateInput extends ClinicalRecordInput {
  version: number;
}

export interface ClinicalRecord extends ClinicalRecordInput {
  id: string;
  patient_id: string;
  status: string;
  opened_at: string;
  version: number;
  created_at: string;
  updated_at: string;
  terminology: ClinicalTerminology;
}

export interface ClinicalRecordEnvelope {
  exists: boolean;
  record: ClinicalRecord | null;
  terminology: ClinicalTerminology;
}

export interface MedicalHistoryItem {
  id: string;
  type: string;
  present: "SI" | "NO" | "DESCONOCIDO";
  detail: string | null;
  severity: string | null;
  status: string;
  source: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface MedicalHistoryItemInput {
  type: string;
  present: "SI" | "NO" | "DESCONOCIDO";
  detail?: string | null;
  severity?: string | null;
  status?: string;
  source?: string | null;
  version?: number | null;
}

export interface MedicalHistoryResponse {
  items: MedicalHistoryItem[];
  record_version: number;
  medical_history_state: string;
}

export interface AllergyInput {
  type: string;
  substance: string;
  reaction?: string | null;
  severity: string;
  status: string;
  critical_alert: boolean;
  observations?: string | null;
}

export interface Allergy extends AllergyInput {
  id: string;
  reaction: string | null;
  observations: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface AllergyUpdateInput extends AllergyInput {
  version: number;
}

export interface AllergyListResponse {
  items: Allergy[];
  record_version: number;
  allergies_state: string;
}

export interface MedicationInput {
  name: string;
  dose?: string | null;
  frequency?: string | null;
  route?: string | null;
  since?: string | null;
  reason?: string | null;
  prescriber?: string | null;
  status: string;
  observations?: string | null;
}

export interface Medication extends MedicationInput {
  id: string;
  dose: string | null;
  frequency: string | null;
  route: string | null;
  since: string | null;
  reason: string | null;
  prescriber: string | null;
  observations: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface MedicationUpdateInput extends MedicationInput {
  version: number;
}

export type ClinicalEvolutionStatus = "DRAFT" | "SIGNED" | "VOIDED_BY_COMPENSATING_RECORD";
export type ClinicalEvolutionProcedureAction = "PLANNED" | "PERFORMED" | "REVIEWED" | "SUSPENDED";

export interface ClinicalEvolutionProcedureInput {
  treatment_id?: string | null;
  procedure_id: string;
  action: ClinicalEvolutionProcedureAction;
  observations?: string | null;
}

export interface ClinicalEvolutionInput {
  appointment_id?: string | null;
  treatment_id?: string | null;
  site_id?: string | null;
  dentist_id?: string | null;
  attended_at?: string | null;
  reason?: string | null;
  subjective?: string | null;
  objective?: string | null;
  assessment?: string | null;
  performed_procedure?: string | null;
  anesthesia?: string | null;
  materials?: string | null;
  administered_medications?: string | null;
  findings?: string | null;
  complications?: string | null;
  indications?: string | null;
  recommendations?: string | null;
  next_control_at?: string | null;
  next_control_reason?: string | null;
  followup_id?: string | null;
  observations?: string | null;
  procedures: ClinicalEvolutionProcedureInput[];
}

export interface ClinicalEvolutionUpdateInput extends ClinicalEvolutionInput {
  version: number;
}

export interface ClinicalEvolutionProcedure {
  id: string;
  treatment_id: string | null;
  procedure_id: string;
  procedure_name: string | null;
  action: ClinicalEvolutionProcedureAction;
  observations: string | null;
  created_at: string;
}

export interface ClinicalEvolutionAddendumInput {
  reason: string;
  content: string;
  dentist_id?: string | null;
  site_id?: string | null;
}

export interface ClinicalEvolutionAddendum {
  id: string;
  evolution_id: string;
  reason: string;
  content: string;
  dentist_id: string;
  dentist_name: string | null;
  site_id: string;
  site_name: string | null;
  content_hash: string | null;
  created_by: string;
  created_at: string;
}

export interface ClinicalEvolution extends ClinicalEvolutionInput {
  id: string;
  patient_id: string;
  clinical_record_id: string;
  treatment_name: string | null;
  site_id: string;
  site_name: string | null;
  dentist_id: string;
  dentist_name: string | null;
  attended_at: string;
  timezone_name: string;
  status: ClinicalEvolutionStatus;
  version: number;
  content_hash: string | null;
  signed_at: string | null;
  signed_by: string | null;
  created_by: string;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
  procedures: ClinicalEvolutionProcedure[];
  addenda: ClinicalEvolutionAddendum[];
  terminology: ClinicalTerminology;
}

export interface ClinicalEvolutionListResponse {
  items: ClinicalEvolution[];
}

export interface ClinicalTimelineItem {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string | null;
  title: string;
  summary: string | null;
  clinical_date: string;
  site_id: string | null;
  site_name: string | null;
  dentist_id: string | null;
  dentist_name: string | null;
  metadata: Record<string, unknown> | null;
}

export interface ClinicalTimelineResponse {
  items: ClinicalTimelineItem[];
  terminology: ClinicalTerminology;
}

export interface MedicationListResponse {
  items: Medication[];
  record_version: number;
}

export interface ClinicalSummary {
  patient_id: string;
  exists: boolean;
  terminology: ClinicalTerminology;
  limited: boolean;
  has_critical_alerts: boolean;
  requires_clinical_precaution: boolean;
  message: string | null;
  opened_at: string | null;
  updated_at: string | null;
  allergies_state: string | null;
  medical_history_state: string | null;
  critical_allergies: Allergy[];
  active_medications: Medication[];
  relevant_medical_history: MedicalHistoryItem[];
  active_diagnoses: unknown[];
  last_evolution: unknown | null;
}
