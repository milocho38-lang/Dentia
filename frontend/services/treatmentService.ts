import { apiBlob, apiRequest } from "@/services/apiClient";
import type {
  Budget,
  FinanceBreakdownItem,
  FinanceDashboard,
  PatientBalanceItem,
  Payment,
  Procedure,
  ProcedureCatalogItem,
  ProcedureCatalogListResponse,
  Treatment,
  TreatmentListResponse,
} from "@/types/treatment";

export function listTreatments(query = "") {
  return apiRequest<TreatmentListResponse>(`/api/treatments${query}`);
}

export function createTreatment(data: {
  patient_id: string;
  name: string;
  description?: string | null;
  specialty?: string | null;
  responsible_dentist_id?: string | null;
  main_site_id?: string | null;
  start_date?: string | null;
  observations?: string | null;
}) {
  return apiRequest<Treatment>("/api/treatments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getTreatment(treatmentId: string) {
  return apiRequest<Treatment>(`/api/treatments/${treatmentId}`);
}

export function approveTreatment(treatmentId: string) {
  return apiRequest<Treatment>(`/api/treatments/${treatmentId}/approve`, {
    method: "POST",
  });
}

export function closeTreatment(treatmentId: string) {
  return apiRequest<Treatment>(`/api/treatments/${treatmentId}/close`, {
    method: "POST",
  });
}

export function cancelTreatment(treatmentId: string, reason: string) {
  return apiRequest<Treatment>(`/api/treatments/${treatmentId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}

export function listProcedures(treatmentId: string) {
  return apiRequest<Procedure[]>(`/api/treatments/${treatmentId}/procedures`);
}

export function listProcedureCatalog(query = "") {
  return apiRequest<ProcedureCatalogListResponse>(`/api/procedure-catalog${query}`);
}

export function createProcedureCatalogItem(data: {
  name: string;
  category?: string | null;
  description?: string | null;
  suggested_value?: string | null;
  suggested_scope_type?: string | null;
  is_active?: boolean;
}) {
  return apiRequest<ProcedureCatalogItem>("/api/procedure-catalog", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateProcedureCatalogItem(
  itemId: string,
  data: {
    name?: string;
    category?: string | null;
    description?: string | null;
    suggested_value?: string | null;
    suggested_scope_type?: string | null;
    is_active?: boolean;
  },
) {
  return apiRequest<ProcedureCatalogItem>(`/api/procedure-catalog/${itemId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function activateProcedureCatalogItem(itemId: string) {
  return apiRequest<ProcedureCatalogItem>(`/api/procedure-catalog/${itemId}/activate`, {
    method: "POST",
  });
}

export function deactivateProcedureCatalogItem(itemId: string) {
  return apiRequest<ProcedureCatalogItem>(`/api/procedure-catalog/${itemId}/deactivate`, {
    method: "POST",
  });
}

export function createProcedure(
  treatmentId: string,
  data: {
    catalog_procedure_id?: string | null;
    name: string;
    category?: string | null;
    dentist_id?: string | null;
    site_id?: string | null;
    unit_value: string;
    quantity: string;
    estimated_date?: string | null;
    observations?: string | null;
    scope_type?: string;
    zone?: string | null;
    tooth?: string | null;
    surfaces?: string[] | null;
  },
) {
  return apiRequest<Procedure>(`/api/treatments/${treatmentId}/procedures`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateProcedure(
  treatmentId: string,
  procedureId: string,
  data: {
    catalog_procedure_id?: string | null;
    name?: string;
    category?: string | null;
    dentist_id?: string | null;
    site_id?: string | null;
    unit_value?: string;
    quantity?: string;
    estimated_date?: string | null;
    observations?: string | null;
    scope_type?: string;
    zone?: string | null;
    tooth?: string | null;
    surfaces?: string[] | null;
  },
) {
  return apiRequest<Procedure>(
    `/api/treatments/${treatmentId}/procedures/${procedureId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function deleteProcedure(treatmentId: string, procedureId: string) {
  return apiRequest<void>(
    `/api/treatments/${treatmentId}/procedures/${procedureId}`,
    { method: "DELETE" },
  );
}

export function markProcedureDone(treatmentId: string, procedureId: string) {
  return apiRequest<Procedure>(
    `/api/treatments/${treatmentId}/procedures/${procedureId}/mark-done`,
    { method: "POST" },
  );
}

export function cancelProcedure(
  treatmentId: string,
  procedureId: string,
  reason: string,
) {
  return apiRequest<Procedure>(
    `/api/treatments/${treatmentId}/procedures/${procedureId}/cancel`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    },
  );
}

export function createBudget(
  treatmentId: string,
  data: {
    discount_type?: string | null;
    discount_value: string;
    observations?: string | null;
    expires_on?: string | null;
  },
) {
  return apiRequest<Budget>(`/api/treatments/${treatmentId}/budget`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function approveBudget(budgetId: string) {
  return apiRequest<Budget>(`/api/budgets/${budgetId}/approve`, {
    method: "POST",
  });
}

export function submitBudget(budgetId: string) {
  return apiRequest<Budget>(`/api/budgets/${budgetId}/submit`, {
    method: "POST",
  });
}

export function rejectBudget(budgetId: string) {
  return apiRequest<Budget>(`/api/budgets/${budgetId}/reject`, {
    method: "POST",
  });
}

export function downloadBudgetPdf(budgetId: string) {
  return apiBlob(`/api/budgets/${budgetId}/pdf`);
}

export function duplicateBudgetVersion(budgetId: string) {
  return apiRequest<Budget>(`/api/budgets/${budgetId}/duplicate-version`, {
    method: "POST",
  });
}

export async function listBudgets() {
  const response = await apiRequest<{ items: Budget[]; total: number }>(
    "/api/budgets",
  );
  return response.items;
}

export function createPayment(
  treatmentId: string,
  data: {
    site_id: string;
    dentist_id?: string | null;
    procedure_ids?: string[];
    paid_at: string;
    value: string;
    payment_method: string;
    reference?: string | null;
    observation?: string | null;
  },
) {
  return apiRequest<Payment>(`/api/treatments/${treatmentId}/payments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function listPayments() {
  const response = await apiRequest<{ items: Payment[]; total: number }>(
    "/api/payments",
  );
  return response.items;
}

export function reversePayment(paymentId: string, reason: string) {
  return apiRequest<Payment>(`/api/payments/${paymentId}/reverse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}

export function downloadPaymentReceipt(paymentId: string) {
  return apiBlob(`/api/payments/${paymentId}/receipt`);
}

export function getFinanceDashboard() {
  return apiRequest<FinanceDashboard>("/api/finance/dashboard");
}

export async function getFinanceBySite() {
  const response = await apiRequest<{ items: FinanceBreakdownItem[] }>(
    "/api/finance/by-site",
  );
  return response.items;
}

export async function getFinanceByDentist() {
  const response = await apiRequest<{ items: FinanceBreakdownItem[] }>(
    "/api/finance/by-dentist",
  );
  return response.items;
}

export async function getPatientBalances() {
  const response = await apiRequest<{ items: PatientBalanceItem[] }>(
    "/api/finance/patient-balances",
  );
  return response.items;
}
