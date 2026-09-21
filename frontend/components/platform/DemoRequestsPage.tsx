"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import {
  listDemoRequestOwners,
  listDemoRequests,
} from "@/services/demoRequestService";
import type {
  DemoRequestFilters,
  DemoRequestListItem,
  DemoRequestOwner,
  DemoRequestStatus,
} from "@/types/demoRequest";

export const DEMO_STATUS_LABELS: Record<DemoRequestStatus, string> = {
  NEW: "Nuevo",
  CONTACTED: "Contactado",
  DEMO_SCHEDULED: "Demo agendada",
  DEMO_COMPLETED: "Demo realizada",
  CONVERTED: "Convertido",
  NOT_CONTINUING: "No continúa",
};

export const PRACTICE_LABELS: Record<string, string> = {
  INDEPENDENT_DENTIST: "Odontólogo independiente",
  DENTAL_OFFICE: "Consultorio odontológico",
  DENTAL_CLINIC: "Clínica odontológica",
};

export function formatDemoDate(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

const emptyFilters: DemoRequestFilters = {
  search: "",
  status: "",
  country: "",
  assigned_to_user_id: "",
  created_from: "",
  created_to: "",
};

export function DemoRequestsPage() {
  const [items, setItems] = useState<DemoRequestListItem[]>([]);
  const [owners, setOwners] = useState<DemoRequestOwner[]>([]);
  const [filters, setFilters] = useState<DemoRequestFilters>(emptyFilters);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(activeFilters = filters) {
    setLoading(true);
    setError(null);
    try {
      const [requests, ownerResponse] = await Promise.all([
        listDemoRequests(activeFilters),
        listDemoRequestOwners(),
      ]);
      setItems(requests.items);
      setOwners(ownerResponse.items);
    } catch {
      setError("No fue posible cargar las solicitudes de demo.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(emptyFilters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submit(event: FormEvent) {
    event.preventDefault();
    load();
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
          Administración
        </p>
        <h1 className="mt-2 text-3xl font-black text-slate-950">Solicitudes de demo</h1>
        <p className="mt-2 text-sm text-slate-500">
          Seguimiento comercial de solicitudes recibidas desde dentiapro.com.
        </p>
      </header>

      <form onSubmit={submit} className="mt-6 grid gap-3 rounded-2xl border bg-white p-4 shadow-sm md:grid-cols-3 xl:grid-cols-6">
        <label className="md:col-span-2">
          <span className="mb-1 block text-xs font-bold text-slate-600">Nombre o email</span>
          <input
            value={filters.search}
            onChange={(event) => setFilters({ ...filters, search: event.target.value })}
            className="min-h-11 w-full rounded-xl border px-3"
            placeholder="Buscar"
          />
        </label>
        <FilterSelect label="Estado" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })}>
          <option value="">Todos</option>
          {Object.entries(DEMO_STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </FilterSelect>
        <FilterSelect label="País" value={filters.country} onChange={(value) => setFilters({ ...filters, country: value })}>
          <option value="">Todos</option>
          <option value="CO">Colombia</option>
          <option value="CL">Chile</option>
          <option value="OTHER">Otro</option>
        </FilterSelect>
        <FilterSelect label="Responsable" value={filters.assigned_to_user_id} onChange={(value) => setFilters({ ...filters, assigned_to_user_id: value })}>
          <option value="">Todos</option>
          {owners.map((owner) => <option key={owner.id} value={owner.id}>{owner.name}</option>)}
        </FilterSelect>
        <div className="flex items-end gap-2">
          <button className="min-h-11 rounded-xl bg-green-700 px-4 font-bold text-white">Filtrar</button>
          <button
            type="button"
            className="min-h-11 rounded-xl border px-4 font-bold text-slate-600"
            onClick={() => { setFilters(emptyFilters); load(emptyFilters); }}
          >
            Limpiar
          </button>
        </div>
        <label>
          <span className="mb-1 block text-xs font-bold text-slate-600">Desde</span>
          <input type="date" value={filters.created_from} onChange={(event) => setFilters({ ...filters, created_from: event.target.value })} className="min-h-11 w-full rounded-xl border px-3" />
        </label>
        <label>
          <span className="mb-1 block text-xs font-bold text-slate-600">Hasta</span>
          <input type="date" value={filters.created_to} onChange={(event) => setFilters({ ...filters, created_to: event.target.value })} className="min-h-11 w-full rounded-xl border px-3" />
        </label>
      </form>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      <section className="mt-5 overflow-hidden rounded-2xl border bg-white shadow-sm">
        {loading ? (
          <div className="flex justify-center py-16"><Spinner className="h-7 w-7 text-green-700" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y">
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "Fecha", "Nombre", "País / ciudad", "Práctica", "Odontólogos", "Estado", "Responsable", "",
                  ].map((heading) => <th key={heading} className="px-4 py-3 text-left text-xs font-bold uppercase text-slate-500">{heading}</th>)}
                </tr>
              </thead>
              <tbody className="divide-y">
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="whitespace-nowrap px-4 py-4 text-sm">{formatDemoDate(item.created_at)}</td>
                    <td className="px-4 py-4"><p className="font-bold">{item.first_name} {item.last_name}</p><p className="text-xs text-slate-500">{item.email}</p></td>
                    <td className="px-4 py-4 text-sm">{item.country} · {item.city}</td>
                    <td className="px-4 py-4 text-sm">{PRACTICE_LABELS[item.practice_type]}</td>
                    <td className="px-4 py-4 text-sm">{item.dentist_count}</td>
                    <td className="px-4 py-4"><span className="rounded-full bg-green-50 px-2 py-1 text-xs font-bold text-green-800">{DEMO_STATUS_LABELS[item.status]}</span></td>
                    <td className="px-4 py-4 text-sm">{item.assigned_to?.name ?? "Sin asignar"}</td>
                    <td className="px-4 py-4 text-right"><Link href={`/administracion/solicitudes-demo/${item.id}`} className="font-bold text-green-700">Ver</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!items.length && <p className="py-14 text-center text-sm text-slate-500">No hay solicitudes con estos filtros.</p>}
          </div>
        )}
      </section>
    </div>
  );
}

function FilterSelect({ label, value, onChange, children }: { label: string; value?: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return (
    <label>
      <span className="mb-1 block text-xs font-bold text-slate-600">{label}</span>
      <select value={value ?? ""} onChange={(event) => onChange(event.target.value)} className="min-h-11 w-full rounded-xl border bg-white px-3">{children}</select>
    </label>
  );
}
