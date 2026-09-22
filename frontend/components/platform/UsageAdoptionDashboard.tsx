"use client";

import { useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import {
  hasOrthodonticActivity,
  hasUsageActivity,
  isPeriodComplete,
  managedAppointments,
} from "@/lib/usageAdoptionView.mjs";
import {
  getUsageContext,
  getUserUsageAdoption,
} from "@/services/usageAdoptionService";
import type {
  UsageAdoptionResponse,
  UsageContextCompany,
  UsagePeriodMode,
  UsageWeeklyTrendItem,
} from "@/types/usageAdoption";

const periodOptions: Array<{ value: UsagePeriodMode; label: string }> = [
  { value: "last_7_days", label: "Últimos 7 días" },
  { value: "last_30_days", label: "Últimos 30 días" },
  { value: "pilot_to_date", label: "Desde inicio del piloto" },
  { value: "custom", label: "Personalizado" },
];

const trendOptions: Array<{
  key: keyof Omit<UsageWeeklyTrendItem, "week_start">;
  label: string;
}> = [
  { key: "appointments_activity", label: "Actividad en Agenda" },
  { key: "unique_patients", label: "Pacientes únicos" },
  { key: "evolutions_signed", label: "Evoluciones firmadas" },
  { key: "treatments_created", label: "Tratamientos" },
  { key: "consents_created", label: "Consentimientos" },
  { key: "orthodontic_activity", label: "Ortodoncia" },
];

function dateForTimezone(timezone: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

function formatLocalDateTime(value: string | null, timezone: string) {
  if (!value) return "Sin actividad";
  return new Intl.DateTimeFormat("es-CO", {
    timeZone: timezone,
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatShortDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", {
    day: "numeric",
    month: "short",
  }).format(new Date(`${value}T12:00:00Z`));
}

export function UsageAdoptionDashboard() {
  const [companies, setCompanies] = useState<UsageContextCompany[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [userId, setUserId] = useState("");
  const [siteId, setSiteId] = useState("");
  const [periodMode, setPeriodMode] = useState<UsagePeriodMode>("last_30_days");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [contextLoading, setContextLoading] = useState(true);
  const [companyLoading, setCompanyLoading] = useState(false);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const [report, setReport] = useState<UsageAdoptionResponse | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setContextLoading(true);
    getUsageContext(undefined, controller.signal)
      .then((response) => setCompanies(response.companies))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setContextError("No fue posible cargar el contexto de uso y adopción.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setContextLoading(false);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!companyId) return;
    const controller = new AbortController();
    setCompanyLoading(true);
    setContextError(null);
    getUsageContext(companyId, controller.signal)
      .then((response) => {
        const selected = response.companies.find((item) => item.id === companyId);
        if (selected) {
          setCompanies((current) =>
            current.map((item) => (item.id === selected.id ? selected : item)),
          );
        }
      })
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setContextError("No fue posible cargar los usuarios de la empresa.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setCompanyLoading(false);
      });
    return () => controller.abort();
  }, [companyId]);

  const company = useMemo(
    () => companies.find((item) => item.id === companyId) ?? null,
    [companies, companyId],
  );
  const user = useMemo(
    () => company?.users.find((item) => item.id === userId) ?? null,
    [company, userId],
  );
  const periodReady = isPeriodComplete(periodMode, startDate, endDate);

  useEffect(() => {
    if (!company || !user || !periodReady) {
      setReport(null);
      setMetricsError(null);
      return;
    }
    const controller = new AbortController();
    setMetricsLoading(true);
    setMetricsError(null);
    getUserUsageAdoption(
      {
        companyId: company.id,
        userId: user.id,
        dentistId: user.dentist?.id,
        siteId: siteId || undefined,
        periodMode,
        startDate: startDate || undefined,
        endDate:
          endDate ||
          (periodMode === "pilot_to_date"
            ? dateForTimezone(company.timezone)
            : undefined),
      },
      controller.signal,
    )
      .then(setReport)
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setReport(null);
          setMetricsError("No fue posible cargar las métricas para estos filtros.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setMetricsLoading(false);
      });
    return () => controller.abort();
  }, [company, endDate, periodMode, periodReady, siteId, startDate, user]);

  function changeCompany(value: string) {
    setCompanyId(value);
    setUserId("");
    setSiteId("");
    setReport(null);
  }

  return (
    <div className="mx-auto max-w-7xl pb-10">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
          Plataforma
        </p>
        <h1 className="mt-2 text-3xl font-black text-slate-950">Uso y adopción</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
          Actividad atribuible de usuarios piloto. Estas métricas describen uso del
          producto; no califican desempeño clínico ni comparan profesionales.
        </p>
      </header>

      <section
        aria-label="Filtros de uso y adopción"
        className="mt-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        {contextError && <Alert tone="error">{contextError}</Alert>}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <FilterSelect
            label="Empresa"
            value={companyId}
            disabled={contextLoading}
            onChange={changeCompany}
          >
            <option value="">{contextLoading ? "Cargando empresas…" : "Selecciona una empresa"}</option>
            {companies.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}{item.is_active ? "" : " · Inactiva"}
              </option>
            ))}
          </FilterSelect>

          <FilterSelect
            label="Usuario / odontólogo"
            value={userId}
            disabled={!company || companyLoading}
            onChange={(value) => {
              setUserId(value);
              setReport(null);
            }}
          >
            <option value="">{companyLoading ? "Cargando usuarios…" : "Selecciona un usuario"}</option>
            {company?.users.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name} · {item.role_names.join(", ") || "Sin rol"}
                {item.dentist ? " · Odontólogo" : ""}
                {item.is_active ? "" : " · Inactivo"}
              </option>
            ))}
          </FilterSelect>

          <FilterSelect
            label="Sede"
            value={siteId}
            disabled={!company}
            onChange={setSiteId}
          >
            <option value="">Todas las sedes</option>
            {company?.sites.map((site) => (
              <option key={site.id} value={site.id} disabled={!site.is_active}>
                {site.name}{site.is_active ? "" : " · Inactiva"}
              </option>
            ))}
          </FilterSelect>

          <FilterSelect
            label="Periodo"
            value={periodMode}
            onChange={(value) => {
              setPeriodMode(value as UsagePeriodMode);
              setReport(null);
            }}
          >
            {periodOptions.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </FilterSelect>
        </div>

        {(periodMode === "pilot_to_date" || periodMode === "custom") && (
          <div className="mt-4 grid gap-4 border-t border-slate-100 pt-4 sm:grid-cols-2 xl:max-w-2xl">
            <DateField
              label={periodMode === "pilot_to_date" ? "Inicio del piloto" : "Desde"}
              value={startDate}
              onChange={setStartDate}
            />
            {periodMode === "custom" && (
              <DateField label="Hasta" value={endDate} onChange={setEndDate} />
            )}
            {periodMode === "pilot_to_date" && !startDate && (
              <p className="self-end pb-3 text-xs leading-5 text-amber-700">
                Indica la fecha real de inicio. Dentia no la infiere sin una fuente fiable.
              </p>
            )}
          </div>
        )}

        {user && (
          <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4 text-xs">
            <ContextBadge>{user.status}</ContextBadge>
            {user.role_names.map((role) => <ContextBadge key={role}>{role}</ContextBadge>)}
            {user.dentist && <ContextBadge>Perfil odontológico: {user.dentist.status}</ContextBadge>}
            {company && <ContextBadge>Zona horaria: {company.timezone}</ContextBadge>}
          </div>
        )}
      </section>

      {!company || !user ? (
        <InitialState />
      ) : !periodReady ? (
        <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
          Completa el periodo para consultar las métricas.
        </div>
      ) : metricsLoading ? (
        <DashboardSkeleton />
      ) : metricsError ? (
        <div className="mt-6"><Alert tone="error">{metricsError}</Alert></div>
      ) : report ? (
        <UsageReport report={report} userName={user.name} />
      ) : null}
    </div>
  );
}

