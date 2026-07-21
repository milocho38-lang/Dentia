"use client";

import Link from "next/link";
import {
  FormEvent,
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/services/apiClient";
import {
  createAllergy,
  createClinicalRecord,
  createClinicalEvolution,
  createClinicalEvolutionAddendum,
  createMedication,
  getAllergies,
  getClinicalRecord,
  getClinicalTimeline,
  getMedicalHistory,
  getMedications,
  listClinicalEvolutions,
  signClinicalEvolution,
  updateAllergy,
  updateClinicalEvolutionDraft,
  updateClinicalRecordDraft,
  updateMedicalHistory,
  updateMedication,
} from "@/services/clinicalRecordService";
import { listDentists } from "@/services/organizationService";
import { getPatient } from "@/services/patientService";
import { listProcedures, listTreatments } from "@/services/treatmentService";
import type {
  AuthSite,
} from "@/types/auth";
import type {
  Allergy,
  ClinicalEvolution,
  ClinicalEvolutionInput,
  ClinicalTimelineItem,
  ClinicalRecord,
  ClinicalRecordInput,
  MedicalHistoryItemInput,
  Medication,
} from "@/types/clinicalRecord";
import type { DentistSiteManagement } from "@/types/organization";
import type { Patient, Responsible } from "@/types/patient";
import type { Procedure, TreatmentListItem } from "@/types/treatment";

const DEFAULT_TERMINOLOGY = {
  record: "Historia Clínica",
  open_record: "Abrir historia clínica",
  summary: "Resumen clínico",
};

const MEDICAL_TYPES = [
  "hipertensión",
  "enfermedad cardiovascular",
  "diabetes",
  "trastorno de coagulación",
  "enfermedad respiratoria",
  "enfermedad renal",
  "enfermedad hepática",
  "enfermedad neurológica",
  "inmunosupresión",
  "cáncer",
  "hospitalización",
  "cirugía",
  "transfusión",
  "prótesis o dispositivo",
  "embarazo",
  "lactancia",
  "otro",
];

const INFORMANT_RELATION_OPTIONS = [
  { value: "MOTHER", label: "Madre", relationship: "Madre" },
  { value: "FATHER", label: "Padre", relationship: "Padre" },
  { value: "GUARDIAN", label: "Acudiente", relationship: "Acudiente" },
  { value: "PARTNER", label: "Esposo(a) / Pareja", relationship: "Esposo(a) / Pareja" },
  { value: "CHILD", label: "Hijo(a)", relationship: "Hijo(a)" },
  { value: "CAREGIVER", label: "Cuidador(a)", relationship: "Cuidador(a)" },
  {
    value: "LEGAL_REPRESENTATIVE",
    label: "Representante legal",
    relationship: "Representante legal",
  },
  { value: "OTHER", label: "Otro", relationship: "Otro" },
];

function emptyRecord(activeSiteId?: string | null): ClinicalRecordInput {
  return {
    opening_site_id: activeSiteId ?? null,
    opening_dentist_id: null,
    chief_complaint: "",
    current_situation: "",
    situation_start: "",
    situation_evolution: "",
    symptoms: "",
    previous_treatments: "",
    informant_type: "",
    informant_responsible_id: null,
    informant_name: "",
    informant_relationship: "",
    informant_document: "",
    observations: "",
    habits: {},
    dental_history: {},
    allergies_state: "NO_CONFIRMADA",
    medical_history_state: "NO_CONFIRMADO",
  };
}

function toDatetimeLocalValue(value: string | null | undefined) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60_000);
  return local.toISOString().slice(0, 16);
}

function fromDatetimeLocalValue(value: string) {
  return value ? new Date(value).toISOString() : null;
}

function emptyEvolution(
  activeSiteId?: string | null,
  dentistId?: string | null,
): ClinicalEvolutionInput {
  return {
    site_id: activeSiteId ?? null,
    dentist_id: dentistId ?? null,
    attended_at: new Date().toISOString(),
    reason: "",
    subjective: "",
    objective: "",
    assessment: "",
    performed_procedure: "",
    anesthesia: "",
    materials: "",
    administered_medications: "",
    findings: "",
    complications: "",
    indications: "",
    recommendations: "",
    next_control_at: null,
    next_control_reason: "",
    observations: "",
    treatment_id: null,
    procedures: [],
  };
}

function formatDate(value: string | null, withTime = false) {
  if (!value) return "No registrado";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    ...(withTime ? { timeStyle: "short" as const } : {}),
  }).format(new Date(value));
}

function errorMessage(error: unknown, fallback: string) {
  return error instanceof ApiError
    ? error.detail ?? error.message
    : fallback;
}

function patientDocument(patient: Patient) {
  return patient.document_type === "Sin documento" ? "" : patient.document ?? "";
}

function patientInformantPatch(patient: Patient): Partial<ClinicalRecordInput> {
  return {
    informant_type: "PATIENT",
    informant_responsible_id: null,
    informant_name: patient.full_name,
    informant_relationship: null,
    informant_document: patientDocument(patient),
  };
}

function typeFromRelationship(relationship: string | null | undefined) {
  const normalized = (relationship ?? "").toLocaleLowerCase("es-CO");
  if (normalized.includes("madre")) return "MOTHER";
  if (normalized.includes("padre")) return "FATHER";
  if (normalized.includes("pareja") || normalized.includes("espos")) return "PARTNER";
  if (normalized.includes("hijo") || normalized.includes("hija")) return "CHILD";
  if (normalized.includes("cuidador") || normalized.includes("cuidadora")) return "CAREGIVER";
  if (normalized.includes("legal")) return "LEGAL_REPRESENTATIVE";
  if (normalized.includes("acudiente") || normalized.includes("tutor")) return "GUARDIAN";
  return "OTHER";
}

function responsibleInformantPatch(
  responsible: Responsible,
): Partial<ClinicalRecordInput> {
  return {
    informant_type: typeFromRelationship(responsible.relationship),
    informant_responsible_id: responsible.id,
    informant_name: responsible.name,
    informant_relationship: responsible.relationship,
    informant_document: responsible.document ?? "",
  };
}

function matchingResponsible(
  patient: Patient,
  record: Pick<
    ClinicalRecordInput,
    "informant_name" | "informant_document" | "informant_relationship"
  >,
) {
  return patient.responsibles.find((responsible) => {
    if (!responsible.is_active) return false;
    const sameDocument =
      responsible.document &&
      record.informant_document &&
      responsible.document === record.informant_document;
    const sameName =
      responsible.name.trim().toLocaleLowerCase("es-CO") ===
      (record.informant_name ?? "").trim().toLocaleLowerCase("es-CO");
    const sameRelationship =
      responsible.relationship.trim().toLocaleLowerCase("es-CO") ===
      (record.informant_relationship ?? "").trim().toLocaleLowerCase("es-CO");
    return Boolean(sameDocument || (sameName && sameRelationship));
  });
}

function defaultInformantPatch(patient: Patient): Partial<ClinicalRecordInput> {
  if (!patient.is_minor) return patientInformantPatch(patient);
  const activeResponsibles = patient.responsibles.filter(
    (responsible) => responsible.is_active,
  );
  const primary = patient.responsibles.find(
    (responsible) => responsible.is_active && responsible.is_primary,
  );
  if (primary) return responsibleInformantPatch(primary);
  if (activeResponsibles.length > 0) return {};
  return {
    informant_type: "OTHER",
    informant_responsible_id: null,
    informant_relationship: "Otro",
  };
}

function normalizeInformantBeforeSubmit(
  patient: Patient,
  form: ClinicalRecordInput,
): { payload?: ClinicalRecordInput; error?: string } {
  if (!patient.is_minor && (!form.informant_type || form.informant_type === "PATIENT")) {
    return { payload: { ...form, ...patientInformantPatch(patient) } };
  }
  if (patient.is_minor && form.informant_type === "PATIENT") {
    return {
      error: "El paciente menor debe tener un responsable o informante adulto.",
    };
  }
  if (!form.informant_name?.trim()) {
    return { error: "Ingrese el nombre del informante." };
  }
  if (!form.informant_relationship?.trim()) {
    return { error: "Seleccione la relación con el paciente." };
  }
  return { payload: form };
}

