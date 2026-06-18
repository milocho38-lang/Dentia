"use client";

import { UserMenu } from "@/components/layout/UserMenu";
import { useAuth } from "@/hooks/useAuth";

export function AppHeader({ onMenuOpen }: { onMenuOpen: () => void }) {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-20 flex min-h-20 items-center justify-between border-b border-slate-200/80 bg-white/90 px-5 backdrop-blur-xl sm:px-7 lg:px-9">
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Abrir navegación"
          onClick={onMenuOpen}
          className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition hover:bg-slate-50 lg:hidden"
        >
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
            <path
              d="M5 7h14M5 12h14M5 17h14"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
            Espacio de trabajo
          </p>
          <p className="mt-1 text-sm font-bold text-slate-800">
            {user?.active_site_id ? "Sede activa" : "Dentia"}
          </p>
        </div>
      </div>
      <UserMenu />
    </header>
  );
}
