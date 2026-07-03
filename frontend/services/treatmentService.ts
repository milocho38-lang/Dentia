import { apiRequest } from "@/services/apiClient";
import type {
  Budget,
  FinanceBreakdownItem,
  FinanceDashboard,
  PatientBalanceItem,
  Payment,
  Procedure,
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

export function createProcedure(
  treatmentId: string,
  data: {
    name: string;
    category?: string | null;
    dentist_id?: string | null;
    site_id?: string | null;
    unit_value: string;
    quantity: string;
    estimated_date?: string | null;
    observations?: string | null;
  },
) {
  return apiRequest<Procedure>(`/api/treatments/${treatmentId}/procedures`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
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
