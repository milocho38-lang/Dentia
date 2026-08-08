"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { listSites } from "@/services/organizationService";
import { approveConsentLibraryEquivalence, cloneConsentLibraryVersion, getConsentLibrarySourceReview, installConsentLibraryVersion, listConsentLibrary } from "@/services/consentLibraryService";
import { listProcedureCatalog } from "@/services/treatmentService";
import {
  createConsentTemplate,
  createDraftFromConsentVersion,
  getConsentDocumentKinds,
  getConsentTemplate,
  getConsentVariables,
  listConsentTemplates,
  listConsentVersions,
  previewConsentVersion,
  publishConsentVersion,
  retireConsentVersion,
  updateConsentVersion,
  validateConsentVersion,
  voidConsentDraft,
} from "@/services/consentTemplateService";
import type { Site } from "@/types/organization";
import type { ProcedureCatalogItem } from "@/types/treatment";
import type {
  ConsentCatalogItem,
  ConsentPreview,
  ConsentTemplate,
  ConsentVersion,
  ConsentVersionInput,
} from "@/types/consentTemplate";
import type { ConsentLibraryDocument, ConsentLibraryEquivalenceApprovalInput, ConsentLibrarySourceReview, ConsentLibraryVersion } from "@/types/consentLibrary";
import {
  buildConsentTemplateQuery,
  createEmptyConsentTemplateForm,
  toggleCustomConsentTitle,
  unregisteredVariablesError,
  updateConsentTemplateName,
} from "@/components/consents/consentTemplateUi";
import { ConsentVisualEditor } from "@/components/consents/ConsentVisualEditor";
import { ConsentRestrictedMarkdown } from "@/components/consents/ConsentRestrictedMarkdown";

const statusLabel: Record<string, string> = {
  DRAFT: "Borrador",
  PUBLISHED: "Publicada",
  SUPERSEDED: "Reemplazada",
  RETIRED: "Retirada",
  VOIDED: "Anulada",
};

const emptyDraft: ConsentVersionInput = {
  title: "",
  content: "",
  change_summary: null,
  scope_type: "GENERAL",
  priority: 0,
  site_ids: [],
  procedure_ids: [],
  specialties: [],
};

const approvalChecklistLabels: { key: keyof Omit<ConsentLibraryEquivalenceApprovalInput, "reviewer_name" | "reviewed_date" | "review_reference" | "reason">; label: string }[] = [
  { key: "clinical_text_faithful", label: "Texto clínico fiel" },
  { key: "risks_preserved", label: "Riesgos preservados" },
  { key: "warnings_preserved", label: "Advertencias preservadas" },
  { key: "values_preserved", label: "Valores, porcentajes y plazos preservados" },
  { key: "variables_correct", label: "Variables institucionales correctas" },
  { key: "titles_limits_correct", label: "Títulos y límites correctos" },
  { key: "signer_correct", label: "Firmante correcto" },
  { key: "classification_correct", label: "Clasificación documental correcta" },
  { key: "country_approved", label: "Variante país revisada" },
  { key: "odontological_review", label: "Revisión odontológica registrada" },
  { key: "legal_equivalence_review", label: "Revisión jurídica de equivalencia registrada" },
];

function createEmptyApprovalForm(): ConsentLibraryEquivalenceApprovalInput {
  return {
    reviewer_name: "",
    reviewed_date: new Date().toISOString().slice(0, 10),
    review_reference: "",
    reason: "",
    clinical_text_faithful: false,
    risks_preserved: false,
    warnings_preserved: false,
    values_preserved: false,
    variables_correct: false,
    titles_limits_correct: false,
    signer_correct: false,
    classification_correct: false,
    country_approved: false,
    odontological_review: false,
    legal_equivalence_review: false,
  };
}

function draftFrom(version: ConsentVersion): ConsentVersionInput {
  return {
    title: version.title,
    content: version.content,
    change_summary: version.change_summary,
    scope_type: version.scope_type,
    priority: version.priority,
    site_ids: version.site_ids,
    procedure_ids: version.procedure_ids,
    specialties: version.specialties,
  };
}

function libraryCompatibilityLabel(version: ConsentLibraryVersion): string {
  if (version.electronic_readiness_status === "BLOCKED") return "Pendiente de adaptación para flujo electrónico";
  if ((version.signer_compatibility === "PATIENT_SELF" || version.signer_compatibility === "ADULT_SELF") && version.normalization_status !== "BLOCKED") return "Apto para adulto en nombre propio";
  if (version.signer_compatibility === "PATIENT_OR_RESPONSIBLE_ADULT" || version.signer_compatibility === "ADULT_OR_REPRESENTATIVE") return "Paciente o adulto responsable";
  if (version.signer_compatibility === "RESPONSIBLE_ADULT_REQUIRED" || version.signer_compatibility === "REPRESENTATIVE_REQUIRED") return "Adulto responsable requerido";
  if (version.signer_compatibility === "NO_PATIENT_SIGNATURE" || version.signer_compatibility === "NO_SIGNATURE") return "No requiere firma";
  if (version.signer_compatibility === "SPECIAL_WORKFLOW" || version.signer_compatibility === "FUTURE_WORKFLOW") return "Flujo especial";
  if (version.normalization_status === "BLOCKED") return "Bloqueada para uso con pacientes";
  return "Requiere revisión";
}

