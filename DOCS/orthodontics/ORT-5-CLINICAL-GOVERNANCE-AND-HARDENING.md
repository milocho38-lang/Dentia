# ORT-5 — Gobernanza clínica y hardening integral

## Alcance y decisión de persistencia

ORT-5 consolida ORT-1–4 sin crear entidades, columnas, estados ni permisos. No
requiere migración. El módulo continúa desactivado por defecto y no se habilita
en producción mediante este cambio.

## Lifecycle final

| Estado | Transiciones de entrada | Transiciones de salida | Escritura clínica |
| --- | --- | --- | --- |
| `DRAFT` | creación de caso | `ACTIVE` | resumen básico; no evolución ni ficha |
| `ACTIVE` | activación o reactivación | `SUSPENDED`, `COMPLETED` | permitida con todos los gates |
| `SUSPENDED` | suspensión explícita | `ACTIVE`, `COMPLETED` | bloqueada; lectura completa |
| `COMPLETED` | cierre o interrupción | ninguna | bloqueada; lectura histórica |

`COMPLETED + closure_reason_code=DISCONTINUED` representa un tratamiento
interrumpido. La UI lo presenta como **Interrumpido**, distinto de
**Completado**. La interrupción exige motivo. Un tratamiento posterior crea un
nuevo caso; un caso cerrado nunca se reabre.

Las mutaciones usan bloqueo de fila y `row_version`. Un conflicto devuelve 409;
no existe último-write-wins silencioso. La reactivación es explícita, queda
auditada como `ORTHODONTIC_CASE_REACTIVATED` y no se deriva de una cita.

## Acceso y política histórica

Las escrituras requieren conjuntamente:

- permiso clínico de la operación;
- tenant coincidente;
- usuario y perfil odontológico activos;
- entitlement vigente;
- assignment activo;
- scope de la sede principal del caso;
- estado compatible del caso.

La lectura de historia ya creada se conserva después de retirar entitlement o
assignment cuando el profesional mantiene `clinical.view`, identidad activa,
mismo tenant y scope de sede. Esto aplica uniformemente a workspace, caso,
evoluciones y versiones de ficha. Un odontólogo inactivo no opera con su antigua
identidad; otro profesional autorizado del tenant puede consultar el historial.

Retirar entitlement o assignment preserva casos, borradores, evoluciones,
fichas, hashes y relaciones. Los borradores quedan read-only; no se eliminan ni
se transfieren automáticamente. El mensaje clínico es: “Tu acceso de
Ortodoncia ya no está habilitado”.

## Responsable clínico

El responsable histórico nunca se borra ni se reasigna automáticamente. Si su
usuario, perfil o assignment deja de estar operativo, la API conserva su ID y
nombre y expone `responsible_dentist_available=false`. La UI advierte
“Responsable histórico no disponible”.

Para continuar se requiere un cambio explícito a un odontólogo activo, assigned,
del mismo tenant y con scope en la sede. El evento registra responsable anterior,
nuevo responsable, actor y timestamp; además aparece una entrada no duplicada en
la timeline. Las evoluciones históricas conservan su autor original.

## Evoluciones, catálogos y adendas

Una evolución firmada es inmutable. El hash genérico cubre el payload clínico y
el fragmento ORT; el fragmento incluye schema, arcos, snapshots de códigos y
labels, alineadores, elásticos, microtornillos, indicaciones, control y alertas.
La API recalcula la evidencia y expone `integrity_status=PASS|FAIL`.

Las opciones de catálogo base son inmutables. Las personalizadas son
tenant-scoped y se retiran, no se borran. Antes de firmar se revalidan todas las
referencias del borrador: si una opción fue retirada, la firma se bloquea con un
error tipado y el snapshot del borrador permanece intacto. Una firma previa no
cambia al retirar el catálogo.

Las correcciones siguen usando la adenda genérica de Dentia; no existe un sistema
paralelo ORT. La adenda no muta el original ni su hash. La política vigente exige
entitlement y assignment activos también para la adenda ortodóncica. Permitir
adendas tras pérdida comercial sería una ampliación de escritura y queda como
decisión explícita pendiente para producto/jurídico en ORT-6.

El resumen no reinterpreta el texto libre de una adenda como reemplazo
estructurado. La evolución firmada sigue siendo la fuente del resumen y la
adenda se conserva como aclaración cronológica. Cualquier semántica de
“corrección vigente” estructurada requiere una decisión clínica futura.

## Ficha clínica versionada

Una versión finalizada congela schema, contenido, snapshots de labels, actor,
fecha clínica y zona horaria. Su SHA-256 se recalcula al leer y se expone como
`integrity_status=PASS|FAIL`. Una nueva versión clona una versión finalizada,
queda en `DRAFT` y conserva `based_on_version_id`; nunca modifica la anterior.

