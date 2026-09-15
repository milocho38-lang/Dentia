import { apiRequest } from "@/services/apiClient";
import type { CatalogType, OrthodonticCatalog, OrthodonticCatalogOption, OrthodonticEvolution, OrthodonticEvolutionPayload } from "@/types/orthodonticEvolution";

export const getOrthodonticCatalog = (type: CatalogType) =>
  apiRequest<OrthodonticCatalog>(`/api/orthodontics/catalogs/${type}`);
export const addOrthodonticCatalogOption = (type: CatalogType, label: string, intervalValue?: number, intervalUnit?: "WEEK" | "MONTH") =>
  apiRequest<OrthodonticCatalogOption>(`/api/orthodontics/catalogs/${type}/options`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ label, interval_value: intervalValue ?? null, interval_unit: intervalUnit ?? null }) });
export const listOrthodonticEvolutions = (caseId: string) =>
  apiRequest<{ items: OrthodonticEvolution[] }>(`/api/orthodontics/cases/${caseId}/evolutions`);
export const createOrthodonticEvolution = (caseId: string, payload: OrthodonticEvolutionPayload) =>
  apiRequest<OrthodonticEvolution>(`/api/orthodontics/cases/${caseId}/evolutions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
export const updateOrthodonticEvolution = (item: OrthodonticEvolution, payload: OrthodonticEvolutionPayload) =>
  apiRequest<OrthodonticEvolution>(`/api/orthodontics/evolutions/${item.id}/draft`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...payload, row_version: item.row_version, clinical_evolution_version: item.clinical_evolution_version }) });
export const signOrthodonticEvolution = (item: OrthodonticEvolution) =>
  apiRequest<OrthodonticEvolution>(`/api/orthodontics/evolutions/${item.id}/sign`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ row_version: item.row_version, clinical_evolution_version: item.clinical_evolution_version, confirm_complete: true }) });
