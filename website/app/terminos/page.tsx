import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Términos de uso del sitio web",
  description: "Condiciones de uso de la web informativa y del formulario de demostración de Dentia Pro.",
  alternates: { canonical: "/terminos" },
};

export default function TermsPage() {
  return (
    <section className="section empty-page">
      <article className="container narrow prose-card">
        <h1>Términos de uso del sitio web</h1>
        <p><strong>Dentia Pro</strong></p>
        <p><strong>Fecha de entrada en vigor:</strong> 3 de octubre de 2026.</p>

        <h2>1. Quién opera este sitio</h2>
        <p>
          Este sitio informativo es operado actualmente por Camilo Andres Medina Romero y Kimberly Astudillo
          Sánchez. La identidad y los canales del responsable del tratamiento se detallan en la <a href="/privacidad">Política de privacidad y tratamiento de datos personales</a>.
        </p>
        <p>
          Estos términos se aplican únicamente al sitio y a su formulario. No modifican contratos ni
          condiciones particulares del software Dentia.
        </p>

        <h2>2. Finalidad del sitio</h2>
        <p>
          El sitio presenta Dentia Pro y permite solicitar información o una demostración. No permite contratar
          el servicio, realizar pagos ni activar una suscripción en línea. Enviar una solicitud no celebra un
          contrato ni genera un cargo.
        </p>

        <h2>3. Información sobre el producto</h2>
        <p>
          Las descripciones del sitio explican funcionalidades del producto. Las capacidades que se encuentren
          en desarrollo y las condiciones particulares deberán identificarse y concretarse antes de una
          contratación.
        </p>
        <p>
          Estos términos no fijan tarifas, permanencia, renovación, reembolsos ni niveles de servicio, y no
          cambian acuerdos previos. Tampoco excluyen los efectos que la ley atribuya a la publicidad y a la
          información ofrecida al público.
        </p>

        <h2>4. Solicitudes de demostración</h2>
        <p>
          Debes proporcionar datos propios y correctos, y contar con facultad suficiente si consultas en nombre
          de una organización. La demostración solo queda coordinada cuando Dentia la confirma.
        </p>
        <p>
          El formulario no es un canal clínico. No incluyas datos de pacientes, menores, diagnósticos, historias
          clínicas, imágenes de salud, credenciales ni información de pagos. Esta regla no altera las
          condiciones que puedan aplicar al uso de la aplicación bajo un contrato específico.
        </p>

        <h2>5. Uso permitido</h2>
        <p>Debes utilizar el sitio de forma lícita. No está permitido:</p>
        <ul>
          <li>suplantar identidades o facilitar datos de terceros sin autorización;</li>
          <li>introducir malware o intentar accesos no autorizados;</li>
          <li>interferir con el funcionamiento o la seguridad del sitio;</li>
          <li>enviar mensajes fraudulentos, abusivos o ajenos a su finalidad;</li>
          <li>vulnerar derechos de propiedad intelectual o de terceros.</li>
        </ul>

        <h2>6. Propiedad intelectual</h2>
        <p>
          Los contenidos, elementos visuales, marcas y software pertenecen a sus respectivos titulares. La
          consulta del sitio no concede derechos de explotación comercial. Los usos permitidos por la ley y
          las autorizaciones expresas permanecen vigentes. Las marcas de terceros pertenecen a sus titulares.
        </p>

        <h2>7. Información clínica</h2>
        <p>
          La información del sitio y de una demostración explica el funcionamiento del software. No constituye
          diagnóstico, tratamiento ni asesoría clínica. Las decisiones profesionales y el tratamiento de datos
          clínicos se rigen por las normas y los acuerdos aplicables al servicio correspondiente.
        </p>

        <h2>8. Disponibilidad</h2>
        <p>
          El sitio puede presentar interrupciones por mantenimiento, actualizaciones o incidencias. No se
          garantiza disponibilidad ininterrumpida ni un resultado específico de la demostración. Nada de lo
          anterior excluye responsabilidades o derechos que legalmente no puedan limitarse.
        </p>

        <h2>9. Enlaces y servicios externos</h2>
        <p>
          Los enlaces y servicios de terceros se sujetan a sus propias condiciones y políticas. Esto no excluye
          las obligaciones que correspondan cuando un proveedor trate datos por cuenta de Dentia.
        </p>

        <h2>10. Privacidad</h2>
        <p>
          La <a href="/privacidad">Política de privacidad y tratamiento de datos personales</a> explica cómo se
          tratan los datos del sitio. Visitarlo no autoriza cualquier uso de información. La casilla del
          formulario contiene una autorización específica para responder y dar seguimiento a la solicitud de
          demostración.
        </p>
        <p>
          El canal de privacidad es <a href="mailto:dentiapro.notificaciones@gmail.com">dentiapro.notificaciones@gmail.com</a>.
        </p>

        <h2>11. Actualizaciones</h2>
        <p>
          Las actualizaciones de estos términos mostrarán su fecha de vigencia. No tendrán efectos retroactivos
          sobre contratos específicos ni reducirán derechos imperativos.
        </p>

        <h2>12. Normas aplicables</h2>
        <p>
          Se aplicarán las normas y autoridades competentes que correspondan legalmente en cada caso. Estos
          términos no imponen arbitraje obligatorio, jurisdicción exclusiva ni renuncia al derecho de presentar
          reclamaciones ante las autoridades o tribunales competentes.
        </p>
      </article>
    </section>
  );
}
