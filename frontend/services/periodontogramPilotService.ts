import { apiRequest } from "@/services/apiClient";
import type {
  PeriodontogramPilot,
  PeriodontogramPilotAccess,
} from "@/types/periodontogramPilot";

export const getPlatformPeriodontogramPilot = (companyId: string) =>
  apiRequest<PeriodontogramPilot>(
    `/api/platform/companies/${companyId}/periodontogram-pilot`,
  );

export const updatePlatformPeriodontogramPilot = (
  companyId: string,
  enabled: boolean,
) =>
  apiRequest<PeriodontogramPilot>(
    `/api/platform/companies/${companyId}/periodontogram-pilot`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    },
  );

export const updatePlatformPeriodontogramPilotDentist = (
  companyId: string,
  dentistId: string,
  enabled: boolean,
) =>
  apiRequest<PeriodontogramPilot>(
    `/api/platform/companies/${companyId}/periodontogram-pilot/dentists/${dentistId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    },
  );

export const getPeriodontogramPilotAccess = () =>
  apiRequest<PeriodontogramPilotAccess>("/api/periodontograms/access");
