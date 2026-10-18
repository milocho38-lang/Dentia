import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  {
    files: ["components/agenda/AgendaView.tsx"],
    rules: { "@next/next/no-location-assign-relative-destination": "off" },
  },
  {
    files: ["app/**/consentimiento/**/page.tsx"],
    rules: { "react-hooks/refs": "off" },
  },
  {
    files: ["components/patients/ClinicalRecordPage.tsx"],
    rules: { "react-hooks/preserve-manual-memoization": "off" },
  },
  {
    // These components passed the Next 15 core-web-vitals baseline. Next 16
    // newly enables this React compiler-era rule; keep exceptions explicit so
    // new files remain protected and remediation can be tracked independently.
    files: [
      "app/**/consentimiento/**/page.tsx",
      "components/agenda/AgendaView.tsx",
      "components/consents/ConsentAccessPanel.tsx",
      "components/consents/ConsentPaperPanel.tsx",
      "components/consents/ConsentTemplatesPage.tsx",
      "components/consents/PatientConsentsWorkspace.tsx",
      "components/followups/FollowupList.tsx",
      "components/odontogram/classic/RealDualOdontogramPreview.tsx",
      "components/odontogram/inspector/AddPlannedProcedureDialog.tsx",
      "components/organization/DentistSiteManagementPage.tsx",
      "components/organization/SiteList.tsx",
      "components/orthodontics/OrthodonticClinicalRecordPanel.tsx",
      "components/orthodontics/OrthodonticEvolutionPanel.tsx",
      "components/orthodontics/OrthodonticPatientWorkspace.tsx",
      "components/orthodontics/OrthodonticsAssignmentPage.tsx",
      "components/orthodontics/PlatformUserOrthodonticsAddon.tsx",
      "components/patients/ClinicalRecordPage.tsx",
      "components/patients/OdontogramPage.tsx",
      "components/patients/PatientDetail.tsx",
      "components/patients/PatientFilesWorkspace.tsx",
      "components/patients/PatientList.tsx",
      "components/periodontogram/PeriodontogramWorkspace.tsx",
      "components/platform/DemoRequestDetailPage.tsx",
      "components/platform/DemoRequestsPage.tsx",
      "components/platform/PlatformCompanyPages.tsx",
      "components/platform/UsageAdoptionDashboard.tsx",
      "components/reports/ReportsDashboard.tsx",
      "components/treatments/ProcedureCatalogPage.tsx",
      "components/treatments/TreatmentPages.tsx",
      "components/users/TemporaryPasswordDialog.tsx",
      "components/users/UserDetail.tsx",
      "components/users/UserList.tsx",
    ],
    rules: { "react-hooks/set-state-in-effect": "off" },
  },
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);
