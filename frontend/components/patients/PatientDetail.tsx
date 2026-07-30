"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Modal } from "@/components/shared/Modal";
import { Spinner } from "@/components/shared/Spinner";
import { ConfirmDialog } from "@/components/users/ConfirmDialog";
import { ClinicalRecordPage } from "@/components/patients/ClinicalRecordPage";
import { OdontogramPage } from "@/components/patients/OdontogramPage";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/services/apiClient";
import { getAgendaOptions } from "@/services/agendaService";
import { getClinicalSummary } from "@/services/clinicalRecordService";
import {
  createClinicalDocument,
  downloadClinicalDocumentPdf,
  duplicateClinicalDocument,
  finalizeClinicalDocument,
  listClinicalDocuments,
  previewClinicalDocument,
  updateClinicalDocument,
  voidClinicalDocument,
} from "@/services/clinicalDocumentService";
import { getAppointmentFollowup } from "@/services/followupService";
import {
  createResponsible,
  deactivatePatient,
  deleteResponsible,
  getPatientAppointments,
  getPatientSummary,
  reactivatePatient,
  updateResponsible,
} from "@/services/patientService";
import {
  createPayment,
  createTreatment,
  downloadBudgetPdf,
  downloadPaymentReceipt,
  listBudgets,
  listPayments,
  listProcedures,
  listTreatments,
} from "@/services/treatmentService";
import {
  createPrescription,
  downloadPrescriptionPdf,
  duplicatePrescription,
  finalizePrescription,
  listPrescriptions,
  previewPrescription,
  updatePrescription,
  voidPrescription,
} from "@/services/prescriptionService";
import type { AgendaOptions } from "@/types/agenda";
import type {
  PatientAppointment,
  PatientSummary,
  Responsible,
  ResponsibleInput,
} from "@/types/patient";
import type { ClinicalSummary } from "@/types/clinicalRecord";
import type { ClinicalDocument, ClinicalDocumentInput, ClinicalDocumentType } from "@/types/clinicalDocument";
import type { Followup } from "@/types/followup";
import type { Prescription, PrescriptionInput, PrescriptionItemInput } from "@/types/prescription";
import type { Budget, Payment, Procedure, TreatmentListItem } from "@/types/treatment";

function formatDate(value: string | null, withTime = false) {
  if (!value) return "No registrado";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    ...(withTime ? { timeStyle: "short" as const } : {}),
  }).format(new Date(value));
}

function money(value: string | number | null | undefined) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(value ?? 0));
}

type PatientWorkspaceTab =
  | "summary"
  | "clinical"
  | "odontogram"
  | "treatments"
  | "finance"
  | "agenda"
  | "documents"
  | "files";