export function ClinicalRecordPage({
  patientId,
  embedded = false,
}: {
  patientId: string;
  embedded?: boolean;
}) {
  const { user, hasPermission } = useAuth();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [record, setRecord] = useState<ClinicalRecord | null>(null);
  const [form, setForm] = useState<ClinicalRecordInput>(
    emptyRecord(user?.active_site_id),
  );
  const [terminology, setTerminology] = useState(DEFAULT_TERMINOLOGY);
  const [dentists, setDentists] = useState<DentistSiteManagement[]>([]);
  const [medicalItems, setMedicalItems] = useState<MedicalHistoryItemInput[]>(
    MEDICAL_TYPES.map((type) => ({
      type,
      present: "DESCONOCIDO",
      status: "activo",
    })),
  );
  const [allergies, setAllergies] = useState<Allergy[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [evolutions, setEvolutions] = useState<ClinicalEvolution[]>([]);
  const [timeline, setTimeline] = useState<ClinicalTimelineItem[]>([]);
  const [treatments, setTreatments] = useState<TreatmentListItem[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [selectedEvolutionId, setSelectedEvolutionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canEdit =
    hasPermission("clinical_records.update_draft") &&
    hasPermission("clinical_records.view_sensitive");
  const canCreate =
    hasPermission("clinical_records.create") &&
    hasPermission("clinical_records.view_sensitive");
  const canViewEvolutions =
    hasPermission("clinical_evolutions.view") &&
    hasPermission("clinical_records.view_sensitive");
  const canCreateEvolution =
    hasPermission("clinical_evolutions.create") &&
    hasPermission("clinical_records.view_sensitive");
  const canUpdateEvolution =
    hasPermission("clinical_evolutions.update_draft") &&
    hasPermission("clinical_records.view_sensitive");
  const canSignEvolution =
    hasPermission("clinical_evolutions.sign") &&
    hasPermission("clinical_records.view_sensitive");
  const canAddAddendum =
    hasPermission("clinical_evolutions.add_addendum") &&
    hasPermission("clinical_records.view_sensitive");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [patientData, envelope] = await Promise.all([
        getPatient(patientId),
        getClinicalRecord(patientId),
      ]);
      setPatient(patientData);
      setTerminology(envelope.terminology ?? DEFAULT_TERMINOLOGY);
      if (envelope.record) {
        const responsible = matchingResponsible(patientData, envelope.record);
        const isPatientInformant =
          !patientData.is_minor &&
          ((envelope.record.informant_type ?? "").toUpperCase() === "PATIENT" ||
            (!envelope.record.informant_relationship &&
              envelope.record.informant_name === patientData.full_name));
        setRecord(envelope.record);
        setForm({
          opening_site_id: envelope.record.opening_site_id,
          opening_dentist_id: envelope.record.opening_dentist_id,
          chief_complaint: envelope.record.chief_complaint ?? "",
          current_situation: envelope.record.current_situation ?? "",
          situation_start: envelope.record.situation_start ?? "",
          situation_evolution: envelope.record.situation_evolution ?? "",
          symptoms: envelope.record.symptoms ?? "",
          previous_treatments: envelope.record.previous_treatments ?? "",
          informant_type: isPatientInformant
            ? "PATIENT"
            : envelope.record.informant_type ?? "",
          informant_responsible_id: responsible?.id ?? null,
          informant_name: envelope.record.informant_name ?? "",
          informant_relationship: envelope.record.informant_relationship ?? "",
          informant_document: envelope.record.informant_document ?? "",
          observations: envelope.record.observations ?? "",
          habits: envelope.record.habits ?? {},
          dental_history: envelope.record.dental_history ?? {},
          allergies_state: envelope.record.allergies_state,
          medical_history_state: envelope.record.medical_history_state,
        });
        const [
          loadedMedical,
          loadedAllergies,
          loadedMeds,
          loadedEvolutions,
          loadedTimeline,
          loadedTreatments,
        ] = await Promise.all([
          getMedicalHistory(patientId),
          getAllergies(patientId),
          getMedications(patientId),
          canViewEvolutions
            ? listClinicalEvolutions(patientId)
            : Promise.resolve({ items: [] }),
          hasPermission("clinical_timeline.view")
            ? getClinicalTimeline(patientId)
            : Promise.resolve({ items: [], terminology: envelope.terminology ?? DEFAULT_TERMINOLOGY }),
          hasPermission("treatments.view")
            ? listTreatments(`?patient_id=${patientId}`)
            : Promise.resolve({ items: [], total: 0 }),
        ]);
        const byType = new Map(
          loadedMedical.items.map((item) => [item.type, item]),
        );
        setMedicalItems(
          MEDICAL_TYPES.map((type) => {
            const item = byType.get(type);
            return item
              ? {
                  type: item.type,
                  present: item.present,
                  detail: item.detail,
                  severity: item.severity,
                  status: item.status,
                  source: item.source,
                  version: item.version,
                }
              : { type, present: "DESCONOCIDO", status: "activo" };
          }),
        );
        setAllergies(loadedAllergies.items);
        setMedications(loadedMeds.items);
        setEvolutions(loadedEvolutions.items);
        setTimeline(loadedTimeline.items);
        setTreatments(loadedTreatments.items);
      } else {
        setRecord(null);
        setEvolutions([]);
        setTimeline([]);
        setTreatments([]);
        setProcedures([]);
        setForm({
          ...emptyRecord(user?.active_site_id),
          ...defaultInformantPatch(patientData),
        });
      }
      try {
        const dentistResponse = await listDentists();
        const activeDentists = dentistResponse.items.filter(
          (item) => item.status === "Activo",
        );
        setDentists(activeDentists);
        if (!envelope.record) {
          const ownDentist = activeDentists.find(
            (item) => item.user_id === user?.id,
          );
          setForm((current) => ({
            ...current,
            ...(!patientData.is_minor && !current.informant_type
              ? patientInformantPatch(patientData)
              : {}),
            opening_site_id:
              current.opening_site_id ?? user?.active_site_id ?? null,
            opening_dentist_id:
              current.opening_dentist_id ?? ownDentist?.id ?? null,
          }));
        }
      } catch {
        setDentists([]);
      }
    } catch (loadError) {
      setError(errorMessage(loadError, "No fue posible cargar la historia clínica."));
    } finally {
      setLoading(false);
    }
  }, [patientId, user?.active_site_id, user?.id, canViewEvolutions, hasPermission]);

  useEffect(() => {
    load();
  }, [load]);

  const criticalAllergies = allergies.filter(
    (item) => item.critical_alert && item.status !== "descartada",
  );
  const activeMedications = medications.filter((item) => item.status === "activo");
  const relevantMedical = medicalItems.filter((item) => item.present === "SI");
  const ownDentist = dentists.find((item) => item.user_id === user?.id);
  const selectedEvolution =
    evolutions.find((item) => item.id === selectedEvolutionId) ?? null;

  function updateField<K extends keyof ClinicalRecordInput>(
    key: K,
    value: ClinicalRecordInput[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateHabit(key: keyof ClinicalRecordInput["habits"], value: string) {
    setForm((current) => ({
      ...current,
      habits: { ...current.habits, [key]: value },
    }));
  }

  function updateDentalHistory(
    key: keyof ClinicalRecordInput["dental_history"],
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      dental_history: { ...current.dental_history, [key]: value },
    }));
  }

  async function saveRecord(event: FormEvent) {
    event.preventDefault();
    if (!patient) return;
    const normalized = normalizeInformantBeforeSubmit(patient, form);
    if (normalized.error || !normalized.payload) {
      setError(normalized.error ?? "Seleccione quién suministra la información.");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const saved = record
        ? await updateClinicalRecordDraft(patientId, {
            ...normalized.payload,
            version: record.version,
          })
        : await createClinicalRecord(patientId, normalized.payload);
      setRecord(saved);
      setTerminology(saved.terminology);
      setMessage(`${saved.terminology.record} guardada correctamente.`);
    } catch (saveError) {
      if (saveError instanceof ApiError && saveError.status === 409) {
        await load();
        setMessage(`${terminology.record} cargada. Ya había sido abierta.`);
      } else {
        setError(errorMessage(saveError, "No fue posible guardar la historia clínica."));
      }
    } finally {
      setSaving(false);
    }
  }

  async function openClinicalRecord() {
    if (!patient) return;
    if (!canCreate) {
      setError(`No tienes permiso para abrir la ${terminology.record.toLowerCase()}.`);
      return;
    }
    const normalized = normalizeInformantBeforeSubmit(patient, form);
    if (normalized.error || !normalized.payload) {
      setError(normalized.error ?? "Seleccione quién suministra la información.");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const saved = await createClinicalRecord(patientId, normalized.payload);
      setRecord(saved);
      setTerminology(saved.terminology);
      setForm({
        opening_site_id: saved.opening_site_id,
        opening_dentist_id: saved.opening_dentist_id,
        chief_complaint: saved.chief_complaint ?? "",
        current_situation: saved.current_situation ?? "",
        situation_start: saved.situation_start ?? "",
        situation_evolution: saved.situation_evolution ?? "",
        symptoms: saved.symptoms ?? "",
        previous_treatments: saved.previous_treatments ?? "",
        informant_type: saved.informant_type ?? "",
        informant_responsible_id: null,
        informant_name: saved.informant_name ?? "",
        informant_relationship: saved.informant_relationship ?? "",
        informant_document: saved.informant_document ?? "",
        observations: saved.observations ?? "",
        habits: saved.habits ?? {},
        dental_history: saved.dental_history ?? {},
        allergies_state: saved.allergies_state,
        medical_history_state: saved.medical_history_state,
      });
      setAllergies([]);
      setMedications([]);
      setMessage(`${saved.terminology.record} abierta correctamente.`);
    } catch (openError) {
      if (openError instanceof ApiError && openError.status === 409) {
        await load();
        setMessage(`${terminology.record} cargada. Ya había sido abierta.`);
      } else if (openError instanceof ApiError && openError.status === 403) {
        setError(`No tienes permiso para abrir la ${terminology.record.toLowerCase()}.`);
      } else {
        setError(
          errorMessage(
            openError,
            `No fue posible abrir la ${terminology.record.toLowerCase()}. Inténtalo nuevamente.`,
          ),
        );
      }
    } finally {
      setSaving(false);
    }
  }

  async function saveMedicalHistory() {
    if (!record) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await updateMedicalHistory(patientId, {
        record_version: record.version,
        medical_history_state: form.medical_history_state,
        items: medicalItems,
      });
      setMedicalItems(response.items.map((item) => ({ ...item })));
      await load();
      setMessage("Antecedentes médicos guardados.");
    } catch (saveError) {
      setError(errorMessage(saveError, "No fue posible guardar antecedentes."));
    } finally {
      setSaving(false);
    }
  }

  async function addAllergy(data: {
    type: string;
    substance: string;
    severity: string;
    critical_alert: boolean;
  }) {
    setSaving(true);
    setError(null);
    try {
      await createAllergy(patientId, {
        ...data,
        reaction: null,
        status: "confirmada",
        observations: null,
      });
      await load();
      setMessage("Alergia registrada.");
    } catch (saveError) {
      setError(errorMessage(saveError, "No fue posible registrar la alergia."));
    } finally {
      setSaving(false);
    }
  }

  async function toggleAllergyStatus(item: Allergy) {
    setSaving(true);
    setError(null);
    try {
      await updateAllergy(patientId, item.id, {
        type: item.type,
        substance: item.substance,
        reaction: item.reaction,
        severity: item.severity,
        critical_alert: item.critical_alert,
        observations: item.observations,
        status: item.status === "descartada" ? "confirmada" : "descartada",
        version: item.version,
      });
      await load();
    } catch (saveError) {
      setError(errorMessage(saveError, "No fue posible actualizar la alergia."));
    } finally {
      setSaving(false);
    }
  }

  async function addMedication(data: { name: string; dose: string; frequency: string }) {
    setSaving(true);
    setError(null);
    try {
      await createMedication(patientId, {
        name: data.name,
        dose: data.dose || null,
        frequency: data.frequency || null,
        route: null,
        since: null,
        reason: null,
        prescriber: null,
        status: "activo",
        observations: null,
      });
      await load();
      setMessage("Medicamento registrado.");
    } catch (saveError) {
      setError(errorMessage(saveError, "No fue posible registrar el medicamento."));
    } finally {
      setSaving(false);
    }
  }

  async function suspendMedication(item: Medication) {
    setSaving(true);
    setError(null);
    try {
      await updateMedication(patientId, item.id, {
        name: item.name,
        dose: item.dose,
        frequency: item.frequency,
        route: item.route,
        since: item.since,
        reason: item.reason,
        prescriber: item.prescriber,
        observations: item.observations,
        status: item.status === "activo" ? "suspendido" : "activo",
        version: item.version,
      });
      await load();
    } catch (saveError) {
      setError(errorMessage(saveError, "No fue posible actualizar el medicamento."));
    } finally {
      setSaving(false);
    }
  }

  const refreshClinicalActivity = useCallback(async () => {
    if (!record) return;
    const [loadedEvolutions, loadedTimeline] = await Promise.all([
      canViewEvolutions
        ? listClinicalEvolutions(patientId)
        : Promise.resolve({ items: [] }),
      hasPermission("clinical_timeline.view")
        ? getClinicalTimeline(patientId)
        : Promise.resolve({ items: [], terminology }),
    ]);
    setEvolutions(loadedEvolutions.items);
    setTimeline(loadedTimeline.items);
  }, [canViewEvolutions, hasPermission, patientId, record, terminology]);

  const loadTreatmentProcedures = useCallback(async (treatmentId: string | null) => {
    if (!treatmentId) {
      setProcedures([]);
      return;
    }
    try {
      setProcedures(await listProcedures(treatmentId));
    } catch {
      setProcedures([]);
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 text-slate-500">
        <Spinner className="h-7 w-7 text-dentia-primary" />
        Cargando historia clínica…
      </div>
    );
  }

  if (!patient) {
    return <Alert tone="error">{error ?? "Paciente no encontrado."}</Alert>;
  }

  return (
    <div className={embedded ? "space-y-5" : "mx-auto max-w-6xl space-y-6"}>
      {!embedded && (
        <>
          <Link
            href={`/pacientes/${patientId}`}
            className="text-sm font-bold text-green-700 hover:underline"
          >
            ← Volver al paciente
          </Link>

          <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-green-700">
                  {terminology.record}
                </p>
                <h1 className="mt-2 text-3xl font-black text-slate-950">
                  {patient.full_name}
                </h1>
                <p className="mt-2 text-sm text-slate-500">
                  Registro longitudinal clínico. Las evoluciones firmadas llegarán en
                  C015C; esta fase cubre apertura, antecedentes, alergias y resumen.
                </p>
              </div>
              <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm">
                <p className="font-bold text-slate-900">
                  {record ? "Abierta" : "Sin historia abierta"}
                </p>
                <p className="text-slate-500">
                  {record
                    ? `Versión ${record.version} · ${formatDate(record.updated_at, true)}`
                    : terminology.open_record}
                </p>
              </div>
            </div>
          </header>
        </>
      )}

      {error && <Alert tone="error">{error}</Alert>}
      {message && <Alert tone="info">{message}</Alert>}

      {!canCreate && !record && (
        <Alert tone="info">
          No tienes permiso para abrir el detalle clínico completo de este
          paciente.
        </Alert>
      )}

      {!record && (
        <section className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-green-700">
            {terminology.record}
          </p>
          <h2 className="mt-3 text-2xl font-black text-slate-950">
            Este paciente aún no tiene {terminology.record.toLowerCase()} abierta.
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-600">
            Abre el expediente clínico longitudinal para registrar motivo de
            consulta, antecedentes, alergias, medicamentos y alertas clínicas.
            No se crearán evoluciones ni firmas en esta fase.
          </p>
          <div className="mx-auto mt-6 max-w-3xl text-left">
            <InformantSection
              patient={patient}
              form={form}
              disabled={!canCreate || saving}
              onPatch={(patch) =>
                setForm((current) => ({ ...current, ...patch }))
              }
            />
          </div>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            {canCreate ? (
              <button
                type="button"
                onClick={openClinicalRecord}
                disabled={saving}
                className="min-h-12 rounded-xl bg-green-700 px-6 font-bold text-white disabled:opacity-60"
              >
                {saving ? "Abriendo…" : terminology.open_record}
              </button>
            ) : (
              <span className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold text-slate-500">
                No tienes permiso para abrir la {terminology.record.toLowerCase()}.
              </span>
            )}
            {!embedded && (
              <Link
                href={`/pacientes/${patientId}`}
                className="min-h-12 rounded-xl border border-slate-300 px-6 py-3 font-bold text-slate-700"
              >
                Volver al paciente
              </Link>
            )}
          </div>
        </section>
      )}

      {record && (
        <>
          <ClinicalAlerts
            criticalAllergies={criticalAllergies}
            activeMedications={activeMedications}
            relevantMedical={relevantMedical}
          />

      <form onSubmit={saveRecord} className="space-y-6">
        <Section title="Apertura">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-slate-700">
                Sede de apertura
              </span>
              <select
                value={form.opening_site_id ?? ""}
                onChange={(event) =>
                  updateField("opening_site_id", event.target.value || null)
                }
                disabled={!canEdit && Boolean(record)}
                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
              >
                <option value="">Sin sede específica</option>
                {user?.sites.map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-slate-700">
                Odontólogo de apertura
              </span>
              <select
                value={form.opening_dentist_id ?? ""}
                onChange={(event) =>
                  updateField("opening_dentist_id", event.target.value || null)
                }
                disabled={!canEdit && Boolean(record)}
                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
              >
                <option value="">No asignado</option>
                {dentists.map((dentist) => (
                  <option key={dentist.id} value={dentist.id}>
                    {dentist.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {patient.is_minor && (
            <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              Paciente menor de edad. Selecciona un responsable registrado o
              informa qué adulto suministra los datos clínicos. Se guarda un
              snapshot mínimo para trazabilidad.
            </div>
          )}
          <div className="mt-4">
            <InformantSection
              patient={patient}
              form={form}
              disabled={!canEdit && Boolean(record)}
              onPatch={(patch) =>
                setForm((current) => ({ ...current, ...patch }))
              }
            />
          </div>
        </Section>

        <Section title="Motivo y situación actual">
          <div className="grid gap-4 lg:grid-cols-2">
            <TextArea
              label="Motivo de consulta"
              value={form.chief_complaint ?? ""}
              onChange={(value) => updateField("chief_complaint", value)}
            />
            <TextArea
              label="Situación actual"
              value={form.current_situation ?? ""}
              onChange={(value) => updateField("current_situation", value)}
            />
            <TextInput
              label="Inicio de la situación"
              value={form.situation_start ?? ""}
              onChange={(value) => updateField("situation_start", value)}
            />
            <TextInput
              label="Síntomas"
              value={form.symptoms ?? ""}
              onChange={(value) => updateField("symptoms", value)}
            />
            <TextArea
              label="Evolución"
              value={form.situation_evolution ?? ""}
              onChange={(value) => updateField("situation_evolution", value)}
            />
            <TextArea
              label="Tratamientos previos"
              value={form.previous_treatments ?? ""}
              onChange={(value) => updateField("previous_treatments", value)}
            />
          </div>
        </Section>

        <Section title="Hábitos">
          <div className="grid gap-4 md:grid-cols-3">
            <TextInput label="Tabaco" value={form.habits.tobacco ?? ""} onChange={(value) => updateHabit("tobacco", value)} />
            <TextInput label="Alcohol" value={form.habits.alcohol ?? ""} onChange={(value) => updateHabit("alcohol", value)} />
            <TextInput label="Bruxismo" value={form.habits.bruxism ?? ""} onChange={(value) => updateHabit("bruxism", value)} />
            <TextInput label="Higiene oral" value={form.habits.oral_hygiene ?? ""} onChange={(value) => updateHabit("oral_hygiene", value)} />
            <TextInput label="Frecuencia cepillado" value={form.habits.brushing_frequency ?? ""} onChange={(value) => updateHabit("brushing_frequency", value)} />
            <TextInput label="Seda dental" value={form.habits.dental_floss ?? ""} onChange={(value) => updateHabit("dental_floss", value)} />
          </div>
        </Section>

        <Section title="Antecedentes odontológicos">
          <div className="grid gap-4 md:grid-cols-2">
            <TextInput label="Última consulta" value={form.dental_history.last_visit ?? ""} onChange={(value) => updateDentalHistory("last_visit", value)} />
            <TextInput label="Tratamientos previos" value={form.dental_history.previous_treatments ?? ""} onChange={(value) => updateDentalHistory("previous_treatments", value)} />
            <TextInput label="Ortodoncia" value={form.dental_history.orthodontics ?? ""} onChange={(value) => updateDentalHistory("orthodontics", value)} />
            <TextInput label="Implantes" value={form.dental_history.implants ?? ""} onChange={(value) => updateDentalHistory("implants", value)} />
            <TextInput label="Cirugías" value={form.dental_history.surgeries ?? ""} onChange={(value) => updateDentalHistory("surgeries", value)} />
            <TextInput label="Sensibilidad" value={form.dental_history.sensitivity ?? ""} onChange={(value) => updateDentalHistory("sensitivity", value)} />
            <TextArea label="Observaciones odontológicas" value={form.dental_history.observations ?? ""} onChange={(value) => updateDentalHistory("observations", value)} />
            <TextArea label="Observaciones generales" value={form.observations ?? ""} onChange={(value) => updateField("observations", value)} />
          </div>
        </Section>

        {(canCreate || (record && canEdit)) && (
          <div className="sticky bottom-4 z-10 flex justify-end rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-lg backdrop-blur">
            <button
              type="submit"
              disabled={saving}
              className="rounded-xl bg-green-700 px-6 py-3 font-bold text-white disabled:opacity-60"
            >
              {saving ? "Guardando…" : record ? "Guardar cambios" : terminology.open_record}
            </button>
          </div>
        )}
      </form>

          <ClinicalEvolutionsSection
            patientId={patientId}
            evolutions={evolutions}
            selectedEvolution={selectedEvolution}
            timeline={timeline}
            treatments={treatments}
            procedures={procedures}
            sites={user?.sites ?? []}
            dentists={dentists}
            ownDentistId={ownDentist?.id ?? null}
            activeSiteId={user?.active_site_id ?? null}
            canView={canViewEvolutions}
            canCreate={canCreateEvolution}
            canUpdate={canUpdateEvolution}
            canSign={canSignEvolution}
            canAddAddendum={canAddAddendum}
            saving={saving}
            terminologyRecord={terminology.record}
            onSelect={setSelectedEvolutionId}
            onProceduresLoad={loadTreatmentProcedures}
            onSavingChange={setSaving}
            onMessage={setMessage}
            onError={setError}
            onRefresh={refreshClinicalActivity}
          />

          <MedicalHistorySection
            items={medicalItems}
            state={form.medical_history_state}
            canEdit={canEdit}
            saving={saving}
            onStateChange={(value) => updateField("medical_history_state", value)}
            onItemsChange={setMedicalItems}
            onSave={saveMedicalHistory}
          />
          <AllergiesSection
            items={allergies}
            state={form.allergies_state}
            canEdit={canEdit}
            saving={saving}
            onStateChange={(value) => updateField("allergies_state", value)}
            onAdd={addAllergy}
            onToggle={toggleAllergyStatus}
          />
          <MedicationsSection
            items={medications}
            canEdit={canEdit}
            saving={saving}
            onAdd={addMedication}
            onToggle={suspendMedication}
          />
        </>
      )}
    </div>
  );
}

function ClinicalEvolutionsSection({
  patientId,
  evolutions,
  selectedEvolution,
  timeline,
  treatments,
  procedures,
  sites,
  dentists,
  ownDentistId,
  activeSiteId,
  canView,
  canCreate,
  canUpdate,
  canSign,
  canAddAddendum,
  saving,
  terminologyRecord,
  onSelect,
  onProceduresLoad,
  onSavingChange,
  onMessage,
  onError,
  onRefresh,
}: {
  patientId: string;
  evolutions: ClinicalEvolution[];
  selectedEvolution: ClinicalEvolution | null;
  timeline: ClinicalTimelineItem[];
  treatments: TreatmentListItem[];
  procedures: Procedure[];
  sites: AuthSite[];
  dentists: DentistSiteManagement[];
  ownDentistId: string | null;
  activeSiteId: string | null;
  canView: boolean;
  canCreate: boolean;
  canUpdate: boolean;
  canSign: boolean;
  canAddAddendum: boolean;
  saving: boolean;
  terminologyRecord: string;
  onSelect: (id: string | null) => void;
  onProceduresLoad: (treatmentId: string | null) => Promise<void>;
  onSavingChange: (saving: boolean) => void;
  onMessage: (message: string | null) => void;
  onError: (message: string | null) => void;
  onRefresh: () => Promise<void>;
}) {
  const [mode, setMode] = useState<"idle" | "new" | "edit">("idle");
  const [draft, setDraft] = useState<ClinicalEvolutionInput>(
    emptyEvolution(activeSiteId, ownDentistId),
  );
  const [addendumReason, setAddendumReason] = useState("");
  const [addendumContent, setAddendumContent] = useState("");

  useEffect(() => {
    if (mode === "edit" && selectedEvolution) {
      setDraft({
        appointment_id: selectedEvolution.appointment_id,
        treatment_id: selectedEvolution.treatment_id,
        site_id: selectedEvolution.site_id,
        dentist_id: selectedEvolution.dentist_id,
        attended_at: selectedEvolution.attended_at,
        reason: selectedEvolution.reason ?? "",
        subjective: selectedEvolution.subjective ?? "",
        objective: selectedEvolution.objective ?? "",
        assessment: selectedEvolution.assessment ?? "",
        performed_procedure: selectedEvolution.performed_procedure ?? "",
        anesthesia: selectedEvolution.anesthesia ?? "",
        materials: selectedEvolution.materials ?? "",
        administered_medications: selectedEvolution.administered_medications ?? "",
        findings: selectedEvolution.findings ?? "",
        complications: selectedEvolution.complications ?? "",
        indications: selectedEvolution.indications ?? "",
        recommendations: selectedEvolution.recommendations ?? "",
        next_control_at: selectedEvolution.next_control_at,
        next_control_reason: selectedEvolution.next_control_reason ?? "",
        followup_id: selectedEvolution.followup_id,
        observations: selectedEvolution.observations ?? "",
        procedures: selectedEvolution.procedures.map((item) => ({
          treatment_id: item.treatment_id,
          procedure_id: item.procedure_id,
          action: item.action,
          observations: item.observations,
        })),
      });
      onProceduresLoad(selectedEvolution.treatment_id ?? null);
    }
  }, [mode, selectedEvolution, onProceduresLoad]);

  if (!canView) {
    return (
      <Section title="Evoluciones">
        <Alert tone="info">
          No tienes permiso para consultar evoluciones clínicas completas.
        </Alert>
      </Section>
    );
  }

  function startNew() {
    const initial = emptyEvolution(activeSiteId, ownDentistId);
    setDraft(initial);
    setMode("new");
    onSelect(null);
    onProceduresLoad(null);
    onError(null);
    onMessage(null);
  }

  function selectEvolution(evolution: ClinicalEvolution) {
    onSelect(evolution.id);
    setMode(evolution.status === "DRAFT" ? "edit" : "idle");
    onError(null);
    onMessage(null);
  }

  function patchDraft(patch: Partial<ClinicalEvolutionInput>) {
    setDraft((current) => ({ ...current, ...patch }));
  }

  async function saveDraft() {
    onSavingChange(true);
    onError(null);
    onMessage(null);
    try {
      if (mode === "edit" && selectedEvolution) {
        await updateClinicalEvolutionDraft(selectedEvolution.id, {
          ...draft,
          version: selectedEvolution.version,
        });
        onMessage("Borrador de evolución guardado.");
      } else {
        const created = await createClinicalEvolution(patientId, draft);
        onSelect(created.id);
        setMode("edit");
        onMessage("Evolución clínica creada como borrador.");
      }
      await onRefresh();
    } catch (error) {
      onError(errorMessage(error, "No fue posible guardar la evolución."));
    } finally {
      onSavingChange(false);
    }
  }

  async function signDraft() {
    if (!selectedEvolution) return;
    const confirmed = window.confirm(
      "Después de firmar esta evolución no podrá editarse. Las correcciones posteriores deberán registrarse mediante una adenda.",
    );
    if (!confirmed) return;
    onSavingChange(true);
    onError(null);
    onMessage(null);
    try {
      await signClinicalEvolution(selectedEvolution.id, selectedEvolution.version);
      setMode("idle");
      onMessage("Evolución clínica firmada y cerrada.");
      await onRefresh();
    } catch (error) {
      onError(errorMessage(error, "No fue posible firmar la evolución."));
    } finally {
      onSavingChange(false);
    }
  }

  async function saveAddendum() {
    if (!selectedEvolution) return;
    onSavingChange(true);
    onError(null);
    onMessage(null);
    try {
      await createClinicalEvolutionAddendum(selectedEvolution.id, {
        reason: addendumReason,
        content: addendumContent,
        site_id: selectedEvolution.site_id,
        dentist_id: selectedEvolution.dentist_id,
      });
      setAddendumReason("");
      setAddendumContent("");
      onMessage("Adenda clínica agregada.");
      await onRefresh();
    } catch (error) {
      onError(errorMessage(error, "No fue posible agregar la adenda."));
    } finally {
      onSavingChange(false);
    }
  }

  const selectedIsSigned = selectedEvolution?.status === "SIGNED";
  const showForm = mode === "new" || (mode === "edit" && selectedEvolution?.status === "DRAFT");

  return (
    <Section title="Evoluciones">
      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
          <div>
            <h3 className="text-lg font-black text-slate-950">
              Evoluciones clínicas
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              Borradores editables, firma/cierre inmutable y correcciones por
              adenda dentro de la {terminologyRecord.toLowerCase()}.
            </p>
          </div>
          {canCreate && (
            <button
              type="button"
              onClick={startNew}
              className="rounded-xl bg-green-700 px-4 py-3 text-sm font-bold text-white"
            >
              Nueva evolución
            </button>
          )}
        </div>

        <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <div className="space-y-3">
            {evolutions.length === 0 ? (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                No hay evoluciones registradas.
              </div>
            ) : (
              evolutions.map((evolution) => (
                <button
                  key={evolution.id}
                  type="button"
                  onClick={() => selectEvolution(evolution)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    selectedEvolution?.id === evolution.id
                      ? "border-green-500 bg-green-50"
                      : "border-slate-200 bg-white hover:border-green-200"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-black text-slate-900">
                      {formatDate(evolution.attended_at, true)}
                    </span>
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-bold ${
                        evolution.status === "SIGNED"
                          ? "bg-green-100 text-green-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {evolution.status === "SIGNED" ? "Firmada" : "Borrador"}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    {evolution.dentist_name ?? "Odontólogo no asignado"} ·{" "}
                    {evolution.site_name ?? "Sin sede"}
                  </p>
                  <p className="mt-1 line-clamp-2 text-sm text-slate-500">
                    {evolution.reason ||
                      evolution.performed_procedure ||
                      evolution.assessment ||
                      "Sin resumen clínico aún."}
                  </p>
                </button>
              ))
            )}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            {showForm ? (
              <ClinicalEvolutionForm
                draft={draft}
                procedures={procedures}
                treatments={treatments}
                sites={sites}
                dentists={dentists}
                canUpdate={mode === "new" ? canCreate : canUpdate}
                saving={saving}
                selectedEvolution={selectedEvolution}
                onPatch={patchDraft}
                onProceduresLoad={onProceduresLoad}
                onSave={saveDraft}
                onSign={signDraft}
                canSign={canSign}
              />
            ) : selectedEvolution ? (
              <ClinicalEvolutionReadOnly
                evolution={selectedEvolution}
                canAddAddendum={canAddAddendum && selectedIsSigned}
                saving={saving}
                addendumReason={addendumReason}
                addendumContent={addendumContent}
                onAddendumReason={setAddendumReason}
                onAddendumContent={setAddendumContent}
                onSaveAddendum={saveAddendum}
              />
            ) : (
              <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">
                Selecciona una evolución o crea una nueva.
              </div>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <h3 className="text-sm font-black text-slate-900">
            Línea de tiempo clínica
          </h3>
          <div className="mt-3 space-y-3">
            {timeline.length === 0 ? (
              <p className="text-sm text-slate-500">Sin eventos clínicos aún.</p>
            ) : (
              timeline.map((item) => (
                <div key={item.id} className="rounded-xl bg-white p-4 shadow-sm">
                  <p className="text-xs font-bold uppercase tracking-[0.14em] text-green-700">
                    {formatDate(item.clinical_date, true)}
                  </p>
                  <p className="mt-1 font-bold text-slate-900">{item.title}</p>
                  {item.summary && (
                    <p className="mt-1 text-sm text-slate-600">{item.summary}</p>
                  )}
                  <p className="mt-2 text-xs text-slate-500">
                    {item.dentist_name ?? "Sin odontólogo"} ·{" "}
                    {item.site_name ?? "Sin sede"}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Section>
  );
}

function ClinicalEvolutionForm({
  draft,
  procedures,
  treatments,
  sites,
  dentists,
  canUpdate,
  saving,
  selectedEvolution,
  canSign,
  onPatch,
  onProceduresLoad,
  onSave,
  onSign,
}: {
  draft: ClinicalEvolutionInput;
  procedures: Procedure[];
  treatments: TreatmentListItem[];
  sites: AuthSite[];
  dentists: DentistSiteManagement[];
  canUpdate: boolean;
  saving: boolean;
  selectedEvolution: ClinicalEvolution | null;
  canSign: boolean;
  onPatch: (patch: Partial<ClinicalEvolutionInput>) => void;
  onProceduresLoad: (treatmentId: string | null) => Promise<void>;
  onSave: () => Promise<void>;
  onSign: () => Promise<void>;
}) {
  const selectedProcedureIds = new Set(
    draft.procedures.map((item) => item.procedure_id),
  );
  const disabled = !canUpdate || saving;

  function toggleProcedure(procedure: Procedure, checked: boolean) {
    if (checked) {
      onPatch({
        procedures: [
          ...draft.procedures,
          {
            treatment_id: procedure.treatment_id,
            procedure_id: procedure.id,
            action: "PERFORMED",
            observations: null,
          },
        ],
      });
      return;
    }
    onPatch({
      procedures: draft.procedures.filter(
        (item) => item.procedure_id !== procedure.id,
      ),
    });
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-amber-700">
            Borrador
          </p>
          <h3 className="text-lg font-black text-slate-950">
            {selectedEvolution ? "Editar evolución" : "Nueva evolución"}
          </h3>
        </div>
        {selectedEvolution && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
            Versión {selectedEvolution.version}
          </span>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label>
          <span className="mb-2 block text-sm font-bold text-slate-700">
            Fecha/hora clínica
          </span>
          <input
            type="datetime-local"
            value={toDatetimeLocalValue(draft.attended_at)}
            onChange={(event) =>
              onPatch({ attended_at: fromDatetimeLocalValue(event.target.value) })
            }
            disabled={disabled}
            className="min-h-11 w-full rounded-xl border border-slate-300 px-3"
          />
        </label>
        <label>
          <span className="mb-2 block text-sm font-bold text-slate-700">Sede</span>
          <select
            value={draft.site_id ?? ""}
            onChange={(event) => onPatch({ site_id: event.target.value || null })}
            disabled={disabled}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
          >
            <option value="">Seleccionar sede</option>
            {sites.map((site) => (
              <option key={site.id} value={site.id}>
                {site.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="mb-2 block text-sm font-bold text-slate-700">
            Odontólogo
          </span>
          <select
            value={draft.dentist_id ?? ""}
            onChange={(event) => onPatch({ dentist_id: event.target.value || null })}
            disabled={disabled}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
          >
            <option value="">Seleccionar odontólogo</option>
            {dentists.map((dentist) => (
              <option key={dentist.id} value={dentist.id}>
                {dentist.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="mb-2 block text-sm font-bold text-slate-700">
            Tratamiento
          </span>
          <select
            value={draft.treatment_id ?? ""}
            onChange={async (event) => {
              const treatmentId = event.target.value || null;
              onPatch({ treatment_id: treatmentId, procedures: [] });
              await onProceduresLoad(treatmentId);
            }}
            disabled={disabled}
            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
          >
            <option value="">Sin tratamiento vinculado</option>
            {treatments.map((treatment) => (
              <option key={treatment.id} value={treatment.id}>
                {treatment.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <TextArea label="Motivo de la atención" value={draft.reason ?? ""} onChange={(value) => onPatch({ reason: value })} />
        <TextArea label="Subjetivo" value={draft.subjective ?? ""} onChange={(value) => onPatch({ subjective: value })} />
        <TextArea label="Objetivo / Examen" value={draft.objective ?? ""} onChange={(value) => onPatch({ objective: value })} />
        <TextArea label="Evaluación / Diagnóstico" value={draft.assessment ?? ""} onChange={(value) => onPatch({ assessment: value })} />
        <TextArea label="Procedimiento realizado" value={draft.performed_procedure ?? ""} onChange={(value) => onPatch({ performed_procedure: value })} />
        <TextArea label="Anestesia y materiales" value={`${draft.anesthesia ?? ""}${draft.materials ? `\nMateriales: ${draft.materials}` : ""}`} onChange={(value) => onPatch({ anesthesia: value })} />
        <TextArea label="Medicamentos administrados" value={draft.administered_medications ?? ""} onChange={(value) => onPatch({ administered_medications: value })} />
        <TextArea label="Hallazgos y complicaciones" value={`${draft.findings ?? ""}${draft.complications ? `\nComplicaciones: ${draft.complications}` : ""}`} onChange={(value) => onPatch({ findings: value })} />
        <TextArea label="Indicaciones" value={draft.indications ?? ""} onChange={(value) => onPatch({ indications: value })} />
        <TextArea label="Recomendaciones" value={draft.recommendations ?? ""} onChange={(value) => onPatch({ recommendations: value })} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label>
          <span className="mb-2 block text-sm font-bold text-slate-700">
            Próximo control
          </span>
          <input
            type="datetime-local"
            value={toDatetimeLocalValue(draft.next_control_at)}
            onChange={(event) =>
              onPatch({ next_control_at: fromDatetimeLocalValue(event.target.value) })
            }
            disabled={disabled}
            className="min-h-11 w-full rounded-xl border border-slate-300 px-3"
          />
        </label>
        <TextInput
          label="Motivo próximo control"
          value={draft.next_control_reason ?? ""}
          onChange={(value) => onPatch({ next_control_reason: value })}
          disabled={disabled}
        />
      </div>

      {draft.treatment_id && (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-black text-slate-900">
            Procedimientos vinculados
          </p>
          <p className="mt-1 text-xs text-slate-500">
            La vinculación clínica no modifica automáticamente el estado económico
            ni operativo del procedimiento.
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {procedures.map((procedure) => (
              <label key={procedure.id} className="flex gap-3 rounded-xl bg-white p-3 text-sm">
                <input
                  type="checkbox"
                  checked={selectedProcedureIds.has(procedure.id)}
                  onChange={(event) => toggleProcedure(procedure, event.target.checked)}
                  disabled={disabled}
                />
                <span>
                  <span className="block font-bold text-slate-800">
                    {procedure.name}
                  </span>
                  <span className="text-slate-500">
                    {procedure.scope_label} · {procedure.status}
                  </span>
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
        <button
          type="button"
          onClick={onSave}
          disabled={disabled}
          className="rounded-xl bg-green-700 px-5 py-3 font-bold text-white disabled:opacity-60"
        >
          {saving ? "Guardando…" : "Guardar borrador"}
        </button>
        {selectedEvolution && canSign && (
          <button
            type="button"
            onClick={onSign}
            disabled={saving}
            className="rounded-xl border border-green-700 px-5 py-3 font-bold text-green-800 disabled:opacity-60"
          >
            Firmar y cerrar
          </button>
        )}
      </div>
    </div>
  );
}

function ClinicalEvolutionReadOnly({
  evolution,
  canAddAddendum,
  saving,
  addendumReason,
  addendumContent,
  onAddendumReason,
  onAddendumContent,
  onSaveAddendum,
}: {
  evolution: ClinicalEvolution;
  canAddAddendum: boolean;
  saving: boolean;
  addendumReason: string;
  addendumContent: string;
  onAddendumReason: (value: string) => void;
  onAddendumContent: (value: string) => void;
  onSaveAddendum: () => Promise<void>;
}) {
  const fields = [
    ["Motivo", evolution.reason],
    ["Subjetivo", evolution.subjective],
    ["Objetivo / Examen", evolution.objective],
    ["Evaluación", evolution.assessment],
    ["Procedimiento realizado", evolution.performed_procedure],
    ["Anestesia", evolution.anesthesia],
    ["Materiales", evolution.materials],
    ["Medicamentos administrados", evolution.administered_medications],
    ["Hallazgos", evolution.findings],
    ["Complicaciones", evolution.complications],
    ["Indicaciones", evolution.indications],
    ["Recomendaciones", evolution.recommendations],
    ["Observaciones", evolution.observations],
  ].filter(([, value]) => value);

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-green-200 bg-green-50 p-4">
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-green-700">
          Firmada
        </p>
        <h3 className="mt-1 text-lg font-black text-slate-950">
          Evolución clínica cerrada
        </h3>
        <p className="mt-1 text-sm text-slate-600">
          {formatDate(evolution.attended_at, true)} ·{" "}
          {evolution.dentist_name ?? "Sin odontólogo"} ·{" "}
          {evolution.site_name ?? "Sin sede"}
        </p>
        {evolution.content_hash && (
          <p className="mt-2 break-all text-xs text-slate-500">
            Integridad técnica SHA-256: {evolution.content_hash}
          </p>
        )}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-xl border border-slate-200 p-4">
            <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
              {label}
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-800">
              {value}
            </p>
          </div>
        ))}
      </div>

      {evolution.procedures.length > 0 && (
        <div className="rounded-2xl border border-slate-200 p-4">
          <p className="font-bold text-slate-900">Procedimientos vinculados</p>
          <div className="mt-3 space-y-2">
            {evolution.procedures.map((procedure) => (
              <div key={procedure.id} className="rounded-xl bg-slate-50 p-3 text-sm">
                <span className="font-bold">{procedure.procedure_name}</span>{" "}
                <span className="text-slate-500">· {procedure.action}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-2xl border border-slate-200 p-4">
        <p className="font-bold text-slate-900">Adendas</p>
        {evolution.addenda.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">Sin adendas.</p>
        ) : (
          <div className="mt-3 space-y-3">
            {evolution.addenda.map((addendum) => (
              <div key={addendum.id} className="rounded-xl bg-slate-50 p-3 text-sm">
                <p className="font-bold text-slate-900">{addendum.reason}</p>
                <p className="mt-1 whitespace-pre-wrap text-slate-700">
                  {addendum.content}
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  {formatDate(addendum.created_at, true)} ·{" "}
                  {addendum.dentist_name ?? "Sin odontólogo"}
                </p>
              </div>
            ))}
          </div>
        )}
        {canAddAddendum && (
          <div className="mt-4 grid gap-3">
            <TextInput
              label="Motivo de la adenda"
              value={addendumReason}
              onChange={onAddendumReason}
              disabled={saving}
            />
            <TextArea
              label="Contenido de la adenda"
              value={addendumContent}
              onChange={onAddendumContent}
            />
            <button
              type="button"
              onClick={onSaveAddendum}
              disabled={saving}
              className="justify-self-end rounded-xl bg-green-700 px-5 py-3 font-bold text-white disabled:opacity-60"
            >
              Agregar adenda
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function InformantSection({
  patient,
  form,
  disabled,
  onPatch,
}: {
  patient: Patient;
  form: ClinicalRecordInput;
  disabled: boolean;
  onPatch: (patch: Partial<ClinicalRecordInput>) => void;
}) {
  const activeResponsibles = patient.responsibles.filter(
    (responsible) => responsible.is_active,
  );
  const otherSelected =
    form.informant_type !== "PATIENT" && !form.informant_responsible_id;
  const relationshipOption =
    INFORMANT_RELATION_OPTIONS.find(
      (option) => option.value === form.informant_type,
    ) ?? INFORMANT_RELATION_OPTIONS.at(-1)!;

  function selectOther() {
    const option =
      INFORMANT_RELATION_OPTIONS.find(
        (item) => item.value === form.informant_type,
      ) ?? INFORMANT_RELATION_OPTIONS.at(-1)!;
    onPatch({
      informant_type:
        form.informant_type && form.informant_type !== "PATIENT"
          ? form.informant_type
          : "OTHER",
      informant_relationship: option.relationship,
      informant_responsible_id: null,
      informant_name: form.informant_responsible_id ? "" : form.informant_name,
      informant_document: form.informant_responsible_id
        ? ""
        : form.informant_document,
    });
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div>
        <h3 className="text-sm font-black text-slate-950">
          Información suministrada por
        </h3>
        <p className="mt-1 text-sm leading-6 text-slate-600">
          Persona que proporciona los antecedentes y datos clínicos del
          paciente.
        </p>
      </div>

      {!patient.is_minor ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <RadioCard
            checked={form.informant_type === "PATIENT" || !form.informant_type}
            disabled={disabled}
            title="El paciente"
            description={patient.full_name}
            onChange={() => onPatch(patientInformantPatch(patient))}
          />
          <RadioCard
            checked={otherSelected}
            disabled={disabled}
            title="Otra persona"
            description="Familiar, cuidador o representante."
            onChange={selectOther}
          />
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          {activeResponsibles.length > 0 ? (
            <div className="grid gap-3 md:grid-cols-2">
              {activeResponsibles.map((responsible) => (
                <RadioCard
                  key={responsible.id}
                  checked={form.informant_responsible_id === responsible.id}
                  disabled={disabled}
                  title={`${responsible.name}${
                    responsible.is_primary ? " · Principal" : ""
                  }`}
                  description={`${responsible.relationship}${
                    responsible.document ? ` · ${responsible.document}` : ""
                  }`}
                  onChange={() => onPatch(responsibleInformantPatch(responsible))}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <p className="font-bold">
                Este paciente menor no tiene un responsable principal registrado.
              </p>
              <p className="mt-1">
                Puedes volver al detalle del paciente para registrarlo o dejar
                constancia de otra persona adulta como informante.
              </p>
              <Link
                href={`/pacientes/${patient.id}`}
                className="mt-2 inline-block font-bold text-amber-950 underline"
              >
                Ir al detalle del paciente
              </Link>
            </div>
          )}
          <RadioCard
            checked={otherSelected}
            disabled={disabled}
            title="Otra persona"
            description="Adulto que suministra la información durante la atención."
            onChange={selectOther}
          />
        </div>
      )}

      {otherSelected && (
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <label className="block">
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Relación con el paciente
            </span>
            <select
              value={relationshipOption.value}
              onChange={(event) => {
                const option =
                  INFORMANT_RELATION_OPTIONS.find(
                    (item) => item.value === event.target.value,
                  ) ?? INFORMANT_RELATION_OPTIONS.at(-1)!;
                onPatch({
                  informant_type: option.value,
                  informant_relationship: option.relationship,
                });
              }}
              disabled={disabled}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 disabled:bg-slate-100"
            >
              {INFORMANT_RELATION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <TextInput
            label="Nombre completo"
            value={form.informant_name ?? ""}
            onChange={(value) => onPatch({ informant_name: value })}
            disabled={disabled}
          />
          <TextInput
            label="Documento opcional"
            value={form.informant_document ?? ""}
            onChange={(value) => onPatch({ informant_document: value })}
            disabled={disabled}
          />
        </div>
      )}

      {!otherSelected && form.informant_name && (
        <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-700">
          <span className="font-bold">Snapshot:</span> {form.informant_name}
          {form.informant_relationship ? ` · ${form.informant_relationship}` : ""}
          {form.informant_document ? ` · ${form.informant_document}` : ""}
        </div>
      )}
    </div>
  );
}

function RadioCard({
  checked,
  disabled,
  title,
  description,
  onChange,
}: {
  checked: boolean;
  disabled: boolean;
  title: string;
  description: string;
  onChange: () => void;
}) {
  return (
    <label
      className={`flex cursor-pointer gap-3 rounded-xl border bg-white p-4 text-left transition ${
        checked ? "border-green-500 ring-2 ring-green-100" : "border-slate-200"
      } ${disabled ? "cursor-not-allowed opacity-70" : "hover:border-green-300"}`}
    >
      <input
        type="radio"
        checked={checked}
        disabled={disabled}
        onChange={onChange}
        className="mt-1"
      />
      <span>
        <span className="block font-bold text-slate-900">{title}</span>
        <span className="mt-1 block text-sm text-slate-500">{description}</span>
      </span>
    </label>
  );
}

function ClinicalAlerts({
  criticalAllergies,
  activeMedications,
  relevantMedical,
}: {
  criticalAllergies: Allergy[];
  activeMedications: Medication[];
  relevantMedical: MedicalHistoryItemInput[];
}) {
  const hasAlert =
    criticalAllergies.length || activeMedications.length || relevantMedical.length;
  if (!hasAlert) {
    return (
      <div className="rounded-2xl border border-green-200 bg-green-50 p-4 text-sm text-green-800">
        Sin alertas clínicas críticas registradas en C015B.
      </div>
    );
  }
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      <AlertBox
        tone="danger"
        title="Alergias críticas"
        items={criticalAllergies.map((item) => `${item.substance} · ${item.severity}`)}
      />
      <AlertBox
        tone="warning"
        title="Medicamentos activos"
        items={activeMedications.map((item) => item.name)}
      />
      <AlertBox
        tone="warning"
        title="Antecedentes relevantes"
        items={relevantMedical.map((item) => item.type)}
      />
    </div>
  );
}

function AlertBox({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "danger" | "warning";
}) {
  const classes =
    tone === "danger"
      ? "border-red-200 bg-red-50 text-red-900"
      : "border-amber-200 bg-amber-50 text-amber-900";
  return (
    <div className={`rounded-2xl border p-4 text-sm ${classes}`}>
      <p className="font-black">{title}</p>
      {items.length ? (
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 opacity-75">Sin registros.</p>
      )}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <details open className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <summary className="cursor-pointer px-6 py-5 text-lg font-black text-slate-900">
        {title}
      </summary>
      <div className="border-t border-slate-100 p-6">{children}</div>
    </details>
  );
}

function TextInput({
  label,
  value,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-slate-700">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        className="min-h-11 w-full rounded-xl border border-slate-300 px-3 disabled:bg-slate-100"
      />
    </label>
  );
}

function TextArea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-slate-700">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={4}
        className="w-full rounded-xl border border-slate-300 px-3 py-2"
      />
    </label>
  );
}

function MedicalHistorySection({
  items,
  state,
  canEdit,
  saving,
  onStateChange,
  onItemsChange,
  onSave,
}: {
  items: MedicalHistoryItemInput[];
  state: string;
  canEdit: boolean;
  saving: boolean;
  onStateChange: (value: string) => void;
  onItemsChange: (items: MedicalHistoryItemInput[]) => void;
  onSave: () => Promise<void>;
}) {
  function update(index: number, patch: Partial<MedicalHistoryItemInput>) {
    onItemsChange(
      items.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item,
      ),
    );
  }
  return (
    <Section title="Antecedentes médicos">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <select
          value={state}
          onChange={(event) => onStateChange(event.target.value)}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-3"
        >
          <option value="NO_CONFIRMADO">Información no confirmada</option>
          <option value="NIEGA_ANTECEDENTES">Niega antecedentes relevantes</option>
          <option value="CON_ANTECEDENTES">Con antecedentes registrados</option>
        </select>
        {canEdit && (
          <button
            type="button"
            onClick={onSave}
            disabled={saving}
            className="rounded-xl bg-green-700 px-4 py-2 font-bold text-white disabled:opacity-60"
          >
            Guardar antecedentes
          </button>
        )}
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div
            key={item.type}
            className="grid gap-3 rounded-xl border border-slate-200 p-3 md:grid-cols-[1fr_150px_1.5fr]"
          >
            <p className="font-bold capitalize text-slate-800">{item.type}</p>
            <select
              value={item.present}
              onChange={(event) =>
                update(index, {
                  present: event.target.value as "SI" | "NO" | "DESCONOCIDO",
                })
              }
              className="min-h-10 rounded-xl border border-slate-300 bg-white px-3"
            >
              <option value="DESCONOCIDO">Desconocido</option>
              <option value="NO">No</option>
              <option value="SI">Sí</option>
            </select>
            <input
              value={item.detail ?? ""}
              onChange={(event) => update(index, { detail: event.target.value })}
              placeholder="Detalle / observación"
              className="min-h-10 rounded-xl border border-slate-300 px-3"
            />
          </div>
        ))}
      </div>
    </Section>
  );
}

function AllergiesSection({
  items,
  state,
  canEdit,
  saving,
  onStateChange,
  onAdd,
  onToggle,
}: {
  items: Allergy[];
  state: string;
  canEdit: boolean;
  saving: boolean;
  onStateChange: (value: string) => void;
  onAdd: (data: {
    type: string;
    substance: string;
    severity: string;
    critical_alert: boolean;
  }) => Promise<void>;
  onToggle: (item: Allergy) => Promise<void>;
}) {
  const [type, setType] = useState("medicamento");
  const [substance, setSubstance] = useState("");
  const [severity, setSeverity] = useState("desconocida");
  const [critical, setCritical] = useState(false);
  return (
    <Section title="Alergias">
      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={state}
          onChange={(event) => onStateChange(event.target.value)}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-3"
        >
          <option value="NO_CONFIRMADA">Información no confirmada</option>
          <option value="NIEGA_ALERGIAS">Niega alergias conocidas</option>
          <option value="CON_ALERGIAS">Con alergias registradas</option>
        </select>
      </div>
      {canEdit && (
        <div className="mb-5 grid gap-3 rounded-2xl bg-slate-50 p-4 md:grid-cols-[140px_1fr_160px_auto_auto]">
          <select value={type} onChange={(event) => setType(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3">
            {["medicamento", "anestésico", "látex", "alimento", "otro"].map((option) => <option key={option}>{option}</option>)}
          </select>
          <input value={substance} onChange={(event) => setSubstance(event.target.value)} placeholder="Sustancia" className="min-h-11 rounded-xl border border-slate-300 px-3" />
          <select value={severity} onChange={(event) => setSeverity(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3">
            {["leve", "moderada", "severa", "anafilaxia", "desconocida"].map((option) => <option key={option}>{option}</option>)}
          </select>
          <label className="flex items-center gap-2 text-sm font-bold text-red-800">
            <input type="checkbox" checked={critical} onChange={(event) => setCritical(event.target.checked)} />
            Crítica
          </label>
          <button
            type="button"
            disabled={saving || !substance.trim()}
            onClick={async () => {
              await onAdd({ type, substance, severity, critical_alert: critical });
              setSubstance("");
              setCritical(false);
            }}
            className="rounded-xl bg-green-700 px-4 py-2 font-bold text-white disabled:opacity-60"
          >
            Agregar
          </button>
        </div>
      )}
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-4">
            <div>
              <p className="font-bold text-slate-900">{item.substance}</p>
              <p className="text-sm text-slate-500">{item.type} · {item.severity} · {item.status}</p>
              {item.critical_alert && <span className="mt-2 inline-flex rounded-full bg-red-100 px-2 py-1 text-xs font-bold text-red-800">Alerta crítica</span>}
            </div>
            {canEdit && (
              <button type="button" onClick={() => onToggle(item)} className="text-sm font-bold text-green-700">
                {item.status === "descartada" ? "Reactivar" : "Descartar"}
              </button>
            )}
          </div>
        ))}
        {!items.length && <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">Sin alergias registradas.</p>}
      </div>
    </Section>
  );
}

function MedicationsSection({
  items,
  canEdit,
  saving,
  onAdd,
  onToggle,
}: {
  items: Medication[];
  canEdit: boolean;
  saving: boolean;
  onAdd: (data: { name: string; dose: string; frequency: string }) => Promise<void>;
  onToggle: (item: Medication) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [dose, setDose] = useState("");
  const [frequency, setFrequency] = useState("");
  const activeCount = useMemo(
    () => items.filter((item) => item.status === "activo").length,
    [items],
  );
  return (
    <Section title={`Medicamentos actuales (${activeCount} activos)`}>
      {canEdit && (
        <div className="mb-5 grid gap-3 rounded-2xl bg-slate-50 p-4 md:grid-cols-[1fr_160px_180px_auto]">
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Medicamento" className="min-h-11 rounded-xl border border-slate-300 px-3" />
          <input value={dose} onChange={(event) => setDose(event.target.value)} placeholder="Dosis" className="min-h-11 rounded-xl border border-slate-300 px-3" />
          <input value={frequency} onChange={(event) => setFrequency(event.target.value)} placeholder="Frecuencia" className="min-h-11 rounded-xl border border-slate-300 px-3" />
          <button
            type="button"
            disabled={saving || !name.trim()}
            onClick={async () => {
              await onAdd({ name, dose, frequency });
              setName("");
              setDose("");
              setFrequency("");
            }}
            className="rounded-xl bg-green-700 px-4 py-2 font-bold text-white disabled:opacity-60"
          >
            Agregar
          </button>
        </div>
      )}
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-4">
            <div>
              <p className="font-bold text-slate-900">{item.name}</p>
              <p className="text-sm text-slate-500">{[item.dose, item.frequency, item.status].filter(Boolean).join(" · ")}</p>
            </div>
            {canEdit && (
              <button type="button" onClick={() => onToggle(item)} className="text-sm font-bold text-green-700">
                {item.status === "activo" ? "Suspender" : "Reactivar"}
              </button>
            )}
          </div>
        ))}
        {!items.length && <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">Sin medicamentos registrados.</p>}
      </div>
    </Section>
  );
}
