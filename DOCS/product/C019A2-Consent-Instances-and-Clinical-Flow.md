# C019A.2 — Instancias de consentimiento y flujo clínico previo a firma

## Alcance

C019A.2 conecta las plantillas publicadas de C019A.1 con pacientes, sedes, citas, tratamientos, procedimientos y profesionales reales. Una selección múltiple crea una instancia independiente por versión de plantilla y conserva un consecutivo tenant `CNS-######`.

El módulo permite preparar borradores, resolver variables registradas, previsualizar el documento completo, confirmar la revisión profesional, sellar snapshots y hashes, consultar auditoría y anular administrativamente. No implementa firma, OTP, QR, enlace, portal, envío ni PDF final.

## Flujo de usuario

Paciente → Consentimientos → Crear consentimiento:

1. Seleccionar sede, profesional, cita, tratamiento y procedimientos compatibles.
2. Consultar todas las plantillas publicadas aplicables mediante el motor de C019A.1.
3. Seleccionar una o varias plantillas y revisar datos faltantes con etiquetas humanas.
4. Previsualizar cada documento con datos reales autorizados.
5. Crear borradores de forma transaccional.
6. El profesional seleccionado confirma explícitamente que revisó el contenido.
7. La instancia queda congelada en `READY_FOR_REVIEW` para que C019A.3 pueda emitir posteriormente una sesión.

## Estados implementados

- `DRAFT`: editable, previsualizable y anulable.
- `READY_FOR_REVIEW`: revisión profesional confirmada; contenido y contexto sellados e inmutables.
- `VOIDED`: anulación administrativa con motivo e historial conservado.

`PENDING_SIGNATURE` no se crea en esta fase. Según la máquina canónica C019A.0, ese estado implica que ya se emitió una sesión, enlace o QR. El endpoint reservado responde `409` hasta C019A.3.

## Reglas funcionales

- Solo se usan versiones `PUBLISHED`, activas, vigentes y aplicables al contexto.
- País e idioma se derivan de la empresa y no se aceptan desde el cliente.
- Las relaciones se validan dentro de empresa y sede autorizada.
- Las variables singulares de procedimiento quedan vacías si se eligen varios; `procedures.list` representa la colección sin ambigüedad.
- Un dato faltante se muestra y bloquea la confirmación profesional.
- La identidad del paciente se corrige en su dato maestro, no dentro del consentimiento.
- Si cambia el contexto después del sellado, debe anularse la instancia y crearse otra.

## Roles

- `ADMINISTRATOR`: lectura, creación, edición de borrador, anulación y auditoría; no confirma clínicamente.
- `DENTIST_ADMIN`: acceso empresarial completo y confirmación del caso propio seleccionado.
- `DENTIST`: lectura, creación, edición y confirmación cuando es el profesional seleccionado.
- `SECRETARY`: lectura, creación y edición administrativa de borradores; no confirma ni anula.
- `PLATFORM_ADMIN`: sin acceso clínico tenant.

## Límites

No se sembraron textos legales ni se definieron reglas universales para menores, representación, rechazo, revocación, suficiencia jurídica de firma, testigos, intérpretes o retención. Permanecen sujetos a las fases C019A.3–C019A.5 y revisión clínica/jurídica por país.
