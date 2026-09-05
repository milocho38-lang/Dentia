import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Términos y condiciones",
  description: "Página reservada para los términos y condiciones públicos de Dentia.",
  alternates: { canonical: "/terminos" },
};

export default function TermsPage() {
  return (
    <section className="section empty-page">
      <article className="container narrow prose-card">
        <span className="legal-placeholder">Documento pendiente de revisión y publicación</span>
        <h1>Términos y condiciones</h1>
        <p>
          Esta ruta está lista para recibir los términos comerciales y de uso definitivos de Dentia una vez
          hayan sido revisados y aprobados.
        </p>
        <h2>Alcance de este marcador</h2>
        <p>
          El contenido actual identifica una dependencia previa al lanzamiento público. No constituye un
          contrato, una oferta ni reemplaza los términos que deberán regir el servicio.
        </p>
      </article>
    </section>
  );
}
