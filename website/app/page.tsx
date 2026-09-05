import Link from "next/link";
import { FinalCta } from "@/components/FinalCta";
import { ProductScreenshot } from "@/components/ProductScreenshot";
import { screenshots } from "@/lib/screenshots";

const journey = [
  ["Agenda", "Organiza citas y disponibilidad."],
  ["Paciente", "Centraliza su contexto administrativo."],
  ["Historia clínica", "Registra y consulta su evolución."],
  ["Tratamiento", "Ordena lo planeado y realizado."],
  ["Consentimiento", "Gestiona documentos y aceptación."],
  ["Pago", "Conserva saldos y comprobantes."],
  ["Seguimiento", "Mantén visibles los controles."],
];

export default function HomePage() {
  return (
    <>
      <section className="hero section">
        <div className="container hero__grid">
          <div className="hero__copy">
            <p className="eyebrow">Gestión odontológica conectada</p>
            <h1>Toda tu consulta odontológica en un solo lugar.</h1>
            <p>
              Gestiona agenda, pacientes, historia clínica, tratamientos, consentimientos, pagos y
              seguimiento desde una sola plataforma diseñada para la operación real de consultorios y
              clínicas odontológicas.
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
      </section>

      <section className="section section--tint">
        <div className="container problem-grid">
          <div>
            <p className="eyebrow">Menos fragmentación</p>
            <h2>Tu consulta no debería depender de cinco herramientas diferentes.</h2>
            <p>
              Agenda en una aplicación, pacientes en otro lugar, historias clínicas separadas,
              consentimientos impresos, pagos por aparte y seguimientos dispersos. Cuando la información
              está fragmentada, administrar la consulta consume tiempo que debería dedicarse a los pacientes.
            </p>
          </div>
          <div className="unified-flow" aria-label="De información dispersa a una sola operación en Dentia">
            <div className="unified-flow__card">
              <strong>Información dispersa</strong>
              <span>Citas, documentos, saldos y controles en lugares diferentes.</span>
            </div>
            <span className="unified-flow__arrow" aria-hidden="true">→</span>
            <div className="unified-flow__card unified-flow__card--dentia">
              <strong>Dentia</strong>
              <span>El contexto del paciente acompaña cada paso del equipo.</span>
            </div>
            <span className="unified-flow__arrow" aria-hidden="true">→</span>
            <div className="unified-flow__card">
              <strong>Una sola operación</strong>
              <span>Más claridad para la práctica clínica y administrativa.</span>
            </div>
          </div>
        </div>
      </section>

      <section className="section section--compact">
        <div className="container">
          <div className="section-heading section-heading--center">
            <p className="eyebrow">Un flujo continuo</p>
            <h2>Del primer contacto al seguimiento del paciente.</h2>
            <p>Cada etapa conserva el contexto necesario para que el siguiente paso sea más claro.</p>
          </div>
          <div className="journey">
            {journey.map(([title, copy]) => (
              <div className="journey__step" key={title}>
                <strong>{title}</strong>
                <span>{copy}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container story-stack">
          <article className="story-row">
            <div className="story-row__copy">
              <p className="eyebrow">Para independientes</p>
              <h2>Organiza tu consulta incluso si tú mismo la administras.</h2>
              <p>
                Dentia te ayuda a manejar agenda, pacientes, historia clínica, tratamientos, documentos y
                pagos desde un mismo lugar, incluso si trabajas sin secretaria.
              </p>
              <Link className="text-link" href="/producto">Explorar el producto</Link>
            </div>
            <div className="story-row__visuals">
              <ProductScreenshot
                src={screenshots.agenda}
                alt="Agenda mensual de Dentia con citas odontológicas organizadas por estado"
              />
            </div>
          </article>

          <article className="story-row story-row--reverse">
            <div className="story-row__copy">
              <p className="eyebrow">Para clínicas</p>
              <h2>Y crece contigo cuando tu práctica se convierte en clínica.</h2>
              <p>
                Administra odontólogos, usuarios, permisos y sedes manteniendo la información organizada por
                empresa y con controles de acceso según el rol de cada persona.
              </p>
              <span className="feature-note">Organización multiempresa con acceso por roles</span>
            </div>
            <div className="story-row__visuals">
              <ProductScreenshot
                src={screenshots.configuracion}
                alt="Configuración de Clínica Dental Aurora dentro de Dentia"
              />
            </div>
          </article>

          <article className="story-row">
            <div className="story-row__copy">
              <p className="eyebrow">Contexto clínico</p>
              <h2>La información clínica donde realmente la necesitas.</h2>
              <p>
                Consulta la historia del paciente, registra evoluciones, utiliza el odontograma y relaciona
                procedimientos y documentos sin perder la trazabilidad del tratamiento.
              </p>
              <Link className="text-link" href="/producto#odontograma">Conocer el odontograma</Link>
            </div>
            <div className="story-row__visuals story-row__visuals--pair">
              <ProductScreenshot
                src={screenshots.historiaClinica}
                alt="Historia clínica de Dentia con evolución firmada y línea de tiempo"
              />
              <ProductScreenshot
                src={screenshots.odontograma}
                alt="Odontograma clínico dual de Dentia con Dental Inspector"
              />
            </div>
          </article>

          <article className="story-row story-row--reverse">
            <div className="story-row__copy">
              <p className="eyebrow">Plan y ejecución</p>
              <h2>Del diagnóstico al tratamiento, sin perder el contexto.</h2>
              <p>
                Organiza procedimientos, presupuestos y avance clínico para que el odontólogo y el equipo
                administrativo tengan claridad sobre lo planeado, realizado y pendiente.
              </p>
            </div>
            <div className="story-row__visuals story-row__visuals--pair">
              <ProductScreenshot
                src={screenshots.tratamientos}
                alt="Tratamientos odontológicos en Dentia con estado, responsable y saldo"
              />
              <ProductScreenshot
                src={screenshots.presupuesto}
                alt="Presupuesto odontológico aprobado en Dentia"
              />
            </div>
          </article>

          <article className="story-row">
            <div className="story-row__copy">
              <p className="eyebrow">Documentos clínicos</p>
              <h2>Consentimientos integrados al proceso clínico.</h2>
              <p>
                Prepara y gestiona consentimientos desde Dentia, compártelos mediante un enlace seguro y
                conserva la trazabilidad técnica de la aceptación junto con el documento final.
              </p>
              <p>
                Para situaciones especiales, Dentia también permite conservar el proceso en papel y su copia
                digitalizada.
              </p>
              <span className="feature-note">La imagen muestra configuración y gestión de plantillas</span>
            </div>
            <div className="story-row__visuals">
              <ProductScreenshot
                src={screenshots.consentimientos}
                alt="Configuración y gestión de plantillas de consentimientos en Dentia"
              />
            </div>
          </article>

          <article className="story-row story-row--reverse">
            <div className="story-row__copy">
              <p className="eyebrow">Finanzas del paciente</p>
              <h2>El contexto financiero también permanece junto al paciente.</h2>
              <p>
                Registra pagos, consulta saldos y genera comprobantes sin separar la información financiera
                del resto del proceso de atención.
              </p>
            </div>
            <div className="story-row__visuals">
              <ProductScreenshot
                src={screenshots.finanzas}
                alt="Panel financiero de Dentia con ingresos, saldos y tratamientos activos"
              />
            </div>
          </article>

          <article className="story-row">
            <div className="story-row__copy">
              <p className="eyebrow">Continuidad de atención</p>
              <h2>No pierdas de vista los controles pendientes.</h2>
              <p>
                Mantén visibles pacientes con controles pendientes, próximos, vencidos o ya programados.
              </p>
            </div>
            <div className="story-row__visuals">
              <ProductScreenshot
                src={screenshots.seguimientos}
                alt="Seguimientos de pacientes en Dentia clasificados por prioridad y estado"
              />
            </div>
          </article>
        </div>
      </section>

      <section className="section section--tint">
        <div className="container security-grid">
          <div className="security-panel">
            <p className="eyebrow eyebrow--light">Seguridad por diseño</p>
            <h2>Diseñado para trabajar con información sensible.</h2>
            <p>
              Dentia combina controles de acceso, separación entre organizaciones y trazabilidad para
              acompañar una operación clínica responsable.
            </p>
            <Link className="button button--light" href="/seguridad">Conocer la seguridad de Dentia</Link>
          </div>
          <ul className="security-list">
            <li>Usuarios y permisos según el rol de cada persona.</li>
            <li>Separación de información entre organizaciones.</li>
            <li>Conexiones HTTPS para el acceso a la plataforma.</li>
            <li>Trazabilidad de acciones críticas.</li>
            <li>Controles específicos para información clínica y financiera.</li>
          </ul>
        </div>
      </section>

      <section className="section">
        <div className="container implementation-grid">
          <article className="implementation-card">
            <strong>Implementación progresiva</strong>
            <h2>No tienes que cambiar toda tu operación en un día.</h2>
            <p>
              Puedes comenzar con agenda y pacientes e incorporar progresivamente historia clínica,
              tratamientos, consentimientos y pagos a medida que tu equipo se familiariza con Dentia.
            </p>
          </article>
          <article className="implementation-card">
            <strong>Estado actual</strong>
            <h2>Dentia está creciendo junto a odontólogos reales.</h2>
            <p>
              Actualmente trabajamos con prácticas fundadoras en Colombia y Chile para perfeccionar la
              experiencia antes de ampliar nuestra apertura comercial.
            </p>
          </article>
        </div>
      </section>

      <section className="section section--tint">
        <div className="container">
          <div className="section-heading section-heading--center">
            <p className="eyebrow">Precios transparentes</p>
            <h2>Planes para comenzar y crecer.</h2>
            <p>
              Todos los planes incluyen las funcionalidades principales de Dentia. Los planes para clínicas
              crecen según el número de odontólogos.
            </p>
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