function libraryBlockingMessage(version: ConsentLibraryVersion): string {
  if (version.electronic_readiness_status === "BLOCKED") return "Pendiente de adaptación para flujo electrónico.";
  if (version.signer_compatibility === "PATIENT_OR_RESPONSIBLE_ADULT" || version.signer_compatibility === "ADULT_OR_REPRESENTATIVE") return "El documento puede usar paciente adulto o adulto responsable según el caso. Pendiente revisión de equivalencia.";
  if (version.signer_compatibility === "NO_PATIENT_SIGNATURE" || version.signer_compatibility === "NO_SIGNATURE") return "Documento de indicaciones. No requiere firma de consentimiento.";
  if (version.signer_compatibility === "SPECIAL_WORKFLOW" || version.signer_compatibility === "FUTURE_WORKFLOW") return "Requiere un flujo documental especial, aún no implementado para consentimientos comunes.";
  if (version.signer_compatibility === "RESPONSIBLE_ADULT_REQUIRED" || version.signer_compatibility === "REPRESENTATIVE_REQUIRED") return "Este documento requiere adulto responsable; la instalación oficial queda pendiente de equivalencia.";
  return version.signer_blocking_reason || version.normalization_alerts[0] || "Requiere revisión humana antes de usarse.";
}

function libraryCurrentVersion(item: ConsentLibraryDocument, countryCode: "CO" | "CL"): ConsentLibraryVersion | undefined {
  const versions = item.versions.filter((version) => version.country_code === countryCode);
  return versions.find((version) => version.is_current) ?? [...versions].sort((a, b) => b.version_number - a.version_number)[0];
}

function libraryVersionHistory(item: ConsentLibraryDocument, countryCode: "CO" | "CL"): ConsentLibraryVersion[] {
  const current = libraryCurrentVersion(item, countryCode);
  return item.versions
    .filter((version) => version.country_code === countryCode && version.id !== current?.id)
    .sort((a, b) => b.version_number - a.version_number);
}

function isLibraryVersion(value: ConsentLibraryVersion | undefined): value is ConsentLibraryVersion {
  return Boolean(value);
}

function CheckList({ items, selected, onChange }: { items: { id: string; name: string }[]; selected: string[]; onChange: (next: string[]) => void }) {
  return (
    <div className="max-h-40 space-y-1 overflow-y-auto rounded-xl border border-slate-200 p-2">
      {items.length === 0 ? <p className="p-2 text-xs text-slate-400">Sin opciones disponibles.</p> : items.map((item) => (
        <label key={item.id} className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-slate-50">
          <input type="checkbox" checked={selected.includes(item.id)} onChange={(event) => onChange(event.target.checked ? [...selected, item.id] : selected.filter((id) => id !== item.id))} />
          {item.name}
        </label>
      ))}
    </div>
  );
}

