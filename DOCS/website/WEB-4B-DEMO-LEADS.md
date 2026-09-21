# WEB-4B — Solicitudes de demo

## Objetivo y alcance

WEB-4B conecta el formulario público de `dentiapro.com` con un flujo comercial mínimo y trazable dentro de Dentia. El visitante registra una solicitud; un Administrador de plataforma puede consultarla, asignarla, registrar contacto, agendar la demo, añadir notas y cerrar el resultado.

No es un CRM. No integra calendarios, WhatsApp, lead scoring, campañas ni creación automática de empresas.

## Modelo de dominio

`DemoRequest` es una entidad global de plataforma y no tiene `empresa_id`, porque el prospecto todavía no es cliente de Dentia.

Contiene:

- identidad y contacto mínimos: nombre, apellido, email normalizado y teléfono;
- contexto comercial: país, ciudad, tipo de práctica y cantidad exacta de odontólogos;
- mensaje original opcional e inmutable desde la UI interna;
- fuente `WEBSITE`;
- estado, responsable de plataforma y datos de agenda;
- fechas de contacto y conversión;
- evidencia de autorización: `consent_at` y `consent_version`;
- `row_version` para evitar sobreescrituras concurrentes;
- huella SHA-256 para deduplicación temporal, sin almacenar IP en claro;
- resultado del intento de notificación interna.

`DemoRequestNote` conserva notas internas append-only con autor y fecha. No se sobrescriben notas anteriores.

## Estados

| Código | Etiqueta | Siguientes estados permitidos |
|---|---|---|
| `NEW` | Nuevo | Contactado, demo agendada, no continúa |
| `CONTACTED` | Contactado | Demo agendada, no continúa |
| `DEMO_SCHEDULED` | Demo agendada | Demo realizada, no continúa |
| `DEMO_COMPLETED` | Demo realizada | Convertido, no continúa, reprogramación |
| `CONVERTED` | Convertido | Terminal |
| `NOT_CONTINUING` | No continúa | Terminal |

Marcar como convertido no crea una empresa ni inicia onboarding automáticamente.

## API

### Pública

`POST /api/public/demo-requests`

- no requiere autenticación;
- exige todos los campos del formulario salvo el mensaje;
- exige autorización de contacto;
- normaliza email y sanea texto plano;
- aplica honeypot, rate limit y deduplicación temporal;
- responde sin ID interno;
- usa `Cache-Control: no-store`.

La website usa un rewrite same-origin limitado a esa ruta. `API_PROXY_TARGET` es una variable fija de proceso; no se habilita CORS ni se construye el destino desde datos del visitante.

### Plataforma

Base: `/api/platform/demo-requests`

- `GET /`: listado paginado y filtros;
- `GET /owners`: responsables elegibles;
- `GET /{id}`: detalle y notas;
- `PATCH /{id}/assignment`: asignación;
- `PATCH /{id}/status`: transición de estado;
- `PATCH /{id}/schedule`: agenda de demo;
- `POST /{id}/notes`: nueva nota append-only.

Las mutaciones requieren el `row_version` vigente. Un conflicto devuelve HTTP 409 y obliga a recargar.

## UX pública

El formulario `/demo` solicita nombre, apellido, país, ciudad, email, teléfono, tipo de práctica y número de odontólogos. El mensaje es opcional. Incluye un checkbox sin marcar y enlace a `/privacidad`.

Durante el envío el botón queda deshabilitado. El éxito y el error se muestran en línea; ante error no se limpian los campos. Se mantienen labels visibles, autocomplete, `type=email`, `type=tel`, `inputMode` y layout de una columna en móvil.

## Gestión Platform Admin

La navegación privada incorpora `Administración → Solicitudes de demo`. El listado permite búsqueda por nombre/email y filtros por estado, país, responsable y fecha. El detalle separa contacto, datos comerciales, seguimiento, agenda y notas internas.

Los responsables elegibles son usuarios activos con membresía activa `PLATFORM_ADMIN`. Un usuario tenant no puede asignarse por manipulación de request.

## RBAC

| Rol | `platform.demo_requests.view` | `platform.demo_requests.manage` |
|---|---:|---:|
| `PLATFORM_ADMIN` | Sí | Sí |
| `ADMINISTRATOR` | No | No |
| `DENTIST_ADMIN` | No | No |
| `DENTIST` | No | No |
| `SECRETARY` | No | No |

