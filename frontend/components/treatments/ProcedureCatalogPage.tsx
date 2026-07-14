"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import {
  activateProcedureCatalogItem,
  createProcedureCatalogItem,
  deactivateProcedureCatalogItem,
  listProcedureCatalog,
  updateProcedureCatalogItem,
} from "@/services/treatmentService";
import type { ProcedureCatalogItem } from "@/types/treatment";

const scopeLabels: Record<string, string> = {
  GENERAL: "General",
  ZONE: "Zona",
  TOOTH: "Diente",
  TOOTH_SURFACE: "Superficie dental",
};

function money(value: string | null) {
  if (!value) return "—";
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

const emptyForm = {
  name: "",
  category: "",
  description: "",
  suggested_value: "",
  suggested_scope_type: "",
  is_active: true,
};

type CatalogFormState = typeof emptyForm;

function toForm(item: ProcedureCatalogItem): CatalogFormState {
  return {
    name: item.name,
    category: item.category ?? "",
    description: item.description ?? "",
    suggested_value: item.suggested_value ?? "",
    suggested_scope_type: item.suggested_scope_type ?? "",
    is_active: item.is_active,
  };
}

export function ProcedureCatalogPage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("procedure_catalog.manage");
  const [items, setItems] = useState<ProcedureCatalogItem[]>([]);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("");
  const [editing, setEditing] = useState<ProcedureCatalogItem | null>(null);
  const [form, setForm] = useState<CatalogFormState>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set("busqueda", search.trim());
      if (activeFilter) params.set("activo", activeFilter);
      const response = await listProcedureCatalog(params.size ? `?${params.toString()}` : "");
      setItems(response.items);
    } catch {
      setError("No fue posible cargar el catálogo de procedimientos.");
    } finally {
      setLoading(false);
    }
  }, [activeFilter, search]);

  useEffect(() => {
    load();
  }, [load]);

  function startEdit(item: ProcedureCatalogItem) {
    setEditing(item);
    setForm(toForm(item));
    setSuccess(null);
    setError(null);
  }

  function resetForm() {
    setEditing(null);
    setForm(emptyForm);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const payload = {
        name: form.name,
        category: form.category || null,
        description: form.description || null,
        suggested_value: form.suggested_value || null,
        suggested_scope_type: form.suggested_scope_type || null,
        is_active: form.is_active,
      };
      if (editing) {
        await updateProcedureCatalogItem(editing.id, payload);
        setSuccess("Procedimiento actualizado.");
      } else {
        await createProcedureCatalogItem(payload);
        setSuccess("Procedimiento creado.");
      }
      resetForm();
      await load();
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "No fue posible guardar el procedimiento.";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  async function toggleStatus(item: ProcedureCatalogItem) {
    setError(null);
    setSuccess(null);
    try {
      if (item.is_active) {
        await deactivateProcedureCatalogItem(item.id);
        setSuccess("Procedimiento inactivado.");
      } else {
        await activateProcedureCatalogItem(item.id);
        setSuccess("Procedimiento reactivado.");
      }
      await load();
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "No fue posible cambiar el estado.";
      setError(message);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header>
        <p className="text-sm font-bold uppercase tracking-wide text-green-700">
          Configuración
        </p>
        <h1 className="mt-2 text-3xl font-black text-slate-950">
          Catálogo de procedimientos
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">
          Define los procedimientos frecuentes de la clínica para evitar nombres duplicados
          y acelerar la creación de tratamientos.
        </p>
      </header>

      {error && <Alert tone="error">{error}</Alert>}
      {success && <Alert tone="info">{success}</Alert>}

      {canManage && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-black text-slate-950">
            {editing ? "Editar procedimiento" : "Crear procedimiento"}
          </h2>
          <form onSubmit={submit} className="mt-5 grid gap-4 lg:grid-cols-3">
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Nombre del procedimiento
              </span>
              <input
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm"
                required
              />
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Categoría opcional
              </span>
              <input
                value={form.category}
                onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}
                className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm"
                placeholder="Operatoria, endodoncia…"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Valor sugerido
              </span>
              <input
                value={form.suggested_value}
                onChange={(event) => setForm((current) => ({ ...current, suggested_value: event.target.value }))}
                type="number"
                min="0"
                className="min-h-11 w-full rounded-xl border border-slate-300 px-3 text-sm"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Alcance sugerido
              </span>
              <select
                value={form.suggested_scope_type}
                onChange={(event) => setForm((current) => ({ ...current, suggested_scope_type: event.target.value }))}
                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
              >
                <option value="">Sin sugerencia</option>
                {Object.entries(scopeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Estado
              </span>
              <select
                value={form.is_active ? "true" : "false"}
                onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.value === "true" }))}
                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm"
              >
                <option value="true">Activo</option>
                <option value="false">Inactivo</option>
              </select>
            </label>
            <label className="lg:col-span-3">
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                Descripción opcional
              </span>
              <textarea
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                rows={3}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <div className="flex flex-wrap gap-3 lg:col-span-3">
              <button
                disabled={saving}
                className="min-h-11 rounded-xl bg-dentia-primary px-5 text-sm font-bold text-white hover:bg-green-700 disabled:opacity-60"
              >
                {saving ? "Guardando…" : editing ? "Guardar cambios" : "Crear procedimiento"}
              </button>
              {editing && (
                <button
                  type="button"
                  onClick={resetForm}
                  className="min-h-11 rounded-xl border border-slate-200 px-5 text-sm font-bold text-slate-600 hover:bg-slate-50"
                >
                  Cancelar edición
                </button>
              )}
            </div>
          </form>
        </section>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-black text-slate-950">Procedimientos</h2>
            <p className="mt-1 text-sm text-slate-500">
              Cada empresa ve únicamente su propio catálogo.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-[minmax(220px,1fr)_160px_auto]">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar procedimiento"
              className="min-h-11 rounded-xl border border-slate-300 px-3 text-sm"
            />
            <select
              value={activeFilter}
              onChange={(event) => setActiveFilter(event.target.value)}
              className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm"
            >
              <option value="">Todos</option>
              <option value="true">Activos</option>
              <option value="false">Inactivos</option>
            </select>
            <button
              onClick={load}
              className="min-h-11 rounded-xl border border-green-200 px-4 text-sm font-bold text-green-700 hover:bg-green-50"
            >
              Buscar
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner className="h-7 w-7 text-dentia-primary" />
          </div>
        ) : (
          <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {["Nombre", "Categoría", "Valor sugerido", "Alcance sugerido", "Estado", "Acciones"].map((heading) => (
                    <th key={heading} className="px-4 py-3 text-left text-xs font-black uppercase tracking-wide text-slate-500">
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="px-4 py-3">
                      <p className="font-bold text-slate-900">{item.name}</p>
                      {item.description && <p className="mt-1 text-xs text-slate-500">{item.description}</p>}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{item.category ?? "—"}</td>
                    <td className="px-4 py-3 font-bold text-slate-900">{money(item.suggested_value)}</td>
                    <td className="px-4 py-3 text-slate-600">
                      {item.suggested_scope_type ? scopeLabels[item.suggested_scope_type] ?? item.suggested_scope_type : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-1 text-xs font-bold ${item.is_active ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>
                        {item.is_active ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {canManage && (
                        <>
                          <button onClick={() => startEdit(item)} className="text-xs font-bold text-sky-700 hover:underline">
                            Editar
                          </button>
                          <button onClick={() => toggleStatus(item)} className="ml-3 text-xs font-bold text-orange-700 hover:underline">
                            {item.is_active ? "Inactivar" : "Reactivar"}
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!items.length && <p className="px-4 py-8 text-sm text-slate-500">No hay procedimientos registrados.</p>}
          </div>
        )}
      </section>
    </div>
  );
}
