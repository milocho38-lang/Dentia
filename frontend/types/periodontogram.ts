export type PeriodontalExamStatus = "DRAFT" | "FINALIZED";
export type PeriodontalToothState = "PRESENT" | "ABSENT" | "IMPLANT";
export type PeriodontalSiteCode =
  | "BUCCAL_DISTAL"
  | "BUCCAL_MID"
  | "BUCCAL_MESIAL"
  | "LINGUAL_DISTAL"
  | "LINGUAL_MID"
  | "LINGUAL_MESIAL";

export interface PeriodontalSite {
  site_code: PeriodontalSiteCode;
  probing_depth_mm: number | null;
  gingival_margin_mm: number | null;
  clinical_attachment_level_mm: number | null;
  is_periodontal_pocket: boolean;
  bleeding_on_probing: boolean | null;
  plaque: boolean | null;
  suppuration: boolean | null;
}

export interface PeriodontalTooth {
  fdi_number: number;
  state: PeriodontalToothState;
  mobility_grade: number | null;
  furcation_mesial: boolean | null;
  furcation_distal: boolean | null;
  clinical_note: string | null;
  sites: PeriodontalSite[];
}

export interface PeriodontalIndex {
  positive_sites: number;
  evaluated_sites: number;
  percentage: number | null;
}

export interface PeriodontalExamSnapshot {
  teeth: PeriodontalTooth[];
  coverage: {
    eligible_sites: number;
    evaluated_sites: number;
    incomplete: boolean;
  };
  indices: {
    bop: PeriodontalIndex;
    plaque: PeriodontalIndex;
  };
  [key: string]: unknown;
}

export interface PeriodontalDraftBatchUpdate {
  row_version: number;
  teeth?: Array<{
    fdi_number: number;
    state?: PeriodontalToothState;
    mobility_grade?: number | null;
    furcation_mesial?: boolean | null;
    furcation_distal?: boolean | null;
    clinical_note?: string | null;
    clear_clinical_data?: boolean;
  }>;
  sites?: Array<{
    fdi_number: number;
    site_code: PeriodontalSiteCode;
    probing_depth_mm?: number | null;
    gingival_margin_mm?: number | null;
    bleeding_on_probing?: boolean | null;
    plaque?: boolean | null;
    suppuration?: boolean | null;
  }>;
}

export interface PeriodontalExamVersion {
  id: string;
  exam_id: string;
  version_number: number;
  status: PeriodontalExamStatus;
  schema_version: string;
  row_version: number;
  content: Record<string, unknown>;
  snapshot: PeriodontalExamSnapshot | null;
  snapshot_hash: string | null;
  integrity_status: "NOT_APPLICABLE" | "PASS" | "FAIL";
  supersedes_version_id: string | null;
  correction_reason: string | null;
  created_by_user_id: string;
  finalized_by_user_id: string | null;
  finalized_at: string | null;
  created_at: string;
}

export interface PeriodontalEvolutionSummary {
  id: string;
  attended_at: string;
  timezone_name: string;
  status: "DRAFT" | "SIGNED" | "VOIDED_BY_COMPENSATING_RECORD";
  site_id: string;
  site_name: string;
  dentist_id: string;
  dentist_name: string;
}

export interface PeriodontalExam {
  id: string;
  company_id: string;
  patient_id: string;
  site_id: string;
  site_name: string;
  timezone_name: string;
  responsible_dentist_id: string;
  professional_name: string;
  evolution_id: string | null;
  linked_evolution: PeriodontalEvolutionSummary | null;
  status: PeriodontalExamStatus;
  clinical_date: string;
  finalized_at: string | null;
  row_version: number;
  current_version: PeriodontalExamVersion;
  versions: PeriodontalExamVersion[];
  teeth: PeriodontalTooth[];
  coverage: {
    eligible_sites: number;
    evaluated_sites: number;
    incomplete: boolean;
  };
  indices: {
    bop: PeriodontalIndex;
    plaque: PeriodontalIndex;
  };
  created_at: string;
  updated_at: string;
}

export interface PeriodontalExamHistoryItem {
  id: string;
  clinical_date: string;
  professional_name: string;
  site_name: string;
  status: PeriodontalExamStatus;
  current_version_number: number;
  allowed_actions: Array<"VIEW" | "FINALIZE" | "CORRECT">;
  created_at: string;
}

export interface PeriodontalExamList {
  items: PeriodontalExamHistoryItem[];
  total: number;
}

export interface PeriodontalExamAction {
  success: boolean;
  message: string;
  exam: PeriodontalExam;
}

export interface PeriodontalEvolutionCandidateList {
  items: PeriodontalEvolutionSummary[];
}
