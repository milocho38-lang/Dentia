"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";

const roleLabels: Record<string, string> = {
  ADMINISTRATOR: "Administrador",
  SECRETARY: "Secretaria",
  DENTIST: "Odontólogo",
  DENTIST_ADMIN: "Odontólogo Administrador",
};

function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function UserMenu() {
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();

  if (!user) {
    return null;
  }

  async function handleLogout() {
    if (loggingOut) {
      return;
    }
    setLoggingOut(true);
    try {
      await logout();
    } finally {
      router.replace("/login");
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className="flex min-h-11 items-center gap-3 rounded-xl px-2 py-1.5 text-left transition hover:bg-slate-100"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-xs font-bold text-white">
          {initials(user.name)}
        </span>
        <span className="hidden max-w-40 sm:block">
          <span className="block truncate text-sm font-bold text-slate-800">
            {user.name}
          </span>
          <span className="block truncate text-xs text-slate-500">
            {roleLabels[user.roles[0]] ?? user.roles[0] ?? "Usuario"}
          </span>
        </span>
        <svg viewBox="0 0 20 20" className="hidden h-4 w-4 text-slate-400 sm:block">
          <path
            d="m6 8 4 4 4-4"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      </button>

      {open && (
        <>
          <button
            type="button"
            aria-label="Cerrar menú de usuario"
            className="fixed inset-0 z-40 cursor-default"
            onClick={() => setOpen(false)}
          />
          <div
            role="menu"
            className="absolute right-0 z-50 mt-2 w-72 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/10"
          >
            <div className="border-b border-slate-100 px-5 py-4">
              <p className="truncate text-sm font-bold text-slate-900">
                {user.name}
              </p>
              <p className="mt-1 truncate text-xs text-slate-500">{user.email}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {user.roles.map((role) => (
                  <span
                    key={role}
                    className="rounded-full bg-green-50 px-2.5 py-1 text-[11px] font-bold text-green-700"
                  >
                    {roleLabels[role] ?? role}
                  </span>
                ))}
              </div>
            </div>
            <button
              type="button"
              role="menuitem"
              disabled={loggingOut}
              onClick={handleLogout}
              className="flex min-h-12 w-full items-center gap-3 px-5 py-3 text-left text-sm font-bold text-red-700 transition hover:bg-red-50 disabled:opacity-60"
            >
              {loggingOut ? (
                <Spinner className="h-5 w-5" />
              ) : (
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
                  <path
                    d="M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4m5-4 3-3-3-3m3 3H9"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              )}
              {loggingOut ? "Cerrando sesión…" : "Cerrar sesión"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
