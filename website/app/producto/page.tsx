import type { Metadata } from "next";
import { FinalCta } from "@/components/FinalCta";
import { PageHero } from "@/components/PageHero";
import { ProductScreenshot } from "@/components/ProductScreenshot";
import { screenshots } from "@/lib/screenshots";

export const metadata: Metadata = {
  title: "Producto",
  description: "Conoce cómo Dentia conecta la operación clínica y administrativa de una práctica odontológica.",
  alternates: { canonical: "/producto" },
};

const features = [
  {
    id: "agenda",
    title: "Agenda",
    copy: "Organiza citas, estados y disponibilidad en una vista que ayuda al equipo a entender el día y anticipar la atención.",
    image: screenshots.agenda,
    alt: "Agenda mensual de Dentia con citas y estados",
  },
  {
    id: "pacientes",
    title: "Pacientes",
    copy: "Consulta información administrativa, responsables y contexto de atención desde un expediente organizado por paciente.",
    image: screenshots.pacientes,
    alt: "Listado de pacientes sintéticos en Dentia",
  },
  {
    id: "historia-clinica",
    title: "Historia clínica",
    copy: "Registra evoluciones, conserva cierres clínicos y consulta una línea de tiempo que mantiene la continuidad del expediente.",
    image: screenshots.historiaClinica,
    alt: "Historia clínica de Dentia con evolución firmada",
  },
  {
    id: "odontograma",
    title: "Odontograma",
    copy: "Visualiza hallazgos y superficies, selecciona cada pieza y consulta su contexto mediante un inspector clínico conectado.",
    image: screenshots.odontograma,
    alt: "Odontograma dual de Dentia con pieza seleccionada",
  },
  {
    id: "tratamientos",
    title: "Tratamientos",
    copy: "Mantén claridad sobre procedimientos, responsables, estados, valores y avance sin separar el plan de su contexto clínico.",
    image: screenshots.tratamientos,
    alt: "Listado de tratamientos odontológicos en Dentia",
  },
  {
    id: "presupuestos",
    title: "Presupuestos",
    copy: "Construye propuestas versionadas y consulta qué fue aprobado para conservar una referencia clara durante la ejecución.",
    image: screenshots.presupuesto,
    alt: "Presupuesto odontológico aprobado en Dentia",
  },
  {
    id: "consentimientos",
    title: "Consentimientos",
    copy: "Gestiona plantillas y contenido versionado, prepara documentos para pacientes y conserva la trazabilidad técnica del proceso de aceptación.",
    image: screenshots.consentimientos,
    alt: "Configuración y gestión de plantillas de consentimientos",
  },
  {
    id: "finanzas",
    title: "Finanzas",
    copy: "Registra pagos, consulta saldos y genera comprobantes vinculados al paciente y al tratamiento correspondiente.",
    image: screenshots.finanzas,
    alt: "Indicadores financieros y saldos en Dentia",
  },
  {
    id: "seguimientos",
    title: "Seguimientos",
    copy: "Identifica controles pendientes, próximos, vencidos y programados para sostener la continuidad después de la atención.",
    image: screenshots.seguimientos,
    alt: "Seguimientos de pacientes clasificados por estado",
  },
  {
    id: "organizacion",
    title: "Usuarios y sedes",
    copy: "Configura la empresa, organiza sedes y administra accesos según las responsabilidades de cada integrante del equipo.",
    image: screenshots.configuracion,
    alt: "Configuración de empresa y sedes en Dentia",
  },
];

export default function ProductPage() {
  return (
    <>
      <PageHero eyebrow="El producto" title="Una plataforma que conserva el contexto de cada paciente.">
        <p>
          Dentia reúne las tareas clínicas y administrativas que acompañan la atención odontológica, sin
          convertir la consulta en una colección de herramientas desconectadas.
        </p>
      </PageHero>
      <section className="section">
        <div className="container feature-grid">
          {features.map((feature) => (
            <article className="feature-card" id={feature.id} key={feature.id}>
              <div>
                <p className="eyebrow">{feature.title}</p>
                <h2>{feature.title}</h2>
                <p>{feature.copy}</p>
              </div>
              <ProductScreenshot src={feature.image} alt={feature.alt} />
            </article>
          ))}
        </div>
      </section>
      <FinalCta />
    </>
  );
}
