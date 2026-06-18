"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function AccessDeniedPage() {
  const { hasPermission } = useAuth();
  const canViewDashboard = hasPermission("dashboard.view");

  return (
    <div className="mx-auto flex min-h-[65vh] max-w-xl items-center justify-center">
      <section className="w-full rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-10">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 text-amber-600">
          <svg viewBox="0 0 24 24" className="h-8 w-8" fill="none">
            <path
              d="M12 9v4m0 4h.01M10.3 4.3 3.2 17a2 2 0 0 0 1.7 3h14.2a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <p className="mt-6 text-xs font-bold uppercase tracking-[0.16em] text-amber-600">
          Acceso restringido
        </p>
        <h1 className="mt-3 text-2xl font-bold text-slate-900">
          No tienes permisos para esta sección
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Si necesitas acceder, solicita al administrador que revise los
          permisos asociados a tu cuenta.
        </p>
        {canViewDashboard && (
          <Link
            href="/dashboard"
            className="mt-7 inline-flex min-h-11 items-center justify-center rounded-xl bg-dentia-primary px-5 py-2.5 text-sm font-bold text-white transition hover:bg-green-700"
          >
            Volver al dashboard
          </Link>
        )}
      </section>
    </div>
  );
}
