const normalizeUrl = (value: string) => value.replace(/\/$/, "");

export const siteUrl = normalizeUrl(
  process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3010",
);

export const appUrl = normalizeUrl(
  process.env.NEXT_PUBLIC_APP_URL ?? "https://app.dentiapro.com",
);

export const siteIsIndexable =
  process.env.NEXT_PUBLIC_SITE_INDEXABLE?.toLowerCase() === "true";

export const siteName = "Dentia";
export const siteDescription =
  "Gestión odontológica para agenda, pacientes, historia clínica, tratamientos, consentimientos, pagos y seguimiento.";

export const mainNavigation = [
  { href: "/producto", label: "Producto" },
  { href: "/precios", label: "Precios" },
  { href: "/seguridad", label: "Seguridad" },
  { href: "/demo", label: "Solicitar demo" },
] as const;
