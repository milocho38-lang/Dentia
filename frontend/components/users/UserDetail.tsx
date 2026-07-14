"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Alert } from "@/components/shared/Alert";
import { Spinner } from "@/components/shared/Spinner";
import { ConfirmDialog } from "@/components/users/ConfirmDialog";
import { TemporaryPasswordDialog } from "@/components/users/TemporaryPasswordDialog";
import { useAuth } from "@/hooks/useAuth";
import {
  changeUserStatus,
  enableClinicalRole,
  getAccessOptions,
  getUser,
  getUserAudit,
  getUserSessions,
  resetUserPassword,
  revokeAllUserSessions,
  revokeUserSession,
  updateUserRoles,
  updateUserSites,
} from "@/services/userService";
import type {
  AccessOptions,
  ManagedUser,
  UserAuditEvent,
  UserSession,
} from "@/types/user";

type Tab = "info" | "access" | "sessions" | "audit";

function formatDate(value: string | null) {
  if (!value) return "Nunca";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function UserDetail({ userId }: { userId: string }) {
  const { hasPermission } = useAuth();
  const [user, setUser] = useState<ManagedUser | null>(null);
  const [tab, setTab] = useState<Tab>("info");
  const [options, setOptions] = useState<AccessOptions | null>(null);
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [audit, setAudit] = useState<UserAuditEvent[]>([]);
  const [roleIds, setRoleIds] = useState<string[]>([]);
  const [siteIds, setSiteIds] = useState<string[]>([]);
  const [defaultSiteId, setDefaultSiteId] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<{
    title: string;
    description: string;
    label: string;
    action: () => Promise<void>;
    tone?: "danger" | "primary";
  } | null>(null);

  const loadUser = useCallback(async () => {
    setLoading(true);
    try {
      const loaded = await getUser(userId);
      setUser(loaded);
      setRoleIds(loaded.roles.map((role) => role.id));
      setSiteIds(loaded.sites.map((site) => site.id));
      setDefaultSiteId(loaded.default_site_id ?? "");
    } catch {
      setError("No fue posible cargar el usuario.");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (tab === "access" && !options) {
      getAccessOptions().then(setOptions).catch(() => {
        setError("No fue posible cargar las opciones de acceso.");
      });
    }
    if (tab === "sessions" && hasPermission("sessions.view_all")) {
      getUserSessions(userId).then(setSessions).catch(() => {
        setError("No fue posible cargar las sesiones.");
      });
    }
    if (tab === "audit" && hasPermission("audit.view")) {
      getUserAudit(userId).then(setAudit).catch(() => {
        setError("No fue posible cargar la auditoría.");
      });
    }
  }, [hasPermission, options, tab, userId]);

  async function runConfirmedAction() {
    if (!confirmation) return;
    setSaving(true);
    setError(null);
    try {
      await confirmation.action();
      setConfirmation(null);
      await loadUser();
    } catch {
      setError("No fue posible completar la acción.");
    } finally {
      setSaving(false);
    }
  }

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 text-slate-500">
        <Spinner className="h-7 w-7 text-dentia-primary" />
        Cargando usuario…
      </div>
    );
  }

  const tabs: { id: Tab; label: string; visible: boolean }[] = [
    { id: "info", label: "Información", visible: true },
    {
      id: "access",
      label: "Acceso",
      visible:
        hasPermission("users.assign_roles") ||
        hasPermission("users.assign_sites"),
    },
    {
      id: "sessions",
      label: "Sesiones",
      visible: hasPermission("sessions.view_all"),
    },
    { id: "audit", label: "Auditoría", visible: hasPermission("audit.view") },
  ];
  const roleCodes = user.roles.map((role) => role.code);
  const hasClinicalAdminRole = roleCodes.includes("DENTIST_ADMIN");
  const hasClinicalRole =
    hasClinicalAdminRole || roleCodes.includes("DENTIST");
  const hasAdministratorRole = roleCodes.includes("ADMINISTRATOR");
  const suggestedClinicalRole: "DENTIST" | "DENTIST_ADMIN" =
    hasAdministratorRole ? "DENTIST_ADMIN" : "DENTIST";

  return (
    <div className="mx-auto max-w-6xl">
      <Link
        href="/configuracion/usuarios"
        className="text-sm font-bold text-green-700 hover:underline"
      >
        ← Volver a usuarios
      </Link>
      <div className="mt-5 flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-bold text-slate-950">{user.name}</h1>
            <span
              className={`rounded-full px-3 py-1 text-xs font-bold ${
                user.is_locked
                  ? "bg-red-50 text-red-700"
                  : user.status === "Activo"
                    ? "bg-green-50 text-green-700"
                    : "bg-slate-100 text-slate-600"
              }`}
            >
              {user.is_locked ? "Bloqueado" : user.status}
            </span>
          </div>
          <p className="mt-2 text-sm text-slate-500">{user.email}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {hasPermission("users.update") && (
            <Link
              href={`/configuracion/usuarios/${user.id}/editar`}
              className="inline-flex min-h-11 items-center rounded-xl border border-slate-300 px-4 font-bold text-slate-700 hover:bg-slate-50"
            >
              Editar
            </Link>
          )}
          {hasPermission("users.reset_password") && (
            <button
              onClick={() =>
                setConfirmation({
                  title: "Restablecer contraseña",
                  description:
                    "Se cerrarán todas las sesiones y se generará una contraseña temporal visible una sola vez.",
                  label: "Restablecer",
                  action: async () => {
                    const response = await resetUserPassword(user.id);
                    setPassword(response.temporary_password);
                  },
                })
              }
              className="min-h-11 rounded-xl border border-slate-300 px-4 font-bold text-slate-700 hover:bg-slate-50"
            >
              Resetear contraseña
            </button>
          )}
          {user.is_locked && hasPermission("users.unlock") && (
            <button
              onClick={() =>
                setConfirmation({
                  title: "Desbloquear usuario",
                  description:
                    "Se limpiarán el bloqueo temporal y los intentos fallidos.",
                  label: "Desbloquear",
                  tone: "primary",
                  action: async () => {
                    await changeUserStatus(user.id, "unlock");
                  },
                })
              }
              className="min-h-11 rounded-xl bg-amber-500 px-4 font-bold text-white"
            >
              Desbloquear
            </button>
          )}
        </div>
      </div>

      {error && <div className="mt-5"><Alert tone="error">{error}</Alert></div>}

      <div className="mt-7 flex gap-1 overflow-x-auto border-b border-slate-200">
        {tabs.filter((item) => item.visible).map((item) => (
          <button
            key={item.id}
            onClick={() => setTab(item.id)}
            className={`border-b-2 px-4 py-3 text-sm font-bold ${
              tab === item.id
                ? "border-dentia-primary text-green-700"
                : "border-transparent text-slate-500"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === "info" && (
        <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_320px]">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">Datos del usuario</h2>
            <dl className="mt-5 grid gap-5 sm:grid-cols-2">
              {[
                ["Correo", user.email],
                ["Teléfono", user.phone ?? "No registrado"],
                ["Sede predeterminada", user.default_site_name ?? "Sin sede"],
                ["Último acceso", formatDate(user.last_login_at)],
                ["Creado", formatDate(user.created_at)],
                [
                  "Cambio obligatorio",
                  user.must_change_password ? "Pendiente" : "No requerido",
                ],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs font-bold uppercase tracking-wide text-slate-400">
                    {label}
                  </dt>
                  <dd className="mt-1 text-sm font-semibold text-slate-800">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">Estado</h2>
            <div className="mt-5 space-y-3">
              {user.status !== "Activo" && hasPermission("users.update") && (
                <button
                  onClick={() =>
                    setConfirmation({
                      title: "Activar usuario",
                      description:
                        "El usuario podrá iniciar sesión con sus roles y sedes asignados.",
                      label: "Activar",
                      tone: "primary",
                      action: async () => {
                        await changeUserStatus(user.id, "activate");
                      },
                    })
                  }
                  className="min-h-11 w-full rounded-xl bg-dentia-primary px-4 font-bold text-white"
                >
                  Activar
                </button>
              )}
              {user.status === "Activo" && hasPermission("users.update") && (
                <button
                  onClick={() =>
                    setConfirmation({
                      title: "Suspender usuario",
                      description:
                        "El usuario perderá acceso y se revocarán sus sesiones.",
                      label: "Suspender",
                      action: async () => {
                        await changeUserStatus(user.id, "suspend");
                      },
                    })
                  }
                  className="min-h-11 w-full rounded-xl border border-orange-300 px-4 font-bold text-orange-700"
                >
                  Suspender
                </button>
              )}
              {user.status !== "Inactivo" &&
                hasPermission("users.deactivate") && (
                  <button
                    onClick={() =>
                      setConfirmation({
                        title: "Desactivar usuario",
                        description:
                          "El registro se conservará, pero el usuario perderá acceso.",
                        label: "Desactivar",
                        action: async () => {
                          await changeUserStatus(user.id, "deactivate");
                        },
                      })
                    }
                    className="min-h-11 w-full rounded-xl border border-red-300 px-4 font-bold text-red-700"
                  >
                    Desactivar
                  </button>
                )}
            </div>
          </section>
        </div>
      )}

      {tab === "access" && options && (
        <div className="mt-6 grid gap-5 lg:grid-cols-2">
          <section className="rounded-2xl border border-green-200 bg-green-50 p-6 shadow-sm lg:col-span-2">
            <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-green-700">
                  Función administrativa y clínica
                </p>
                <h2 className="mt-2 text-lg font-black text-slate-950">
                  {hasClinicalRole
                    ? "Este usuario ya tiene función clínica"
                    : "Habilitar función clínica para este usuario"}
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Esta acción conserva los roles actuales y agrega el rol clínico
                  correspondiente junto con el perfil odontólogo. Después de
                  aplicarla, el usuario debe cerrar sesión e iniciar nuevamente
                  para recibir permisos actualizados.
                </p>
                {hasAdministratorRole && (
                  <p className="mt-2 text-sm font-semibold text-green-800">
                    El usuario conservará ADMINISTRATOR y sumará DENTIST_ADMIN.
                  </p>
                )}
              </div>
              {hasPermission("users.assign_roles") &&
                hasPermission("sites.manage") && (
                  <button
                    disabled={saving || hasClinicalAdminRole}
                    onClick={() =>
                      setConfirmation({
                        title: "Habilitar función clínica",
                        description:
                          "Se creará o reutilizará el perfil odontólogo, se agregará el rol clínico sin retirar roles existentes y se revocarán sesiones para actualizar permisos en el próximo inicio de sesión.",
                        label: hasClinicalRole
                          ? "Actualizar función clínica"
                          : "Habilitar",
                        tone: "primary",
                        action: async () => {
                          setUser(
                            await enableClinicalRole(
                              user.id,
                              suggestedClinicalRole,
                            ),
                          );
                        },
                      })
                    }
                    className="min-h-11 rounded-xl bg-green-700 px-5 font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {hasClinicalAdminRole
                      ? "Función clínica activa"
                      : "Habilitar función clínica"}
                  </button>
                )}
            </div>
          </section>
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">Roles</h2>
            <div className="mt-4 space-y-2">
              {options.roles.map((role) => (
                <label key={role.id} className="flex gap-3 rounded-xl border border-slate-200 p-3">
                  <input
                    type="checkbox"
                    disabled={!hasPermission("users.assign_roles")}
                    checked={roleIds.includes(role.id)}
                    onChange={(event) =>
                      setRoleIds((current) =>
                        event.target.checked
                          ? [...current, role.id]
                          : current.filter((id) => id !== role.id),
                      )
                    }
                    className="mt-1 accent-green-600"
                  />
                  <span>
                    <span className="block text-sm font-bold">{role.name}</span>
                    <span className="text-xs text-slate-500">{role.description}</span>
                  </span>
                </label>
              ))}
            </div>
            {hasPermission("users.assign_roles") && (
              <button
                disabled={saving || !roleIds.length}
                onClick={async () => {
                  setSaving(true);
                  try {
                    setUser(await updateUserRoles(user.id, roleIds));
                  } finally {
                    setSaving(false);
                  }
                }}
                className="mt-5 min-h-11 w-full rounded-xl bg-dentia-primary font-bold text-white disabled:opacity-50"
              >
                Guardar roles
              </button>
            )}
          </section>
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900">Sedes</h2>
            <div className="mt-4 space-y-2">
              {options.sites.map((site) => (
                <label key={site.id} className="flex items-center gap-3 rounded-xl border border-slate-200 p-3">
                  <input
                    type="checkbox"
                    disabled={!hasPermission("users.assign_sites")}
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
                    className="accent-green-600"
                  />
                  <span className="text-sm font-bold">{site.name}</span>
                </label>
              ))}
            </div>
            <select
              disabled={!hasPermission("users.assign_sites")}
              value={defaultSiteId}
              onChange={(event) => setDefaultSiteId(event.target.value)}
              className="mt-5 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4"
            >
              <option value="">Sede predeterminada</option>
              {options.sites
                .filter((site) => siteIds.includes(site.id))
                .map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.name}
                  </option>
                ))}
            </select>
            {hasPermission("users.assign_sites") && (
              <button
                disabled={saving || !siteIds.length || !defaultSiteId}
                onClick={async () => {
                  setSaving(true);
                  try {
                    setUser(
                      await updateUserSites(
                        user.id,
                        siteIds,
                        defaultSiteId,
                      ),
                    );
                  } finally {
                    setSaving(false);
                  }
                }}
                className="mt-5 min-h-11 w-full rounded-xl bg-dentia-primary font-bold text-white disabled:opacity-50"
              >
                Guardar sedes
              </button>
            )}
          </section>
        </div>
      )}

      {tab === "sessions" && (
        <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 p-5">
            <h2 className="text-lg font-bold text-slate-900">Sesiones</h2>
            {hasPermission("sessions.revoke_all") && (
              <button
                onClick={() =>
                  setConfirmation({
                    title: "Revocar todas las sesiones",
                    description:
                      "El usuario deberá iniciar sesión nuevamente en todos sus dispositivos.",
                    label: "Revocar todas",
                    action: async () => {
                      await revokeAllUserSessions(user.id);
                      setSessions(await getUserSessions(user.id));
                    },
                  })
                }
                className="text-sm font-bold text-red-700"
              >
                Revocar todas
              </button>
            )}
          </div>
          <div className="divide-y divide-slate-100">
            {sessions.map((item) => (
              <div key={item.id} className="flex flex-col justify-between gap-4 p-5 sm:flex-row">
                <div>
                  <p className="font-bold text-slate-800">
                    {item.active_site_name ?? "Sin sede"}
                    <span className={`ml-2 rounded-full px-2 py-1 text-xs ${
                      item.is_active ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-500"
                    }`}>
                      {item.is_active ? "Activa" : "Revocada"}
                    </span>
                  </p>
                  <p className="mt-2 text-xs text-slate-500">
                    Última actividad: {formatDate(item.last_seen_at)}
                  </p>
                  <p className="mt-1 max-w-2xl truncate text-xs text-slate-400">
                    {item.ip_address ?? "IP no disponible"} · {item.user_agent ?? "Dispositivo no identificado"}
                  </p>
                </div>
                {item.is_active && hasPermission("sessions.revoke_all") && (
                  <button
                    onClick={() =>
                      setConfirmation({
                        title: "Revocar sesión",
                        description: "Esta sesión dejará de ser válida inmediatamente.",
                        label: "Revocar",
                        action: async () => {
                          await revokeUserSession(user.id, item.id);
                          setSessions(await getUserSessions(user.id));
                        },
                      })
                    }
                    className="text-sm font-bold text-red-700"
                  >
                    Revocar
                  </button>
                )}
              </div>
            ))}
            {!sessions.length && (
              <p className="p-10 text-center text-sm text-slate-500">
                No hay sesiones registradas.
              </p>
            )}
          </div>
        </section>
      )}

      {tab === "audit" && (
        <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">Auditoría</h2>
          <div className="mt-5 space-y-4">
            {audit.map((event) => (
              <article key={event.id} className="border-l-2 border-green-200 pl-4">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-bold text-slate-800">{event.action}</p>
                  <span className="rounded-full bg-green-50 px-2 py-0.5 text-[11px] font-bold text-green-700">
                    {event.result}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {formatDate(event.occurred_at)}
                </p>
                {event.detail && (
                  <pre className="mt-2 overflow-x-auto rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
                    {JSON.stringify(event.detail, null, 2)}
                  </pre>
                )}
              </article>
            ))}
            {!audit.length && (
              <p className="py-8 text-center text-sm text-slate-500">
                No hay eventos administrativos.
              </p>
            )}
          </div>
        </section>
      )}

      <ConfirmDialog
        open={Boolean(confirmation)}
        title={confirmation?.title ?? ""}
        description={confirmation?.description ?? ""}
        confirmLabel={confirmation?.label ?? "Confirmar"}
        tone={confirmation?.tone}
        busy={saving}
        onClose={() => setConfirmation(null)}
        onConfirm={runConfirmedAction}
      />
      <TemporaryPasswordDialog
        password={password}
        onClose={() => setPassword(null)}
      />
    </div>
  );
}
