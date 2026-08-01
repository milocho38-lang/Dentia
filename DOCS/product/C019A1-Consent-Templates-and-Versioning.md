# C019A.1 — Plantillas y versiones de consentimientos

## Alcance

C019A.1 incorpora la administración multiempresa de plantillas que alimentará C019A.2. No crea instancias de paciente, documentos firmables, enlaces, QR, OTP, correo, portal, representantes operativos, firmas ni PDF final.

El contenido jurídico no se suministra ni se siembra. Cada clínica debe incorporar contenido revisado clínica y jurídicamente.

## Experiencia de administración

La ruta `/configuracion/consentimientos` permite:

- buscar y filtrar plantillas por estado, país y tipo;
- crear una identidad de plantilla con una versión 1 en borrador;
- editar el contenido con una barra visual, datos automáticos y aplicabilidad;
- validar y previsualizar exclusivamente con datos ficticios;
- publicar con confirmación explícita de inmutabilidad;
- consultar el historial;
- crear un borrador desde una versión anterior;
- retirar una publicación o anular un borrador con motivo.

No existe ninguna selección de paciente en esta pantalla.

### Editor visual

El modo predeterminado oculta la sintaxis interna y presenta los datos automáticos como etiquetas humanas. La barra permite crear títulos, subtítulos, negrillas, listas y separadores, además de insertar datos agrupados por paciente, profesional, empresa, sede, tratamiento, procedimiento y documento.

El pegado desde editores de texto conserva texto, párrafos y listas básicas disponibles, descarta HTML y estilos externos y avisa cuando limpia formato incompatible. El modo avanzado queda disponible únicamente para usuarios con permiso de edición y permite revisar el código de plantilla sin cambiar el contenido persistido.

La conversión es solo de presentación: una plantilla existente se abre con etiquetas humanas, pero se guarda usando el mismo `RESTRICTED_MARKDOWN_V1` y las mismas claves registradas. Las etiquetas desconocidas se resaltan, conservan su clave para corrección y bloquean la publicación.

El editor usa un documento visual estructurado: cada dato automático conserva su nombre técnico independientemente del texto mostrado. La serialización visual, el modo avanzado y la reapertura comparten el mismo conversor bidireccional, por lo que títulos, párrafos, negrillas, listas, separadores y espacios alrededor de etiquetas se mantienen al guardar.

Un texto histórico escrito literalmente como `[Nombre completo del paciente]` se conserva como texto normal. Dentia no lo reinterpreta silenciosamente como dato automático, porque podría tratarse de contenido deliberado; debe corregirse manualmente insertando el dato desde el catálogo visual.

## Estados

| Estado | Editable | Disponible para C019A.2 | Transición permitida |
|---|---:|---:|---|
| `DRAFT` | Sí | No | `PUBLISHED`, `VOIDED` |
| `PUBLISHED` | No | Sí | `SUPERSEDED`, `RETIRED` |
| `SUPERSEDED` | No | No | Terminal |
| `RETIRED` | No | No | Terminal; puede servir como base de otro borrador |
| `VOIDED` | No | No | Terminal |

Publicar una nueva versión reemplaza prospectivamente a la publicada anterior dentro de la misma transacción. Nunca se elimina historial.

## Tipos documentales

El catálogo inicial incluye consentimiento clínico general, consentimiento por procedimiento, autorizaciones de tratamiento, imágenes, datos y comunicaciones, consentimiento de representante, rechazo, revocación, constancia de información y otro configurable. La existencia del tipo no habilita todavía su flujo operativo.

## Variables

La sintaxis es `{{ namespace.key }}`. Solo admite claves registradas para paciente, empresa, sede, profesional, tratamiento, procedimiento y documento. No admite expresiones, filtros, funciones, atributos dinámicos ni ejecución de código.

La publicación falla si existe una variable desconocida o sintaxis incompleta. La previsualización usa valores marcados como demostración y nunca consulta pacientes.

## Aplicabilidad

La identidad define empresa, país e idioma. Cada versión congela:

- ámbito `GENERAL` o `SPECIFIC`;
- prioridad de 0 a 1000;
- sedes;
- procedimientos;
- especialidades explícitas.

Una versión específica requiere al menos un criterio. Las asociaciones solo pueden pertenecer a la empresa activa. C019A.1 devuelve candidatos; no decide automáticamente cuál consentimiento debe utilizar un paciente.

## Permisos

| Rol real | Lectura | Crear | Editar borrador | Publicar | Retirar | Anular | Auditoría |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ADMINISTRATOR` | Sí | Sí | Sí | Sí | Sí | Sí | Sí |
| `DENTIST_ADMIN` | Sí | Sí | Sí | Sí | Sí | Sí | Sí |
| `DENTIST` | Sí | Sí | Solo borradores propios | No | No | No | No |
| `SECRETARY` | Sí | No | No | No | No | No | No |
| `PLATFORM_ADMIN` | No | No | No | No | No | No | No |

Las acciones ocultas en frontend también están protegidas en backend.

## Límites MVP

- países configurados: Colombia (`CO`, `es-CO`) y Chile (`CL`, `es-CL`);
- contenido máximo: 50.000 caracteres;
- máximo 50 variables distintas, 100 sedes, 100 procedimientos y 50 especialidades por versión;
- sin HTML, enlaces o imágenes Markdown;
- sin textos jurídicos preinstalados;
- sin selección clínica automática ambigua.
