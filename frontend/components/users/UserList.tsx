"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { listUsers } from "@/services/userService";
import type { ManagedUser, UserListResponse } from "@/types/user";

const statusClasses: Record<string, string> = {
  Activo: "bg-green-50 text-green-700",
  Pendiente: "bg-amber-50 text-amber-700",
  Suspendido: "bg-orange-50 text-orange-700",
  Inactivo: "bg-slate-100 text-slate-600",
};

export function UserList() {
  const { hasPermission } = useAuth();
  const [response, setResponse] = useState<UserListResponse | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({ page: String(page), page_size: "20" });
    if (search.trim()) params.set("search", search.trim());
    if (status) params.set("status", status);
    try {
      setResponse(await listUsers(`?${params}`));
    } catch {
      setError("No fue posible cargar los usuarios.");
    } finally {
      setLoading(false);
    }
  }, [page, search, status]);

  useEffect(() => {
    load();
  }, [load]);

  function handleFilter(event: FormEvent) {
    event.preventDefault();
    setPage(1);
    load();
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
            Configuración
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Usuarios</h1>
          <p className="mt-2 text-sm text-slate-500">
            Administra acceso, roles, sedes y sesiones.
          </p>
        </div>
        {hasPermission("users.create") &&
          hasPermission("users.assign_roles") &&
          hasPermission("users.assign_sites") && (
          <Link
            href="/configuracion/usuarios/nuevo"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-dentia-primary px-5 font-bold text-white hover:bg-green-700"
          >
            Crear usuario
          </Link>
          )}
      </div>

      <form
        onSubmit={handleFilter}
        className="mt-7 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-[1fr_220px_auto]"
      >
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Buscar por nombre o correo"
          className="min-h-11 rounded-xl border border-slate-300 px-4"
        />
        <select
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-4"
        >
          <option value="">Todos los estados</option>
          <option>Pendiente</option>
          <option>Activo</option>
          <option>Suspendido</option>
          <option>Inactivo</option>
        </select>
        <button className="min-h-11 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50">
          Buscar
        </button>
      </form>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}

      <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center gap-3 py-16 text-slate-500">
            <Spinner className="h-6 w-6 text-dentia-primary" />
            Cargando usuarios…
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  {["Usuario", "Roles", "Sede", "Estado", "Sesiones", ""].map(
                    (heading) => (
                      <th
                        key={heading}
                        className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500"
                      >
                        {heading}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {response?.items.map((user: ManagedUser) => (
                  <tr key={user.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-4">
                      <p className="font-bold text-slate-900">{user.name}</p>
                      <p className="mt-1 text-sm text-slate-500">{user.email}</p>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex max-w-xs flex-wrap gap-1">
                        {user.roles.map((role) => (
                          <span
                            key={role.id}
                            className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold text-slate-600"
                          >
                            {role.name}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">
                      {user.default_site_name ?? "Sin sede"}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                          user.is_locked
                            ? "bg-red-50 text-red-700"
                            : statusClasses[user.status]
                        }`}
                      >
                        {user.is_locked ? "Bloqueado" : user.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">
                      {user.active_sessions}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        href={`/configuracion/usuarios/${user.id}`}
                        className="text-sm font-bold text-green-700 hover:underline"
                      >
                        Ver detalle
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!response?.items.length && (
              <p className="py-14 text-center text-sm text-slate-500">
                No se encontraron usuarios.
              </p>
            )}
          </div>
        )}
      </div>

      {response && response.pages > 1 && (
        <div className="mt-5 flex items-center justify-between text-sm">
          <span className="text-slate-500">{response.total} usuarios</span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((current) => current - 1)}
              className="rounded-xl border border-slate-300 px-4 py-2 font-bold disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              disabled={page >= response.pages}
              onClick={() => setPage((current) => current + 1)}
              className="rounded-xl border border-slate-300 px-4 py-2 font-bold disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
