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
              <p className="eyebrow">Gestión odontológica conectada</p>
              <h1>Toda tu consulta odontológica en un solo lugar.</h1>
              <p>
                Conecta agenda, pacientes, historia clínica, tratamientos, consentimientos, pagos y
                seguimiento en una plataforma diseñada para consultorios y clínicas odontológicas.
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
                En validación con prácticas odontológicas reales en Colombia y Chile.
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
            <h2>Para tu consulta de hoy y la clínica que quieres construir.</h2>
          </div>
          <div className="audience-grid">
            <article className="audience-card">
              <span className="audience-card__label">Odontólogo independiente</span>
              <h3>Organiza tu consulta, incluso si tú mismo la administras.</h3>
              <p>
                Mantén conectados pacientes, atención clínica, documentos y pagos sin depender de varias
                herramientas o de un equipo administrativo grande.
              </p>
              <Link className="text-link" href="/producto">Explorar el producto</Link>
            </article>
            <article className="audience-card audience-card--clinic">
              <span className="audience-card__label">Clínica o consultorio</span>
              <h3>Incorpora equipo y sedes sin perder el control.</h3>
              <p>
                Administra odontólogos, usuarios, permisos y sedes con información separada por empresa y
                acceso según el rol de cada persona.
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
              <h3>Implementación progresiva</h3>
              <p>
                Comienza con agenda y pacientes e incorpora historia clínica, tratamientos, documentos y
                pagos a medida que tu equipo se familiariza.
              </p>
            </article>
            <article className="trust-card">
              <span>03</span>
              <h3>Acompañamiento cercano</h3>
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
            <h2>Dentia está creciendo junto a odontólogos reales.</h2>
            <p>
              Trabajamos con prácticas fundadoras para perfeccionar la experiencia antes de ampliar nuestra
              apertura comercial.
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
            <p className="eyebrow">Precios transparentes</p>
            <h2>Planes para comenzar y crecer.</h2>
            <p>Las funcionalidades principales están incluidas. Los planes crecen según el número de odontólogos.</p>
          </div>
          <div className="pricing-preview">
            <article className="price-card">
              <span className="price-card__country">Colombia</span>
              <span className="price-card__amount">Desde $85.000 <small>COP/mes</small></span>
              <p>Para odontólogos independientes y clínicas que quieren ordenar su operación.</p>
            </article>
            <article className="price-card">
              <span className="price-card__country">Chile</span>
              <span className="price-card__amount">Desde $23.900 <small>CLP/mes</small></span>
              <p>La misma plataforma, con planes adaptados al crecimiento de la práctica.</p>
            </article>
          </div>
          <div className="pricing-action">
            <Link className="button button--primary" href="/precios">Ver precios</Link>
          </div>
        </div>
      </section>

      <FinalCta />
    </>
  );
}