Estos permisos no conceden acceso clínico ni acceso a un tenant.

## Privacidad y seguridad

- No se solicitan datos clínicos.
- El mensaje original no se convierte en nota editable.
- React renderiza texto, no HTML; el backend elimina tags y caracteres de control antes de persistir.
- La IP se usa únicamente en memoria para rate limiting y como material de una huella SHA-256 con secreto del servidor. No se guarda la IP pública en la solicitud ni en su evento de creación.
- La auditoría nunca incluye email, teléfono ni mensaje.
- Los endpoints internos requieren permisos de plataforma y emiten `no-store`.
- La lista de destinatarios de correo y el remitente se configuran por entorno.

## Notificaciones

Variables:

```text
DEMO_REQUEST_NOTIFICATION_EMAILS=ventas@example.com,socia@example.com
DEMO_REQUEST_FROM_EMAIL=no-reply@example.com
DEMO_REQUEST_CONSENT_VERSION=DENTIA_PRIVACY_POLICY_V1
```

La solicitud y su auditoría se confirman en PostgreSQL antes de intentar SMTP. Si el envío falla, el lead permanece guardado con `notification_status=FAILED` y un código técnico no sensible. Si no hay destinatarios configurados queda `NOT_CONFIGURED`.

La confirmación automática al prospecto queda pendiente: el MVP evita duplicar políticas de correo comercial y no promete un tiempo de contacto. El formulario ya entrega confirmación inmediata en pantalla.

## Agenda de demo

La agenda registra fecha/hora con offset, zona IANA, responsable y enlace HTTP/HTTPS opcional. No crea eventos en calendarios externos ni envía invitaciones. Reprogramar conserva la auditoría del cambio; las notas se conservan por separado.

## Auditoría y observabilidad

Eventos auditados:

- `DEMO_REQUEST_CREATED`;
- `DEMO_REQUEST_ASSIGNED`;
- `DEMO_REQUEST_STATUS_CHANGED`;
- `DEMO_REQUEST_SCHEDULED`;
- `DEMO_REQUEST_NOTE_ADDED`;
- `DEMO_REQUEST_CONVERTED`;
- `DEMO_REQUEST_CLOSED`;
- resultado de notificación.

Los logs operativos usan los nombres `demo_request_created`, `demo_request_notification_sent`, `demo_request_notification_failed` y eventos anti-spam sin incluir PII.

## Migración y rollback

La migración `20260921_0040_demo_requests.py` parte de `20260914_0039` y crea las dos tablas, índices, constraints y permisos. El downgrade elimina primero relaciones rol-permiso y notas, seguido por solicitudes y permisos.

Rollback funcional recomendado antes de producción:

1. retirar el código WEB-4B;
2. si no existe información que deba conservarse, ejecutar downgrade a `20260914_0039`;
3. si ya existen solicitudes reales, conservar tablas y revertir solo la superficie de aplicación hasta exportar/retener los datos según política.

## Pruebas

- Backend DB-backed: creación, validación, consentimiento, saneamiento, honeypot, rate limit, deduplicación, persistencia ante fallo SMTP, listado, detalle, responsables, agenda, estados, notas, concurrencia, auditoría y RBAC.
- Website: contrato de campos, consentimiento, estados loading/success/error, protección de doble clic, proxy same-origin y responsive.
- Frontend privado: navegación, PermissionGate, columnas, filtros, detalle, agenda, acciones y servicios.
- Seguridad: registro explícito de la ruta pública y caracterización DB-backed de rutas de plataforma.

## Flujo manual local

1. Abrir la website en `/demo`.
2. Crear `Ana Demo`, Chile, clínica, 3 odontólogos con datos `example.test`.
3. Verificar “Solicitud recibida”.
4. Iniciar como Platform Admin y abrir `Administración → Solicitudes de demo`.
5. Filtrar, abrir, asignar responsable y marcar contacto.
6. Agendar demo, registrar nota y marcar realizada.
7. Finalizar como convertido o no continúa.
8. Confirmar que un administrador tenant recibe 403 y no ve la navegación.
