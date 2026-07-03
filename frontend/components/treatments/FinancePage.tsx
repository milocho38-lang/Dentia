"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import {
  getFinanceByDentist,
  getFinanceBySite,
  getFinanceDashboard,
  getPatientBalances,
} from "@/services/treatmentService";
import type {
  FinanceBreakdownItem,
  FinanceDashboard,
  PatientBalanceItem,
} from "@/types/treatment";

function money(value: string | number) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export function FinancePage() {
  const [dashboard, setDashboard] = useState<FinanceDashboard | null>(null);
  const [bySite, setBySite] = useState<FinanceBreakdownItem[]>([]);
  const [byDentist, setByDentist] = useState<FinanceBreakdownItem[]>([]);
  const [balances, setBalances] = useState<PatientBalanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getFinanceDashboard(),
      getFinanceBySite(),
      getFinanceByDentist(),
      getPatientBalances(),
    ])
      .then(([loadedDashboard, loadedSites, loadedDentists, loadedBalances]) => {
        setDashboard(loadedDashboard);
        setBySite(loadedSites);
        setByDentist(loadedDentists);
        setBalances(loadedBalances);
      })
      .catch(() => setError("No fue posible cargar el dashboard económico."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-7 w-7 text-dentia-primary" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
            Gestión económica
          </p>
          <h1 className="mt-2 text-3xl font-black text-slate-950">Finanzas</h1>
          <p className="mt-2 text-sm text-slate-500">
            Ingresos reales, cartera y resumen por sede/odontólogo.
          </p>
        </div>
        <Link
          href="/tratamientos"
          className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50"
        >
          Ver tratamientos
        </Link>
      </header>

      {error && <Alert tone="error">{error}</Alert>}

      {dashboard && (
        <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
          <Metric label="Hoy" value={money(dashboard.income_today)} />
          <Metric label="Mes" value={money(dashboard.income_month)} />
          <Metric label="Año" value={money(dashboard.income_year)} />
          <Metric label="Pendiente" value={money(dashboard.receivables_total)} tone="orange" />
          <Metric label="Tratamientos activos" value={String(dashboard.active_treatments)} />
          <Metric label="Ticket promedio" value={money(dashboard.average_ticket)} />
        </section>
      )}

      <section className="grid gap-6 lg:grid-cols-3">
        <Breakdown title="Ingresos por sede" items={bySite} />
        <Breakdown title="Ingresos por odontólogo" items={byDentist} />
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-black text-slate-950">Pacientes con saldo</h2>
          <div className="mt-4 space-y-3">
            {balances.map((item) => (
              <div key={item.patient_id} className="flex justify-between gap-3 rounded-xl bg-slate-50 p-3 text-sm">
                <span className="font-bold text-slate-800">{item.patient_name}</span>
                <span className="font-black text-orange-700">{money(item.balance)}</span>
              </div>
            ))}
            {!balances.length && (
              <p className="text-sm text-slate-500">No hay cartera pendiente.</p>
            )}
          </div>
        </section>
      </section>
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "green",
}: {
  label: string;
  value: string;
  tone?: "green" | "orange";
}) {
  return (
    <div className={`rounded-2xl border p-5 shadow-sm ${tone === "orange" ? "border-orange-100 bg-orange-50" : "border-green-100 bg-white"}`}>
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-black text-slate-950">{value}</p>
    </div>
  );
}

function Breakdown({ title, items }: { title: string; items: FinanceBreakdownItem[] }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <div className="mt-4 space-y-3">
        {items.map((item, index) => (
          <div key={`${item.id ?? index}-${item.name}`} className="flex justify-between gap-3 rounded-xl bg-slate-50 p-3 text-sm">
            <span className="font-bold text-slate-800">{item.name}</span>
            <span className="font-black text-green-700">{money(item.value)}</span>
          </div>
        ))}
        {!items.length && <p className="text-sm text-slate-500">Sin datos todavía.</p>}
      </div>
    </section>
  );
}
