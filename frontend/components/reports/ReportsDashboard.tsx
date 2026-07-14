"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { getAgendaOptions } from "@/services/agendaService";
import { getExecutiveSummary } from "@/services/reportService";
import type { AgendaOptions } from "@/types/agenda";
import type {
  ActionItems,
  ExecutiveSummary,
  ReportChartItem,
  ReportFilters,
  ReportMetric,
} from "@/types/report";

const PRESETS = [
  { value: "today", label: "Hoy" },
  { value: "yesterday", label: "Ayer" },
  { value: "week_current", label: "Semana actual" },
  { value: "month_current", label: "Mes actual" },
  { value: "month_previous", label: "Mes anterior" },
  { value: "year_current", label: "Año actual" },
  { value: "custom", label: "Rango personalizado" },
];

function money(value: string | number) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

function number(value: string | number) {
  return new Intl.NumberFormat("es-CO", {
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function localDateTime(value: string, timeZone = "America/Bogota") {
  return new Intl.DateTimeFormat("es-CO", {
    timeZone,
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function ReportsDashboard() {
  const [filters, setFilters] = useState<ReportFilters>({
    preset: "month_current",
  });
  const [draftFilters, setDraftFilters] = useState<ReportFilters>({
    preset: "month_current",
  });
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [options, setOptions] = useState<AgendaOptions | null>(null);
  const [tab, setTab] = useState("resumen");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [loadedSummary, loadedOptions] = await Promise.all([
        getExecutiveSummary(filters),
        getAgendaOptions(),
      ]);
      setSummary(loadedSummary);
      setOptions(loadedOptions);
    } catch {
      setError("No fue posible cargar el Centro de Reportes.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const visibleTabs = useMemo(() => {
    const tabs = [
      { id: "resumen", label: "Resumen", visible: true },
      { id: "agenda", label: "Agenda", visible: !!summary?.appointments },
      { id: "tratamientos", label: "Tratamientos", visible: !!summary?.treatments },
      { id: "finanzas", label: "Finanzas", visible: !!summary?.finance },
      { id: "seguimientos", label: "Seguimientos", visible: !!summary?.followups },
      { id: "clinica", label: "Actividad clínica", visible: !!summary?.clinical },
    ];
    return tabs.filter((item) => item.visible);
  }, [summary]);

  if (loading && !summary) {
    return (
      <div className="flex min-h-[420px] items-center justify-center gap-3 text-slate-500">
        <Spinner className="h-7 w-7 text-dentia-primary" />
        Cargando reportes…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
            Centro de Reportes
          </p>
          <h1 className="mt-2 text-3xl font-black text-slate-950">
            Dashboard Ejecutivo
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-500">
            Operación, actividad clínica, ingresos recibidos, producción,
            ventas aprobadas y cartera se muestran por separado.
          </p>
          {summary && (
            <p className="mt-2 text-xs font-semibold text-slate-400">
              Última actualización: {localDateTime(summary.generated_at, summary.timezone)} · Zona global: {summary.timezone}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={load}
          className="min-h-11 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50"
        >
          Actualizar
        </button>
      </header>

      {error && <Alert tone="error">{error}</Alert>}

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr_auto]">
          <FieldSelect
            label="Rango"
            value={draftFilters.preset}
            options={PRESETS}
            onChange={(value) => setDraftFilters((current) => ({ ...current, preset: value }))}
          />
          <FieldSelect
            label="Sede"
            value={draftFilters.site_id ?? ""}
            options={[
              { value: "", label: "Todas mis sedes" },
              ...(options?.sites.map((site) => ({ value: site.id, label: site.name })) ?? []),
            ]}
            onChange={(value) => setDraftFilters((current) => ({ ...current, site_id: value || undefined }))}
          />
          <FieldSelect
            label="Odontólogo"
            value={draftFilters.dentist_id ?? ""}
            options={[
              { value: "", label: "Todos" },
              ...(options?.dentists.map((dentist) => ({ value: dentist.id, label: dentist.name })) ?? []),
            ]}
            onChange={(value) => setDraftFilters((current) => ({ ...current, dentist_id: value || undefined }))}
          />
          <div className="flex items-end gap-2">
            <button
              type="button"
              onClick={() => setFilters(draftFilters)}
              className="min-h-11 rounded-xl bg-dentia-primary px-5 font-bold text-white hover:bg-green-700"
            >
              Aplicar
            </button>
            <button
              type="button"
              onClick={() => {
                const clean = { preset: "month_current" };
                setDraftFilters(clean);
                setFilters(clean);
              }}
              className="min-h-11 rounded-xl border border-slate-300 px-4 font-bold text-slate-700"
            >
              Limpiar
            </button>
          </div>
        </div>
        {draftFilters.preset === "custom" && (
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <FieldInput
              label="Desde"
              type="date"
              value={draftFilters.date_from ?? ""}
              onChange={(value) => setDraftFilters((current) => ({ ...current, date_from: value }))}
            />
            <FieldInput
              label="Hasta"
              type="date"
              value={draftFilters.date_to ?? ""}
              onChange={(value) => setDraftFilters((current) => ({ ...current, date_to: value }))}
            />
          </div>
        )}
      </section>

      {summary && (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {summary.metrics.slice(0, 12).map((metric) => (
              <MetricCard key={metric.key} metric={metric} />
            ))}
            {!summary.metrics.length && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
                No hay métricas disponibles para tus permisos.
              </div>
            )}
          </section>

          <nav className="flex flex-wrap gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
            {visibleTabs.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setTab(item.id)}
                className={`rounded-xl px-4 py-2 text-sm font-bold ${
                  tab === item.id
                    ? "bg-green-700 text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>

          {tab === "resumen" && <SummaryTab summary={summary} />}
          {tab === "agenda" && summary.appointments && (
            <AgendaTab summary={summary} />
          )}
          {tab === "tratamientos" && summary.treatments && (
            <TreatmentsTab summary={summary} />
          )}
          {tab === "finanzas" && summary.finance && (
            <FinanceTab summary={summary} />
          )}
          {tab === "seguimientos" && summary.followups && (
            <FollowupsTab summary={summary} />
          )}
          {tab === "clinica" && summary.clinical && (
            <ClinicalTab summary={summary} />
          )}
        </>
      )}
    </div>
  );
}

function MetricCard({ metric }: { metric: ReportMetric }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
        {metric.label}
      </p>
      <p className="mt-2 text-2xl font-black text-slate-950">
        {metric.unit === "money" ? money(metric.value) : number(metric.value)}
      </p>
      {metric.description && (
        <p className="mt-1 text-xs text-slate-500">{metric.description}</p>
      )}
    </article>
  );
}

function SummaryTab({ summary }: { summary: ExecutiveSummary }) {
  return (
    <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
      <div className="space-y-6">
        {summary.appointments && (
          <ChartCard title="Citas por estado" items={summary.appointments.by_status} />
        )}
        {summary.treatments && (
          <ChartCard title="Tratamientos por estado" items={summary.treatments.by_status} />
        )}
      </div>
      <ActionTables items={summary.action_items} financial={summary.permissions.financial} clinical={summary.permissions.clinical_aggregate} />
    </section>
  );
}

function AgendaTab({ summary }: { summary: ExecutiveSummary }) {
  const appointments = summary.appointments!;
  return (
    <section className="grid gap-6 xl:grid-cols-3">
      <StatsCard
        title="Agenda y atención"
        rows={[
          ["Citas creadas", appointments.created],
          ["Atendidas", appointments.attended],
          ["Confirmadas", appointments.confirmed],
          ["Canceladas", appointments.cancelled],
          ["No asistió", appointments.no_show],
          ["Sobrecupos", appointments.overbooked],
          ["Tasa de asistencia", `${appointments.attendance_rate}%`],
        ]}
      />
      <ChartCard title="Citas por estado" items={appointments.by_status} />
      <ChartCard title="Citas por odontólogo" items={appointments.by_dentist} />
    </section>
  );
}

function TreatmentsTab({ summary }: { summary: ExecutiveSummary }) {
  const treatments = summary.treatments!;
  return (
    <section className="grid gap-6 xl:grid-cols-3">
      <StatsCard
        title="Tratamientos"
        rows={[
          ["Activos", treatments.active],
          ["Aprobados", treatments.approved],
          ["En ejecución", treatments.in_progress],
          ["Pausados", treatments.paused],
          ["Finalizados", treatments.finalized],
          ["Con saldo", treatments.with_balance],
          ["Sin movimiento", treatments.without_movement],
          ["Avance promedio", `${treatments.average_progress}%`],
        ]}
      />
      <ChartCard title="Tratamientos por estado" items={treatments.by_status} />
      <ActionTables items={summary.action_items} financial={false} clinical={false} only="stale" />
    </section>
  );
}

function FinanceTab({ summary }: { summary: ExecutiveSummary }) {
  const finance = summary.finance!;
  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MiniMetric label="Ingresos rango" value={money(finance.income_range)} />
        <MiniMetric label="Producción clínica" value={money(finance.clinical_production_range)} />
        <MiniMetric label="Ventas aprobadas" value={money(finance.approved_sales_range)} />
        <MiniMetric label="Cartera" value={money(finance.receivables_total)} tone="orange" />
        <MiniMetric label="Pacientes con saldo" value={String(finance.patients_with_balance)} tone="orange" />
      </div>
      <div className="grid gap-6 xl:grid-cols-3">
        <ChartCard title="Ingresos por mes" items={finance.income_by_month} moneyValues />
        <ChartCard title="Cartera por antigüedad" items={finance.receivables_aging} moneyValues />
        <ChartCard title="Ingresos por medio de pago" items={finance.income_by_method} moneyValues />
      </div>
      <ActionTables items={summary.action_items} financial clinical={false} only="receivables" />
    </section>
  );
}

function FollowupsTab({ summary }: { summary: ExecutiveSummary }) {
  const followups = summary.followups!;
  return (
    <section className="grid gap-6 xl:grid-cols-3">
      <StatsCard
        title="Seguimientos"
        rows={[
          ["Abiertos", followups.open],
          ["Vencidos", followups.overdue],
          ["Programados", followups.scheduled],
          ["Completados", followups.completed],
          ["Con cita futura", followups.with_future_appointment],
        ]}
      />
      <ChartCard title="Seguimientos por motivo" items={followups.by_reason} />
      <ActionTables items={summary.action_items} financial={false} clinical={false} only="followups" />
    </section>
  );
}

function ClinicalTab({ summary }: { summary: ExecutiveSummary }) {
  const clinical = summary.clinical!;
  return (
    <section className="grid gap-6 xl:grid-cols-3">
      <StatsCard
        title="Actividad clínica"
        rows={[
          ["Procedimientos realizados", clinical.performed_procedures],
          ["Pacientes atendidos", clinical.attended_patients],
          ["Evoluciones creadas", clinical.evolutions_created],
          ["Evoluciones firmadas", clinical.evolutions_signed],
          ["Borradores", clinical.evolutions_draft],
          ["Historias/Fichas abiertas", clinical.clinical_records_opened],
          ["Pacientes con alertas", clinical.patients_with_critical_alerts],
        ]}
      />
      <ChartCard title="Procedimientos más realizados" items={clinical.top_procedures} />
      <ActionTables items={summary.action_items} financial={false} clinical only="drafts" />
    </section>
  );
}

function MiniMetric({
  label,
  value,
  tone = "green",
}: {
  label: string;
  value: string;
  tone?: "green" | "orange";
}) {
  return (
    <article className={`rounded-2xl border p-4 ${tone === "orange" ? "border-orange-100 bg-orange-50" : "border-green-100 bg-white"}`}>
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-black text-slate-950">{value}</p>
    </article>
  );
}

function StatsCard({ title, rows }: { title: string; rows: [string, string | number][] }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <dl className="mt-4 space-y-3">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-3 border-b border-slate-100 pb-2 text-sm last:border-0">
            <dt className="text-slate-500">{label}</dt>
            <dd className="font-black text-slate-900">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function ChartCard({
  title,
  items,
  moneyValues = false,
}: {
  title: string;
  items: ReportChartItem[];
  moneyValues?: boolean;
}) {
  const max = Math.max(...items.map((item) => Number(item.value || 0)), 0);
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <div className="mt-4 space-y-3">
        {items.filter((item) => Number(item.value) > 0).map((item) => {
          const width = max ? Math.max(8, (Number(item.value) / max) * 100) : 0;
          return (
            <div key={item.label}>
              <div className="mb-1 flex justify-between gap-3 text-xs font-bold text-slate-600">
                <span>{item.label}</span>
                <span>{moneyValues ? money(item.value) : number(item.value)}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-green-600"
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          );
        })}
        {!items.some((item) => Number(item.value) > 0) && (
          <p className="text-sm text-slate-500">Sin datos para este rango.</p>
        )}
      </div>
    </section>
  );
}

function ActionTables({
  items,
  financial,
  clinical,
  only,
}: {
  items: ActionItems | null;
  financial: boolean;
  clinical: boolean;
  only?: "followups" | "stale" | "receivables" | "drafts";
}) {
  if (!items) return null;
  return (
    <div className="space-y-6">
      {(!only || only === "followups") && (
        <TableCard
          title="Seguimientos vencidos"
          empty="No hay seguimientos vencidos."
          rows={items.overdue_followups.map((item) => ({
            key: item.followup_id,
            main: item.patient_name,
            detail: `${item.reason} · ${item.days_overdue} días vencido · ${item.site_name}`,
            href: "/seguimientos",
          }))}
        />
      )}
      {(!only || only === "stale") && (
        <TableCard
          title="Tratamientos sin movimiento"
          empty="No hay tratamientos sin movimiento."
          rows={items.stale_treatments.map((item) => ({
            key: item.treatment_id,
            main: item.treatment_name,
            detail: `${item.patient_name} · ${item.days_without_movement} días · saldo ${money(item.balance)}`,
            href: `/tratamientos/${item.treatment_id}`,
          }))}
        />
      )}
      {!only && (
        <TableCard
          title="Citas pendientes de confirmar"
          empty="No hay citas pendientes de confirmar."
          rows={items.pending_confirmations.map((item) => ({
            key: item.appointment_id,
            main: item.patient_name,
            detail: `${localDateTime(item.starts_at)} · ${item.site_name} · ${item.phone}`,
            href: "/agenda",
          }))}
        />
      )}
      {financial && (!only || only === "receivables") && (
        <TableCard
          title="Pacientes con cartera"
          empty="No hay cartera pendiente."
          rows={items.patient_receivables.map((item) => ({
            key: `${item.treatment_id}-${item.patient_id}`,
            main: item.patient_name,
            detail: `${item.treatment_name} · ${money(item.balance)} · ${item.aging_days} días`,
            href: `/tratamientos/${item.treatment_id}`,
          }))}
        />
      )}
      {clinical && (!only || only === "drafts") && (
        <TableCard
          title="Borradores clínicos pendientes"
          empty="No hay borradores clínicos pendientes."
          rows={items.clinical_drafts.map((item) => ({
            key: item.evolution_id,
            main: item.patient_name,
            detail: `${item.dentist_name} · ${item.days_in_draft} días en borrador`,
            href: `/pacientes/${item.patient_id}/historia-clinica`,
          }))}
        />
      )}
    </div>
  );
}

function TableCard({
  title,
  empty,
  rows,
}: {
  title: string;
  empty: string;
  rows: { key: string; main: string; detail: string; href: string }[];
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <div className="mt-4 divide-y divide-slate-100">
        {rows.map((row) => (
          <Link
            key={row.key}
            href={row.href}
            className="block py-3 text-sm hover:bg-slate-50"
          >
            <p className="font-black text-slate-900">{row.main}</p>
            <p className="mt-1 text-slate-500">{row.detail}</p>
          </Link>
        ))}
        {!rows.length && <p className="text-sm text-slate-500">{empty}</p>}
      </div>
    </section>
  );
}

function FieldSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value?: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label>
      <span className="mb-2 block text-xs font-bold uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <select
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function FieldInput({
  label,
  type,
  value,
  onChange,
}: {
  label: string;
  type: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      <span className="mb-2 block text-xs font-bold uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3"
      />
    </label>
  );
}
