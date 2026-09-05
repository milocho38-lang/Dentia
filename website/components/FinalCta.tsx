import Link from "next/link";

export function FinalCta() {
  return (
    <section className="final-cta section">
      <div className="container final-cta__inner">
        <div>
          <p className="eyebrow eyebrow--light">Un recorrido a tu medida</p>
          <h2>Conoce cómo funcionaría Dentia en tu práctica.</h2>
          <p>Te mostramos la plataforma con un recorrido enfocado en la forma en que trabajas hoy.</p>
        </div>
        <Link className="button button--light" href="/demo">
          Solicitar demostración
        </Link>
      </div>
    </section>
  );
}
