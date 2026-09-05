import type { Metadata } from "next";
import { DemoForm } from "@/components/DemoForm";
import { PageHero } from "@/components/PageHero";

export const metadata: Metadata = {
  title: "Solicitar demostración",
  description: "Solicita un recorrido de Dentia enfocado en tu práctica odontológica.",
  alternates: { canonical: "/demo" },
};

export default function DemoPage() {
  return (
    <>
      <PageHero eyebrow="Conoce Dentia" title="Una demostración enfocada en tu forma de trabajar.">
        <p>
          Cuéntanos cómo está organizada tu práctica para preparar un recorrido por los módulos que más
          pueden ayudarte hoy.
        </p>
      </PageHero>
      <section className="section">
        <div className="container demo-layout">
          <div>
            <p className="eyebrow">Qué puedes esperar</p>
            <h2>Una conversación sobre tu operación, no una presentación genérica.</h2>
            <p>
              Revisaremos el recorrido desde la agenda hasta el seguimiento y resolveremos preguntas sobre
              adopción, usuarios y crecimiento de la práctica.
            </p>
            <div className="demo-points" aria-label="Contenido de la demostración">
              <div className="demo-point"><span>Recorrido por los módulos relevantes para tu práctica.</span></div>
              <div className="demo-point"><span>Contexto para odontólogos independientes y clínicas.</span></div>
              <div className="demo-point"><span>Espacio para revisar implementación y próximos pasos.</span></div>
            </div>
          </div>
          <DemoForm />
        </div>
      </section>
    </>
  );
}
