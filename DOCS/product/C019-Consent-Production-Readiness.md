# C019 — Preparación productiva de consentimientos

Estado: procedimiento técnico aprobado; habilitación productiva sujeta a compuertas verificables.

## Modelo de responsabilidades

Dentia asegura el procedimiento técnico: aislamiento por empresa, identidad y OTP, declaraciones, firma, adulto responsable, trazabilidad, snapshots, evidencia, PDF final, integridad, almacenamiento inmutable, flujo en papel, digitalización y auditoría.

La clínica asegura la revisión y adecuación clínica del contenido exacto de cada versión tenant que publica, además de la custodia documental que corresponda a su práctica. Las plantillas de Biblioteca Dentia son sugerencias y puntos de partida; no constituyen una certificación jurídica universal del contenido final utilizado por cada clínica.

El procedimiento `DENTIA_CONSENT_PROCEDURE_V1` registra que el flujo electrónico y en papel, las declaraciones y el flujo de adulto responsable fueron revisados externamente y considerados adecuados para el uso previsto en Colombia y Chile. El registro no identifica personas ni afirma una garantía universal de cumplimiento normativo.

## Revisión de contenido por la clínica

Antes de publicar una versión tenant, un usuario con rol `ADMINISTRATOR` o `DENTIST_ADMIN` debe confirmar el texto:

> Confirmo que la clínica revisó el contenido de esta plantilla y considera que es adecuado para su utilización con pacientes. La clínica asume responsabilidad sobre el contenido publicado.

La revisión queda vinculada a empresa, versión tenant, hash canónico, usuario, fecha, versión y hash del texto de confirmación, origen y versión de biblioteca fuente cuando existe. `PLATFORM_ADMIN` no puede asumir esta decisión por la clínica.

La revisión no se hereda. Editar el borrador, crear otra versión o cambiar el hash invalida la revisión anterior. Esto aplica por igual a:

- instalación exacta `DENTIA_LIBRARY`;
- copia editable `CLONED_FROM_DENTIA`;
- plantilla propia `CLINIC_CUSTOM`.

Una instalación exacta conserva procedencia y texto de Biblioteca Dentia, pero nace como borrador pendiente de adopción tenant. Permanece de solo lectura; si la clínica necesita cambios debe crear una copia editable.

## Declaraciones y procedimiento

Las declaraciones históricas `DRAFT_LEGAL_REVIEW_V1` se conservan. La migración 0031 agrega versiones inmutables `APPROVED_V1` para:

- `CONSENT_PATIENT_SELF_CO`;
- `CONSENT_PATIENT_SELF_CL`;
- `CONSENT_RESPONSIBLE_ADULT_CO`;
- `CONSENT_RESPONSIBLE_ADULT_CL`.

Cada versión aprobada congela país, locale, actor, orden, texto, hash, procedimiento, referencia de revisión, fecha de registro técnico y vigencia. Producción selecciona únicamente una versión aprobada y vigente; local y test conservan siempre las declaraciones de prueba y la marca de documento de prueba.

## Compuerta productiva

La aceptación electrónica real exige simultáneamente:

- `APP_ENV=production`, depuración desactivada y frontend público HTTPS autorizado;
- aceptación habilitada, cookie pública segura, storage persistente, OTP/sesión válidos y SMTP configurado;
- procedimiento aprobado para país y canal;
- declaraciones aprobadas y vigentes;
- versión tenant `PUBLISHED`;
- revisión clínica tenant activa cuyo hash coincide exactamente;
- workflow estándar, signer policy compatible y aptitud electrónica `READY`;
- canal electrónico permitido.

El flujo papel aplica la misma revisión tenant, publicación, procedimiento y configuración segura, sin exigir SMTP. Cualquier compuerta faltante falla cerrada en producción.

En local y test, `is_test_document` siempre es verdadero y toda salida conserva `DOCUMENTO DE PRUEBA — NO VÁLIDO PARA USO CLÍNICO`. En producción no se degrada silenciosamente a un documento real incompleto: la creación o firma se bloquea.

## Barreras técnicas que permanecen

La adopción de contenido por la clínica no supera barreras del procedimiento. Permanecen bloqueados en el flujo estándar:

- readiness `BLOCKED`;
- `SPECIAL_WORKFLOW`, incluidos rechazo de tratamiento, no garantía, aprobación estética y retiro de ortodoncia;
- documentos `NO_PATIENT_SIGNATURE`, como certificados e indicaciones.

## Corrección odontopediátrica

`CONS_ODONTOPEDIATRIA` tenía contenido NORM5 técnicamente `READY` y signer policy `RESPONSIBLE_ADULT_REQUIRED`, pero conservaba `supports_electronic_signature=false` de metadata legacy. La importación crea la versión inmutable 4 para CO y CL, conserva exactamente contenido y hashes de la versión 3 y cambia únicamente la capacidad electrónica y sus notas de trazabilidad. La versión 3 no se modifica.

## Auditoría y operación

Se auditan la confirmación e invalidación de revisión tenant y la publicación posterior a revisión, sin incluir contenido clínico ni PII. Los registros inmutables de procedimiento y declaraciones conservan quiénes participaron mediante roles, no nombres.

La configuración real de SMTP y la habilitación operativa corresponden al despliegue posterior; este desarrollo no configura proveedores ni despliega. La revocación/corrección no destructiva de consentimientos ya firmados queda separada como `C019A.6.4`.
