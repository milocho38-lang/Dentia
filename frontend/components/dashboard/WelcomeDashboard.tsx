"use client";

import { Alert } from "@/components/shared/Alert";
import { useAuth } from "@/hooks/useAuth";

const roleLabels: Record<string, string> = {
  ADMINISTRATOR: "Administrador",
  SECRETARY: "Secretaria",
  DENTIST: "Odontólogo",
  DENTIST_ADMIN: "Odontólogo Administrador",
};

const readinessItems = [
  {
    title: "Acceso seguro",
    description: "Tu sesión está activa y protegida.",
    icon: (
      <path
        d="M7 10V8a5 5 0 0 1 10 0v2m-9 0h8a2 2 0 0 1 2 2v7H6v-7a2 2 0 0 1 2-2Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    ),
  },
  {
    title: "Permisos preparados",
    description: "La navegación se adapta a tus responsabilidades.",
    icon: (
      <path
        d="M9 12.5 11 14l4-5m5 3c0 5-3.5 8-8 9-4.5-1-8-4-8-9V5.5L12 3l8 2.5V12Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
  },
  {
    title: "Contexto de sede",
    description: "La sesión conserva la sede operativa asignada.",
    icon: (
      <path
        d="M12 21s7-5.1 7-12a7 7 0 1 0-14 0c0 6.9 7 12 7 12Zm0-9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
  },
];

export function WelcomeDashboard() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  const firstName = user.name.trim().split(/\s+/)[0] || user.name;

  return (
    <div className="mx-auto max-w-6xl">
      <section className="relative overflow-hidden rounded-3xl bg-slate-950 px-7 py-8 text-white shadow-xl shadow-slate-900/10 sm:px-10 sm:py-10">
        <div className="absolute -right-20 -top-28 h-80 w-80 rounded-full bg-green-500/20 blur-3xl" />
        <div className="absolute bottom-0 right-8 h-40 w-40 rounded-full bg-emerald-400/10 blur-2xl" />
        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-bold text-green-200 ring-1 ring-white/10">
            <span className="h-2 w-2 rounded-full bg-green-400" />
            Sesión activa
          </span>
          <h1 className="mt-6 text-3xl font-bold tracking-tight sm:text-4xl">
            Hola, {firstName}.
          </h1>
          <p className="mt-3 max-w-xl text-base leading-7 text-slate-300">
            Bienvenido a Dentia. Este es tu punto de partida para una gestión
            odontológica clara, segura y ordenada.
          </p>
        </div>
      </section>

      {user.must_change_password && (
        <div className="mt-6">
          <Alert tone="warning">
            Tu cuenta requiere cambio de contraseña. El flujo de cambio será
            habilitado en una siguiente entrega; contacta al administrador si
            necesitas renovar tu credencial.
          </Alert>
        </div>
      )}

      <section className="mt-7 grid gap-4 md:grid-cols-3">
        {readinessItems.map((item) => (
          <article
            key={item.title}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-green-50 text-dentia-primary">
              <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none">
                {item.icon}
              </svg>
            </div>
            <h2 className="mt-5 text-base font-bold text-slate-900">
              {item.title}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              {item.description}
            </p>
          </article>
        ))}
      </section>

      <section className="mt-7 grid gap-5 lg:grid-cols-[1.35fr_0.65fr]">
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
                Inicio
              </p>
              <h2 className="mt-2 text-xl font-bold text-slate-900">
                Tu espacio está preparado
              </h2>
            </div>
            <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-bold text-green-700">
              C005E
            </span>
          </div>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600">
            Los módulos operativos se incorporarán progresivamente. Dentia solo
            mostrará opciones disponibles y autorizadas para tu usuario.
          </p>
          <div className="mt-6 flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 p-4">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-dentia-primary shadow-sm">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
                <path
                  d="m5 12 4 4L19 6"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
            <div>
              <p className="text-sm font-bold text-slate-800">
                Autenticación completada
              </p>
              <p className="mt-0.5 text-xs text-slate-500">
                Login, renovación y cierre de sesión disponibles.
              </p>
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
            Tu perfil
          </p>
          <p className="mt-3 truncate text-base font-bold text-slate-900">
            {user.name}
          </p>
          <p className="mt-1 truncate text-sm text-slate-500">{user.email}</p>
          <div className="mt-5 flex flex-wrap gap-2">
            {user.roles.map((role) => (
              <span
                key={role}
                className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700"
              >
                {roleLabels[role] ?? role}
              </span>
            ))}
          </div>
          <p className="mt-5 text-xs text-slate-400">
            {user.permissions.length} permisos efectivos
          </p>
        </article>
      </section>
    </div>
  );
}
