"use client";

import { FormEvent, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { ApiError } from "@/services/apiClient";
import { getAccessOptions } from "@/services/userService";
import type {
  AccessOptions,
  ManagedUser,
  UserCreateInput,
  UserUpdateInput,
} from "@/types/user";

export function UserForm({
  user,
  onSubmit,
  submitLabel,
}: {
  user?: ManagedUser;
  onSubmit: (data: UserCreateInput | UserUpdateInput) => Promise<void>;
  submitLabel: string;
}) {
  const editing = Boolean(user);
  const [options, setOptions] = useState<AccessOptions | null>(null);
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [roleIds, setRoleIds] = useState(user?.roles.map((role) => role.id) ?? []);
  const [siteIds, setSiteIds] = useState(user?.sites.map((site) => site.id) ?? []);
  const [defaultSiteId, setDefaultSiteId] = useState(
    user?.default_site_id ?? "",
  );
  const [loading, setLoading] = useState(!editing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editing) return;
    getAccessOptions()
      .then(setOptions)
      .catch(() => setError("No fue posible cargar roles y sedes."))
      .finally(() => setLoading(false));
  }, [editing]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!name.trim() || !email.trim()) {
      setError("Completa nombre y correo.");
      return;
    }
    if (!editing && (!roleIds.length || !siteIds.length || !defaultSiteId)) {
      setError("Selecciona al menos un rol, una sede y la sede predeterminada.");
      return;
    }
    setSaving(true);
    try {
      await onSubmit(
        editing
          ? { name: name.trim(), email: email.trim(), phone: phone.trim() || null }
          : {
              name: name.trim(),
              email: email.trim(),
              phone: phone.trim() || null,
              role_ids: roleIds,
              site_ids: siteIds,
              default_site_id: defaultSiteId,
            },
      );
    } catch (submitError) {
      setError(
        submitError instanceof ApiError
          ? submitError.detail ?? submitError.message
          : "No fue posible guardar el usuario.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-3 py-10 text-slate-500">
        <Spinner className="h-6 w-6 text-dentia-primary" />
        Cargando opciones…
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-7">
      {error && <Alert tone="error">{error}</Alert>}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">Información básica</h2>
        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          <label className="sm:col-span-2">
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Nombre completo
            </span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={200}
              className="min-h-12 w-full rounded-xl border border-slate-300 px-4 focus:border-dentia-primary focus:outline-none focus:ring-4 focus:ring-green-100"
            />
          </label>
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Correo electrónico
            </span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              maxLength={320}
              className="min-h-12 w-full rounded-xl border border-slate-300 px-4 focus:border-dentia-primary focus:outline-none focus:ring-4 focus:ring-green-100"
            />
          </label>
          <label>
            <span className="mb-2 block text-sm font-bold text-slate-700">
              Teléfono
            </span>
            <input
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              maxLength={50}
              className="min-h-12 w-full rounded-xl border border-slate-300 px-4 focus:border-dentia-primary focus:outline-none focus:ring-4 focus:ring-green-100"
            />
          </label>
        </div>
      </section>

      {!editing && options && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">Acceso inicial</h2>
          <p className="mt-1 text-sm text-slate-500">
            El usuario se creará Pendiente y recibirá una contraseña temporal.
          </p>
          <div className="mt-6 grid gap-7 lg:grid-cols-2">
            <div>
              <p className="text-sm font-bold text-slate-700">Roles</p>
              <div className="mt-3 space-y-2">
                {options.roles.map((role) => (
                  <label
                    key={role.id}
                    className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"
                  >
                    <input
                      type="checkbox"
                      checked={roleIds.includes(role.id)}
                      onChange={(event) =>
                        setRoleIds((current) =>
                          event.target.checked
                            ? [...current, role.id]
                            : current.filter((id) => id !== role.id),
                        )
                      }
                      className="mt-1 h-4 w-4 accent-green-600"
                    />
                    <span>
                      <span className="block text-sm font-bold text-slate-800">
                        {role.name}
                      </span>
                      <span className="mt-0.5 block text-xs leading-5 text-slate-500">
                        {role.description}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-700">Sedes</p>
              <div className="mt-3 space-y-2">
                {options.sites.map((site) => (
                  <label
                    key={site.id}
                    className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"
                  >
                    <input
                      type="checkbox"
                      checked={siteIds.includes(site.id)}
                      onChange={(event) => {
                        setSiteIds((current) =>
                          event.target.checked
                            ? [...current, site.id]
                            : current.filter((id) => id !== site.id),
                        );
                        if (!event.target.checked && defaultSiteId === site.id) {
                          setDefaultSiteId("");
                        }
                      }}
                      className="h-4 w-4 accent-green-600"
                    />
                    <span className="text-sm font-bold text-slate-800">
                      {site.name}
                    </span>
                  </label>
                ))}
              </div>
              <label className="mt-5 block">
                <span className="mb-2 block text-sm font-bold text-slate-700">
                  Sede predeterminada
                </span>
                <select
                  value={defaultSiteId}
                  onChange={(event) => setDefaultSiteId(event.target.value)}
                  className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4"
                >
                  <option value="">Selecciona una sede</option>
                  {options.sites
                    .filter((site) => siteIds.includes(site.id))
                    .map((site) => (
                      <option key={site.id} value={site.id}>
                        {site.name}
                      </option>
                    ))}
                </select>
              </label>
            </div>
          </div>
        </section>
      )}

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={saving}
          className="flex min-h-12 items-center gap-2 rounded-xl bg-dentia-primary px-6 font-bold text-white hover:bg-green-700 disabled:opacity-60"
        >
          {saving && <Spinner className="h-5 w-5" />}
          {submitLabel}
        </button>
      </div>
    </form>
  );
}
