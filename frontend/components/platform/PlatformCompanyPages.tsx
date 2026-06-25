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
} from "@/services/platformService";
import type {
  PlatformCompanyDetail,
  PlatformCompanyInput,
  PlatformCompanyListItem,
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
        <section className="rounded-2xl border bg-white p-6 shadow-sm">
          <h2 className="font-black">Usuarios principales</h2>
          <div className="mt-4 space-y-3">
            {company.users.map((user) => (
              <div key={user.id} className="rounded-xl bg-slate-50 p-4 text-sm">
                <p className="font-bold">{user.name}</p>
                <p className="mt-1 text-slate-500">{user.email} · {user.status}</p>
                <p className="mt-1 text-xs font-bold text-slate-500">{user.roles.join(", ")}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
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