function UsageReport({ report, userName }: { report: UsageAdoptionResponse; userName: string }) {
  const hasActivity = hasUsageActivity(report);
  const orthoActivity = hasOrthodonticActivity(report.orthodontics);
  const timezone = report.period.timezone;
  const cards = [
    { label: "Última actividad", value: formatLocalDateTime(report.general.last_activity_at, timezone), compact: true },
    { label: "Días activos", value: report.general.active_days },
    { label: "Citas gestionadas", value: managedAppointments(report.agenda) },
    { label: "Pacientes únicos con actividad", value: report.patients.unique_patients_with_actor_activity },
    { label: "Evoluciones firmadas", value: report.clinical.clinical_evolutions_signed },
    { label: "Tratamientos creados", value: report.treatments.treatments_created },
  ];

  return (
    <div className="mt-6 space-y-6">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-bold text-slate-900">{userName}</p>
          <p className="mt-1 text-xs text-slate-500">
            {report.period.start_date} — {report.period.end_date} · {timezone}
          </p>
        </div>
        <p className="text-xs text-slate-400">Catálogo {report.metric_catalog_version}</p>
      </div>

      {!hasActivity && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
          <p className="font-bold text-slate-900">Sin actividad en el periodo</p>
          <p className="mt-2 text-sm text-slate-500">
            No se registró actividad de Dentia para este usuario en el periodo seleccionado.
          </p>
        </div>
      )}

      <section aria-label="Resumen de actividad" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        {cards.map((card) => (
          <SummaryCard key={card.label} {...card} />
        ))}
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        <MetricSection
          title="Agenda"
          description={report.agenda.appointment_active_days
            ? `Agenda registra actividad en ${report.agenda.appointment_active_days} días del periodo.`
            : "Sin actividad en Agenda durante este periodo."}
          metrics={[
            ["Citas creadas", report.agenda.appointments_created],
            ["Confirmadas", report.agenda.appointments_confirmed_by_actor],
            ["Reprogramadas", report.agenda.appointments_rescheduled_by_actor],
            ["Completadas", report.agenda.appointments_completed_by_actor],
            ["Canceladas", report.agenda.appointments_cancelled_by_actor],
            ["Días activos", report.agenda.appointment_active_days],
            ["Pacientes únicos", report.agenda.unique_patients_with_appointment_activity],
          ]}
        />
        <MetricSection
          title="Pacientes"
          description="Actividad agregada; no se muestran pacientes ni identificadores."
          metrics={[
            ["Pacientes creados", report.patients.patients_created_by_actor],
            ["Pacientes únicos con actividad", report.patients.unique_patients_with_actor_activity],
          ]}
        />
        <MetricSection
          title="Historia clínica"
          description={report.clinical.clinical_evolutions_created
            ? "Actividad clínica atribuida al profesional seleccionado."
            : "Sin actividad en Historia clínica durante este periodo."}
          metrics={[
            ["Historias abiertas", report.clinical.clinical_records_opened],
            ["Evoluciones creadas", report.clinical.clinical_evolutions_created],
            ["Evoluciones firmadas", report.clinical.clinical_evolutions_signed],
            ["Addenda", report.clinical.addenda_created],
            ["Borradores actuales creados", report.clinical.current_drafts_created_in_period],
            ["Pacientes únicos", report.clinical.unique_patients_with_clinical_activity],
          ]}
        />
        <MetricSection
          title="Tratamientos"
          description={report.treatments.treatments_created
            ? "Creación y avance de tratamientos, sin información financiera."
            : "Sin actividad en Tratamientos durante este periodo."}
          metrics={[
            ["Tratamientos creados", report.treatments.treatments_created],
            ["Procedimientos registrados", report.treatments.treatment_procedures_registered],
            ["Tratamientos completados", report.treatments.treatments_completed_by_actor],
            ["Presupuestos creados", report.treatments.budgets_created],
            ["Versiones de presupuesto", report.treatments.budget_versions_created],
            ["Presupuestos aceptados", report.treatments.budgets_accepted_by_actor],
            ["Pacientes únicos", report.treatments.unique_patients_with_treatment_activity],
          ]}
        />
        <MetricSection
          title="Consentimientos"
          description={report.consents.consents_created
            ? "Estados agregados del flujo de consentimiento."
            : "Sin actividad en Consentimientos durante este periodo."}
          metrics={[
            ["Generados", report.consents.consents_created],
            ["Enviados o compartidos", report.consents.consents_shared],
            ["Aceptados", report.consents.consents_accepted],
            ["Pendientes", report.consents.consents_pending],
            ["Pacientes únicos", report.consents.unique_patients_with_consent_activity],
          ]}
        />
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <SectionHeader title="Ortodoncia" description="Actividad agregada del módulo especializado." />
          {!report.orthodontics_enabled && !orthoActivity ? (
            <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              <p className="font-bold text-slate-800">Ortodoncia no habilitada</p>
              <p className="mt-1">La empresa no tiene un entitlement activo para este módulo.</p>
            </div>
          ) : (
            <MetricGrid metrics={[
              ["Casos creados", report.orthodontics.orthodontic_cases_created],
              ["Casos activos", report.orthodontics.orthodontic_cases_active],
              ["Evoluciones creadas", report.orthodontics.orthodontic_evolutions_created],
              ["Evoluciones firmadas", report.orthodontics.orthodontic_evolutions_signed],
              ["Fichas finalizadas", report.orthodontics.orthodontic_records_finalized],
              ["Pacientes únicos", report.orthodontics.unique_patients_with_orthodontic_activity],
            ]} />
          )}
        </section>
      </div>

      <WeeklyTrend data={report.weekly_trend} />

      <section className="rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
        <SectionHeader
          title="Actividad administrativa"
          description="Separada de la adopción clínica. No incluye montos."
        />
        <MetricGrid metrics={[
          ["Pagos registrados", report.administrative_activity.payments_registered],
          ["Reversos", report.administrative_activity.payments_reversed],
        ]} />
      </section>

      <section className="rounded-2xl border border-dashed border-slate-300 bg-white p-5">
        <SectionHeader
          title="Métricas aún no atribuibles"
          description="Dentia muestra explícitamente lo que todavía no puede medir con precisión."
        />
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {report.unsupported_metrics.map((metric) => (
            <div key={metric.code} className="rounded-xl bg-slate-50 p-4">
              <p className="text-sm font-bold text-slate-700">No disponible</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">{metric.reason}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function WeeklyTrend({ data }: { data: UsageWeeklyTrendItem[] }) {
  const [metric, setMetric] = useState<keyof Omit<UsageWeeklyTrendItem, "week_start">>("appointments_activity");
  const selected = trendOptions.find((item) => item.key === metric) ?? trendOptions[0];
  const values = data.map((item) => item[metric] as number);
  const maximum = Math.max(...values, 1);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <SectionHeader title="Tendencia semanal" description="Una serie a la vez para facilitar la lectura." />
        <label className="sm:w-64">
          <span className="sr-only">Métrica de tendencia</span>
          <select
            value={metric}
            onChange={(event) => setMetric(event.target.value as typeof metric)}
            className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold"
          >
            {trendOptions.map((option) => <option key={option.key} value={option.key}>{option.label}</option>)}
          </select>
        </label>
      </div>
      <div className="mt-5 overflow-x-auto" role="img" aria-label={`Tendencia semanal: ${selected.label}`}>
        <div className="flex min-w-[620px] items-end gap-3 border-b border-slate-200 px-2 pt-6">
          {data.map((item) => {
            const value = item[metric] as number;
            return (
              <div key={item.week_start} className="flex min-w-16 flex-1 flex-col items-center justify-end">
                <span className="mb-2 text-xs font-black text-slate-700">{value}</span>
                <div
                  className="w-full max-w-14 rounded-t-lg bg-green-500 transition-[height]"
                  style={{ height: `${Math.max((value / maximum) * 150, value ? 10 : 2)}px` }}
                />
                <span className="my-2 text-[11px] text-slate-500">{formatShortDate(item.week_start)}</span>
              </div>
            );
          })}
        </div>
        {!data.length && <p className="py-10 text-center text-sm text-slate-500">Sin semanas dentro del periodo.</p>}
      </div>
    </section>
  );
}

function MetricSection({ title, description, metrics }: { title: string; description: string; metrics: Array<[string, number]> }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <SectionHeader title={title} description={description} />
      <MetricGrid metrics={metrics} />
    </section>
  );
}

function SectionHeader({ title, description }: { title: string; description: string }) {
  return <div><h2 className="text-lg font-black text-slate-950">{title}</h2><p className="mt-1 text-xs leading-5 text-slate-500">{description}</p></div>;
}

function MetricGrid({ metrics }: { metrics: Array<[string, number]> }) {
  return (
    <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
      {metrics.map(([label, value]) => (
        <div key={label} className="rounded-xl bg-slate-50 p-3">
          <dt className="text-xs leading-4 text-slate-500">{label}</dt>
          <dd className="mt-1 text-xl font-black text-slate-900">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function SummaryCard({ label, value, compact = false }: { label: string; value: string | number; compact?: boolean }) {
  return (
    <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-bold leading-4 text-slate-500">{label}</p>
      <p className={`mt-2 font-black text-slate-950 ${compact ? "break-words text-sm leading-5" : "text-3xl"}`}>{value}</p>
    </div>
  );
}

function InitialState() {
  return (
    <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-14 text-center">
      <p className="font-black text-slate-900">Selecciona una empresa y un usuario</p>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
        Dentia no carga métricas hasta tener un contexto válido. Los resultados son agregados y no contienen información clínica de pacientes.
      </p>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="mt-6 space-y-5" aria-label="Cargando métricas">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, index) => <div key={index} className="h-28 animate-pulse rounded-2xl bg-slate-200" />)}
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-64 animate-pulse rounded-2xl bg-slate-200" />)}
      </div>
    </div>
  );
}

function FilterSelect({ label, value, disabled = false, onChange, children }: { label: string; value: string; disabled?: boolean; onChange: (value: string) => void; children: React.ReactNode }) {
  return (
    <label>
      <span className="mb-1 block text-xs font-bold text-slate-600">{label}</span>
      <select value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm disabled:bg-slate-100 disabled:text-slate-400">{children}</select>
    </label>
  );
}

function DateField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label><span className="mb-1 block text-xs font-bold text-slate-600">{label}</span><input type="date" value={value} onChange={(event) => onChange(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-200 px-3 text-sm" /></label>;
}

function ContextBadge({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full bg-slate-100 px-3 py-1.5 font-bold text-slate-600">{children}</span>;
}
