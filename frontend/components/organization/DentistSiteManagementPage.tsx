"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { listDentists, updateDentistSites } from "@/services/organizationService";
import type { DentistSiteManagement } from "@/types/organization";

export function DentistSiteManagementPage() {
  const { hasPermission } = useAuth();
  const canEdit = hasPermission("sites.manage");
  const [items, setItems] = useState<DentistSiteManagement[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const response = await listDentists();
      setItems(response.items);
    } catch {
      setError("No fue posible cargar los odontólogos.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggleSite(dentist: DentistSiteManagement, siteId: string) {
    if (!canEdit) return;
    setSavingId(dentist.id);
    setError(null);
    setMessage(null);
    const nextIds = dentist.site_ids.includes(siteId)
      ? dentist.site_ids.filter((id) => id !== siteId)
      : [...dentist.site_ids, siteId];
    try {
      const updated = await updateDentistSites(dentist.id, nextIds);
      setItems((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setMessage("Asociación de sedes actualizada.");
    } catch {
      setError("No fue posible actualizar las sedes del odontólogo.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
          Configuración
        </p>
        <h1 className="mt-2 text-3xl font-black text-slate-950">
          Odontólogos y sedes
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Asociación operativa mínima para que un odontólogo pueda atender en
          varias sedes.
        </p>
      </header>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      {message && <div className="mt-5"><Alert tone="info">{message}</Alert></div>}

      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex justify-center gap-3 py-16 text-slate-500">
            <Spinner className="h-6 w-6 text-dentia-primary" />
            Cargando odontólogos…
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {items.map((dentist) => (
              <article key={dentist.id} className="p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-black text-slate-900">
                      {dentist.name}
                    </h2>
                    <p className="mt-1 text-xs font-bold uppercase text-green-700">
                      {dentist.status}
                    </p>
                  </div>
                  {savingId === dentist.id && (
                    <span className="inline-flex items-center gap-2 text-sm text-slate-500">
                      <Spinner className="h-4 w-4" />
                      Guardando…
                    </span>
                  )}
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {dentist.sites.map((site) => (
                    <label
                      key={site.id}
                      className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"
                    >
                      <input
                        type="checkbox"
                        checked={dentist.site_ids.includes(site.id)}
                        disabled={!canEdit || savingId === dentist.id}
                        onChange={() => toggleSite(dentist, site.id)}
                        className="mt-1 h-4 w-4 accent-green-700"
                      />
                      <span>
                        <span className="block font-bold text-slate-900">
                          {site.name}
                        </span>
                        <span className="block text-xs text-slate-500">
                          {site.address} · {site.timezone}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
              </article>
            ))}
            {!items.length && (
              <p className="py-14 text-center text-sm text-slate-500">
                No hay odontólogos activos para configurar.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