El payload se valida mediante allowlist, tipos, opciones, longitudes y un límite
técnico de 512.000 bytes de JSON. Campos desconocidos, duplicados, tipos erróneos
y payload excesivo se rechazan sin truncamiento silencioso.

## Resumen y timeline

El resumen usa únicamente la última evolución `SIGNED`; los drafts no lo
alimentan. Presenta plan/aparatología del caso, última visita, procedimiento,
indicaciones, próximo control, cita vigente y alerta activa. La ficha se resume
solo por versión/estado y se consulta en su pestaña.

Labels clínicos usados:

- Tratamiento de Ortodoncia iniciado;
- Evolución de Ortodoncia firmada;
- Historia/Ficha clínica de Ortodoncia finalizada;
- Tratamiento de Ortodoncia suspendido;
- Tratamiento de Ortodoncia reactivado;
- Tratamiento de Ortodoncia completado o interrumpido.

## Auditoría y seguridad

La cobertura incluye entitlement, seats, caso, evolución, adenda, ficha y
catálogo. Los eventos iniciados por usuario conservan actor/sesión/timestamp. El
detalle de auditoría contiene IDs, códigos, versiones y hashes, no el contenido
clínico completo.

Todos los recursos se consultan con tenant en el predicado. Los schemas prohíben
campos extra, por lo que cliente no asigna `company_id`, autores, firmantes,
hashes ni auditoría. No existen endpoints DELETE clínicos. React escapa texto al
renderizar y los labels custom rechazan markup; el contenido manual se trata
como texto.

Los datos ORT residen en PostgreSQL y quedan cubiertos por el backup existente;
no se creó storage paralelo. Colombia y Chile comparten modelo y seguridad y
solo cambia el label Historia/Ficha según país.

## Estados UX

- sin case y con acceso: CTA para crear borrador;
- sin acceso: aviso de acceso retirado y solo historial;
- suspendido: banner de reactivación, sin controles de escritura;
- cerrado: banner de conservación histórica;
- responsable no disponible: advertencia y cambio explícito;
- evolución: Borrador/Firmada y alerta si falla integridad;
- ficha: Borrador/Finalizada, Versión actual/Histórica y alerta de integridad;
- selector de caso en Evoluciones y Ficha para consultar casos históricos.

## Registro consolidado de decisiones clínicas pendientes

| Tema | Clasificación | Motivo |
| --- | --- | --- |
| Semántica y estructura de alineadores | `CAN_VALIDATE_DURING_PILOT` | el texto libre actual preserva fidelidad sin imponer catálogo |
| Catálogo y configuración de elásticos | `CAN_VALIDATE_DURING_PILOT` | requiere vocabulario del odontólogo piloto |
| Unidad/formato de medida de microtornillo | `CAN_VALIDATE_DURING_PILOT` | no debe inferirse una unidad clínica |
| ATM y modo single/multi | `CAN_VALIDATE_DURING_PILOT` | marcado explícitamente en schema |
| Jarabak, clase esqueletal y CPI | `CAN_VALIDATE_DURING_PILOT` | definición/unidades pendientes de homologación |
| Unidades cefalométricas | `CAN_VALIDATE_DURING_PILOT` | captura textual evita falsa normalización |
| Vía aérea y palpación | `CAN_VALIDATE_DURING_PILOT` | opciones clínicas por validar |
| Estructura de alertas | `CAN_VALIDATE_DURING_PILOT` | alerta textual activa cubre el piloto |
| Semántica “Sin cambios” | `CAN_VALIDATE_DURING_PILOT` | no se fuerza como hallazgo clínico |
| Adenda después de pérdida de entitlement/assignment | `CAN_VALIDATE_DURING_PILOT` | requiere decisión producto/jurídica antes de ampliar escritura |
| Reemplazo estructurado del resumen por adenda | `POST_MVP` | el mecanismo actual es aclaratorio, no sustitutivo |
| PDF específico de Ortodoncia | `POST_MVP` | la historia general ya conserva evidencia |
| Link directo caso → tratamiento | `POST_MVP` | no se duplica Treatment en el piloto |

Ningún pendiente actual impide probar de forma segura el flujo base con
entitlement activo; tampoco se presenta como definición clínica aprobada.

## Validaciones ORT-5

- lifecycle, reactivación y concurrencia por versión;
- lectura histórica y bloqueo de escrituras tras pérdida de entitlement/seat;
- preservación de borradores;
- responsable histórico y transferencia explícita;
- integridad positiva y tamper controlado de evolución/ficha;
- catálogo retirado antes de firma;
- RBAC, cross-tenant e IDOR heredados de ORT-1–4;
- estados frontend y navegación de historia;
- caracterización de rutas, DB-backed, hardening, auth y fechas clínicas.
