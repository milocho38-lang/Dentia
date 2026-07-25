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
import { getOdontogramCatalog } from "@/services/odontogramService";
import type { OdontogramCatalogItem } from "@/types/odontogram";
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
  odontogram_behavior: "UNCONFIGURED",
  odontogram_scope_type: "",
  allowed_diagnosis_catalog_item_ids: [] as string[],
  default_performed_catalog_item_id: "",
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
    odontogram_behavior: item.odontogram_behavior ?? "UNCONFIGURED",
    odontogram_scope_type: item.odontogram_scope_type ?? "",
    allowed_diagnosis_catalog_item_ids: item.allowed_diagnosis_catalog_item_ids ?? [],
    default_performed_catalog_item_id: item.default_performed_catalog_item_id ?? "",
    is_active: item.is_active,
  };
}

export function ProcedureCatalogPage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("procedure_catalog.manage");
  const [items, setItems] = useState<ProcedureCatalogItem[]>([]);
  const [odontogramCatalog, setOdontogramCatalog] = useState<OdontogramCatalogItem[]>([]);
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
      const [response, odontogramItems] = await Promise.all([
        listProcedureCatalog(params.size ? `?${params.toString()}` : ""),
        getOdontogramCatalog(),
      ]);
      setItems(response.items);
      setOdontogramCatalog(odontogramItems);
    } catch {
      setError("No fue posible cargar el catálogo de procedimientos.");
    } finally {
      setLoading(false);
    }
  }, [activeFilter, search]);

  const diagnosisOptions = odontogramCatalog.filter((item) =>
    ["DIAGNOSIS", "FINDING"].includes(item.type) && item.is_active
  );
  const performedOptions = odontogramCatalog.filter((item) =>
    item.type === "PERFORMED_PROCEDURE" && item.is_active
  );

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
        odontogram_behavior: form.odontogram_behavior,
        odontogram_scope_type: form.odontogram_scope_type || null,
        allowed_diagnosis_catalog_item_ids:
          form.odontogram_behavior === "REQUIRES_DIAGNOSIS" || form.odontogram_behavior === "OPTIONAL_DIAGNOSIS"
            ? form.allowed_diagnosis_catalog_item_ids
            : [],
        default_performed_catalog_item_id: form.default_performed_catalog_item_id || null,
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
            <div className="rounded-2xl border border-orange-100 bg-orange-50/60 p-4 lg:col-span-3">
              <p className="text-sm font-black text-orange-950">Configuración odontográfica</p>
              <p className="mt-1 text-xs text-orange-800">
                Define si este procedimiento puede o debe registrar un diagnóstico confirmado en el odontograma. No se infiere por nombre.
              </p>
              <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <label>
                  <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-orange-800">
                    Comportamiento
                  </span>
                  <select
                    value={form.odontogram_behavior}
                    onChange={(event) => setForm((current) => ({
                      ...current,
                      odontogram_behavior: event.target.value,
                      allowed_diagnosis_catalog_item_ids:
                        ["REQUIRES_DIAGNOSIS", "OPTIONAL_DIAGNOSIS"].includes(event.target.value)
                          ? current.allowed_diagnosis_catalog_item_ids
                          : [],
                    }))}
                    className="min-h-11 w-full rounded-xl border border-orange-200 bg-white px-3 text-sm"
                  >
                    <option value="UNCONFIGURED">Sin configurar</option>
                    <option value="NO_CHANGE">No cambia odontograma</option>
                    <option value="OPTIONAL_DIAGNOSIS">Diagnóstico opcional</option>
                    <option value="REQUIRES_DIAGNOSIS">Requiere diagnóstico</option>
                  </select>
                </label>
                <label>
                  <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-orange-800">
                    Alcance odontográfico esperado
                  </span>
                  <select
                    value={form.odontogram_scope_type}
                    onChange={(event) => setForm((current) => ({ ...current, odontogram_scope_type: event.target.value }))}
                    className="min-h-11 w-full rounded-xl border border-orange-200 bg-white px-3 text-sm"
                  >
                    <option value="">Sin definición</option>
                    {Object.entries(scopeLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-orange-800">
                    Resultado realizado sugerido
                  </span>
                  <select
                    value={form.default_performed_catalog_item_id}
                    onChange={(event) => setForm((current) => ({ ...current, default_performed_catalog_item_id: event.target.value }))}
                    className="min-h-11 w-full rounded-xl border border-orange-200 bg-white px-3 text-sm"
                  >
                    <option value="">Sin sugerencia</option>
                    {performedOptions.map((item) => (
                      <option key={item.id} value={item.id}>{item.name}</option>
                    ))}
                  </select>
                </label>
              </div>
              {["REQUIRES_DIAGNOSIS", "OPTIONAL_DIAGNOSIS"].includes(form.odontogram_behavior) && (
                <fieldset className="mt-4">
                  <legend className="mb-2 block text-xs font-black uppercase tracking-wide text-orange-800">
                    Diagnósticos o hallazgos permitidos
                  </legend>
                  <div className="grid max-h-52 gap-2 overflow-y-auto rounded-xl border border-orange-100 bg-white p-3 sm:grid-cols-2 lg:grid-cols-3">
                    {diagnosisOptions.map((item) => (
                      <label key={item.id} className="flex items-center gap-2 text-xs font-bold text-slate-700">
                        <input
                          type="checkbox"
                          checked={form.allowed_diagnosis_catalog_item_ids.includes(item.id)}
                          onChange={() => setForm((current) => ({
                            ...current,
                            allowed_diagnosis_catalog_item_ids: current.allowed_diagnosis_catalog_item_ids.includes(item.id)
                              ? current.allowed_diagnosis_catalog_item_ids.filter((id) => id !== item.id)
                              : [...current.allowed_diagnosis_catalog_item_ids, item.id],
                          }))}
                        />
                        {item.name}
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}
            </div>
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
                  {["Nombre", "Categoría", "Valor sugerido", "Alcance sugerido", "Odontograma", "Estado", "Acciones"].map((heading) => (
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
                    <td className="px-4 py-3 text-xs text-slate-600">
                      <span className="font-bold">
                        {item.odontogram_behavior === "REQUIRES_DIAGNOSIS"
                          ? "Requiere diagnóstico"
                          : item.odontogram_behavior === "OPTIONAL_DIAGNOSIS"
                            ? "Diagnóstico opcional"
                            : item.odontogram_behavior === "NO_CHANGE"
                              ? "Sin cambio"
                              : "Sin configurar"}
                      </span>
                      {item.allowed_diagnoses.length > 0 && (
                        <p className="mt-1 text-slate-500">
                          {item.allowed_diagnoses.map((diagnosis) => diagnosis.name).join(", ")}
                        </p>
                      )}
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