export function PatientDetail({ patientId }: { patientId: string }) {
  const { hasPermission } = useAuth();
  const searchParams = useSearchParams();
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [appointments, setAppointments] = useState<PatientAppointment[]>([]);
  const [clinicalSummary, setClinicalSummary] =
    useState<ClinicalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [responsibleOpen, setResponsibleOpen] = useState(false);
  const [editingResponsible, setEditingResponsible] =
    useState<Responsible | null>(null);
  const [confirmation, setConfirmation] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedAppointment, setSelectedAppointment] =
    useState<PatientAppointment | null>(null);
  const [followup, setFollowup] = useState<Followup | null>(null);
  const [followupLoading, setFollowupLoading] = useState(false);
  const [followupMessage, setFollowupMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<PatientWorkspaceTab>("summary");
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [workspaceLoaded, setWorkspaceLoaded] = useState(false);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [patientTreatments, setPatientTreatments] = useState<TreatmentListItem[]>([]);
  const [patientBudgets, setPatientBudgets] = useState<Budget[]>([]);
  const [patientPayments, setPatientPayments] = useState<Payment[]>([]);
  const [agendaOptions, setAgendaOptions] = useState<AgendaOptions | null>(null);
  const [treatmentDialogOpen, setTreatmentDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [paymentTreatmentId, setPaymentTreatmentId] = useState("");
  const [paymentProcedures, setPaymentProcedures] = useState<Procedure[]>([]);
  const [paymentProceduresLoading, setPaymentProceduresLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [loadedSummary, loadedAppointments] = await Promise.all([
        getPatientSummary(patientId),
        getPatientAppointments(patientId),
      ]);
      setSummary(loadedSummary);
      setAppointments(loadedAppointments);
      try {
        setClinicalSummary(await getClinicalSummary(patientId));
      } catch {
        setClinicalSummary(null);
      }
    } catch {
      setError("No fue posible cargar el paciente.");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const tab = searchParams.get("tab");
    if (
      tab &&
      ["summary", "clinical", "odontogram", "treatments", "finance", "agenda", "documents", "files"].includes(tab)
    ) {
      setActiveTab(tab as PatientWorkspaceTab);
    }
  }, [searchParams]);

  const loadWorkspaceData = useCallback(async () => {
    setWorkspaceLoading(true);
    setWorkspaceError(null);
    try {
      const [treatmentsResponse, budgets, payments, options] = await Promise.all([
        hasPermission("treatments.view")
          ? listTreatments(`?patient_id=${patientId}`)
          : Promise.resolve({ items: [], total: 0 }),
        hasPermission("budgets.view") ? listBudgets() : Promise.resolve([]),
        hasPermission("payments.view") ? listPayments() : Promise.resolve([]),
        hasPermission("appointments.view") || hasPermission("payments.create") || hasPermission("treatments.create")
          ? getAgendaOptions()
          : Promise.resolve(null),
      ]);
      setPatientTreatments(treatmentsResponse.items);
      setPatientBudgets(budgets.filter((budget) => budget.patient_id === patientId));
      setPatientPayments(payments.filter((payment) => payment.patient_id === patientId));
      setAgendaOptions(options);
      setWorkspaceLoaded(true);
    } catch {
      setWorkspaceError("No fue posible cargar la información integral del paciente.");
    } finally {
      setWorkspaceLoading(false);
    }
  }, [hasPermission, patientId]);

  useEffect(() => {
    if (
      !workspaceLoaded &&
      ["summary", "treatments", "finance", "documents"].includes(activeTab)
    ) {
      loadWorkspaceData();
    }
  }, [activeTab, loadWorkspaceData, workspaceLoaded]);

  useEffect(() => {
    if (!paymentTreatmentId) {
      setPaymentProcedures([]);
      return;
    }
    setPaymentProceduresLoading(true);
    listProcedures(paymentTreatmentId)
      .then((procedures) =>
        setPaymentProcedures(
          procedures.filter((procedure) => procedure.status !== "Cancelado"),
        ),
      )
      .catch(() => setPaymentProcedures([]))
      .finally(() => setPaymentProceduresLoading(false));
  }, [paymentTreatmentId]);

  if (loading || !summary) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 text-slate-500">
        <Spinner className="h-7 w-7 text-dentia-primary" />
        Cargando paciente…
      </div>
    );
  }

  const patient = summary.patient;
  const activeTreatments = patientTreatments.filter((item) =>
    ["Aprobado", "En ejecución", "Pausado"].includes(item.status),
  );
  const finishedTreatments = patientTreatments.filter(
    (item) => item.status === "Finalizado",
  );
  const pendingBudgets = patientBudgets.filter((budget) =>
    ["Borrador", "Pendiente de aprobación"].includes(budget.status),
  );
  const validPayments = patientPayments.filter((payment) => payment.status === "valido");
  const lastPayment = [...validPayments].sort(
    (a, b) => new Date(b.paid_at).getTime() - new Date(a.paid_at).getTime(),
  )[0];
  const totalPaid = validPayments.reduce(
    (sum, payment) => sum + Number(payment.value),
    0,
  );
  const tabs: {
    id: PatientWorkspaceTab;
    label: string;
    permission?: string;
    disabled?: boolean;
  }[] = [
    { id: "summary", label: "Resumen" },
    {
      id: "clinical",
      label: clinicalSummary?.terminology.record ?? "Historia Clínica",
      permission: "clinical_records.view_sensitive",
    },
    { id: "odontogram", label: "Odontograma", permission: "odontogram.view" },
    { id: "treatments", label: "Tratamientos", permission: "treatments.view" },
    { id: "finance", label: "Finanzas", permission: "payments.view" },
    { id: "agenda", label: "Agenda", permission: "appointments.view" },
    { id: "documents", label: "Documentos" },
    { id: "files", label: "Archivos" },
  ];

  async function changeStatus() {
    setSaving(true);
    setError(null);
    try {
      if (patient.status === "Activo") {
        await deactivatePatient(patient.id);
      } else {
        await reactivatePatient(patient.id);
      }
      setConfirmation(false);
      await load();
    } catch (statusError) {
      setError(
        statusError instanceof ApiError
          ? statusError.detail ?? statusError.message
          : "No fue posible cambiar el estado.",
      );
      setConfirmation(false);
    } finally {
      setSaving(false);
    }
  }

  async function openFollowup(appointment: PatientAppointment) {
    setSelectedAppointment(appointment);
    setFollowup(null);
    setFollowupMessage(null);
    setFollowupLoading(true);
    try {
      const loadedFollowup = await getAppointmentFollowup(
        patient.id,
        appointment.id,
      );
      setFollowup(loadedFollowup);
    } catch (followupError) {
      if (followupError instanceof ApiError && followupError.status === 404) {
        setFollowupMessage("Esta cita no tiene seguimiento asociado.");
      } else {
        setFollowupMessage(
          followupError instanceof ApiError
            ? followupError.detail ?? followupError.message
            : "No fue posible cargar el seguimiento.",
        );
      }
    } finally {
      setFollowupLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <Link
        href="/pacientes"
        className="text-sm font-bold text-green-700 hover:underline"
      >
        ← Volver a pacientes
      </Link>

      <header className="mt-5 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-black text-slate-950">
              {patient.full_name}
            </h1>
            <span
              className={`rounded-full px-3 py-1 text-xs font-bold ${
                patient.status === "Activo"
                  ? "bg-green-50 text-green-700"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {patient.status}
            </span>
            {!patient.profile_complete && (
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
                Perfil incompleto
              </span>
            )}
            {patient.is_minor && (
              <span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-bold text-sky-800">
                Menor de edad
              </span>
            )}
          </div>
          <p className="mt-2 text-sm text-slate-500">
            {patient.document_type === "Sin documento"
              ? "Sin documento"
              : `${patient.document_type} ${patient.document ?? ""}`}{" "}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {hasPermission("patients.update") && (
            <Link
              href={`/pacientes/${patient.id}/editar`}
              className="inline-flex min-h-11 items-center rounded-xl border border-slate-300 px-4 font-bold text-slate-700"
            >
              Editar
            </Link>
          )}
          {hasPermission("patients.deactivate") && (
            <button
              type="button"
              onClick={() => setConfirmation(true)}
              className={`min-h-11 rounded-xl px-4 font-bold ${
                patient.status === "Activo"
                  ? "border border-red-200 text-red-700"
                  : "bg-green-700 text-white"
              }`}
            >
              {patient.status === "Activo" ? "Desactivar" : "Reactivar"}
            </button>
          )}
        </div>
        </div>
      </header>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}

      <nav className="sticky top-0 z-20 mt-6 overflow-x-auto rounded-2xl border border-slate-200 bg-white/95 p-2 shadow-sm backdrop-blur">
        <div className="flex min-w-max gap-2">
          {tabs
            .filter((tab) => !tab.permission || hasPermission(tab.permission))
            .map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`rounded-xl px-5 py-3 text-sm font-black transition ${
                  activeTab === tab.id
                    ? "bg-dentia-primary text-white shadow-sm"
                    : "text-slate-600 hover:bg-green-50 hover:text-green-800"
                }`}
              >
                {tab.label}
              </button>
            ))}
        </div>
      </nav>

      <section className="mt-6">
        {activeTab === "summary" && (
          <PatientSummaryWorkspace
            summary={summary}
            clinicalSummary={clinicalSummary}
            patientTreatments={patientTreatments}
            activeTreatments={activeTreatments.length}
            finishedTreatments={finishedTreatments.length}
            pendingBudgets={pendingBudgets.length}
            lastPayment={lastPayment}
            totalPaid={totalPaid}
            workspaceLoading={workspaceLoading}
            workspaceError={workspaceError}
            onOpenResponsible={() => {
              setEditingResponsible(null);
              setResponsibleOpen(true);
            }}
            onEditResponsible={(responsible) => {
              setEditingResponsible(responsible);
              setResponsibleOpen(true);
            }}
            onDeleteResponsible={async (responsible) => {
              try {
                await deleteResponsible(patient.id, responsible.id);
                await load();
              } catch (deleteError) {
                setError(
                  deleteError instanceof ApiError
                    ? deleteError.detail ?? deleteError.message
                    : "No fue posible retirar el responsable.",
                );
              }
            }}
            canUpdatePatient={hasPermission("patients.update")}
          />
        )}

        {activeTab === "clinical" && (
          hasPermission("clinical_records.view_sensitive") ? (
            <ClinicalRecordPage patientId={patient.id} embedded />
          ) : (
            <AccessCard title="Acceso clínico restringido" />
          )
        )}

        {activeTab === "odontogram" && (
          hasPermission("odontogram.view") ? (
            <OdontogramPage
              patientId={patient.id}
              embedded
              onCommercialDataChanged={loadWorkspaceData}
            />
          ) : (
            <AccessCard title="No tienes permiso para ver el odontograma." />
          )
        )}

        {activeTab === "treatments" && (
          <PatientTreatmentsWorkspace
            treatments={patientTreatments}
            loading={workspaceLoading}
            error={workspaceError}
            canCreate={hasPermission("treatments.create")}
            onCreate={() => setTreatmentDialogOpen(true)}
          />
        )}

        {activeTab === "finance" && (
          <PatientFinanceWorkspace
            treatments={patientTreatments}
            budgets={patientBudgets}
            payments={patientPayments}
            loading={workspaceLoading}
            error={workspaceError}
            canCreatePayment={hasPermission("payments.create")}
            canViewPayments={hasPermission("payments.view")}
            canViewBudgets={hasPermission("budgets.view")}
            onCreatePayment={(treatmentId) => {
              setPaymentTreatmentId(treatmentId);
              setPaymentDialogOpen(true);
            }}
          />
        )}

        {activeTab === "agenda" && (
          <PatientAgendaWorkspace
            appointments={appointments}
            patientId={patient.id}
            canCreate={patient.status === "Activo" && hasPermission("appointments.create")}
            canViewFollowups={hasPermission("followups.view")}
            onOpenFollowup={openFollowup}
          />
        )}

        {activeTab === "documents" && (
          <PatientDocumentsWorkspace
            patientId={patient.id}
            budgets={patientBudgets}
            payments={patientPayments}
            treatments={patientTreatments}
            options={agendaOptions}
            loading={workspaceLoading}
            error={workspaceError}
            canViewBudgets={hasPermission("budgets.view")}
            canViewPayments={hasPermission("payments.view")}
            canViewClinicalDocuments={hasPermission("clinical_documents.view")}
            canCreateClinicalDocuments={hasPermission("clinical_documents.create")}
            canEditClinicalDocuments={hasPermission("clinical_documents.edit_draft")}
            canFinalizeClinicalDocuments={hasPermission("clinical_documents.finalize")}
            canDownloadClinicalDocuments={hasPermission("clinical_documents.download")}
            canVoidClinicalDocuments={hasPermission("clinical_documents.void")}
            canViewPrescriptions={hasPermission("prescriptions.view")}
            canCreatePrescriptions={hasPermission("prescriptions.create")}
            canEditPrescriptions={hasPermission("prescriptions.edit_draft")}
            canFinalizePrescriptions={hasPermission("prescriptions.finalize")}
            canDownloadPrescriptions={hasPermission("prescriptions.download")}
            canVoidPrescriptions={hasPermission("prescriptions.void")}
          />
        )}

        {activeTab === "files" && <PatientFilesPlaceholder />}
      </section>

      <CreateTreatmentDialog
        open={treatmentDialogOpen}
        patientId={patient.id}
        options={agendaOptions}
        onClose={() => setTreatmentDialogOpen(false)}
        onCreated={async () => {
          setTreatmentDialogOpen(false);
          await loadWorkspaceData();
          setActiveTab("treatments");
        }}
      />

      <CreatePatientPaymentDialog
        open={paymentDialogOpen}
        treatments={patientTreatments}
        options={agendaOptions}
        selectedTreatmentId={paymentTreatmentId}
        procedures={paymentProcedures}
        proceduresLoading={paymentProceduresLoading}
        onTreatmentChange={setPaymentTreatmentId}
        onClose={() => {
          setPaymentDialogOpen(false);
          setPaymentTreatmentId("");
        }}
        onCreated={async () => {
          setPaymentDialogOpen(false);
          setPaymentTreatmentId("");
          await loadWorkspaceData();
          setActiveTab("finance");
        }}
      />

      <ResponsibleDialog
        open={responsibleOpen}
        responsible={editingResponsible}
        onClose={() => setResponsibleOpen(false)}
        onSave={async (data) => {
          if (editingResponsible) {
            await updateResponsible(
              patient.id,
              editingResponsible.id,
              data,
            );
          } else {
            await createResponsible(patient.id, data);
          }
          setResponsibleOpen(false);
          await load();
        }}
      />

      <ConfirmDialog
        open={confirmation}
        title={
          patient.status === "Activo"
            ? "Desactivar paciente"
            : "Reactivar paciente"
        }
        description={
          patient.status === "Activo"
            ? "Solo podrá desactivarse si no tiene citas futuras activas."
            : "El paciente volverá a estar disponible para nuevas citas."
        }
        confirmLabel={
          patient.status === "Activo" ? "Desactivar" : "Reactivar"
        }
        busy={saving}
        tone={patient.status === "Activo" ? "danger" : "primary"}
        onClose={() => setConfirmation(false)}
        onConfirm={changeStatus}
      />

      <AppointmentFollowupDialog
        appointment={selectedAppointment}
        followup={followup}
        loading={followupLoading}
        message={followupMessage}
        onClose={() => {
          setSelectedAppointment(null);
          setFollowup(null);
          setFollowupMessage(null);
        }}
      />
    </div>
  );
}

function PatientSummaryWorkspace({
  summary,
  clinicalSummary,
  patientTreatments,
  activeTreatments,
  finishedTreatments,
  pendingBudgets,
  lastPayment,
  totalPaid,
  workspaceLoading,
  workspaceError,
  canUpdatePatient,
  onOpenResponsible,
  onEditResponsible,
  onDeleteResponsible,
}: {
  summary: PatientSummary;
  clinicalSummary: ClinicalSummary | null;
  patientTreatments: TreatmentListItem[];
  activeTreatments: number;
  finishedTreatments: number;
  pendingBudgets: number;
  lastPayment: Payment | undefined;
  totalPaid: number;
  workspaceLoading: boolean;
  workspaceError: string | null;
  canUpdatePatient: boolean;
  onOpenResponsible: () => void;
  onEditResponsible: (responsible: Responsible) => void;
  onDeleteResponsible: (responsible: Responsible) => Promise<void>;
}) {
  const patient = summary.patient;
  return (
    <div className="space-y-5">
      {workspaceError && <Alert tone="error">{workspaceError}</Alert>}
      {workspaceLoading && (
        <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500">
          <Spinner className="h-5 w-5 text-dentia-primary" />
          Actualizando indicadores del paciente…
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-2">
        <MetricGroup title="Información clínica">
          <MiniMetric
            label="Historia clínica"
            value={
              clinicalSummary?.exists
                ? `${clinicalSummary.terminology.record} activa`
                : "Sin apertura"
            }
          />
          <MiniMetric
            label="Alertas clínicas"
            value={
              clinicalSummary?.has_critical_alerts
                ? "Críticas"
                : clinicalSummary?.requires_clinical_precaution
                  ? "Precaución"
                  : "Sin alertas críticas"
            }
            tone={
              clinicalSummary?.has_critical_alerts
                ? "red"
                : clinicalSummary?.requires_clinical_precaution
                  ? "amber"
                  : "green"
            }
          />
          <MiniMetric label="Tratamientos activos" value={String(activeTreatments)} />
          <MiniMetric label="Tratamientos finalizados" value={String(finishedTreatments)} />
        </MetricGroup>

        <MetricGroup title="Agenda">
          <MiniMetric
            label="Próxima cita"
            value={
              summary.next_appointment
                ? formatDate(summary.next_appointment.starts_at, true)
                : "Sin cita futura"
            }
          />
          <MiniMetric
            label="Última cita"
            value={
              summary.last_appointment
                ? formatDate(summary.last_appointment.starts_at, true)
                : "Sin citas anteriores"
            }
          />
          <MiniMetric label="Número de citas" value={String(summary.appointment_count)} />
        </MetricGroup>

        <MetricGroup title="Información financiera">
          <MiniMetric
            label="Último pago"
            value={lastPayment ? money(lastPayment.value) : "Sin pagos"}
            hint={lastPayment ? formatDate(lastPayment.paid_at, true) : undefined}
          />
          <MiniMetric label="Total pagado" value={money(totalPaid)} />
          <MiniMetric label="Presupuestos pendientes" value={String(pendingBudgets)} />
        </MetricGroup>

        <MetricGroup title="Actividad">
          <MiniMetric label="Total de tratamientos" value={String(patientTreatments.length)} />
          <MiniMetric
            label="Próxima acción"
            value={summary.next_appointment ? "Atender cita" : "Agendar control"}
          />
        </MetricGroup>
      </div>

      {clinicalSummary && (
        <section
          className={`rounded-2xl border p-5 shadow-sm ${
            clinicalSummary.has_critical_alerts
              ? "border-red-200 bg-red-50"
              : clinicalSummary.requires_clinical_precaution
                ? "border-amber-200 bg-amber-50"
                : "border-slate-200 bg-white"
          }`}
        >
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                {clinicalSummary.terminology.summary}
              </p>
              <h2 className="mt-1 text-lg font-black text-slate-950">
                {clinicalSummary.exists
                  ? `${clinicalSummary.terminology.record} activa`
                  : `Sin ${clinicalSummary.terminology.record.toLowerCase()} abierta`}
              </h2>
              {clinicalSummary.limited && clinicalSummary.message ? (
                <p className="mt-2 text-sm font-semibold text-amber-900">
                  {clinicalSummary.message}
                </p>
              ) : clinicalSummary.exists ? (
                <p className="mt-2 text-sm text-slate-600">
                  Apertura: {formatDate(clinicalSummary.opened_at, true)} ·
                  Última actualización: {formatDate(clinicalSummary.updated_at, true)}
                  {clinicalSummary.has_critical_alerts
                    ? " · Presenta alergias críticas"
                    : ""}
                </p>
              ) : (
                <p className="mt-2 text-sm text-slate-600">
                  Este paciente aún no tiene {clinicalSummary.terminology.record.toLowerCase()} abierta.
                </p>
              )}
            </div>
            {clinicalSummary.exists && clinicalSummary.limited && (
                <span className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-500">
                  Acceso clínico restringido
                </span>
            )}
          </div>
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">Datos personales</h2>
          <dl className="mt-5 grid gap-5 sm:grid-cols-2">
            {[
              ["Fecha de nacimiento", formatDate(patient.birth_date)],
              ["Edad", patient.age === null ? "No registrada" : `${patient.age} años`],
              ["Sexo", patient.sex ?? "No registrado"],
              ["Correo", patient.email ?? "No registrado"],
              ["Teléfono alternativo", patient.alternate_phone ?? "No registrado"],
              [
                "Ubicación",
                [patient.city, patient.department].filter(Boolean).join(", ") ||
                  "No registrada",
              ],
              ["Dirección", patient.address ?? "No registrada"],
              [
                "Contacto de emergencia",
                [patient.emergency_contact_name, patient.emergency_contact_mobile]
                  .filter(Boolean)
                  .join(" · ") || "No registrado",
              ],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs font-bold uppercase tracking-wide text-slate-400">
                  {label}
                </dt>
                <dd className="mt-1 text-sm font-semibold text-slate-800">
                  {value}
                </dd>
              </div>
            ))}
          </dl>
          <div className="mt-6 border-t border-slate-100 pt-5">
            <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Observaciones administrativas
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
              {patient.administrative_notes ?? "Sin observaciones."}
            </p>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-bold text-slate-900">Responsables</h2>
            {canUpdatePatient && (
              <button
                type="button"
                onClick={onOpenResponsible}
                className="text-sm font-bold text-green-700"
              >
                + Agregar
              </button>
            )}
          </div>
          <div className="mt-4 space-y-3">
            {patient.responsibles.map((responsible) => (
              <div
                key={responsible.id}
                className="rounded-xl border border-slate-200 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-bold text-slate-900">{responsible.name}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {responsible.relationship} · {responsible.mobile}
                    </p>
                    {responsible.is_primary && (
                      <span className="mt-2 inline-flex rounded-full bg-green-50 px-2 py-1 text-[11px] font-bold text-green-700">
                        Principal
                      </span>
                    )}
                  </div>
                  {canUpdatePatient && (
                    <div className="flex gap-2 text-xs font-bold">
                      <button
                        type="button"
                        onClick={() => onEditResponsible(responsible)}
                        className="text-green-700"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => onDeleteResponsible(responsible)}
                        className="text-red-700"
                      >
                        Retirar
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {!patient.responsibles.length && (
              <p className="py-6 text-center text-sm text-slate-500">
                No hay responsables registrados.
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function PatientTreatmentsWorkspace({
  treatments,
  loading,
  error,
  canCreate,
  onCreate,
}: {
  treatments: TreatmentListItem[];
  loading: boolean;
  error: string | null;
  canCreate: boolean;
  onCreate: () => void;
}) {
  return (
    <WorkspacePanel
      title="Tratamientos del paciente"
      description="Planes clínicos y económicos asociados al paciente actual."
      action={
        canCreate ? (
          <button
            type="button"
            onClick={onCreate}
            className="min-h-10 rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white"
          >
            Crear tratamiento
          </button>
        ) : null
      }
    >
      {error && <Alert tone="error">{error}</Alert>}
      {loading ? (
        <LoadingLine label="Cargando tratamientos…" />
      ) : (
        <ResponsiveTable
          empty="Este paciente todavía no tiene tratamientos."
          headings={["Tratamiento", "Estado clínico", "Odontólogo", "Valor", "Estado financiero", "Acciones"]}
          rows={treatments.map((item) => [
            <div key="name">
              <p className="font-bold text-slate-900">{item.name}</p>
              <p className="mt-1 text-xs text-slate-500">
                Actualizado: {formatDate(item.updated_at, true)}
              </p>
            </div>,
            <StatusBadge key="status" value={item.status} />,
            item.responsible_dentist_name ?? "—",
            money(item.final_value),
            Number(item.balance) > 0 ? (
              <span key="balance" className="font-bold text-orange-700">
                Saldo {money(item.balance)}
              </span>
            ) : (
              <span key="balance" className="font-bold text-green-700">Al día</span>
            ),
            <Link
              key="action"
              href={`/tratamientos/${item.id}`}
              className="text-sm font-bold text-green-700 hover:underline"
            >
              Ver tratamiento
            </Link>,
          ])}
        />
      )}
    </WorkspacePanel>
  );
}

function PatientFinanceWorkspace({
  treatments,
  budgets,
  payments,
  loading,
  error,
  canCreatePayment,
  canViewPayments,
  canViewBudgets,
  onCreatePayment,
}: {
  treatments: TreatmentListItem[];
  budgets: Budget[];
  payments: Payment[];
  loading: boolean;
  error: string | null;
  canCreatePayment: boolean;
  canViewPayments: boolean;
  canViewBudgets: boolean;
  onCreatePayment: (treatmentId: string) => void;
}) {
  const validPayments = payments.filter((payment) => payment.status === "valido");
  const paid = validPayments.reduce((sum, payment) => sum + Number(payment.value), 0);
  const balance = treatments.reduce((sum, treatment) => sum + Number(treatment.balance), 0);
  return (
    <div className="space-y-6">
      {error && <Alert tone="error">{error}</Alert>}
      <div className="grid gap-4 md:grid-cols-3">
        <MiniMetric label="Total pagado" value={money(paid)} />
        <MiniMetric label="Saldo pendiente" value={money(balance)} tone={balance > 0 ? "amber" : "green"} />
        <MiniMetric label="Comprobantes emitidos" value={String(payments.length)} />
      </div>

      <WorkspacePanel
        title="Presupuestos"
        description="Presupuestos del paciente y descarga de PDF."
      >
        {loading ? (
          <LoadingLine label="Cargando presupuestos…" />
        ) : canViewBudgets ? (
          <ResponsiveTable
            empty="Sin presupuestos."
            headings={["Fecha", "Tratamiento", "Estado", "Valor", "Acciones"]}
            rows={budgets.map((budget) => [
              formatDate(budget.issued_at, true),
              treatmentName(treatments, budget.treatment_id),
              <StatusBadge key="status" value={budget.status} />,
              money(budget.final_value),
              <button
                key="pdf"
                type="button"
                onClick={() => downloadBlob(() => downloadBudgetPdf(budget.id), `presupuesto-${budget.number ?? budget.version}.pdf`)}
                className="text-sm font-bold text-green-700 hover:underline"
              >
                Descargar PDF
              </button>,
            ])}
          />
        ) : (
          <AccessCard title="No tienes permiso para ver presupuestos." />
        )}
      </WorkspacePanel>

      <WorkspacePanel
        title="Pagos y comprobantes"
        description="Historial de pagos del paciente y emisión de comprobantes."
        action={
          canCreatePayment && treatments.length ? (
            <button
              type="button"
              onClick={() => onCreatePayment(treatments[0].id)}
              className="min-h-10 rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white"
            >
              Registrar pago
            </button>
          ) : null
        }
      >
        {loading ? (
          <LoadingLine label="Cargando pagos…" />
        ) : canViewPayments ? (
          <ResponsiveTable
            empty="Sin pagos registrados."
            headings={["Fecha", "Tratamiento", "Comprobante", "Valor", "Medio", "Acciones"]}
            rows={payments.map((payment) => [
              formatDate(payment.paid_at, true),
              payment.treatment_name,
              payment.receipt_number,
              money(payment.value),
              payment.payment_method,
              <button
                key="receipt"
                type="button"
                onClick={() => downloadBlob(() => downloadPaymentReceipt(payment.id), `comprobante-${payment.receipt_number}.pdf`)}
                className="text-sm font-bold text-green-700 hover:underline"
              >
                Descargar comprobante
              </button>,
            ])}
          />
        ) : (
          <AccessCard title="No tienes permiso para ver pagos." />
        )}
      </WorkspacePanel>
    </div>
  );
}

function PatientAgendaWorkspace({
  appointments,
  patientId,
  canCreate,
  canViewFollowups,
  onOpenFollowup,
}: {
  appointments: PatientAppointment[];
  patientId: string;
  canCreate: boolean;
  canViewFollowups: boolean;
  onOpenFollowup: (appointment: PatientAppointment) => void;
}) {
  return (
    <WorkspacePanel
      title="Agenda del paciente"
      description="Historial de citas y acciones operativas sin volver a buscar al paciente."
      action={
        canCreate ? (
          <Link
            href={`/agenda?patient_id=${patientId}&new=1`}
            className="inline-flex min-h-10 items-center rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white"
          >
            Nueva cita
          </Link>
        ) : null
      }
    >
      <ResponsiveTable
        empty="El paciente todavía no tiene citas."
        headings={["Fecha", "Tipo", "Odontólogo", "Sede", "Estado", "Acciones"]}
        rows={appointments.map((appointment) => [
          formatDate(appointment.starts_at, true),
          appointment.appointment_type_name,
          appointment.dentist_name,
          appointment.site_name,
          <StatusBadge key="status" value={appointment.status} />,
          <div key="actions" className="flex flex-wrap gap-3">
            <Link href={`/agenda?appointment_id=${appointment.id}`} className="font-bold text-green-700 hover:underline">
              Ver detalle
            </Link>
            {canViewFollowups && (
              <button
                type="button"
                onClick={() => onOpenFollowup(appointment)}
                className="font-bold text-green-700 hover:underline"
              >
                Ver seguimiento
              </button>
            )}
          </div>,
        ])}
      />
    </WorkspacePanel>
  );
}

function PatientDocumentsWorkspace({
  patientId,
  budgets,
  payments,
  treatments,
  options,
  loading,
  error,
  canViewBudgets,
  canViewPayments,
  canViewClinicalDocuments,
  canCreateClinicalDocuments,
  canEditClinicalDocuments,
  canFinalizeClinicalDocuments,
  canDownloadClinicalDocuments,
  canVoidClinicalDocuments,
  canViewPrescriptions,
  canCreatePrescriptions,
  canEditPrescriptions,
  canFinalizePrescriptions,
  canDownloadPrescriptions,
  canVoidPrescriptions,
}: {
  patientId: string;
  budgets: Budget[];
  payments: Payment[];
  treatments: TreatmentListItem[];
  options: AgendaOptions | null;
  loading: boolean;
  error: string | null;
  canViewBudgets: boolean;
  canViewPayments: boolean;
  canViewClinicalDocuments: boolean;
  canCreateClinicalDocuments: boolean;
  canEditClinicalDocuments: boolean;
  canFinalizeClinicalDocuments: boolean;
  canDownloadClinicalDocuments: boolean;
  canVoidClinicalDocuments: boolean;
  canViewPrescriptions: boolean;
  canCreatePrescriptions: boolean;
  canEditPrescriptions: boolean;
  canFinalizePrescriptions: boolean;
  canDownloadPrescriptions: boolean;
  canVoidPrescriptions: boolean;
}) {
  const [clinicalDocuments, setClinicalDocuments] = useState<ClinicalDocument[]>([]);
  const [clinicalLoading, setClinicalLoading] = useState(false);
  const [clinicalError, setClinicalError] = useState<string | null>(null);
  const [editing, setEditing] = useState<ClinicalDocument | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [voiding, setVoiding] = useState<ClinicalDocument | null>(null);
  const [voidReason, setVoidReason] = useState("");
  const [voidingBusy, setVoidingBusy] = useState(false);
  const [form, setForm] = useState<ClinicalDocumentInput>(() => defaultClinicalDocumentForm(options));
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [prescriptionLoading, setPrescriptionLoading] = useState(false);
  const [prescriptionError, setPrescriptionError] = useState<string | null>(null);
  const [editingPrescription, setEditingPrescription] = useState<Prescription | null>(null);
  const [prescriptionFormOpen, setPrescriptionFormOpen] = useState(false);
  const [voidingPrescription, setVoidingPrescription] = useState<Prescription | null>(null);
  const [prescriptionVoidReason, setPrescriptionVoidReason] = useState("");
  const [prescriptionVoidingBusy, setPrescriptionVoidingBusy] = useState(false);
  const [prescriptionForm, setPrescriptionForm] = useState<PrescriptionInput>(() => defaultPrescriptionForm(options));
  const [reviewedAlerts, setReviewedAlerts] = useState(false);

  const loadClinicalDocuments = useCallback(async () => {
    if (!canViewClinicalDocuments) return;
    setClinicalLoading(true);
    setClinicalError(null);
    try {
      const response = await listClinicalDocuments(patientId);
      setClinicalDocuments(response.items);
    } catch (caught) {
      setClinicalError(caught instanceof Error ? caught.message : "No fue posible cargar informes y documentos.");
    } finally {
      setClinicalLoading(false);
    }
  }, [canViewClinicalDocuments, patientId]);

  useEffect(() => {
    loadClinicalDocuments();
  }, [loadClinicalDocuments]);

  const loadPrescriptions = useCallback(async () => {
    if (!canViewPrescriptions) return;
    setPrescriptionLoading(true);
    setPrescriptionError(null);
    try {
      const response = await listPrescriptions(patientId);
      setPrescriptions(response.items);
    } catch (caught) {
      setPrescriptionError(caught instanceof Error ? caught.message : "No fue posible cargar recetas.");
    } finally {
      setPrescriptionLoading(false);
    }
  }, [canViewPrescriptions, patientId]);

  useEffect(() => {
    loadPrescriptions();
  }, [loadPrescriptions]);

  function openNewDocument() {
    setEditing(null);
    setForm(defaultClinicalDocumentForm(options));
    setFormOpen(true);
  }

  function openEditDocument(document: ClinicalDocument) {
    setEditing(document);
    setForm({
      site_id: document.site_id,
      dentist_profile_id: document.dentist_profile_id,
      document_type: document.document_type,
      title: document.title,
      recipient_name: document.recipient_name,
      recipient_entity: document.recipient_entity,
      recipient_specialty: document.recipient_specialty,
      subject: document.subject,
      body: document.body,
      clinical_date: document.clinical_date,
      related_treatment_id: document.related_treatment_id,
      related_evolution_id: document.related_evolution_id,
      related_appointment_id: document.related_appointment_id,
    });
    setFormOpen(true);
  }

  async function saveClinicalDocument(event: FormEvent) {
    event.preventDefault();
    try {
      if (editing) {
        await updateClinicalDocument(editing.id, { ...form, version: editing.version });
      } else {
        await createClinicalDocument(patientId, form);
      }
      setFormOpen(false);
      setEditing(null);
      await loadClinicalDocuments();
    } catch (caught) {
      setClinicalError(caught instanceof Error ? caught.message : "No fue posible guardar el documento.");
    }
  }

  async function previewDocument(document: ClinicalDocument) {
    try {
      const preview = await previewClinicalDocument(document.id);
      const binary = atob(preview.content_base64);
      const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
      const url = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (caught) {
      setClinicalError(caught instanceof Error ? caught.message : "No fue posible previsualizar.");
    }
  }

  async function finalizeDocument(document: ClinicalDocument) {
    if (!window.confirm("Finalizar este documento generará un PDF histórico inmutable. ¿Continuar?")) return;
    try {
      await finalizeClinicalDocument(document.id);
      await loadClinicalDocuments();
    } catch (caught) {
      setClinicalError(caught instanceof Error ? caught.message : "No fue posible finalizar el documento.");
    }
  }

  async function duplicateDocument(document: ClinicalDocument) {
    try {
      await duplicateClinicalDocument(document.id);
      await loadClinicalDocuments();
    } catch (caught) {
      setClinicalError(caught instanceof Error ? caught.message : "No fue posible duplicar el documento.");
    }
  }

  async function confirmVoidDocument(event: FormEvent) {
    event.preventDefault();
    if (!voiding) return;
    const reason = voidReason.trim();
    if (!reason || voidingBusy) return;
    setVoidingBusy(true);
    try {
      await voidClinicalDocument(voiding.id, reason);
      setVoiding(null);
      setVoidReason("");
      await loadClinicalDocuments();
    } catch (caught) {
      setClinicalError(caught instanceof Error ? caught.message : "No fue posible anular el documento.");
    } finally {
      setVoidingBusy(false);
    }
  }

  function openNewPrescription() {
    setEditingPrescription(null);
    setPrescriptionForm(defaultPrescriptionForm(options));
    setReviewedAlerts(false);
    setPrescriptionFormOpen(true);
  }

  function openEditPrescription(prescription: Prescription) {
    setEditingPrescription(prescription);
    setPrescriptionForm({
      site_id: prescription.site_id,
      dentist_profile_id: prescription.dentist_profile_id,
      clinical_date: prescription.clinical_date,
      related_treatment_id: prescription.related_treatment_id,
      related_evolution_id: prescription.related_evolution_id,
      related_appointment_id: prescription.related_appointment_id,
      general_instructions: prescription.general_instructions,
      notes: prescription.notes,
      items: prescription.items.map((item) => ({
        generic_name: item.generic_name,
        brand_name: item.brand_name,
        pharmaceutical_form: item.pharmaceutical_form,
        concentration: item.concentration,
        dose: item.dose,
        route: item.route,
        frequency: item.frequency,
        duration: item.duration,
        total_quantity: item.total_quantity,
        quantity_unit: item.quantity_unit,
        instructions: item.instructions,
      })),
    });
    setReviewedAlerts(prescription.allergies_reviewed);
    setPrescriptionFormOpen(true);
  }

  function updatePrescriptionItem(index: number, patch: Partial<PrescriptionItemInput>) {
    setPrescriptionForm((current) => ({
      ...current,
      items: current.items.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item,
      ),
    }));
  }

  function addPrescriptionItem() {
    setPrescriptionForm((current) => ({
      ...current,
      items: [...current.items, emptyPrescriptionItem()],
    }));
  }

  function removePrescriptionItem(index: number) {
    setPrescriptionForm((current) => ({
      ...current,
      items: current.items.filter((_, itemIndex) => itemIndex !== index),
    }));
  }

  async function savePrescription(event: FormEvent) {
    event.preventDefault();
    try {
      if (editingPrescription) {
        await updatePrescription(editingPrescription.id, { ...prescriptionForm, version: editingPrescription.version });
      } else {
        await createPrescription(patientId, prescriptionForm);
      }
      setPrescriptionFormOpen(false);
      setEditingPrescription(null);
      await loadPrescriptions();
    } catch (caught) {
      setPrescriptionError(caught instanceof Error ? caught.message : "No fue posible guardar la receta.");
    }
  }

  async function previewRx(prescription: Prescription) {
    try {
      const preview = await previewPrescription(prescription.id);
      const binary = atob(preview.content_base64);
      const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
      const url = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (caught) {
      setPrescriptionError(caught instanceof Error ? caught.message : "No fue posible previsualizar la receta.");
    }
  }

  async function finalizeRx(prescription: Prescription) {
    if (!window.confirm(prescriptionFinalizeMessage(prescription))) return;
    try {
      await finalizePrescription(prescription.id, true);
      await loadPrescriptions();
    } catch (caught) {
      setPrescriptionError(caught instanceof Error ? caught.message : "No fue posible finalizar la receta.");
    }
  }

  async function duplicateRx(prescription: Prescription) {
    try {
      await duplicatePrescription(prescription.id);
      await loadPrescriptions();
    } catch (caught) {
      setPrescriptionError(caught instanceof Error ? caught.message : "No fue posible duplicar la receta.");
    }
  }

  async function confirmVoidPrescription(event: FormEvent) {
    event.preventDefault();
    if (!voidingPrescription) return;
    const reason = prescriptionVoidReason.trim();
    if (!reason || prescriptionVoidingBusy) return;
    setPrescriptionVoidingBusy(true);
    try {
      await voidPrescription(voidingPrescription.id, reason);
      setVoidingPrescription(null);
      setPrescriptionVoidReason("");
      await loadPrescriptions();
    } catch (caught) {
      setPrescriptionError(caught instanceof Error ? caught.message : "No fue posible anular la receta.");
    } finally {
      setPrescriptionVoidingBusy(false);
    }
  }

  const generatedDocuments = [
    ...(canViewBudgets
      ? budgets.map((budget) => ({
          id: budget.id,
          type: "Presupuesto PDF",
          name: budget.number ?? `Presupuesto v${budget.version}`,
          date: budget.issued_at,
          action: () => downloadBlob(() => downloadBudgetPdf(budget.id), `presupuesto-${budget.number ?? budget.version}.pdf`),
        }))
      : []),
    ...(canViewPayments
      ? payments.map((payment) => ({
          id: payment.id,
          type: "Comprobante de pago",
          name: payment.receipt_number,
          date: payment.paid_at,
          action: () => downloadBlob(() => downloadPaymentReceipt(payment.id), `comprobante-${payment.receipt_number}.pdf`),
        }))
      : []),
  ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return (
    <WorkspacePanel
      title="Documentos del paciente"
      description="Documentos generados desde Dentia. Los informes clínicos se guardan como documentos históricos trazables."
      action={
        canCreateClinicalDocuments ? (
          <button
            type="button"
            onClick={openNewDocument}
            className="inline-flex min-h-10 items-center rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white"
          >
            Nuevo documento
          </button>
        ) : null
      }
    >
      {error && <Alert tone="error">{error}</Alert>}
      {clinicalError && <Alert tone="error">{clinicalError}</Alert>}

      <section className="space-y-3">
        <div>
          <h3 className="text-base font-black text-slate-950">Informes y documentos</h3>
          <p className="mt-1 text-sm text-slate-500">
            Remisiones, informes clínicos, certificados y cartas vinculadas al paciente.
          </p>
        </div>
        {clinicalLoading ? (
          <LoadingLine label="Cargando informes y documentos…" />
        ) : canViewClinicalDocuments ? (
          <ResponsiveTable
            empty="Este paciente aún no tiene informes o documentos clínicos."
            headings={["Tipo", "Número", "Fecha", "Asunto", "Profesional", "Estado", "Acciones"]}
            rows={clinicalDocuments.map((document) => [
              clinicalDocumentTypeLabel(document.document_type),
              document.document_number ?? "Borrador",
              formatDate(document.clinical_date),
              document.subject ?? document.title ?? "—",
              document.professional_name ?? "—",
              <StatusBadge key="status" value={clinicalDocumentStatusLabel(document.status)} />,
              <div key="actions" className="flex flex-wrap gap-3">
                {document.status === "DRAFT" && canEditClinicalDocuments && (
                  <button type="button" onClick={() => openEditDocument(document)} className="font-bold text-green-700 hover:underline">Editar</button>
                )}
                {document.status === "DRAFT" && (
                  <button type="button" onClick={() => previewDocument(document)} className="font-bold text-sky-700 hover:underline">Previsualizar</button>
                )}
                {document.status === "DRAFT" && canFinalizeClinicalDocuments && (
                  <button type="button" onClick={() => finalizeDocument(document)} className="font-bold text-orange-700 hover:underline">Finalizar</button>
                )}
                {document.status !== "DRAFT" && canDownloadClinicalDocuments && (
                  <button type="button" onClick={() => downloadBlob(() => downloadClinicalDocumentPdf(document.id), `${document.document_number ?? "documento"}.pdf`)} className="font-bold text-green-700 hover:underline">Descargar PDF</button>
                )}
                {document.status !== "DRAFT" && canCreateClinicalDocuments && (
                  <button type="button" onClick={() => duplicateDocument(document)} className="font-bold text-sky-700 hover:underline">Duplicar</button>
                )}
                {document.status === "FINALIZED" && canVoidClinicalDocuments && (
                  <button type="button" onClick={() => { setVoidReason(""); setVoiding(document); }} className="font-bold text-red-700 hover:underline">Anular documento</button>
                )}
              </div>,
            ])}
          />
        ) : (
          <Alert tone="info">No tienes permiso para ver informes clínicos narrativos.</Alert>
        )}
      </section>

      <section className="mt-6 space-y-3">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <h3 className="text-base font-black text-slate-950">Recetas</h3>
            <p className="mt-1 text-sm text-slate-500">
              Prescripciones odontológicas ordinarias con medicamentos estructurados y PDF histórico.
            </p>
          </div>
          {canCreatePrescriptions && (
            <button
              type="button"
              onClick={openNewPrescription}
              className="inline-flex min-h-10 items-center justify-center rounded-xl border border-green-200 bg-green-50 px-4 text-sm font-bold text-green-800"
            >
              Nueva receta
            </button>
          )}
        </div>
        <Alert tone="info">
          Dentia no sustituye recetarios oficiales ni sistemas regulatorios para medicamentos controlados. No calcula dosis ni recomienda medicamentos.
        </Alert>
        {prescriptionError && <Alert tone="error">{prescriptionError}</Alert>}
        {prescriptionLoading ? (
          <LoadingLine label="Cargando recetas…" />
        ) : canViewPrescriptions ? (
          <ResponsiveTable
            empty="Este paciente aún no tiene recetas."
            headings={["Número", "Fecha", "Medicamentos", "Profesional", "Estado", "Acciones"]}
            rows={prescriptions.map((prescription) => [
              prescription.prescription_number ?? "Borrador",
              formatDate(prescription.clinical_date),
              prescriptionMedicationSummary(prescription),
              prescription.professional_name ?? "—",
              <StatusBadge key="status" value={prescriptionStatusLabel(prescription.status)} />,
              <div key="actions" className="flex flex-wrap gap-3">
                {prescription.status === "DRAFT" && canEditPrescriptions && (
                  <button type="button" onClick={() => openEditPrescription(prescription)} className="font-bold text-green-700 hover:underline">Editar</button>
                )}
                {prescription.status === "DRAFT" && (
                  <button type="button" onClick={() => previewRx(prescription)} className="font-bold text-sky-700 hover:underline">Previsualizar</button>
                )}
                {prescription.status === "DRAFT" && canFinalizePrescriptions && (
                  <button type="button" onClick={() => finalizeRx(prescription)} className="font-bold text-orange-700 hover:underline">Finalizar</button>
                )}
                {prescription.status !== "DRAFT" && canDownloadPrescriptions && (
                  <button type="button" onClick={() => downloadBlob(() => downloadPrescriptionPdf(prescription.id), `${prescription.prescription_number ?? "receta"}.pdf`)} className="font-bold text-green-700 hover:underline">Descargar PDF</button>
                )}
                {prescription.status !== "DRAFT" && canCreatePrescriptions && (
                  <button type="button" onClick={() => duplicateRx(prescription)} className="font-bold text-sky-700 hover:underline">Duplicar</button>
                )}
                {prescription.status === "FINALIZED" && canVoidPrescriptions && (
                  <button type="button" onClick={() => { setPrescriptionVoidReason(""); setVoidingPrescription(prescription); }} className="font-bold text-red-700 hover:underline">Anular receta</button>
                )}
              </div>,
            ])}
          />
        ) : (
          <Alert tone="info">No tienes permiso para ver recetas.</Alert>
        )}
      </section>

      <section className="mt-6 space-y-3">
        <div>
          <h3 className="text-base font-black text-slate-950">Otros documentos generados</h3>
          <p className="mt-1 text-sm text-slate-500">Presupuestos y comprobantes emitidos desde módulos comerciales.</p>
        </div>
        {loading ? (
          <LoadingLine label="Cargando documentos…" />
        ) : (
          <ResponsiveTable
            empty="Este paciente aún no tiene presupuestos o comprobantes generados."
            headings={["Tipo", "Documento", "Fecha", "Acciones"]}
            rows={generatedDocuments.map((document) => [
              document.type,
              document.name,
              formatDate(document.date, true),
              <button
                key={document.id}
                type="button"
                onClick={document.action}
                className="text-sm font-bold text-green-700 hover:underline"
              >
                Descargar
              </button>,
            ])}
          />
        )}
      </section>

      <Modal
        open={formOpen}
        title={editing ? "Editar documento" : "Nuevo informe o documento"}
        onClose={() => setFormOpen(false)}
      >
        <form onSubmit={saveClinicalDocument} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Tipo</span>
              <select value={form.document_type} onChange={(event) => setForm((current) => ({ ...current, document_type: event.target.value as ClinicalDocumentType }))} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm">
                <option value="REFERRAL">Remisión</option>
                <option value="CLINICAL_REPORT">Informe clínico</option>
                <option value="CERTIFICATE">Certificado / constancia</option>
                <option value="GENERAL_LETTER">Carta general</option>
              </select>
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Fecha</span>
              <input type="date" value={form.clinical_date} onChange={(event) => setForm((current) => ({ ...current, clinical_date: event.target.value }))} className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm" required />
            </label>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Sede</span>
              <select value={form.site_id} onChange={(event) => setForm((current) => ({ ...current, site_id: event.target.value }))} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm" required>
                <option value="">Seleccionar sede</option>
                {options?.sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
              </select>
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Profesional firmante</span>
              <select value={form.dentist_profile_id ?? ""} onChange={(event) => setForm((current) => ({ ...current, dentist_profile_id: event.target.value || null }))} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm">
                <option value="">Mi perfil profesional</option>
                {options?.dentists.map((dentist) => <option key={dentist.id} value={dentist.id}>{dentist.name}</option>)}
              </select>
            </label>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Destinatario</span>
              <input value={form.recipient_name ?? ""} onChange={(event) => setForm((current) => ({ ...current, recipient_name: event.target.value }))} className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm" placeholder="Especialista o persona destinataria" />
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Especialidad</span>
              <input value={form.recipient_specialty ?? ""} onChange={(event) => setForm((current) => ({ ...current, recipient_specialty: event.target.value }))} className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm" placeholder="Endodoncia, rehabilitación…" />
            </label>
          </div>
          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Entidad / clínica</span>
            <input value={form.recipient_entity ?? ""} onChange={(event) => setForm((current) => ({ ...current, recipient_entity: event.target.value }))} className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm" />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Asunto</span>
            <input value={form.subject ?? ""} onChange={(event) => setForm((current) => ({ ...current, subject: event.target.value }))} className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm" placeholder="Remisión para valoración por endodoncia" />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Contenido del documento *</span>
            <textarea value={form.body} onChange={(event) => setForm((current) => ({ ...current, body: event.target.value }))} rows={9} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="Escriba el contenido del informe, remisión, certificado o carta." required />
          </label>
          <details className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <summary className="cursor-pointer text-sm font-black text-slate-700">Referencias clínicas opcionales</summary>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <label>
                <span className="mb-1 block text-xs font-bold text-slate-500">Tratamiento relacionado</span>
                <select value={form.related_treatment_id ?? ""} onChange={(event) => setForm((current) => ({ ...current, related_treatment_id: event.target.value || null }))} className="min-h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm">
                  <option value="">Sin referencia</option>
                  {treatments.map((treatment) => <option key={treatment.id} value={treatment.id}>{treatment.name}</option>)}
                </select>
              </label>
            </div>
          </details>
          <div className="flex flex-wrap justify-end gap-3">
            <button type="button" onClick={() => setFormOpen(false)} className="min-h-11 rounded-xl border border-slate-200 px-4 text-sm font-bold text-slate-600">Cancelar</button>
            <button className="min-h-11 rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white">Guardar borrador</button>
          </div>
        </form>
      </Modal>

      <Modal open={Boolean(voiding)} title="Anular documento" onClose={() => { if (!voidingBusy) setVoiding(null); }}>
        <form onSubmit={confirmVoidDocument} className="space-y-4">
          <p className="text-sm text-slate-600">Esta acción no elimina el PDF histórico ni consume un nuevo consecutivo. El documento quedará marcado como anulado.</p>
          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Motivo de anulación</span>
            <textarea value={voidReason} onChange={(event) => setVoidReason(event.target.value)} rows={4} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" required minLength={5} />
          </label>
          <div className="flex justify-end gap-3">
            <button type="button" disabled={voidingBusy} onClick={() => setVoiding(null)} className="min-h-11 rounded-xl border border-slate-200 px-4 text-sm font-bold text-slate-600 disabled:opacity-50">Cancelar</button>
            <button disabled={voidingBusy || voidReason.trim().length < 5} className="min-h-11 rounded-xl bg-red-600 px-4 text-sm font-bold text-white disabled:opacity-50">{voidingBusy ? "Anulando…" : "Confirmar anulación"}</button>
          </div>
        </form>
      </Modal>

      <Modal
        open={prescriptionFormOpen}
        title={editingPrescription ? "Editar receta" : "Nueva receta"}
        onClose={() => setPrescriptionFormOpen(false)}
      >
        <form onSubmit={savePrescription} className="space-y-4">
          <Alert tone="info">
            Revise alergias, medicamentos actuales y antecedentes del paciente antes de finalizar. Dentia no calcula dosis ni valida interacciones automáticamente.
          </Alert>
          <ClinicalAlertsSummary prescription={editingPrescription} />
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Fecha</span>
              <input type="date" value={prescriptionForm.clinical_date} onChange={(event) => setPrescriptionForm((current) => ({ ...current, clinical_date: event.target.value }))} className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm" required />
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Sede</span>
              <select value={prescriptionForm.site_id} onChange={(event) => setPrescriptionForm((current) => ({ ...current, site_id: event.target.value }))} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm" required>
                <option value="">Seleccionar sede</option>
                {options?.sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
              </select>
            </label>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Profesional firmante</span>
              <select value={prescriptionForm.dentist_profile_id ?? ""} onChange={(event) => setPrescriptionForm((current) => ({ ...current, dentist_profile_id: event.target.value || null }))} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm">
                <option value="">Mi perfil profesional</option>
                {options?.dentists.map((dentist) => <option key={dentist.id} value={dentist.id}>{dentist.name}</option>)}
              </select>
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Tratamiento relacionado</span>
              <select value={prescriptionForm.related_treatment_id ?? ""} onChange={(event) => setPrescriptionForm((current) => ({ ...current, related_treatment_id: event.target.value || null }))} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm">
                <option value="">Sin referencia</option>
                {treatments.map((treatment) => <option key={treatment.id} value={treatment.id}>{treatment.name}</option>)}
              </select>
            </label>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-black uppercase tracking-wide text-slate-500">Medicamentos</h4>
              <button type="button" onClick={addPrescriptionItem} className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-green-700">
                Agregar medicamento
              </button>
            </div>
            {prescriptionForm.items.map((item, index) => (
              <details key={index} open className="rounded-2xl border border-slate-200 bg-white p-4">
                <summary className="cursor-pointer text-sm font-black text-slate-900">
                  Medicamento {index + 1}: {item.generic_name || "Sin nombre"}
                </summary>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <InputField label="Nombre genérico / principio activo" value={item.generic_name} onChange={(value) => updatePrescriptionItem(index, { generic_name: value })} required />
                  <InputField label="Marca opcional" value={item.brand_name ?? ""} onChange={(value) => updatePrescriptionItem(index, { brand_name: value })} />
                  <InputField label="Forma" value={item.pharmaceutical_form} onChange={(value) => updatePrescriptionItem(index, { pharmaceutical_form: value })} required />
                  <InputField label="Concentración" value={item.concentration} onChange={(value) => updatePrescriptionItem(index, { concentration: value })} required />
                  <InputField label="Dosis" value={item.dose} onChange={(value) => updatePrescriptionItem(index, { dose: value })} required />
                  <InputField label="Vía" value={item.route} onChange={(value) => updatePrescriptionItem(index, { route: value })} required />
                  <InputField label="Frecuencia" value={item.frequency} onChange={(value) => updatePrescriptionItem(index, { frequency: value })} required />
                  <InputField label="Duración" value={item.duration} onChange={(value) => updatePrescriptionItem(index, { duration: value })} required />
                  <InputField label="Cantidad total" value={item.total_quantity} onChange={(value) => updatePrescriptionItem(index, { total_quantity: value })} required />
                  <InputField label="Unidad" value={item.quantity_unit ?? ""} onChange={(value) => updatePrescriptionItem(index, { quantity_unit: value })} />
                </div>
                <label className="mt-3 block">
                  <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Indicaciones</span>
                  <textarea value={item.instructions ?? ""} onChange={(event) => updatePrescriptionItem(index, { instructions: event.target.value })} rows={2} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
                </label>
                {prescriptionForm.items.length > 1 && (
                  <button type="button" onClick={() => removePrescriptionItem(index)} className="mt-3 text-sm font-bold text-red-700 hover:underline">
                    Retirar medicamento
                  </button>
                )}
              </details>
            ))}
          </div>
          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Indicaciones generales</span>
            <textarea value={prescriptionForm.general_instructions ?? ""} onChange={(event) => setPrescriptionForm((current) => ({ ...current, general_instructions: event.target.value }))} rows={3} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
          </label>
          <label className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            <input type="checkbox" className="mt-1" checked={reviewedAlerts} onChange={(event) => setReviewedAlerts(event.target.checked)} />
            <span>Confirmo que revisé alergias, medicamentos actuales y antecedentes relevantes antes de finalizar esta receta.</span>
          </label>
          <div className="flex flex-wrap justify-end gap-3">
            <button type="button" onClick={() => setPrescriptionFormOpen(false)} className="min-h-11 rounded-xl border border-slate-200 px-4 text-sm font-bold text-slate-600">Cancelar</button>
            <button className="min-h-11 rounded-xl bg-dentia-primary px-4 text-sm font-bold text-white">Guardar borrador</button>
          </div>
        </form>
      </Modal>

      <Modal open={Boolean(voidingPrescription)} title="Anular receta" onClose={() => { if (!prescriptionVoidingBusy) setVoidingPrescription(null); }}>
        <form onSubmit={confirmVoidPrescription} className="space-y-4">
          <p className="text-sm text-slate-600">Esta acción no elimina el PDF histórico ni consume un nuevo consecutivo. La receta quedará marcada como anulada.</p>
          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Motivo de anulación</span>
            <textarea value={prescriptionVoidReason} onChange={(event) => setPrescriptionVoidReason(event.target.value)} rows={4} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" required minLength={5} />
          </label>
          <div className="flex justify-end gap-3">
            <button type="button" disabled={prescriptionVoidingBusy} onClick={() => setVoidingPrescription(null)} className="min-h-11 rounded-xl border border-slate-200 px-4 text-sm font-bold text-slate-600 disabled:opacity-50">Cancelar</button>
            <button disabled={prescriptionVoidingBusy || prescriptionVoidReason.trim().length < 5} className="min-h-11 rounded-xl bg-red-600 px-4 text-sm font-bold text-white disabled:opacity-50">{prescriptionVoidingBusy ? "Anulando…" : "Confirmar anulación"}</button>
          </div>
        </form>
      </Modal>
    </WorkspacePanel>
  );
}

function defaultClinicalDocumentForm(options: AgendaOptions | null): ClinicalDocumentInput {
  return {
    site_id: options?.sites[0]?.id ?? "",
    dentist_profile_id: options?.dentists[0]?.id ?? null,
    document_type: "REFERRAL",
    title: null,
    recipient_name: "",
    recipient_entity: "",
    recipient_specialty: "",
    subject: "",
    body: "",
    clinical_date: localCalendarDate(),
    related_treatment_id: null,
    related_evolution_id: null,
    related_appointment_id: null,
  };
}

function emptyPrescriptionItem(): PrescriptionItemInput {
  return {
    generic_name: "",
    brand_name: "",
    pharmaceutical_form: "",
    concentration: "",
    dose: "",
    route: "Oral",
    frequency: "",
    duration: "",
    total_quantity: "",
    quantity_unit: "",
    instructions: "",
  };
}

function defaultPrescriptionForm(options: AgendaOptions | null): PrescriptionInput {
  return {
    site_id: options?.sites[0]?.id ?? "",
    dentist_profile_id: options?.dentists[0]?.id ?? null,
    clinical_date: localCalendarDate(),
    related_treatment_id: null,
    related_evolution_id: null,
    related_appointment_id: null,
    general_instructions: "",
    notes: "",
    items: [emptyPrescriptionItem()],
  };
}

function localCalendarDate(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function prescriptionStatusLabel(status: Prescription["status"]) {
  return {
    DRAFT: "Borrador",
    FINALIZED: "Finalizada",
    VOIDED: "Anulada",
  }[status];
}

function prescriptionMedicationSummary(prescription: Prescription) {
  if (!prescription.items.length) return "Sin medicamentos";
  return prescription.items
    .slice(0, 2)
    .map((item) => item.generic_name)
    .join(" + ") + (prescription.items.length > 2 ? ` + ${prescription.items.length - 2} más` : "");
}

function prescriptionFinalizeMessage(prescription: Prescription) {
  const allergies = prescription.clinical_alerts?.allergies ?? [];
  const medications = prescription.clinical_alerts?.active_medications ?? [];
  const allergyText = allergies.length
    ? allergies.map((item) => `- ${item.substance}${item.reaction ? ` (${item.reaction})` : ""}`).join("\n")
    : "- Sin alergias registradas";
  const medicationText = medications.length
    ? medications.map((item) => `- ${item.name}${item.dose ? ` ${item.dose}` : ""}${item.frequency ? ` · ${item.frequency}` : ""}`).join("\n")
    : "- Sin medicamentos activos registrados";
  return `Va a finalizar esta receta.\n\nMedicamentos:\n${prescription.items.map((item, index) => `${index + 1}. ${item.generic_name} ${item.concentration}`).join("\n") || "- Sin medicamentos"}\n\nAlergias:\n${allergyText}\n\nMedicamentos actuales:\n${medicationText}\n\nConfirma que revisó esta información clínica del paciente.`;
}

function InputField({
  label,
  value,
  onChange,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
}) {
  return (
    <label>
      <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm"
        required={required}
      />
    </label>
  );
}

function ClinicalAlertsSummary({ prescription }: { prescription: Prescription | null }) {
  const allergies = prescription?.clinical_alerts?.allergies ?? [];
  const medications = prescription?.clinical_alerts?.active_medications ?? [];
  if (!prescription) return null;
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
      <p className="font-black">Revisión clínica</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-black uppercase tracking-wide">Alergias registradas</p>
          {allergies.length ? (
            <ul className="mt-1 list-disc space-y-1 pl-5">
              {allergies.map((item, index) => (
                <li key={`${item.substance}-${index}`}>
                  {item.substance}
                  {item.reaction ? ` · ${item.reaction}` : ""}
                  {item.critical_alert ? " · crítica" : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1">Sin alergias registradas.</p>
          )}
        </div>
        <div>
          <p className="text-xs font-black uppercase tracking-wide">Medicamentos actuales</p>
          {medications.length ? (
            <ul className="mt-1 list-disc space-y-1 pl-5">
              {medications.map((item, index) => (
                <li key={`${item.name}-${index}`}>
                  {item.name}
                  {item.dose ? ` · ${item.dose}` : ""}
                  {item.frequency ? ` · ${item.frequency}` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1">Sin medicamentos activos registrados.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function clinicalDocumentTypeLabel(type: ClinicalDocumentType) {
  return {
    REFERRAL: "Remisión",
    CLINICAL_REPORT: "Informe clínico",
    CERTIFICATE: "Certificado / constancia",
    GENERAL_LETTER: "Carta general",
  }[type];
}

function clinicalDocumentStatusLabel(status: ClinicalDocument["status"]) {
  return {
    DRAFT: "Borrador",
    FINALIZED: "Finalizado",
    VOIDED: "Anulado",
  }[status];
}

function PatientFilesPlaceholder() {
  return (
    <WorkspacePanel
      title="Archivos clínicos"
      description="Espacio preparado para radiografías, fotografías, tomografías y documentos PDF clínicos."
    >
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <p className="text-lg font-black text-slate-900">Carga de archivos próximamente</p>
        <p className="mx-auto mt-2 max-w-2xl text-sm leading-6 text-slate-500">
          Esta sección queda reservada para futuras radiografías, fotografías clínicas,
          tomografías, consentimientos, certificados y documentos externos del paciente.
        </p>
      </div>
    </WorkspacePanel>
  );
}

function CreateTreatmentDialog({
  open,
  patientId,
  options,
  onClose,
  onCreated,
}: {
  open: boolean;
  patientId: string;
  options: AgendaOptions | null;
  onClose: () => void;
  onCreated: () => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [dentistId, setDentistId] = useState("");
  const [siteId, setSiteId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Ingresa el nombre del tratamiento.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createTreatment({
        patient_id: patientId,
        name: name.trim(),
        specialty: specialty.trim() || null,
        responsible_dentist_id: dentistId || null,
        main_site_id: siteId || null,
      });
      setName("");
      setSpecialty("");
      setDentistId("");
      setSiteId("");
      await onCreated();
    } catch {
      setError("No fue posible crear el tratamiento.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} title="Crear tratamiento para este paciente" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        {error && <Alert tone="error">{error}</Alert>}
        <label className="block">
          <span className="mb-1.5 block text-sm font-bold text-slate-700">Tratamiento</span>
          <input value={name} onChange={(event) => setName(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-sm font-bold text-slate-700">Especialidad</span>
          <input value={specialty} onChange={(event) => setSpecialty(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            <span className="mb-1.5 block text-sm font-bold text-slate-700">Odontólogo</span>
            <select value={dentistId} onChange={(event) => setDentistId(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3">
              <option value="">Sin asignar</option>
              {options?.dentists.map((dentist) => <option key={dentist.id} value={dentist.id}>{dentist.name}</option>)}
            </select>
          </label>
          <label>
            <span className="mb-1.5 block text-sm font-bold text-slate-700">Sede</span>
            <select value={siteId} onChange={(event) => setSiteId(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3">
              <option value="">Sin sede</option>
              {options?.sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
            </select>
          </label>
        </div>
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} className="min-h-10 rounded-xl border border-slate-300 px-4 font-bold text-slate-700">Cancelar</button>
          <button disabled={saving} className="min-h-10 rounded-xl bg-dentia-primary px-4 font-bold text-white disabled:opacity-60">
            {saving ? "Creando…" : "Crear tratamiento"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function CreatePatientPaymentDialog({
  open,
  treatments,
  options,
  selectedTreatmentId,
  procedures,
  proceduresLoading,
  onTreatmentChange,
  onClose,
  onCreated,
}: {
  open: boolean;
  treatments: TreatmentListItem[];
  options: AgendaOptions | null;
  selectedTreatmentId: string;
  procedures: Procedure[];
  proceduresLoading: boolean;
  onTreatmentChange: (value: string) => void;
  onClose: () => void;
  onCreated: () => Promise<void>;
}) {
  const [value, setValue] = useState("");
  const [method, setMethod] = useState("Efectivo");
  const [siteId, setSiteId] = useState("");
  const [dentistId, setDentistId] = useState("");
  const [reference, setReference] = useState("");
  const [observation, setObservation] = useState("");
  const [procedureIds, setProcedureIds] = useState<string[]>([]);
  const [receiptPayment, setReceiptPayment] = useState<Payment | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setProcedureIds(procedures.map((procedure) => procedure.id));
  }, [procedures]);

  useEffect(() => {
    const treatment = treatments.find((item) => item.id === selectedTreatmentId);
    setSiteId(treatment?.main_site_id ?? "");
    setDentistId(treatment?.responsible_dentist_id ?? "");
  }, [selectedTreatmentId, treatments]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selectedTreatmentId || !siteId || !value) {
      setError("Selecciona tratamiento, sede y valor.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payment = await createPayment(selectedTreatmentId, {
        site_id: siteId,
        dentist_id: dentistId || null,
        procedure_ids: procedureIds,
        paid_at: new Date().toISOString(),
        value,
        payment_method: method,
        reference: reference || null,
        observation: observation || null,
      });
      setReceiptPayment(payment);
      setValue("");
      setReference("");
      setObservation("");
      await onCreated();
    } catch (paymentError) {
      setError(
        paymentError instanceof ApiError
          ? paymentError.detail ?? paymentError.message
          : "No fue posible registrar el pago.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Modal open={open} title="Registrar pago del paciente" onClose={onClose}>
        <form onSubmit={submit} className="space-y-4">
          {error && <Alert tone="error">{error}</Alert>}
          <label className="block">
            <span className="mb-1.5 block text-sm font-bold text-slate-700">Tratamiento</span>
            <select value={selectedTreatmentId} onChange={(event) => onTreatmentChange(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3">
              <option value="">Selecciona tratamiento</option>
              {treatments.map((treatment) => <option key={treatment.id} value={treatment.id}>{treatment.name}</option>)}
            </select>
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-sm font-bold text-slate-700">Valor</span>
              <input value={value} onChange={(event) => setValue(event.target.value)} type="number" min="1" className="min-h-11 w-full rounded-xl border border-slate-300 px-3" />
            </label>
            <label>
              <span className="mb-1.5 block text-sm font-bold text-slate-700">Medio</span>
              <select value={method} onChange={(event) => setMethod(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3">
                {["Efectivo", "Transferencia", "Tarjeta", "Otro"].map((item) => <option key={item}>{item}</option>)}
              </select>
            </label>
            <label>
              <span className="mb-1.5 block text-sm font-bold text-slate-700">Sede</span>
              <select value={siteId} onChange={(event) => setSiteId(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3">
                <option value="">Selecciona sede</option>
                {options?.sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
              </select>
            </label>
            <label>
              <span className="mb-1.5 block text-sm font-bold text-slate-700">Odontólogo</span>
              <select value={dentistId} onChange={(event) => setDentistId(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3">
                <option value="">Sin odontólogo</option>
                {options?.dentists.map((dentist) => <option key={dentist.id} value={dentist.id}>{dentist.name}</option>)}
              </select>
            </label>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-sm font-bold text-slate-700">Referencia</span>
              <input value={reference} onChange={(event) => setReference(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" placeholder="Opcional" />
            </label>
            <label>
              <span className="mb-1.5 block text-sm font-bold text-slate-700">Observación</span>
              <input value={observation} onChange={(event) => setObservation(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-300 px-3" placeholder="Opcional" />
            </label>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-black uppercase tracking-wide text-slate-500">Procedimientos asociados</p>
            {proceduresLoading ? (
              <LoadingLine label="Cargando procedimientos…" />
            ) : (
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {procedures.map((procedure) => (
                  <label key={procedure.id} className="flex gap-2 rounded-xl border border-slate-200 bg-white p-3 text-sm">
                    <input
                      type="checkbox"
                      checked={procedureIds.includes(procedure.id)}
                      onChange={() => setProcedureIds((current) =>
                        current.includes(procedure.id)
                          ? current.filter((id) => id !== procedure.id)
                          : [...current, procedure.id],
                      )}
                    />
                    <span>
                      <span className="font-bold text-slate-900">{procedure.name}</span>
                      <span className="block text-xs text-slate-500">{procedure.scope_label}</span>
                    </span>
                  </label>
                ))}
                {!procedures.length && <p className="text-sm text-slate-500">Sin procedimientos disponibles.</p>}
              </div>
            )}
          </div>
          <div className="flex justify-end gap-3">
            <button type="button" onClick={onClose} className="min-h-10 rounded-xl border border-slate-300 px-4 font-bold text-slate-700">Cancelar</button>
            <button disabled={saving} className="min-h-10 rounded-xl bg-dentia-primary px-4 font-bold text-white disabled:opacity-60">
              {saving ? "Registrando…" : "Registrar pago"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={Boolean(receiptPayment)} title="Pago registrado correctamente" onClose={() => setReceiptPayment(null)}>
        <div className="space-y-4">
          <div className="rounded-2xl bg-green-50 p-4 text-green-900">
            <p className="text-lg font-black">✓ Pago registrado correctamente</p>
            <p className="mt-1 text-sm">Comprobante {receiptPayment?.receipt_number}</p>
          </div>
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => receiptPayment && downloadBlob(() => downloadPaymentReceipt(receiptPayment.id), `comprobante-${receiptPayment.receipt_number}.pdf`)}
              className="min-h-10 rounded-xl bg-dentia-primary px-4 font-bold text-white"
            >
              Descargar comprobante
            </button>
            <button type="button" onClick={() => setReceiptPayment(null)} className="min-h-10 rounded-xl border border-slate-300 px-4 font-bold text-slate-700">
              Cerrar
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}

function WorkspacePanel({
  title,
  description,
  action,
  children,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <h2 className="text-xl font-black text-slate-950">{title}</h2>
          {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function ResponsiveTable({
  headings,
  rows,
  empty,
}: {
  headings: string[];
  rows: React.ReactNode[][];
  empty: string;
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              {headings.map((heading) => (
                <th key={heading} className="px-5 py-3 text-left text-xs font-black uppercase tracking-wide text-slate-500">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row, index) => (
              <tr key={index} className="hover:bg-slate-50/70">
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="px-5 py-4 text-slate-700">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!rows.length && <p className="py-12 text-center text-sm text-slate-500">{empty}</p>}
    </div>
  );
}

function StatusBadge({ value }: { value: string }) {
  const tone = value === "Finalizado" || value === "Atendida" || value === "valido"
    ? "bg-green-50 text-green-700"
    : value === "Cancelado" || value === "Cancelada" || value === "reversado"
      ? "bg-red-50 text-red-700"
      : value === "Pausado" || value === "Pendiente de aprobación"
        ? "bg-amber-50 text-amber-800"
        : "bg-slate-100 text-slate-700";
  return <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${tone}`}>{value}</span>;
}

function MiniMetric({
  label,
  value,
  hint,
  tone = "slate",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "slate" | "green" | "amber" | "red";
}) {
  const colors = {
    slate: "border-slate-200 bg-white text-slate-900",
    green: "border-green-200 bg-green-50 text-green-800",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
    red: "border-red-200 bg-red-50 text-red-900",
  };
  return (
    <div className={`rounded-2xl border p-4 shadow-sm ${colors[tone]}`}>
      <p className="text-xs font-black uppercase tracking-wide opacity-70">{label}</p>
      <p className="mt-2 text-lg font-black">{value}</p>
      {hint && <p className="mt-1 text-xs opacity-70">{hint}</p>}
    </div>
  );
}

function MetricGroup({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-xs font-black uppercase tracking-[0.16em] text-slate-400">
        {title}
      </h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {children}
      </div>
    </section>
  );
}

function LoadingLine({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-10 text-slate-500">
      <Spinner className="h-5 w-5 text-dentia-primary" />
      {label}
    </div>
  );
}

function AccessCard({ title }: { title: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm font-bold text-slate-500">
      {title}
    </div>
  );
}

function treatmentName(treatments: TreatmentListItem[], treatmentId: string) {
  return treatments.find((treatment) => treatment.id === treatmentId)?.name ?? "Tratamiento";
}

async function downloadBlob(load: () => Promise<Blob>, filename: string) {
  const blob = await load();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function AppointmentFollowupDialog({
  appointment,
  followup,
  loading,
  message,
  onClose,
}: {
  appointment: PatientAppointment | null;
  followup: Followup | null;
  loading: boolean;
  message: string | null;
  onClose: () => void;
}) {
  return (
    <Modal open={Boolean(appointment)} title="Seguimiento de la cita" onClose={onClose}>
      <div className="space-y-5">
        {appointment && (
          <div className="rounded-2xl bg-slate-50 p-4 text-sm">
            <p className="font-bold text-slate-900">
              {formatDate(appointment.starts_at, true)} ·{" "}
              {appointment.appointment_type_name}
            </p>
            <p className="mt-1 text-slate-600">
              {appointment.dentist_name} · {appointment.site_name} ·{" "}
              {appointment.status}
            </p>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center gap-3 py-10 text-slate-500">
            <Spinner className="h-6 w-6 text-dentia-primary" />
            Cargando seguimiento…
          </div>
        )}

        {!loading && message && <Alert tone="info">{message}</Alert>}

        {!loading && followup && (
          <div className="space-y-5">
            <div className="grid gap-3 sm:grid-cols-2">
              <FollowupField label="Estado" value={followup.status} />
              <FollowupField
                label="Clasificación"
                value={followup.classification}
              />
              <FollowupField
                label="Control recomendado"
                value={formatDate(followup.followup_date)}
              />
              <FollowupField
                label="Contactar desde"
                value={formatDate(followup.contact_from)}
              />
              <FollowupField
                label="Último contacto"
                value={formatDate(followup.last_contact_at, true)}
              />
              <FollowupField
                label="Próximo contacto"
                value={formatDate(followup.next_contact_at, true)}
              />
              <FollowupField label="Odontólogo" value={followup.dentist_name} />
              <FollowupField label="Sede" value={followup.site_name} />
            </div>

            <section className="rounded-2xl border border-slate-200 p-4">
              <h3 className="font-bold text-slate-900">
                Motivo del seguimiento
              </h3>
              <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">
                {followup.reason}
              </p>
            </section>

            {followup.scheduled_appointment_id && (
              <Alert tone="info">
                Cita futura vinculada:{" "}
                {formatDate(followup.scheduled_appointment_at, true)}
              </Alert>
            )}

            {(followup.attention_description ||
              followup.prescribed_medications) && (
              <section className="rounded-2xl border border-slate-200 p-4">
                <h3 className="font-bold text-slate-900">
                  Resumen de atención
                </h3>
                {followup.attention_description && (
                  <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">
                    {followup.attention_description}
                  </p>
                )}
                {followup.prescribed_medications && (
                  <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">
                    <span className="font-bold">Medicamentos: </span>
                    {followup.prescribed_medications}
                  </p>
                )}
              </section>
            )}

            <section>
              <h3 className="font-bold text-slate-900">
                Historial de gestiones/contactos
              </h3>
              <div className="mt-3 space-y-3">
                {followup.managements.map((management) => (
                  <div
                    key={management.id}
                    className="rounded-xl border border-slate-200 p-3 text-sm"
                  >
                    <p className="font-bold text-slate-900">
                      {management.management_type} · {management.result}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      {formatDate(management.occurred_at, true)}
                    </p>
                    {management.observation && (
                      <p className="mt-2 whitespace-pre-wrap text-slate-700">
                        {management.observation}
                      </p>
                    )}
                    {management.next_contact_at && (
                      <p className="mt-2 text-xs font-bold text-slate-500">
                        Próximo contacto:{" "}
                        {formatDate(management.next_contact_at, true)}
                      </p>
                    )}
                  </div>
                ))}
                {!followup.managements.length && (
                  <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                    Sin gestiones registradas.
                  </p>
                )}
              </div>
            </section>
          </div>
        )}
      </div>
    </Modal>
  );
}

function FollowupField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}

function ResponsibleDialog({
  open,
  responsible,
  onClose,
  onSave,
}: {
  open: boolean;
  responsible: Responsible | null;
  onClose: () => void;
  onSave: (data: ResponsibleInput) => Promise<void>;
}) {
  const [name, setName] = useState(responsible?.name ?? "");
  const [relationship, setRelationship] = useState(
    responsible?.relationship ?? "",
  );
  const [documentType, setDocumentType] = useState(
    responsible?.document_type ?? "CC",
  );
  const [document, setDocument] = useState(responsible?.document ?? "");
  const [mobile, setMobile] = useState(responsible?.mobile ?? "");
  const [email, setEmail] = useState(responsible?.email ?? "");
  const [primary, setPrimary] = useState(responsible?.is_primary ?? false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(responsible?.name ?? "");
    setRelationship(responsible?.relationship ?? "");
    setDocumentType(responsible?.document_type ?? "CC");
    setDocument(responsible?.document ?? "");
    setMobile(responsible?.mobile ?? "");
    setEmail(responsible?.email ?? "");
    setPrimary(responsible?.is_primary ?? false);
    setError(null);
  }, [open, responsible]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSave({
        name,
        relationship,
        document_type: documentType,
        document: documentType === "Sin documento" ? null : document || null,
        mobile,
        email: email || null,
        is_primary: primary,
      });
    } catch (submitError) {
      setError(
        submitError instanceof ApiError
          ? submitError.detail ?? submitError.message
          : "No fue posible guardar el responsable.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={open}
      title={responsible ? "Editar responsable" : "Agregar responsable"}
      onClose={onClose}
    >
      <form onSubmit={submit} className="space-y-4">
        {error && <Alert tone="error">{error}</Alert>}
        <Input label="Nombre completo" value={name} onChange={setName} />
        <Input label="Parentesco" value={relationship} onChange={setRelationship} />
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Tipo de documento
            </span>
            <select
              value={documentType}
              onChange={(event) => setDocumentType(event.target.value)}
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
            >
              {["CC", "TI", "RC", "CE", "Pasaporte", "Otro", "Sin documento"].map(
                (type) => <option key={type}>{type}</option>,
              )}
            </select>
          </label>
          <Input
            label="Documento"
            value={document}
            onChange={setDocument}
            disabled={documentType === "Sin documento"}
          />
          <Input label="Celular" value={mobile} onChange={setMobile} />
          <Input label="Correo" value={email} onChange={setEmail} />
        </div>
        <label className="flex items-center gap-3 text-sm font-bold text-slate-700">
          <input
            type="checkbox"
            checked={primary}
            onChange={(event) => setPrimary(event.target.checked)}
            className="h-4 w-4 accent-green-600"
          />
          Responsable principal
        </label>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="min-h-11 rounded-xl border border-slate-300 px-4 font-bold"
          >
            Cancelar
          </button>
          <button
            disabled={busy}
            className="min-h-11 rounded-xl bg-dentia-primary px-5 font-bold text-white disabled:opacity-60"
          >
            Guardar
          </button>
        </div>
      </form>
    </Modal>
  );
}

function Input({
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
    <label>
      <span className="mb-2 block text-sm font-bold text-slate-700">{label}</span>
      <input
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full rounded-xl border border-slate-300 px-3 disabled:bg-slate-100"
      />
    </label>
  );
}
