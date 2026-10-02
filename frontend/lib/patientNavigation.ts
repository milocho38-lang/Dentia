export const PATIENT_WORKSPACE_TABS = [
  "summary",
  "clinical",
  "odontogram",
  "periodontogram",
  "orthodontics",
  "treatments",
  "agenda",
  "finance",
  "documents",
  "consents",
  "files",
] as const;

export type PatientWorkspaceTab = (typeof PATIENT_WORKSPACE_TABS)[number];

export type PatientNavigationGroupKey =
  | "summary"
  | "clinical"
  | "treatments"
  | "management"
  | "documents";

type DynamicModule = "periodontogram" | "orthodontics";

interface PatientNavigationOptionDefinition {
  tab: PatientWorkspaceTab;
  label: string;
  permission?: string;
  dynamicModule?: DynamicModule;
}

interface PatientNavigationGroupDefinition {
  key: PatientNavigationGroupKey;
  label: string;
  direct?: PatientNavigationOptionDefinition;
  children?: readonly PatientNavigationOptionDefinition[];
}

export interface PatientNavigationOption {
  tab: PatientWorkspaceTab;
  label: string;
}

export interface PatientNavigationGroup {
  key: PatientNavigationGroupKey;
  label: string;
  directTab?: PatientWorkspaceTab;
  children: PatientNavigationOption[];
}

export interface PatientNavigationContext {
  clinicalRecordLabel?: string | null;
  orthodonticsVisible: boolean;
  periodontogramVisible: boolean;
  hasPermission: (permission: string) => boolean;
}

export const PATIENT_NAVIGATION_DEFINITION: readonly PatientNavigationGroupDefinition[] = [
  {
    key: "summary",
    label: "Resumen",
    direct: { tab: "summary", label: "Resumen" },
  },
  {
    key: "clinical",
    label: "Clínica",
    children: [
      {
        tab: "clinical",
        label: "Historia clínica",
        permission: "clinical_records.view_sensitive",
      },
      {
        tab: "odontogram",
        label: "Odontograma",
        permission: "odontogram.view",
      },
      {
        tab: "periodontogram",
        label: "Periodontograma",
        permission: "periodontogram.view",
        dynamicModule: "periodontogram",
      },
      {
        tab: "orthodontics",
        label: "Ortodoncia",
        dynamicModule: "orthodontics",
      },
    ],
  },
  {
    key: "treatments",
    label: "Tratamientos",
    direct: {
      tab: "treatments",
      label: "Tratamientos",
      permission: "treatments.view",
    },
  },
  {
    key: "management",
    label: "Gestión",
    children: [
      {
        tab: "agenda",
        label: "Agenda",
        permission: "appointments.view",
      },
      {
        tab: "finance",
        label: "Finanzas",
        permission: "payments.view",
      },
    ],
  },
  {
    key: "documents",
    label: "Documentos",
    children: [
      { tab: "documents", label: "Documentos" },
      {
        tab: "consents",
        label: "Consentimientos",
        permission: "consent.instance.read",
      },
      { tab: "files", label: "Archivos" },
    ],
  },
] as const;

const TAB_TO_GROUP = new Map<PatientWorkspaceTab, PatientNavigationGroupKey>(
  PATIENT_NAVIGATION_DEFINITION.flatMap((group) => {
    const options = group.direct ? [group.direct] : [...(group.children ?? [])];
    return options.map((option) => [option.tab, group.key] as const);
  }),
);

export function isPatientWorkspaceTab(value: string | null): value is PatientWorkspaceTab {
  return value !== null && (PATIENT_WORKSPACE_TABS as readonly string[]).includes(value);
}

export function patientNavigationGroupForTab(
  tab: PatientWorkspaceTab,
): PatientNavigationGroupKey {
  return TAB_TO_GROUP.get(tab) ?? "summary";
}

function isOptionVisible(
  option: PatientNavigationOptionDefinition,
  context: PatientNavigationContext,
) {
  if (option.permission && !context.hasPermission(option.permission)) {
    return false;
  }
  if (option.dynamicModule === "periodontogram" && !context.periodontogramVisible) {
    return false;
  }
  if (option.dynamicModule === "orthodontics" && !context.orthodonticsVisible) {
    return false;
  }
  return true;
}

function optionLabel(
  option: PatientNavigationOptionDefinition,
  context: PatientNavigationContext,
) {
  if (option.tab === "clinical") {
    return context.clinicalRecordLabel?.trim() || option.label;
  }
  return option.label;
}

export function buildPatientNavigation(
  context: PatientNavigationContext,
): PatientNavigationGroup[] {
  return PATIENT_NAVIGATION_DEFINITION.flatMap((group) => {
    if (group.direct) {
      if (!isOptionVisible(group.direct, context)) {
        return [];
      }
      return [{
        key: group.key,
        label: group.label,
        directTab: group.direct.tab,
        children: [],
      }];
    }

    const children = (group.children ?? [])
      .filter((option) => isOptionVisible(option, context))
      .map((option) => ({
        tab: option.tab,
        label: optionLabel(option, context),
      }));
    if (children.length === 0) {
      return [];
    }
    return [{
      key: group.key,
      label: group.label,
      children,
    }];
  });
}

export function targetTabForPatientGroup(
  group: PatientNavigationGroup,
  activeTab?: PatientWorkspaceTab,
) {
  if (
    activeTab
    && (group.directTab === activeTab || group.children.some((item) => item.tab === activeTab))
  ) {
    return activeTab;
  }
  return group.directTab ?? group.children[0]?.tab ?? null;
}
