import type { Metadata } from "next";
import { screenshots } from "@/lib/screenshots";
import { siteDescription, siteIsIndexable, siteName, siteUrl } from "@/lib/site";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Dentia — Gestión odontológica en un solo lugar",
    template: "%s | Dentia",
  },
  description: siteDescription,
  alternates: { canonical: "/" },
  robots: siteIsIndexable ? { index: true, follow: true } : { index: false, follow: false },
  openGraph: {
    type: "website",
    locale: "es_LA",
    siteName,
    title: "Dentia — Gestión odontológica en un solo lugar",
    description: siteDescription,
    url: "/",
    images: [
      {
        url: screenshots.hero.src,
        width: screenshots.hero.width,
        height: screenshots.hero.height,
        alt: "Dashboard de Dentia con seguimiento de pacientes",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Dentia — Gestión odontológica en un solo lugar",
    description: siteDescription,
    images: [screenshots.hero.src],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <a className="skip-link" href="#contenido-principal">
          Saltar al contenido principal
        </a>
        <SiteHeader />
        <main id="contenido-principal">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
