import Link from "next/link";
import { FinalCta } from "@/components/FinalCta";
import { ProductCarousel } from "@/components/ProductCarousel";
import { ProductScreenshot } from "@/components/ProductScreenshot";
import { screenshots } from "@/lib/screenshots";

export default function HomePage() {
  return (
    <>
      <section className="hero section">
        <div className="container">
          <div className="hero__grid">
            <div className="hero__copy">
              <p className="eyebrow">Menos información dispersa</p>
              <h1>Tu consulta, del primer contacto al seguimiento, en un solo contexto.</h1>
              <p>
                Organiza citas, expediente clínico, tratamientos, documentos, pagos y próximos controles
                sin repartir el trabajo entre varias herramientas.
              </p>
              <div className="hero__actions">
                <Link className="button button--primary" href="/demo">
                  Solicitar demostración
                </Link>
                <Link className="button button--secondary" href="/producto">
                  Conocer Dentia
                </Link>
              </div>
              <span className="trust-line">
                En lanzamiento y validación con prácticas odontológicas reales en Colombia y Chile.
              </span>
            </div>
            <div className="hero__visual">
              <ProductScreenshot
                className="hero-shot"
                src={screenshots.hero}
                alt="Dashboard de Dentia con controles de pacientes pendientes, próximos y programados"
                priority
              />
            </div>
          </div>

          <div className="value-strip" aria-label="De información dispersa a una operación conectada">
            <div>
              <span>Antes</span>
              <strong>Información dispersa</strong>
              <p>Citas, documentos, saldos y controles en lugares diferentes.</p>
            </div>
            <span className="value-strip__arrow" aria-hidden="true">→</span>
            <div className="value-strip__dentia">
              <span>Con Dentia</span>
              <strong>Un solo contexto</strong>
              <p>La información del paciente acompaña cada paso del equipo.</p>
            </div>
            <span className="value-strip__arrow" aria-hidden="true">→</span>
            <div>
              <span>Resultado</span>
              <strong>Una operación más clara</strong>
              <p>Menos fragmentación para la práctica clínica y administrativa.</p>
            </div>
          </div>
        </div>
      </section>

      <ProductCarousel />

      <section className="audience section section--compact">
        <div className="container">
          <div className="section-heading section-heading--center">
            <p className="eyebrow">Crece a tu ritmo</p>
            <h2>Para ordenar una práctica pequeña sin sumar complejidad innecesaria.</h2>
          </div>
          <div className="audience-grid">
            <article className="audience-card">
              <span className="audience-card__label">Odontólogo independiente</span>
              <h3>Organiza tu consulta, incluso si tú mismo la administras.</h3>
              <p>
                Pasa de la agenda al expediente, registra lo realizado y consulta documentos, saldos y
                próximos controles sin reconstruir la historia del paciente en cada paso.
              </p>
              <Link className="text-link" href="/producto">Explorar el producto</Link>
            </article>
            <article className="audience-card audience-card--clinic">
              <span className="audience-card__label">Clínica o consultorio</span>
              <h3>Da acceso al equipo sin mezclar responsabilidades.</h3>
              <p>
                Organiza usuarios, permisos y sedes con información separada por empresa y acceso según el
                rol de cada persona.
              </p>
              <span className="feature-note">Organización multiempresa con acceso por roles</span>
            </article>
          </div>
        </div>
      </section>

      <section className="trust-section section section--tint">
        <div className="container">
          <div className="section-heading section-heading--center">
            <p className="eyebrow">Por qué Dentia</p>
            <h2>Tecnología que acompaña una operación clínica responsable.</h2>
          </div>
          <div className="trust-grid">
            <article className="trust-card trust-card--security">
              <span>01</span>
              <h3>Seguridad por diseño</h3>
              <p>
                Controles de acceso, separación entre organizaciones, conexiones HTTPS y trazabilidad para
                información sensible.
              </p>
              <Link className="text-link" href="/seguridad">Conocer la seguridad</Link>
            </article>
            <article className="trust-card">
              <span>02</span>
              <h3>Un flujo que puedes recorrer por partes</h3>
              <p>
                En la demostración puedes revisar agenda, pacientes, registro clínico, tratamientos,
                documentos, pagos y seguimiento según lo que hoy necesita tu práctica.
              </p>
            </article>
            <article className="trust-card">
              <span>03</span>
              <h3>Una demostración con tu contexto</h3>
              <p>
                Solicita una demostración enfocada en tu forma de trabajo y conoce un recorrido claro para
                adoptar Dentia por etapas.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="validation section section--compact">
        <div className="container validation__inner">
          <div>
            <p className="eyebrow">Validación real</p>
            <h2>Dentia está en lanzamiento y sigue aprendiendo de la práctica real.</h2>
            <p>
              La experiencia se valida con prácticas odontológicas reales de Colombia y Chile para seguir
              afinando el producto alrededor del trabajo clínico y administrativo cotidiano.
            </p>
          </div>
          <div className="validation__countries" aria-label="Países de validación">
            <span>Colombia</span>
            <span>Chile</span>
          </div>
        </div>
      </section>

      <section className="pricing-home section section--tint">
        <div className="container">
          <div className="section-heading section-heading--center">
            <p className="eyebrow">Planes Dentia</p>
            <h2>Conoce una propuesta para el tamaño de tu práctica.</h2>
            <p>Cuéntanos si trabajas de forma independiente o con un equipo para revisar la opción que corresponde.</p>
          </div>
          <div className="pricing-preview">
            <article className="price-card">
              <span className="price-card__country">Práctica independiente</span>
              <span className="price-card__amount">Una propuesta según tu operación</span>
              <p>Para quien atiende y administra su propia consulta.</p>
            </article>
            <article className="price-card">
              <span className="price-card__country">Consultorio o clínica</span>
              <span className="price-card__amount">Una propuesta según el equipo</span>
              <p>Para prácticas que coordinan varios odontólogos, usuarios o sedes.</p>
            </article>
          </div>
          <div className="pricing-action">
            <Link className="button button--primary" href="/precios">Conocer los planes</Link>
          </div>
        </div>
      </section>

      <FinalCta />
    </>
  );
}
