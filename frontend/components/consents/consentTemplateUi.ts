export interface ConsentTemplateFilters {
  search: string;
  country: string;
  documentKind: string;
  status: string;
  siteId?: string;
  procedureId?: string;
  specialty?: string;
}

export interface ConsentTemplateCreateForm {
  code: string;
  name: string;
  description: string;
  document_kind: string;
  country_code: "CO" | "CL";
  language_code: "es-CO" | "es-CL";
  title: string;
  customize_title: boolean;
  content: string;
  scope_type: "GENERAL" | "SPECIFIC";
  site_ids: string[];
  procedure_ids: string[];
  specialties: { code: string; name: string }[];
}

export function createEmptyConsentTemplateForm(): ConsentTemplateCreateForm {
  return {
    code: "",
    name: "",
    description: "",
    document_kind: "PROCEDURE_CONSENT",
    country_code: "CO",
    language_code: "es-CO",
    title: "",
    customize_title: false,
    content: "",
    scope_type: "GENERAL",
    site_ids: [],
    procedure_ids: [],
    specialties: [],
  };
}

export function updateConsentTemplateName(current: ConsentTemplateCreateForm, name: string): ConsentTemplateCreateForm {
  return { ...current, name, title: current.customize_title ? current.title : name };
}

export function toggleCustomConsentTitle(current: ConsentTemplateCreateForm, customize: boolean): ConsentTemplateCreateForm {
  return { ...current, customize_title: customize, title: customize ? current.title : current.name };
}

export function unregisteredVariablesError(variables: string[]): string {
  const detail = variables.length ? `: ${variables.join(", ")}` : ".";
  return `No se puede publicar. Corrige las siguientes variables no registradas${detail}`;
}

export function buildConsentTemplateQuery(filters: ConsentTemplateFilters): string {
  const params = new URLSearchParams();
  if (filters.search.trim()) params.set("q", filters.search.trim());
  if (filters.country) params.set("country", filters.country);
  if (filters.documentKind) params.set("document_kind", filters.documentKind);
  if (filters.status) params.set("status", filters.status);
  if (filters.siteId) params.set("site_id", filters.siteId);
  if (filters.procedureId) params.set("procedure_id", filters.procedureId);
  if (filters.specialty?.trim()) params.set("specialty", filters.specialty.trim());
  return params.size ? `?${params.toString()}` : "";
}

export function insertConsentVariable(content: string, variableCode: string, start: number, end: number) {
  const token = `{{ ${variableCode} }}`;
  return {
    content: `${content.slice(0, start)}${token}${content.slice(end)}`,
    caret: start + token.length,
  };
}

export function consentVersionActions(status: string, permissions: Set<string>) {
  return {
    edit: status === "DRAFT" && permissions.has("consent.template.edit_draft"),
    publish: status === "DRAFT" && permissions.has("consent.template.publish"),
    voidDraft: status === "DRAFT" && permissions.has("consent.template.void_draft"),
    retire: status === "PUBLISHED" && permissions.has("consent.template.retire"),
    createFrom: status !== "VOIDED" && permissions.has("consent.template.create"),
  };
}
