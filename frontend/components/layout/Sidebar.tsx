"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandMark } from "@/components/brand/BrandMark";
import { navigationItems } from "@/config/navigation";
import { useAuth } from "@/hooks/useAuth";

export function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();
  const { hasPermission } = useAuth();
  const visibleItems = navigationItems.filter((item) =>
    hasPermission(item.permission),
  );

  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="Cerrar navegación"
          className="fixed inset-0 z-30 bg-slate-950/35 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-slate-200 bg-white px-5 py-6 transition-transform duration-200 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between">
          <BrandMark />
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar navegación"
            className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100 lg:hidden"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
              <path
                d="m6 6 12 12M18 6 6 18"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        <div className="mt-10 space-y-7">
          {(["Operación", "Configuración"] as const).map((section) => {
            const sectionItems = visibleItems.filter(
              (item) => item.section === section,
            );
            if (!sectionItems.length) return null;
            return <div key={section}>
          <p className="px-3 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">
            {section}
          </p>
          <nav className="mt-3 space-y-1" aria-label={section}>
            {sectionItems.map((item) => {
              const active = pathname === item.href;
              const isAgenda = item.href === "/agenda";
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  aria-current={active ? "page" : undefined}
                  className={`flex min-h-12 items-center gap-3 rounded-xl px-3.5 text-sm font-bold transition ${
                    active
                      ? "bg-green-50 text-green-800"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <span
                    className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                      active
                        ? "bg-dentia-primary text-white"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
                      {isAgenda ? (
                        <path
                          d="M7 3v3m10-3v3M4.5 9h15M6 5h12a2 2 0 0 1 2 2v12H4V7a2 2 0 0 1 2-2Zm2 8h3v3H8v-3Z"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      ) : (
                        <path
                          d="M4 13h6V4H4v9Zm0 7h6v-4H4v4Zm10 0h6v-9h-6v9Zm0-12h6V4h-6v4Z"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinejoin="round"
                        />
                      )}
                    </svg>
                  </span>
                  {item.label}
                </Link>
              );
            })}
          </nav>
            </div>;
          })}
        </div>

        <div className="mt-auto rounded-2xl border border-green-100 bg-green-50/70 p-4">
          <div className="flex items-center gap-2 text-sm font-bold text-green-800">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            Sesión protegida
          </div>
          <p className="mt-2 text-xs leading-5 text-green-700/80">
            Tu acceso está vinculado a una sesión segura y auditada.
          </p>
        </div>
      </aside>
    </>
  );
}
