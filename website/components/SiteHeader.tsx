"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { appUrl, mainNavigation } from "@/lib/site";
import { Brand } from "./Brand";

export function SiteHeader() {
  const pathname = usePathname();
  const [openOnPath, setOpenOnPath] = useState<string | null>(null);
  const open = openOnPath === pathname;

  return (
    <header className="site-header">
      <div className="site-header__inner container">
        <Brand />
        <button
          className="menu-toggle"
          type="button"
          aria-expanded={open}
          aria-controls="primary-navigation"
          aria-label={open ? "Cerrar menú" : "Abrir menú"}
          onClick={() => setOpenOnPath(open ? null : pathname)}
        >
          <span />
          <span />
          <span />
        </button>
        <nav
          id="primary-navigation"
          className={`primary-navigation ${open ? "primary-navigation--open" : ""}`}
          aria-label="Navegación principal"
        >
          <div className="primary-navigation__links">
            {mainNavigation.map((item) => (
              <Link
                href={item.href}
                key={item.href}
                aria-current={pathname === item.href ? "page" : undefined}
              >
                {item.label}
              </Link>
            ))}
          </div>
          <div className="primary-navigation__actions">
            <a className="button button--ghost" href={`${appUrl}/login`}>
              Iniciar sesión
            </a>
            <Link className="button button--primary" href="/demo">
              Solicitar demostración
            </Link>
          </div>
        </nav>
      </div>
    </header>
  );
}
