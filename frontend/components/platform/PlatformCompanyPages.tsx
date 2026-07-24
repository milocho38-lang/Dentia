"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import {
  createPlatformCompany,
  deactivatePlatformCompany,
  getPlatformCompany,
  listPlatformCompanies,
  reactivatePlatformCompany,
  updatePlatformCompanyUserRoles,
} from "@/services/platformService";
import type {
  PlatformCompanyDetail,
  PlatformCompanyInput,
  PlatformCompanyListItem,
  PlatformCompanyUserRoleUpdateInput,
  PlatformUserSummary,
} from "@/types/platform";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function PlatformCompanyListPage() {
  const [items, setItems] = useState<PlatformCompanyListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const response = await listPlatformCompanies(search);
      setItems(response.items);
    } catch {
      setError("No fue posible cargar las empresas.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="mx-auto max-w-6xl">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
            Plataforma
          </p>
          <h1 className="mt-2 text-3xl font-black">Empresas / Clínicas</h1>
          <p className="mt-2 text-sm text-slate-500">
            Alta de clínicas, sedes principales y administradores iniciales.
          </p>
        </div>
        <Link
          href="/configuracion/empresas/nueva"
          className="inline-flex min-h-11 items-center rounded-xl bg-green-700 px-4 font-bold text-white"
        >
          Nueva empresa
        </Link>
      </header>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          load();
        }}
        className="mt-5 flex gap-2"
      >
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Buscar por nombre"
          className="min-h-11 flex-1 rounded-xl border px-3"
        />
        <button className="rounded-xl border px-4 font-bold">Buscar</button>
      </form>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      <section className="mt-5 overflow-hidden rounded-2xl border bg-white shadow-sm">
        {loading ? (
          <div className="flex justify-center py-16">
            <Spinner className="h-7 w-7 text-green-700" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y">
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "Empresa",
                    "País",
                    "Ciudad",
                    "Zona horaria",
                    "Estado",
                    "Sedes",
                    "Usuarios",
                    "Creación",
                    "",
                  ].map((heading) => (
                    <th
                      key={heading}
                      className="px-5 py-3 text-left text-xs font-bold uppercase text-slate-500"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="px-5 py-4">
                      <p className="font-bold">{item.name}</p>
                      <p className="text-xs text-slate-500">
                        {item.company_type ?? "Sin tipo"}
                      </p>
                    </td>
                    <td className="px-5 py-4 text-sm">{item.country ?? "—"}</td>
                    <td className="px-5 py-4 text-sm">{item.city ?? "—"}</td>
                    <td className="px-5 py-4 text-sm">{item.timezone}</td>
                    <td className="px-5 py-4">
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold">
                        {item.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-sm">{item.site_count}</td>
                    <td className="px-5 py-4 text-sm">{item.user_count}</td>
                    <td className="px-5 py-4 text-sm">{formatDate(item.created_at)}</td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        href={`/configuracion/empresas/${item.id}`}
                        className="font-bold text-green-700"
                      >
                        Ver
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!items.length && (
              <p className="py-14 text-center text-sm text-slate-500">
                No hay empresas registradas.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

const initialInput: PlatformCompanyInput = {
  company_name: "",
  company_type: "Profesional independiente",
  tax_id: null,
  phone: null,
  email: null,
  address: "",
  city: "",
  country: "Colombia",
  timezone: "America/Bogota",
  admin_name: "",
  admin_email: "",
  admin_password: null,
};

export function PlatformCompanyCreatePage() {
  const router = useRouter();
  const [data, setData] = useState<PlatformCompanyInput>(initialInput);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [temporaryPassword, setTemporaryPassword] = useState<string | null>(null);

  function setCountry(country: string) {
    setData((current) => ({
      ...current,
      country,
      timezone: country === "Chile" ? "America/Santiago" : "America/Bogota",
    }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setTemporaryPassword(null);
    try {
      const response = await createPlatformCompany(data);
      setTemporaryPassword(response.temporary_password);
      router.push(`/configuracion/empresas/${response.company.id}`);
    } catch {
      setError("No fue posible crear la empresa.");
    } finally {
      setBusy(false);
    }
  }

  const input = (key: keyof PlatformCompanyInput, label: string, type = "text") => (
    <label>
      <span className="mb-1 block text-sm font-bold">{label}</span>
      <input
        type={type}
        value={data[key] ?? ""}
        onChange={(event) =>
          setData({ ...data, [key]: event.target.value || null })
        }
        className="min-h-11 w-full rounded-xl border px-3"
      />
    </label>
  );

  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/configuracion/empresas" className="text-sm font-bold text-green-700">
        ← Volver a empresas
      </Link>
      <h1 className="mt-5 text-3xl font-black">Nueva empresa / clínica</h1>
      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}
      {temporaryPassword && (
        <div className="mt-5">
          <Alert>
            Contraseña temporal generada: <strong>{temporaryPassword}</strong>
          </Alert>
        </div>
      )}
      <form onSubmit={submit} className="mt-6 space-y-6 rounded-3xl border bg-white p-6 shadow-sm">
        <section>
          <h2 className="font-black">Datos de la empresa</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {input("company_name", "Nombre comercial")}
            <label>
              <span className="mb-1 block text-sm font-bold">Tipo de empresa</span>
              <select
                value={data.company_type}
                onChange={(event) => setData({ ...data, company_type: event.target.value })}
                className="min-h-11 w-full rounded-xl border bg-white px-3"
              >
                <option>Profesional independiente</option>
                <option>Consultorio</option>
                <option>Clínica</option>
              </select>
            </label>
            {input("tax_id", "NIT/RUT/identificación tributaria")}
            {input("phone", "Teléfono")}
            {input("email", "Correo", "email")}
            {input("city", "Ciudad")}
            <label>
              <span className="mb-1 block text-sm font-bold">País</span>
              <select
                value={data.country}
                onChange={(event) => setCountry(event.target.value)}
                className="min-h-11 w-full rounded-xl border bg-white px-3"
              >
                <option>Colombia</option>
                <option>Chile</option>
              </select>
            </label>
            <label>
              <span className="mb-1 block text-sm font-bold">Zona horaria</span>
              <select
                value={data.timezone}
                onChange={(event) => setData({ ...data, timezone: event.target.value })}
                className="min-h-11 w-full rounded-xl border bg-white px-3"
              >
                <option>America/Bogota</option>
                <option>America/Santiago</option>
              </select>
            </label>
            <div className="sm:col-span-2">{input("address", "Dirección")}</div>
          </div>
        </section>
        <section>
          <h2 className="font-black">Administrador inicial</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {input("admin_name", "Nombre administrador")}
            {input("admin_email", "Correo administrador", "email")}
            {input("admin_password", "Contraseña temporal opcional")}
          </div>
          <p className="mt-3 text-sm text-slate-500">
            Si no ingresas contraseña, Dentia generará una temporal. El usuario deberá cambiarla al iniciar sesión.
          </p>
        </section>
        <div className="flex justify-end">
          <button
            disabled={
              busy ||
              data.company_name.trim().length < 2 ||
              data.admin_name.trim().length < 2 ||
              data.admin_email.trim().length < 3
            }
            className="rounded-xl bg-green-700 px-5 py-3 font-bold text-white disabled:opacity-50"
          >
            {busy ? "Creando…" : "Crear empresa"}
          </button>
        </div>
      </form>
    </div>
  );
}

export function PlatformCompanyDetailPage({ companyId }: { companyId: string }) {
  const [company, setCompany] = useState<PlatformCompanyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<PlatformUserSummary | null>(null);
  const [modalMode, setModalMode] = useState<"view" | "edit">("view");
  const [notice, setNotice] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      setCompany(await getPlatformCompany(companyId));
    } catch {
      setError("No fue posible cargar la empresa.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyId]);

  async function toggleStatus() {
    if (!company) return;
    if (company.is_active) {
      const response = await deactivatePlatformCompany(company.id);
      setCompany(response.company);
    } else {
      const response = await reactivatePlatformCompany(company.id);
      setCompany(response.company);
    }
  }

  function updateUserInCompany(user: PlatformUserSummary) {
    setCompany((current) =>
      current
        ? {
            ...current,
            users: current.users.map((item) => (item.id === user.id ? user : item)),
          }
        : current,
    );
    setSelectedUser(user);
  }

  if (loading) {
    return <div className="flex justify-center py-20"><Spinner className="h-7 w-7 text-green-700" /></div>;
  }
  if (!company) return <Alert tone="error">{error ?? "Empresa no disponible."}</Alert>;

  return (
    <div className="mx-auto max-w-6xl">
      <Link href="/configuracion/empresas" className="text-sm font-bold text-green-700">
        ← Volver a empresas
      </Link>
      <header className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <h1 className="text-3xl font-black">{company.name}</h1>
          <p className="mt-2 text-sm text-slate-500">
            {company.company_type ?? "Sin tipo"} · {company.country ?? "Sin país"} · {company.timezone}
          </p>
        </div>
        <button onClick={toggleStatus} className="rounded-xl border px-4 py-3 font-bold">
          {company.is_active ? "Inactivar" : "Reactivar"}
        </button>
      </header>
      <div className="mt-6 grid gap-4 sm:grid-cols-4">
        <Card label="Estado" value={company.status} />
        <Card label="Sedes" value={String(company.site_count)} />
        <Card label="Usuarios" value={String(company.user_count)} />
        <Card label="Creación" value={formatDate(company.created_at)} />
      </div>
      <section className="mt-6 rounded-2xl border bg-white p-6 shadow-sm">
        <h2 className="font-black">Datos empresa</h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          {[
            ["Teléfono", company.phone ?? "—"],
            ["Correo", company.email ?? "—"],
            ["Ciudad", company.city ?? "—"],
            ["Dirección", company.address ?? "—"],
            ["Identificación tributaria", company.tax_id ?? "—"],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs font-bold uppercase text-slate-400">{label}</dt>
              <dd className="mt-1 text-sm font-semibold">{value}</dd>
            </div>
          ))}
        </dl>
      </section>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border bg-white p-6 shadow-sm">
          <h2 className="font-black">Sedes</h2>
          <div className="mt-4 space-y-3">
            {company.sites.map((site) => (
              <div key={site.id} className="rounded-xl bg-slate-50 p-4 text-sm">
                <p className="font-bold">{site.name}</p>
                <p className="mt-1 text-slate-500">{site.city} · {site.effective_timezone} · {site.status}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
      {notice && (
        <div className="mt-6">
          <Alert>{notice}</Alert>
        </div>
      )}
      <section className="mt-6 overflow-hidden rounded-2xl border bg-white shadow-sm">
        <div className="border-b p-6">
          <h2 className="font-black">Usuarios de la empresa</h2>
          <p className="mt-1 text-sm text-slate-500">
            Administración de roles empresariales desde Plataforma, sin cambiar de tenant ni exponer datos clínicos.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y">
            <thead className="bg-slate-50">
              <tr>
                {[
                  "Usuario",
                  "Estado",
                  "Roles",
                  "Sedes",
                  "Perfil odontológico",
                  "",
                ].map((heading) => (
                  <th
                    key={heading}
                    className="px-5 py-3 text-left text-xs font-bold uppercase text-slate-500"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {company.users.map((user) => (
                <tr key={user.id}>
                  <td className="px-5 py-4">
                    <p className="font-bold text-slate-950">{user.name}</p>
                    <p className="mt-1 text-sm text-slate-500">{user.email}</p>
                  </td>
                  <td className="px-5 py-4">
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold">
                      {user.status}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex max-w-xs flex-wrap gap-1">
                      {user.role_names.length ? (
                        user.role_names.map((roleName) => (
                          <span
                            key={roleName}
                            className="rounded-full bg-green-50 px-2 py-1 text-xs font-bold text-green-800"
                          >
                            {roleName}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-slate-400">Sin roles</span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-600">
                    {user.sites.length
                      ? user.sites
                          .map((site) => `${site.name}${site.is_default ? " (principal)" : ""}`)
                          .join(", ")
                      : "Sin sedes"}
                  </td>
                  <td className="px-5 py-4 text-sm">
                    {user.dentist_profile ? (
                      <div>
                        <p className="font-bold text-slate-800">
                          {user.dentist_profile.name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {user.dentist_profile.status} ·{" "}
                          {user.dentist_profile.sites.length
                            ? user.dentist_profile.sites.map((site) => site.name).join(", ")
                            : "sin sedes clínicas"}
                        </p>
                      </div>
                    ) : user.needs_dentist_profile ? (
                      <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-bold text-amber-800">
                        Requiere perfil
                      </span>
                    ) : (
                      <span className="text-slate-400">No aplica</span>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedUser(user);
                          setModalMode("view");
                        }}
                        className="rounded-xl border px-3 py-2 text-sm font-bold"
                      >
                        Ver usuario
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedUser(user);
                          setModalMode("edit");
                        }}
                        className="rounded-xl bg-green-700 px-3 py-2 text-sm font-bold text-white"
                      >
                        Editar roles
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!company.users.length && (
            <p className="py-14 text-center text-sm text-slate-500">
              Esta empresa aún no tiene usuarios.
            </p>
          )}
        </div>
      </section>
      {selectedUser && (
        <CompanyUserRolesModal
          company={company}
          user={selectedUser}
          mode={modalMode}
          onClose={() => setSelectedUser(null)}
          onSaved={(user, message) => {
            updateUserInCompany(user);
            setNotice(message);
          }}
        />
      )}
    </div>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <p className="text-xs font-bold uppercase text-slate-400">{label}</p>
      <p className="mt-2 font-black">{value}</p>
    </div>
  );
}

function CompanyUserRolesModal({
  company,
  user,
  mode,
  onClose,
  onSaved,
}: {
  company: PlatformCompanyDetail;
  user: PlatformUserSummary;
  mode: "view" | "edit";
  onClose: () => void;
  onSaved: (user: PlatformUserSummary, message: string) => void;
}) {
  const editable = mode === "edit";
  const [roleIds, setRoleIds] = useState<string[]>(user.role_ids);
  const [siteIds, setSiteIds] = useState<string[]>(user.sites.map((site) => site.id));
  const [defaultSiteId, setDefaultSiteId] = useState<string>(
    user.sites.find((site) => site.is_default)?.id ?? user.sites[0]?.id ?? company.sites[0]?.id ?? "",
  );
  const [status, setStatus] = useState<"Activo" | "Inactivo">(
    user.status === "Inactivo" ? "Inactivo" : "Activo",
  );
  const [ensureDentistProfile, setEnsureDentistProfile] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedRoles = company.role_options.filter((role) => roleIds.includes(role.id));
  const selectedRoleCodes = selectedRoles.map((role) => role.code);
  const hasClinicalRole = selectedRoleCodes.some((code) =>
    ["DENTIST", "DENTIST_ADMIN"].includes(code),
  );
  const willNeedDentistProfile = hasClinicalRole && !user.dentist_profile;

  function toggleRole(roleId: string) {
    setRoleIds((current) =>
      current.includes(roleId)
        ? current.filter((item) => item !== roleId)
        : [...current, roleId],
    );
  }

  function toggleSite(siteId: string) {
    setSiteIds((current) => {
      const next = current.includes(siteId)
        ? current.filter((item) => item !== siteId)
        : [...current, siteId];
      if (!next.includes(defaultSiteId)) {
        setDefaultSiteId(next[0] ?? "");
      }
      return next;
    });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!editable) return;
    setSaving(true);
    setError(null);
    try {
      const payload: PlatformCompanyUserRoleUpdateInput = {
        role_ids: roleIds,
        site_ids: siteIds,
        default_site_id: defaultSiteId,
        status,
        ensure_dentist_profile: ensureDentistProfile,
      };
      const response = await updatePlatformCompanyUserRoles(
        company.id,
        user.id,
        payload,
      );
      onSaved(response.user, response.message);
      onClose();
    } catch {
      setError("No fue posible actualizar los roles del usuario.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/30 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-3xl bg-white shadow-2xl">
        <div className="flex items-start justify-between gap-4 border-b p-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
              {editable ? "Editar roles" : "Ver usuario"}
            </p>
            <h2 className="mt-1 text-2xl font-black text-slate-950">{user.name}</h2>
            <p className="mt-1 text-sm text-slate-500">{user.email}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border px-3 py-1 text-lg font-black"
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>
        <form onSubmit={submit} className="max-h-[calc(90vh-96px)] overflow-y-auto p-6">
          {error && <Alert tone="error">{error}</Alert>}
          <div className="grid gap-4 sm:grid-cols-2">
            <ReadOnlyField label="Empresa" value={company.name} />
            <ReadOnlyField label="Usuario" value={`${user.name} · ${user.email}`} />
            <label>
              <span className="mb-1 block text-sm font-bold">Estado</span>
              <select
                disabled={!editable}
                value={status}
                onChange={(event) => setStatus(event.target.value as "Activo" | "Inactivo")}
                className="min-h-11 w-full rounded-xl border bg-white px-3 disabled:bg-slate-50"
              >
                <option value="Activo">Activo</option>
                <option value="Inactivo">Inactivo</option>
              </select>
            </label>
            <ReadOnlyField
              label="Perfil odontológico"
              value={
                user.dentist_profile
                  ? `${user.dentist_profile.name} · ${user.dentist_profile.status}`
                  : "Sin perfil vinculado"
              }
            />
          </div>

          <section className="mt-6">
            <h3 className="font-black text-slate-950">Roles empresariales disponibles</h3>
            <p className="mt-1 text-sm text-slate-500">
              Esta pantalla no permite asignar Administrador de plataforma.
            </p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {company.role_options.map((role) => (
                <label
                  key={role.id}
                  className="flex gap-3 rounded-2xl border p-4 text-sm"
                >
                  <input
                    type="checkbox"
                    disabled={!editable}
                    checked={roleIds.includes(role.id)}
                    onChange={() => toggleRole(role.id)}
                    className="mt-1 h-4 w-4"
                  />
                  <span>
                    <span className="block font-bold">{role.name}</span>
                    <span className="mt-1 block text-xs text-slate-500">
                      {role.description ?? role.code}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </section>

          <section className="mt-6">
            <h3 className="font-black text-slate-950">Sedes asignadas</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {company.sites.map((site) => {
                const checked = siteIds.includes(site.id);
                return (
                  <div key={site.id} className="rounded-2xl border p-4 text-sm">
                    <label className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        disabled={!editable}
                        checked={checked}
                        onChange={() => toggleSite(site.id)}
                        className="mt-1 h-4 w-4"
                      />
                      <span>
                        <span className="block font-bold">{site.name}</span>
                        <span className="text-xs text-slate-500">
                          {site.city} · {site.status}
                        </span>
                      </span>
                    </label>
                    {checked && (
                      <label className="mt-3 flex items-center gap-2 text-xs font-bold text-slate-600">
                        <input
                          type="radio"
                          disabled={!editable}
                          name="default_site"
                          checked={defaultSiteId === site.id}
                          onChange={() => setDefaultSiteId(site.id)}
                        />
                        Sede principal
                      </label>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

          {willNeedDentistProfile && (
            <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <p className="font-black">Este usuario tendrá rol clínico, pero no tiene perfil odontológico.</p>
              <p className="mt-1">
                Para trabajar como odontólogo, Dentia necesita un perfil profesional vinculado al mismo usuario,
                empresa y sedes seleccionadas.
              </p>
              {editable && (
                <label className="mt-3 flex items-center gap-2 font-bold">
                  <input
                    type="checkbox"
                    checked={ensureDentistProfile}
                    onChange={(event) => setEnsureDentistProfile(event.target.checked)}
                  />
                  Crear o vincular perfil de odontólogo al guardar
                </label>
              )}
              <p className="mt-2 text-xs">
                También puede gestionarse luego desde Configuración → Odontólogos, evitando perfiles duplicados.
              </p>
            </div>
          )}

          {editable && (
            <div className="mt-6 flex flex-col gap-3 border-t pt-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm font-semibold text-slate-500">
                El usuario debe cerrar sesión y volver a iniciar para actualizar sus permisos.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-xl border px-4 py-3 font-bold"
                >
                  Cancelar
                </button>
                <button
                  disabled={saving || !roleIds.length || !siteIds.length || !defaultSiteId}
                  className="rounded-xl bg-green-700 px-4 py-3 font-bold text-white disabled:opacity-50"
                >
                  {saving ? "Guardando…" : "Guardar cambios"}
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-bold uppercase text-slate-400">{label}</p>
      <p className="mt-1 rounded-xl bg-slate-50 px-3 py-3 text-sm font-semibold text-slate-700">
        {value}
      </p>
    </div>
  );
}
