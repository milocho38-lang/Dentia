import type { Metadata } from "next";
import Link from "next/link";
import { FinalCta } from "@/components/FinalCta";
import { PageHero } from "@/components/PageHero";

export const metadata: Metadata = {
  title: "Precios",
  description: "Planes de Dentia para odontólogos independientes y clínicas en Colombia y Chile.",
  alternates: { canonical: "/precios" },
};

const pricing = {
  Colombia: [
    ["Independiente", "$85.000 COP", "1 odontólogo"],
    ["Clínica hasta 3 odontólogos", "$168.000 COP", "Hasta 3 odontólogos"],
    ["Clínica hasta 5 odontólogos", "$252.000 COP", "Hasta 5 odontólogos"],
    ["Clínica hasta 10 odontólogos", "$420.000 COP", "Hasta 10 odontólogos"],
    ["Más de 10", "Solicitar cotización", "Plan según la operación"],
  ],
  Chile: [
    ["Independiente", "$23.900 CLP", "1 odontólogo"],
    ["Clínica hasta 3 odontólogos", "$47.900 CLP", "Hasta 3 odontólogos"],
    ["Clínica hasta 5 odontólogos", "$70.900 CLP", "Hasta 5 odontólogos"],
    ["Clínica hasta 10 odontólogos", "$118.900 CLP", "Hasta 10 odontólogos"],
    ["Más de 10", "Solicitar cotización", "Plan según la operación"],
  ],
} as const;

export default function PricingPage() {
  return (
    <>
      <PageHero eyebrow="Planes Dentia" title="Precios para comenzar y crecer con claridad.">
        <p>
          Todos los planes incluyen las funcionalidades principales de Dentia. El plan cambia según el número
          de odontólogos activos en la práctica.
        </p>
      </PageHero>
      <section className="section">
        <div className="container pricing-tabs">
          {Object.entries(pricing).map(([country, plans]) => (
            <section className="pricing-country" key={country} aria-labelledby={`pricing-${country}`}>
              <div className="pricing-country__heading">
                <div>
                  <p className="eyebrow">Precios finales</p>
                  <h2 id={`pricing-${country}`}>{country}</h2>
                </div>
                <p>Valores mensuales con los impuestos aplicables incluidos según la estrategia comercial vigente.</p>
              </div>
              <div className="pricing-grid">
                {plans.map(([name, amount, detail], index) => (
                  <article className={`pricing-plan ${index === 0 ? "pricing-plan--featured" : ""}`} key={name}>
                    <h3>{name}</h3>
                    <span className="pricing-plan__amount">{amount}</span>
                    {amount !== "Solicitar cotización" && <span className="pricing-plan__period">por mes</span>}
                    <p>{detail}</p>
                  </article>
                ))}
              </div>
            </section>
          ))}
          <p className="launch-note">
            La tarifa especial de lanzamiento podrá mantenerse para clientes que ingresen durante esta etapa
            mientras permanezcan activos, sujeta a ajustes futuros de precio según las condiciones comerciales
            aplicables.
          </p>
          <div className="pricing-action">
            <Link className="button button--primary" href="/demo">Solicitar demostración</Link>
          </div>
        </div>
      </section>
      <FinalCta />
    </>
  );
}
