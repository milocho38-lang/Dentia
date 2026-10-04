import type { Metadata } from "next";
import Link from "next/link";
import { FinalCta } from "@/components/FinalCta";
import { PageHero } from "@/components/PageHero";

export const metadata: Metadata = {
  title: "Planes",
  description: "Conoce las opciones de Dentia para odontólogos independientes, consultorios y clínicas.",
  alternates: { canonical: "/precios" },
};

const plans = [
  {
    name: "Práctica independiente",
    description: "Para odontólogos que atienden y administran su propia consulta.",
    detail: "Revisa en la demostración cómo Dentia conecta el trabajo clínico y administrativo de una práctica individual.",
  },
  {
    name: "Consultorio o clínica",
    description: "Para equipos que coordinan varios odontólogos, usuarios o sedes.",
    detail: "La propuesta se prepara con el contexto de tu equipo y la forma en que hoy organizan la atención.",
  },
] as const;

export default function PricingPage() {
  return (
    <>
      <PageHero eyebrow="Planes Dentia" title="Una propuesta según la forma en que trabaja tu práctica.">
        <p>
          Cuéntanos si trabajas de forma independiente o con un equipo. En la demostración revisamos el
          producto y la opción que corresponde a tu operación.
        </p>
      </PageHero>
      <section className="section">
        <div className="container pricing-tabs">
          <section className="pricing-country" aria-labelledby="plans-title">
            <div className="pricing-country__heading">
              <div>
                <p className="eyebrow">Opciones de servicio</p>
                <h2 id="plans-title">Elige el contexto que más se parece al tuyo.</h2>
              </div>
              <p>Dentia está en lanzamiento y prepara cada propuesta después de conocer la práctica.</p>
            </div>
            <div className="pricing-grid">
              {plans.map((plan, index) => (
                <article className={`pricing-plan ${index === 0 ? "pricing-plan--featured" : ""}`} key={plan.name}>
                  <h3>{plan.name}</h3>
                  <span className="pricing-plan__amount">Conoce la propuesta</span>
                  <p>{plan.description}</p>
                  <p>{plan.detail}</p>
                  <Link className="text-link" href="/demo">Solicitar una demostración</Link>
                </article>
              ))}
            </div>
          </section>
          <div className="pricing-action">
            <Link className="button button--primary" href="/demo">Conocer Dentia y la propuesta</Link>
          </div>
        </div>
      </section>
      <FinalCta />
    </>
  );
}
