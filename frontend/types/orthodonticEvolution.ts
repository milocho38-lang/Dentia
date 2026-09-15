export type CatalogType = "ARCH_MATERIAL" | "ARCH_SIZE" | "CONTROL_INTERVAL";

export interface OrthodonticCatalogOption {
  id: string; catalog_type: CatalogType; scope: "DENTIA_BASE" | "TENANT";
  code: string; label: string; status: "ACTIVE" | "RETIRED"; sort_order: number;
  interval_value: number | null; interval_unit: "WEEK" | "MONTH" | null;
}
export interface OrthodonticCatalog { catalog_type: CatalogType; can_manage: boolean; items: OrthodonticCatalogOption[] }
export interface OrthodonticMiniScrew {
  id?: string; screw_type: "SELF_TAPPING" | "SELF_DRILLING";
  location: "INTERRADICULAR" | "PALATAL" | "RETROMOLAR" | "INFRAZYGOMATIC_OR_ANTERIOR_ALVEOLAR";
  material: "TITANIUM" | "STEEL"; measurement: string; notes: string | null; sort_order?: number;
}
export interface OrthodonticEvolution {
  id: string; orthodontic_case_id: string; clinical_evolution_id: string;
  professional_name: string; site_id: string; attended_at: string; timezone_name: string;
  status: "DRAFT" | "SIGNED" | "VOIDED_BY_COMPENSATING_RECORD";
  row_version: number; clinical_evolution_version: number; signed_at: string | null;
  schema_version: string; performed_summary: string | null; notes: string | null;
  upper_material: OptionSnapshot; upper_size: OptionSnapshot;
  lower_material: OptionSnapshot; lower_size: OptionSnapshot;
  upper_aligner_note: string | null; lower_aligner_note: string | null;
  elastic_type: string | null; elastic_configuration: string | null;
  mini_screws: OrthodonticMiniScrew[]; next_session_instructions: string | null;
  next_control: OptionSnapshot; next_control_value: number | null;
  next_control_unit: "WEEK" | "MONTH" | null; suggested_next_control_date: string | null;
  alert_text: string | null; alert_active: boolean; orthodontic_payload_hash: string | null;
  integrity_status: "NOT_APPLICABLE" | "PASS" | "FAIL";
}
export interface OptionSnapshot { option_id: string | null; code: string | null; label: string | null }
export interface OrthodonticEvolutionPayload {
  performed_summary: string | null; notes: string | null;
  upper_material_option_id: string | null; upper_size_option_id: string | null;
  lower_material_option_id: string | null; lower_size_option_id: string | null;
  upper_aligner_note: string | null; lower_aligner_note: string | null;
  elastic_type: string | null; elastic_configuration: string | null;
  mini_screws: Omit<OrthodonticMiniScrew, "id" | "sort_order">[];
  next_session_instructions: string | null; next_control_option_id: string | null;
  alert_text: string | null; alert_active: boolean;
}