export function ConsentTemplatesPage() {
  const { hasPermission, user } = useAuth();
  const isPlatformAdmin = user?.roles.includes("PLATFORM_ADMIN") ?? false;
  const canCreate = hasPermission("consent.template.create");
  const canReadLibrary = hasPermission("consent.library.read");
  const canInstallLibrary = hasPermission("consent.library.install");
  const canCloneLibrary = hasPermission("consent.library.clone");
  const canManageLibrary = isPlatformAdmin && hasPermission("consent.library.manage");
  const canEdit = hasPermission("consent.template.edit_draft");
  const canPublish = hasPermission("consent.template.publish");
  const canRetire = hasPermission("consent.template.retire");
  const canVoid = hasPermission("consent.template.void_draft");
  const [templates, setTemplates] = useState<ConsentTemplate[]>([]);
  const [libraryItems, setLibraryItems] = useState<ConsentLibraryDocument[]>([]);
  const [activeTab, setActiveTab] = useState<"clinic" | "library">("clinic");
  const [selected, setSelected] = useState<ConsentTemplate | null>(null);
  const [activeDraft, setActiveDraft] = useState<ConsentVersion | null>(null);
  const [versions, setVersions] = useState<ConsentVersion[]>([]);
  const [draft, setDraft] = useState<ConsentVersionInput>(emptyDraft);
  const [kinds, setKinds] = useState<ConsentCatalogItem[]>([]);
  const [variables, setVariables] = useState<ConsentCatalogItem[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [procedures, setProcedures] = useState<ProcedureCatalogItem[]>([]);
  const [search, setSearch] = useState("");
  const [country, setCountry] = useState("");
  const [kind, setKind] = useState("");
  const [status, setStatus] = useState("");
  const [filterSite, setFilterSite] = useState("");
  const [filterProcedure, setFilterProcedure] = useState("");
  const [filterSpecialty, setFilterSpecialty] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [preview, setPreview] = useState<ConsentPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [libraryError, setLibraryError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState(createEmptyConsentTemplateForm);
  const [equivalenceTarget, setEquivalenceTarget] = useState<{ document: ConsentLibraryDocument; version: ConsentLibraryVersion } | null>(null);
  const [sourceReview, setSourceReview] = useState<ConsentLibrarySourceReview | null>(null);
  const [approvalForm, setApprovalForm] = useState<ConsentLibraryEquivalenceApprovalInput>(createEmptyApprovalForm);

  function resetCreateModalState() {
    setCreateForm(createEmptyConsentTemplateForm());
    setError(null);
  }

  function openCreateModal() {
    resetCreateModalState();
    setSaving(false);
    setSuccess(null);
    setShowCreate(true);
  }

  function closeCreateModal() {
    setShowCreate(false);
    resetCreateModalState();
    setSaving(false);
    setSuccess(null);
  }

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setLibraryError(null);
    try {
      const query = buildConsentTemplateQuery({ search, country, documentKind: kind, status, siteId: filterSite, procedureId: filterProcedure, specialty: filterSpecialty });
      const [list, kindItems, variableItems, siteItems, procedureItems] = await Promise.all([
        listConsentTemplates(query),
        getConsentDocumentKinds(),
        getConsentVariables(),
        listSites(),
        listProcedureCatalog(),
      ]);
      const libraryQuery = new URLSearchParams();
      if (search) libraryQuery.set("q", search);
      if (country) libraryQuery.set("country", country);
      setTemplates(list.items);
      if (canReadLibrary) {
        try {
          const library = await listConsentLibrary(libraryQuery.toString() ? `?${libraryQuery.toString()}` : "");
          setLibraryItems(library.items);
        } catch (caught) {
          setLibraryItems([]);
          setLibraryError(caught instanceof Error ? caught.message : "No fue posible cargar la Biblioteca Dentia.");
        }
      } else {
        setLibraryItems([]);
      }
      if (!canReadLibrary && activeTab === "library") setActiveTab("clinic");
      setKinds(kindItems);
      setVariables(variableItems);
      setSites(siteItems.items);
      setProcedures(procedureItems.items);
      if (selected) {
        const refreshed = list.items.find((item) => item.id === selected.id);
        if (refreshed) setSelected(refreshed);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible cargar las plantillas.");
    } finally {
      setLoading(false);
    }
  }, [activeTab, canReadLibrary, country, filterProcedure, filterSite, filterSpecialty, kind, search, selected, status]);

  useEffect(() => {
    void load();
    // La selección se refresca explícitamente después de cada mutación.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [country, filterProcedure, filterSite, filterSpecialty, kind, search, status]);

  const allVersions = useMemo(() => versions, [versions]);

  async function refreshSelected(templateId: string, preferredDraftId?: string) {
    const [item, history] = await Promise.all([getConsentTemplate(templateId), listConsentVersions(templateId)]);
    setSelected(item);
    setTemplates((current) => current.map((entry) => entry.id === item.id ? item : entry));
    setVersions(history);
    const nextDraft = item.draft_versions.find((entry) => entry.id === preferredDraftId) ?? item.draft_versions[0] ?? null;
    setActiveDraft(nextDraft);
    setDraft(nextDraft ? draftFrom(nextDraft) : emptyDraft);
  }

  async function openTemplate(item: ConsentTemplate) {
    setPreview(null);
    setError(null);
    await refreshSelected(item.id);
  }

  async function createTemplate(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createConsentTemplate({
        code: createForm.code,
        name: createForm.name,
        description: createForm.description || null,
        document_kind: createForm.document_kind,
        country_code: createForm.country_code,
        language_code: createForm.language_code,
        initial_version: { ...emptyDraft, title: createForm.title, content: createForm.content, scope_type: createForm.scope_type, site_ids: createForm.site_ids, procedure_ids: createForm.procedure_ids, specialties: createForm.specialties },
      });
      setTemplates((current) => [created, ...current]);
      setShowCreate(false);
      resetCreateModalState();
      setSuccess("Plantilla y versión 1 en borrador creadas.");
      await refreshSelected(created.id, created.draft_versions[0]?.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible crear la plantilla.");
    } finally {
      setSaving(false);
    }
  }

  async function persistDraft() {
    if (!selected || !activeDraft) throw new Error("Selecciona un borrador.");
    const saved = await updateConsentVersion(selected.id, activeDraft, draft);
    await refreshSelected(selected.id, saved.id);
    return saved;
  }

  async function saveDraft() {
    setSaving(true);
    setError(null);
    try {
      await persistDraft();
      setSuccess("Borrador guardado.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible guardar el borrador.");
    } finally {
      setSaving(false);
    }
  }

  async function showPreview() {
    if (!selected || !activeDraft) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await persistDraft();
      const response = await previewConsentVersion(selected.id, saved.id);
      setPreview(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible generar la vista previa.");
    } finally {
      setSaving(false);
    }
  }

  async function validateDraft() {
    if (!selected || !activeDraft) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await persistDraft();
      const result = await validateConsentVersion(selected.id, saved.id);
      if (result.valid) {
        setSuccess(`Validación correcta. ${result.used_variables.length} variable(s) registrada(s).`);
      } else {
        setSuccess(null);
        setError(result.invalid_variables.length
          ? unregisteredVariablesError(result.invalid_variables)
          : `No se puede publicar. Corrige los errores del contenido: ${result.syntax_errors.join(" ")}`);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible validar.");
    } finally {
      setSaving(false);
    }
  }

  async function publishDraft() {
    if (!selected || !activeDraft || !window.confirm("La versión quedará inmutable y reemplazará prospectivamente a la publicada actual. ¿Publicar?")) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await persistDraft();
      await publishConsentVersion(selected.id, saved.id);
      setSuccess("Versión publicada de forma inmutable.");
      await refreshSelected(selected.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible publicar.");
    } finally {
      setSaving(false);
    }
  }

  async function libraryAction(versionId: string, action: "install" | "clone") {
    setSaving(true);
    setError(null);
    try {
      const result = action === "install" ? await installConsentLibraryVersion(versionId) : await cloneConsentLibraryVersion(versionId);
      setSuccess(result.message);
      setActiveTab("clinic");
      await load();
      await refreshSelected(result.template_id, action === "clone" ? result.version_id : undefined);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible usar la biblioteca Dentia.");
    } finally {
      setSaving(false);
    }
  }

  async function openEquivalenceReview(document: ConsentLibraryDocument, version: ConsentLibraryVersion) {
    setError(null);
    setSuccess(null);
    setApprovalForm(createEmptyApprovalForm());
    setEquivalenceTarget({ document, version });
    setSourceReview(null);
    try {
      setSourceReview(await getConsentLibrarySourceReview(version.id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible cargar el texto fuente de revisión.");
    }
  }

  async function approveEquivalence(event: FormEvent) {
    event.preventDefault();
    if (!equivalenceTarget) return;
    setSaving(true);
    setError(null);
    try {
      await approveConsentLibraryEquivalence(equivalenceTarget.version.id, approvalForm);
      setSuccess(`Equivalencia aprobada para ${equivalenceTarget.document.code} ${equivalenceTarget.version.country_code}.`);
      setEquivalenceTarget(null);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible aprobar la equivalencia.");
    } finally {
      setSaving(false);
    }
  }

  async function versionAction(version: ConsentVersion, action: "draft" | "retire" | "void") {
    if (!selected) return;
    const promptText = action === "draft" ? "Resumen del cambio para la nueva versión:" : action === "retire" ? "Motivo obligatorio del retiro:" : "Motivo obligatorio de la anulación:";
    const reason = window.prompt(promptText)?.trim();
    if (!reason) return;
    setSaving(true);
    setError(null);
    try {
      if (action === "draft") {
        const created = await createDraftFromConsentVersion(selected.id, version.id, reason);
        await refreshSelected(selected.id, created.id);
        setSuccess(`Versión ${created.version_number} creada en borrador.`);
      } else if (action === "retire") {
        await retireConsentVersion(selected.id, version.id, reason);
        await refreshSelected(selected.id);
        setSuccess("Versión retirada; el historial permanece disponible.");
      } else {
        await voidConsentDraft(selected.id, version.id, reason);
        await refreshSelected(selected.id);
        setSuccess("Borrador anulado; no fue eliminado.");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible completar la acción.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-bold uppercase tracking-wide text-green-700">Configuración clínica</p>
          <h1 className="mt-2 text-3xl font-black text-slate-950">Plantillas de consentimientos</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-500">Administra contenido versionado e inmutable. Este módulo todavía no crea documentos para pacientes ni implementa firma electrónica.</p>
        </div>
        {canCreate && <button type="button" onClick={openCreateModal} className="rounded-xl bg-dentia-primary px-4 py-3 text-sm font-black text-white disabled:opacity-60" disabled={saving}>Nueva plantilla</button>}
      </header>

      <Alert tone="info">El contenido debe ser revisado clínica y jurídicamente antes de publicarse. Dentia no incluye textos legales preaprobados.</Alert>
      <div className="flex gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm"><button type="button" onClick={() => setActiveTab("clinic")} className={`rounded-xl px-4 py-2 text-sm font-black ${activeTab === "clinic" ? "bg-dentia-primary text-white" : "text-slate-600 hover:bg-slate-50"}`}>Mis plantillas</button>{canReadLibrary && <button type="button" onClick={() => setActiveTab("library")} className={`rounded-xl px-4 py-2 text-sm font-black ${activeTab === "library" ? "bg-dentia-primary text-white" : "text-slate-600 hover:bg-slate-50"}`}>Biblioteca Dentia</button>}</div>
      {error && <Alert tone="error">{error}</Alert>}
      {success && <Alert tone="info">{success}</Alert>}

      <section className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-2 xl:grid-cols-4">
        <input aria-label="Buscar plantillas" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por nombre o código" className="min-h-11 rounded-xl border border-slate-300 px-3 text-sm" />
        <select aria-label="Filtrar por país" value={country} onChange={(event) => setCountry(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm"><option value="">Todos los países</option><option value="CO">Colombia</option><option value="CL">Chile</option></select>
        <select aria-label="Filtrar por tipo" value={kind} onChange={(event) => setKind(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm"><option value="">Todos los tipos</option>{kinds.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select>
        <select aria-label="Filtrar por estado" value={status} onChange={(event) => setStatus(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm"><option value="">Todos los estados</option><option value="DRAFT">Con borrador</option><option value="PUBLISHED">Publicada</option><option value="ACTIVE">Activa</option><option value="INACTIVE">Inactiva</option></select>
        <select aria-label="Filtrar por sede" value={filterSite} onChange={(event) => setFilterSite(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm"><option value="">Todas las sedes</option>{sites.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
        <select aria-label="Filtrar por procedimiento" value={filterProcedure} onChange={(event) => setFilterProcedure(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm"><option value="">Todos los procedimientos</option>{procedures.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
        <input aria-label="Filtrar por especialidad" value={filterSpecialty} onChange={(event) => setFilterSpecialty(event.target.value.toUpperCase())} placeholder="Código de especialidad" className="min-h-11 rounded-xl border border-slate-300 px-3 text-sm" />
      </section>

      {loading ? <div className="flex min-h-48 items-center justify-center"><Spinner /></div> : activeTab === "library" ? (
        <section className="grid gap-4 lg:grid-cols-2">
          {libraryError && <div className="lg:col-span-2"><Alert tone="error">{libraryError}<button type="button" onClick={() => void load()} className="ml-3 rounded-lg border border-red-200 px-3 py-1 text-xs font-black text-red-700">Reintentar</button></Alert></div>}
          {!libraryError && libraryItems.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500 lg:col-span-2">La Biblioteca Dentia todavía no tiene documentos disponibles en esta base de datos.</div>}
          {libraryItems.map((item) => {
            const co = libraryCurrentVersion(item, "CO");
            const cl = libraryCurrentVersion(item, "CL");
            const installable = item.document_type === "INFORMED_CONSENT" && (item.signer_scope === "PATIENT_SELF" || item.signer_scope === "PATIENT_OR_RESPONSIBLE_ADULT" || item.signer_scope === "RESPONSIBLE_ADULT_REQUIRED" || item.signer_scope === "ADULT_SELF" || item.signer_scope === "ADULT_OR_REPRESENTATIVE" || item.signer_scope === "REPRESENTATIVE_REQUIRED") && item.supports_electronic_signature;
            return (
              <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-black uppercase tracking-wide text-green-700">{item.category}</p>
                    <h2 className="mt-1 text-lg font-black text-slate-950">{item.title}</h2>
                    <p className="mt-1 text-xs font-bold text-slate-400">{item.code} · {item.specialty_name ?? "General"} · {item.source_reference}</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-black text-slate-600">{item.document_type}</span>
                </div>
                <p className="mt-3 text-sm text-slate-600">{item.summary}</p>
                <div className="mt-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-800">{installable ? "Documento apto para instalación oficial si la variante está publicada." : "Documento disponible para revisión. Las versiones pendientes pueden copiarse como borrador editable; la instalación oficial requiere aprobación."}</div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {[co, cl].filter(isLibraryVersion).map((version) => (
                    <div key={version.id} className="rounded-xl border border-slate-200 p-3">
                      <p className="text-sm font-black text-slate-900">{version.country_code} · v{version.version_number}</p>
                      {version.is_current && <p className="mt-1 text-xs font-black text-green-700">Versión actual: v{version.version_number}</p>}
                      <p className="mt-1 text-xs text-slate-500">{version.publication_status}</p>
                      <p className="mt-1 text-xs font-bold text-amber-700">Equivalencia: {version.legal_review_status}</p>
                      <p className="mt-1 text-xs font-bold text-slate-600">Normalización: {version.normalization_schema_version ?? version.normalization_status}</p>
                      <p className="mt-1 text-xs font-bold text-slate-600">Aptitud electrónica: {version.electronic_readiness_status === "BLOCKED" ? "Pendiente de adaptación" : version.electronic_readiness_status === "READY" ? "Lista técnicamente" : "Por verificar"}</p>
                      <p className="mt-1 text-xs font-bold text-slate-600">Firmante: {libraryCompatibilityLabel(version)}</p>
                      {version.normalization_schema_version && <p className="mt-1 text-xs text-slate-500">Estado normalización: {version.normalization_status}</p>}
                      {version.is_legacy && <p className="mt-1 rounded-lg bg-red-50 p-2 text-xs font-bold text-red-700">{version.historical_message ?? "Versión histórica no apta para nuevos consentimientos."}</p>}
                      <div className={`mt-2 rounded-lg p-2 text-xs ${version.normalization_status === "BLOCKED" || version.electronic_readiness_status === "BLOCKED" ? "bg-red-50 text-red-800" : "bg-green-50 text-green-800"}`}>{libraryBlockingMessage(version)}{version.signer_blocking_line ? ` Línea ${version.signer_blocking_line}.` : ""}</div>
                      {version.adult_variant_required && <p className="mt-2 text-xs font-bold text-amber-700">Tiene propuesta de variante adulta en el reporte NORM4; no se aprueba automáticamente.</p>}
                      {version.legal_review_status === "APPROVED" && version.clinical_review_status === "APPROVED" && <p className="mt-1 text-xs font-bold text-green-700">Aprobada por {version.equivalence_reviewer_name ?? "revisor registrado"} · {version.review_reference ?? "sin referencia"}</p>}
                      {version.legal_review_status !== "APPROVED" && <p className="mt-1 text-xs text-slate-500">Pendiente de revisión humana antes de instalarse como oficial.</p>}
                      <p className="mt-1 break-all font-mono text-[10px] text-slate-400">{version.normalized_content_sha256}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {canInstallLibrary && installable && version.normalization_status !== "BLOCKED" && version.electronic_readiness_status !== "BLOCKED" && version.publication_status === "PUBLISHED" && version.legal_review_status === "APPROVED" && version.clinical_review_status === "APPROVED" && <button type="button" disabled={saving || item.installed_exact} onClick={() => void libraryAction(version.id, "install")} className="rounded-lg bg-dentia-primary px-3 py-1.5 text-xs font-black text-white disabled:opacity-50">Agregar oficial</button>}
                        {canCloneLibrary && version.normalization_status !== "BLOCKED" && <button type="button" disabled={saving} onClick={() => void libraryAction(version.id, "clone")} className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-black text-slate-700">Crear copia editable</button>}
                        {(version.normalization_status === "BLOCKED" || version.electronic_readiness_status === "BLOCKED") && <span className="rounded-lg bg-red-50 px-3 py-1.5 text-xs font-black text-red-700">{libraryCompatibilityLabel(version)}</span>}
                        {canManageLibrary && <button type="button" disabled={saving} onClick={() => void openEquivalenceReview(item, version)} className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-black text-amber-800">Revisar equivalencia</button>}
                      </div>
                      {libraryVersionHistory(item, version.country_code).length > 0 && (
                        <details className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-2 text-xs text-slate-600">
                          <summary className="cursor-pointer font-black text-slate-700">Ver historial</summary>
                          <div className="mt-2 space-y-2">
                            {libraryVersionHistory(item, version.country_code).map((historyVersion) => (
                              <div key={historyVersion.id} className="rounded-md bg-white p-2">
                                <p className="font-black">{historyVersion.country_code} · v{historyVersion.version_number}</p>
                                <p>{historyVersion.historical_message ?? "Versión anterior preservada para auditoría."}</p>
                                <p>Normalización: {historyVersion.normalization_schema_version ?? historyVersion.normalization_status}</p>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </article>
            );
          })}
        </section>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(320px,0.8fr)_minmax(0,1.7fr)]">
          <section className="space-y-3">
            {templates.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">No hay plantillas para estos filtros.</div>}
            {templates.map((item) => (
              <button key={item.id} type="button" onClick={() => void openTemplate(item)} className={`w-full rounded-2xl border bg-white p-4 text-left shadow-sm transition hover:border-green-300 ${selected?.id === item.id ? "border-green-500 ring-2 ring-green-100" : "border-slate-200"}`}>
                <div className="flex items-start justify-between gap-3"><div><p className="font-black text-slate-950">{item.name}</p><p className="mt-1 text-xs font-bold text-slate-400">{item.code} · {item.country_code} · {item.language_code}</p></div><span className={`rounded-full px-2 py-1 text-[11px] font-black ${item.published_version ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"}`}>{item.published_version ? `Publicada v${item.published_version.version_number}` : "Sin publicar"}</span></div>
                <p className="mt-3 text-xs text-slate-500">{item.draft_versions.length} borrador(es) · {item.versions_count} versión(es)</p>
              </button>
            ))}
          </section>

          <section>
            {!selected ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-sm text-slate-500">Selecciona una plantilla para editar su borrador o consultar el historial.</div> : (
              <div className="space-y-5">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-black text-slate-950">{selected.name}</h2><p className="mt-1 text-sm text-slate-500">{kinds.find((item) => item.code === selected.document_kind)?.label ?? selected.document_kind} · {selected.country_code} · {selected.language_code}</p></div>{selected.published_version && canCreate && <button type="button" onClick={() => void versionAction(selected.published_version!, "draft")} disabled={saving} className="rounded-xl border border-green-200 px-3 py-2 text-sm font-black text-green-700">Nueva versión desde publicada</button>}</div>
                </div>

                {selected.draft_versions.length > 0 && (
                  <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="text-lg font-black text-slate-950">Editor de borrador</h3><select value={activeDraft?.id ?? ""} onChange={(event) => { const version = selected.draft_versions.find((item) => item.id === event.target.value) ?? null; setActiveDraft(version); setDraft(version ? draftFrom(version) : emptyDraft); setPreview(null); }} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm">{selected.draft_versions.map((version) => <option key={version.id} value={version.id}>Versión {version.version_number}</option>)}</select></div>
                    {activeDraft && <div className="mt-5 space-y-5">
                      <div className="grid gap-4 lg:grid-cols-2"><label className="text-sm font-bold text-slate-700">Título<input value={draft.title} disabled={!canEdit} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label><label className="text-sm font-bold text-slate-700">Resumen del cambio<input value={draft.change_summary ?? ""} disabled={!canEdit} onChange={(event) => setDraft((current) => ({ ...current, change_summary: event.target.value || null }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label></div>
                      <ConsentVisualEditor content={draft.content} variables={variables} editable={canEdit} onChange={(content) => setDraft((current) => ({ ...current, content }))} />
                      <div className="grid gap-4 lg:grid-cols-3"><label className="text-sm font-bold text-slate-700">Ámbito<select value={draft.scope_type} disabled={!canEdit} onChange={(event) => setDraft((current) => ({ ...current, scope_type: event.target.value as "GENERAL" | "SPECIFIC", site_ids: [], procedure_ids: [], specialties: [] }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"><option value="GENERAL">General</option><option value="SPECIFIC">Específico</option></select></label><label className="text-sm font-bold text-slate-700">Prioridad futura<input type="number" min="0" max="1000" value={draft.priority} disabled={!canEdit} onChange={(event) => setDraft((current) => ({ ...current, priority: Number(event.target.value) }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label></div>
                      {draft.scope_type === "SPECIFIC" && <div className="grid gap-4 lg:grid-cols-3"><div><p className="mb-1.5 text-sm font-bold text-slate-700">Sedes</p><CheckList items={sites.map((item) => ({ id: item.id, name: item.name }))} selected={draft.site_ids} onChange={(site_ids) => setDraft((current) => ({ ...current, site_ids }))} /></div><div><p className="mb-1.5 text-sm font-bold text-slate-700">Procedimientos</p><CheckList items={procedures.map((item) => ({ id: item.id, name: item.name }))} selected={draft.procedure_ids} onChange={(procedure_ids) => setDraft((current) => ({ ...current, procedure_ids }))} /></div><label className="text-sm font-bold text-slate-700">Especialidades (código:nombre)<textarea value={draft.specialties.map((item) => `${item.code}:${item.name}`).join("\n")} onChange={(event) => setDraft((current) => ({ ...current, specialties: event.target.value.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => { const [code, ...name] = line.split(":"); return { code: code.toUpperCase(), name: name.join(":").trim() || code }; }) }))} rows={6} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" placeholder="ENDODONCIA:Endodoncia" /></label></div>}
                      <div className="flex flex-wrap gap-2">{canEdit && <button type="button" onClick={() => void saveDraft()} disabled={saving} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white">Guardar</button>}<button type="button" onClick={() => void validateDraft()} disabled={saving} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-black text-slate-700">Validar</button><button type="button" onClick={() => void showPreview()} disabled={saving} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-black text-slate-700">Vista previa</button>{canPublish && <button type="button" onClick={() => void publishDraft()} disabled={saving} className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-black text-white">Publicar versión</button>}{canVoid && <button type="button" onClick={() => void versionAction(activeDraft, "void")} disabled={saving} className="rounded-xl border border-red-200 px-4 py-2.5 text-sm font-black text-red-700">Anular borrador</button>}</div>
                    </div>}
                  </div>
                )}

                {preview && <div role="dialog" aria-modal="true" aria-label="Vista previa de demostración" className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4"><div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-2xl"><div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white p-4"><div><p className="text-xs font-black uppercase tracking-wide text-amber-700">{preview.warning}</p><h3 className="mt-1 text-xl font-black text-slate-950">{preview.title}</h3></div><button type="button" onClick={() => setPreview(null)} aria-label="Cerrar vista previa" className="h-10 w-10 rounded-xl border border-slate-200 font-black">×</button></div><div className="p-6"><ConsentRestrictedMarkdown content={preview.rendered_content} /><div className="mt-6 rounded-xl bg-slate-50 p-4 text-xs text-slate-500">Variables usadas: {preview.used_variables.join(", ") || "ninguna"}. Esta previsualización usa exclusivamente datos ficticios.</div></div></div></div>}

                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h3 className="text-lg font-black text-slate-950">Historial de versiones</h3><div className="mt-4 space-y-3">{allVersions.length === 0 ? <p className="text-sm text-slate-500">Sin versiones visibles.</p> : [...allVersions].sort((a, b) => b.version_number - a.version_number).map((version) => <div key={version.id} className="rounded-xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-black text-slate-900">Versión {version.version_number} · {statusLabel[version.status]}</p><p className="mt-1 text-xs text-slate-500">{new Date(version.updated_at).toLocaleString()} · {version.change_summary || "Sin resumen de cambio"}</p>{version.content_sha256 && <p className="mt-1 break-all font-mono text-[10px] text-slate-400">SHA-256 {version.content_sha256}</p>}{version.legacy_quarantined && <p className="mt-2 rounded-lg bg-red-50 p-2 text-xs font-bold text-red-700">{version.legacy_quarantine_message ?? "Versión anterior no apta para nuevos consentimientos"}</p>}{version.retire_reason && <p className="mt-2 text-xs text-red-700">Retiro: {version.retire_reason}</p>}{version.void_reason && <p className="mt-2 text-xs text-red-700">Anulación: {version.void_reason}</p>}</div><div className="flex flex-wrap gap-2">{canCreate && version.status !== "VOIDED" && <button type="button" onClick={() => void versionAction(version, "draft")} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-black">Crear borrador desde versión</button>}{canRetire && version.status === "PUBLISHED" && <button type="button" onClick={() => void versionAction(version, "retire")} className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-black text-red-700">Retirar</button>}</div></div></div>)}</div></div>
              </div>
            )}
          </section>
        </div>
      )}

      {equivalenceTarget && <div role="dialog" aria-modal="true" aria-label="Revisar equivalencia" className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4"><form onSubmit={approveEquivalence} className="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-center justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-wide text-amber-700">Biblioteca Dentia · Plataforma</p><h2 className="mt-1 text-xl font-black text-slate-950">Revisar equivalencia</h2><p className="mt-1 text-sm text-slate-500">{equivalenceTarget.document.code} · {equivalenceTarget.version.country_code} / {equivalenceTarget.version.language_code}</p></div><button type="button" onClick={() => { setEquivalenceTarget(null); setSourceReview(null); }} aria-label="Cerrar revisión de equivalencia" className="h-10 w-10 rounded-xl border border-slate-200 font-black">×</button></div><Alert tone="info">Esta acción aprueba únicamente esta variante. No aprueba masivamente la biblioteca ni reemplaza la revisión humana registrada en el checklist.</Alert>{sourceReview && <div className="mt-5 grid gap-4 lg:grid-cols-2"><div><h3 className="mb-2 text-sm font-black text-slate-900">Texto fuente de procedencia</h3><pre className="max-h-80 overflow-auto rounded-xl bg-slate-950 p-4 text-xs leading-5 text-slate-50">{sourceReview.source_text}</pre></div><div><h3 className="mb-2 text-sm font-black text-slate-900">Contenido normalizado para paciente</h3><pre className="max-h-80 overflow-auto rounded-xl bg-slate-50 p-4 text-xs leading-5 text-slate-700">{sourceReview.normalized_content}</pre></div></div>}<div className="mt-5 grid gap-4 md:grid-cols-2"><label className="text-sm font-bold text-slate-700">Nombre del revisor<input required value={approvalForm.reviewer_name} onChange={(event) => setApprovalForm((current) => ({ ...current, reviewer_name: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label><label className="text-sm font-bold text-slate-700">Fecha de revisión<input required type="date" value={approvalForm.reviewed_date} onChange={(event) => setApprovalForm((current) => ({ ...current, reviewed_date: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label><label className="text-sm font-bold text-slate-700 md:col-span-2">Referencia documental<input required value={approvalForm.review_reference} onChange={(event) => setApprovalForm((current) => ({ ...current, review_reference: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" placeholder="Acta, radicado o documento de revisión" /></label><label className="text-sm font-bold text-slate-700 md:col-span-2">Motivo<textarea required rows={3} value={approvalForm.reason} onChange={(event) => setApprovalForm((current) => ({ ...current, reason: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" placeholder="Describe por qué esta variante puede aprobarse." /></label></div><div className="mt-5 grid gap-2 md:grid-cols-2">{approvalChecklistLabels.map((item) => <label key={item.key} className="flex items-center gap-2 rounded-xl border border-slate-200 p-3 text-sm font-bold text-slate-700"><input type="checkbox" checked={Boolean(approvalForm[item.key])} onChange={(event) => setApprovalForm((current) => ({ ...current, [item.key]: event.target.checked }))} />{item.label}</label>)}</div><div className="mt-5 flex justify-end gap-2"><button type="button" onClick={() => { setEquivalenceTarget(null); setSourceReview(null); }} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-black">Cancelar</button><button disabled={saving} className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-black text-white disabled:opacity-60">Aprobar equivalencia</button></div></form></div>}

      {showCreate && <div role="dialog" aria-modal="true" aria-label="Crear plantilla" className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4"><form onSubmit={createTemplate} className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-center justify-between"><div><h2 className="text-xl font-black text-slate-950">Nueva plantilla</h2><p className="mt-1 text-sm text-slate-500">Se creará la identidad y su versión 1 en borrador.</p></div><button type="button" onClick={closeCreateModal} aria-label="Cerrar" className="h-10 w-10 rounded-xl border border-slate-200 font-black">×</button></div><div className="mt-5 grid gap-4 md:grid-cols-2"><label className="text-sm font-bold">Nombre del consentimiento<input required value={createForm.name} onChange={(event) => setCreateForm((current) => updateConsentTemplateName(current, event.target.value))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /><span className="mt-1 block text-xs font-normal text-slate-500">Nombre con el que encontrará esta plantilla en Dentia.</span></label><label className="text-sm font-bold">Código<input required value={createForm.code} onChange={(event) => setCreateForm((current) => ({ ...current, code: event.target.value.toUpperCase() }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" placeholder="CONSENT-DEMO" /></label><label className="text-sm font-bold">Tipo<select value={createForm.document_kind} onChange={(event) => setCreateForm((current) => ({ ...current, document_kind: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal">{kinds.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label><label className="text-sm font-bold">País<select value={createForm.country_code} onChange={(event) => { const countryCode = event.target.value as "CO" | "CL"; setCreateForm((current) => ({ ...current, country_code: countryCode, language_code: `es-${countryCode}` as "es-CO" | "es-CL" })); }} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"><option value="CO">Colombia — es-CO</option><option value="CL">Chile — es-CL</option></select></label><label className="text-sm font-bold">Ámbito<select value={createForm.scope_type} onChange={(event) => setCreateForm((current) => ({ ...current, scope_type: event.target.value as "GENERAL" | "SPECIFIC", site_ids: [], procedure_ids: [], specialties: [] }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal"><option value="GENERAL">General</option><option value="SPECIFIC">Específico</option></select></label><label className="text-sm font-bold md:col-span-2">Descripción<input value={createForm.description} onChange={(event) => setCreateForm((current) => ({ ...current, description: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /></label><div className="md:col-span-2"><label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={createForm.customize_title} onChange={(event) => setCreateForm((current) => toggleCustomConsentTitle(current, event.target.checked))} />Personalizar título visible</label>{createForm.customize_title && <label className="mt-3 block text-sm font-bold">Título visible<input required value={createForm.title} onChange={(event) => setCreateForm((current) => ({ ...current, title: event.target.value }))} className="mt-1.5 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal" /><span className="mt-1 block text-xs font-normal text-slate-500">Encabezado que aparecerá en el documento para el paciente.</span></label>}</div><div className="md:col-span-2"><p className="mb-1.5 text-sm font-bold">Contenido inicial</p><ConsentVisualEditor content={createForm.content} variables={variables} editable onChange={(content) => setCreateForm((current) => ({ ...current, content }))} /></div></div>{createForm.scope_type === "SPECIFIC" && <div className="mt-4 grid gap-4 md:grid-cols-3"><div><p className="mb-1.5 text-sm font-bold">Sedes</p><CheckList items={sites.map((item) => ({ id: item.id, name: item.name }))} selected={createForm.site_ids} onChange={(site_ids) => setCreateForm((current) => ({ ...current, site_ids }))} /></div><div><p className="mb-1.5 text-sm font-bold">Procedimientos</p><CheckList items={procedures.map((item) => ({ id: item.id, name: item.name }))} selected={createForm.procedure_ids} onChange={(procedure_ids) => setCreateForm((current) => ({ ...current, procedure_ids }))} /></div><label className="text-sm font-bold">Especialidades<textarea rows={6} value={createForm.specialties.map((item) => `${item.code}:${item.name}`).join("\n")} onChange={(event) => setCreateForm((current) => ({ ...current, specialties: event.target.value.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => { const [code, ...name] = line.split(":"); return { code: code.toUpperCase(), name: name.join(":").trim() || code }; }) }))} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" /></label></div>}<div className="mt-5 flex justify-end gap-2"><button type="button" onClick={closeCreateModal} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-black">Cancelar</button><button disabled={saving} className="rounded-xl bg-dentia-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-60">Crear borrador</button></div></form></div>}
    </div>
  );
}
