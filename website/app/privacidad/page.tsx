import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política de privacidad",
  description: "Página reservada para la política de privacidad pública de Dentia.",
  alternates: { canonical: "/privacidad" },
};

export default function PrivacyPage() {
  return (
    <section className="section empty-page">
      <article className="container narrow prose-card">
        <span className="legal-placeholder">Documento pendiente de revisión y publicación</span>
        <h1>Política de privacidad</h1>
        <p>
          Esta página está preparada dentro de la arquitectura del sitio. El texto legal definitivo será
          incorporado únicamente después de su revisión y aprobación correspondiente.
        </p>
        <h2>Antes de la publicación comercial</h2>
        <p>
          Dentia deberá documentar de forma clara el tratamiento de datos aplicable al sitio público, sus
          canales de contacto y los derechos de las personas usuarias. Este marcador no sustituye ese texto.
        </p>
      </article>
    </section>
  );
}
