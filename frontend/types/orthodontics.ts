export interface OrthodonticsSeatSummary { seat_limit: number; assigned_active: number; available: number }
export interface OrthodonticsEntitlement {
  id: string | null; company_id: string; enabled: boolean;
  status: "ACTIVE" | "SUSPENDED" | "DISABLED";
  effective_from: string | null; effective_until: string | null;
  seats: OrthodonticsSeatSummary; created_at: string | null; updated_at: string | null;
}
export interface OrthodonticsDentistAssignment {
  id: string | null; dentist_id: string; dentist_name: string;
  dentist_status: string; dentist_is_active: boolean; user_id: string | null;
  user_is_active: boolean; assigned: boolean; assigned_at: string | null;
}
export interface OrthodonticsAssignmentList { entitlement: OrthodonticsEntitlement; items: OrthodonticsDentistAssignment[] }
export interface OrthodonticsAssignmentAction {
  success: boolean; created: boolean; message: string;
  assignment: OrthodonticsDentistAssignment; seats: OrthodonticsSeatSummary;
}
