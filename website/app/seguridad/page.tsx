import type { Metadata } from "next";
import { FinalCta } from "@/components/FinalCta";
import { PageHero } from "@/components/PageHero";

export const metadata: Metadata = {
  title: "Seguridad",
  description:
    "Conoce los controles con los que Dentia protege el acceso, la separación y la trazabilidad de la información odontológica.",
  alternates: { canonical: "/seguridad" },
};

const controls = [
  {
    title: "Separación entre organizaciones",
    copy: "La información se organiza por empresa para que cada práctica trabaje dentro de su propio contexto operativo.",
  },
  {
    title: "Usuarios, roles y permisos",
    copy: "Los accesos se asignan de acuerdo con las responsabilidades de cada integrante del equipo y las funciones que necesita utilizar.",
  },
  {
    title: "Conexiones protegidas",
    copy: "La aplicación productiva utiliza HTTPS y controles de sesión orientados a proteger el acceso durante la navegación.",
  },
  {
    title: "Trazabilidad de acciones críticas",
    copy: "Dentia conserva registros de operaciones relevantes para facilitar seguimiento, revisión y responsabilidad dentro de la plataforma.",
  },
  {
    title: "Registros clínicos y documentos",
    copy: "Los cierres clínicos, documentos y consentimientos cuentan con controles específicos para preservar su contexto e integridad.",
  },
  {
    title: "Continuidad operativa",
    copy: "La operación contempla respaldos, monitoreo y procedimientos de recuperación para reducir el impacto de incidentes técnicos.",
  },
] as const;

export default function SecurityPage() {
  return (
    <>
      <PageHero eyebrow="Seguridad Dentia" title="Diseñado para trabajar con información sensible.">
        <p>
          La seguridad forma parte de la arquitectura y de la operación de Dentia: desde el acceso por rol
          hasta la trazabilidad de acciones y la separación de cada organización.
        </p>
      </PageHero>

      <section className="section" aria-labelledby="security-controls-title">
        <div className="container">
          <div className="section-heading">
            <p className="eyebrow">Controles actuales</p>
            <h2 id="security-controls-title">Protección aplicada a la operación diaria.</h2>
            <p>
              Presentamos únicamente capacidades verificables del producto actual, sin atribuir
              certificaciones ni garantías jurídicas que no correspondan.
            </p>
          </div>
          <div className="security-detail-grid">
            {controls.map((control, index) => (
              <article className="security-detail" key={control.title}>
                <span className="security-detail__number" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3>{control.title}</h3>
                <p>{control.copy}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section section--tint" aria-labelledby="security-responsibility-title">
        <div className="container implementation-grid">
          <article className="implementation-card">
            <strong>Responsabilidad compartida</strong>
            <h2 id="security-responsibility-title">Controles técnicos y prácticas responsables.</h2>
            <p>
              Dentia aporta controles de acceso, trazabilidad e integridad. Cada organización conserva la
              responsabilidad de administrar sus usuarios, permisos y contenido clínico de forma adecuada.
            </p>
          </article>
          <article className="implementation-card">
            <strong>Evolución continua</strong>
            <h2>Una práctica que se revisa y mejora.</h2>
            <p>
              La seguridad requiere mantenimiento, pruebas y respuesta operativa continua. Dentia incorpora
              estas revisiones como parte del desarrollo y la operación del producto.
            </p>
          </article>
        </div>
      </section>

      <FinalCta />
    </>
  );
}
