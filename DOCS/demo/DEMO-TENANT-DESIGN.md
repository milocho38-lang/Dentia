# WEB-2A — Diseño de tenant demo seguro y reproducible

Estado: diseño técnico implementado y probado por WEB-2B. Este documento no crea la empresa demo ni autoriza su ejecución en producción.

## 1. Objetivo y límites

Diseñar una empresa completamente sintética llamada **Clínica Dental Aurora**, país Colombia y sede **Sede Centro**, para:

- capturas de la website comercial;
- demostraciones comerciales controladas;
- validación visual interna;
- pruebas repetibles sin datos de pacientes reales.

El tenant debe mostrar una práctica activa en Dashboard, Agenda, Pacientes, Seguimientos, Tratamientos, Presupuestos, Historia clínica, Evoluciones, Odontograma, Consentimientos, Pagos, Comprobantes, Documentos clínicos, Sedes, Usuarios y Roles.

Quedan fuera de este diseño:

- RIPS y catálogos regulatorios;
- la website pública WEB-2;
- cambios de DNS, proxy o infraestructura;
- datos de clientes existentes;
- envío real de mensajes a pacientes;
- ejecución automática en el arranque;
- creación o reset del tenant sin una autorización operativa posterior.

## 2. Hallazgos de la auditoría

### 2.1 Multiempresa

Los modelos funcionales inspeccionados contienen alcance de empresa mediante `empresa_id` o `company_id`. Pacientes, citas, seguimientos, tratamientos, presupuestos, pagos, historia clínica, evoluciones, odontogramas, documentos y consentimientos quedan vinculados al tenant. Usuarios, roles, sedes y sus asociaciones también son tenant-scoped.

Las relaciones globales legítimas son:

- catálogo de permisos;
- biblioteca oficial Dentia de consentimientos;
- otros catálogos globales de plataforma.

El tenant demo puede referenciar una versión global de biblioteca, pero la instalación, plantilla resultante, instancia y archivos deben pertenecer a Clínica Dental Aurora. Nunca se debe copiar una plantilla desde otro tenant.

Las claves foráneas simples no garantizan por sí solas que dos padres con UUID distintos pertenezcan a la misma empresa. Por ejemplo, una fila puede tener `empresa_id` y además un `paciente_id` sin clave compuesta `(empresa_id, paciente_id)`. La aplicación evita cruces mediante servicios con filtros de empresa. En consecuencia, el creador demo no puede ser un importador ORM genérico: debe reutilizar servicios de dominio o verificar explícitamente la empresa de cada padre antes de persistir.

### 2.2 Aprovisionamiento existente

El bootstrap actual está diseñado para una instalación completamente vacía y rechaza su uso cuando ya existen empresas o usuarios. No es apropiado para una demo en una instalación activa.

La creación de empresas desde Plataforma sí implementa un aprovisionamiento compatible con una instalación existente:

- crea empresa y sede principal;
- sincroniza permisos y roles del catálogo;
- crea el administrador inicial;
- asigna `ADMINISTRATOR` y `DENTIST_ADMIN`;
- crea perfil odontológico y vínculo con sede;
- crea tipos de cita iniciales;
- genera auditoría.

La futura herramienta demo debe extraer o reutilizar esa misma operación de aprovisionamiento. No debe duplicar el catálogo de seguridad en el script.

### 2.3 Roles reales

Los roles existentes son:

- `ADMINISTRATOR`;
- `PLATFORM_ADMIN`;
- `SECRETARY`;
- `DENTIST`;
- `DENTIST_ADMIN`.

`DENTIST_ADMIN` ya reúne permisos clínicos y de administración básica. `PLATFORM_ADMIN` es global y queda prohibido para cualquier usuario demo.

La cuota comercial cuenta perfiles `Dentist` activos, no el número total de usuarios. Clínica Dental Aurora necesita un límite de al menos tres plazas admitidas por el modelo actual; se propone `max_active_dentists = 3`, con dos perfiles activos.

### 2.4 Estados reales relevantes

La demo debe usar únicamente los valores soportados:

| Dominio | Valores aplicables |
|---|---|
| Citas | `Programada`, `Confirmada`, `Atendida`, `Cancelada`, `No Asistió`, `Reprogramada` |
| Sobrecupo | `is_overbook = true`; no es un estado |
| Seguimientos abiertos | `Pendiente`, `Contactado`, `Cita programada` |
| Seguimientos cerrados | `Cerrado sin cita`, `No desea continuar` |
| Tratamientos | `Borrador`, `Presupuestado`, `Aprobado`, `En ejecución`, `Pausado`, `Finalizado`, `Cancelado` |
| Procedimientos | `Pendiente`, `Agendado`, `En proceso`, `Realizado`, `Cancelado` |
| Presupuestos | `Borrador`, `Pendiente de aprobación`, `Aprobado`, `Rechazado`, `En ejecución`, `Finalizado` |
| Pago válido | `valido` |
| Evolución/odontograma | usar exclusivamente las transiciones y servicios clínicos existentes |
| Consentimiento | `DRAFT`, `READY_FOR_REVIEW`, `PENDING_SIGNATURE`, `SIGNED`, `VOIDED` |
| Canal de consentimiento | `ELECTRONIC` o `PAPER` |
| Documento/receta | `DRAFT`, `FINALIZED`, `VOIDED` |

`Control`, `Valoración`, `Tratamiento`, `Urgencia`, `Limpieza`, `Retiro de puntos` e `Impresión` son tipos o motivos de cita, no estados.

### 2.5 Inmutabilidad y archivos

Los consentimientos finalizados, sus evidencias y manifiestos no pueden crearse como filas decorativas. El flujo electrónico incluye OTP, aceptación, firma, declaraciones, hashes y PDF; el flujo papel incluye packet, páginas, validaciones humanas, consolidado y SHA-256. Ambos deben construirse a través de los servicios reales.

Los documentos clínicos y recetas finalizados conservan snapshots, hashes y ruta de PDF. Los comprobantes de pago se generan bajo demanda a partir del pago y su consecutivo; no requieren almacenar un PDF demo permanente.

Los roots actuales separan archivos por empresa e instancia/documento. La limpieza debe validar rutas resueltas y limitarse al prefijo exacto del UUID del tenant demo.

### 2.6 Correo

En `test` existe un proveedor de correo en memoria; en los demás ambientes se usa SMTP. No existe hoy un modo general de supresión demo para producción. Por tanto, la implementación del CLI debe añadir inyección explícita de un sink de correo para sus flujos, sin cambiar el proveedor normal de clientes. Ejecutar el flujo de consentimiento demo con SMTP productivo antes de tener ese control queda prohibido.

## 3. Estrategias evaluadas

| Estrategia | Seguridad | Idempotencia/reset | Producción | Mantenimiento | Decisión |
|---|---|---|---|---|---|
| Seed de migración | Baja: se ejecutaría junto a esquema y mezclaría datos operativos con migraciones | Difícil de versionar y revertir | Riesgo alto | Alto | Descartada |
| Script administrativo ad hoc | Media; depende de disciplina y suele omitir invariantes | Posible, pero propenso a derivar | Posible con guardrails | Medio/alto | Descartada |
| Fixture reutilizable | Adecuada para tests, no para datos productivos | Buena en DB efímera | No debe importar pytest/factories en producción | Medio | Solo como apoyo de pruebas |
| CLI dedicado | Alta con dry-run, allowlist, bloqueo y auditoría | Control explícito de create/update/reset | Compatible y no automático | Bajo/medio | **Recomendada** |
| Copia de un tenant existente | Inaceptable por PII y vínculos cruzados | No reproducible | Prohibida | Alto | Descartada |

**Estrategia recomendada: `DEMO_CLI`.**

## 4. Arquitectura propuesta

Crear posteriormente una interfaz administrativa dedicada, por ejemplo:

```text
app.cli.demo_tenant
        ↓
DemoTenantOrchestrator
        ├── CompanyProvisioningService compartido
        ├── Agenda/Followup services
        ├── Treatment/Budget/Payment services
        ├── ClinicalRecord/Odontogram services
        ├── Consent services + DemoEmailSink
        ├── ClinicalDocument services
        └── DemoInvariantAuditor
```

El CLI será la única superficie de ejecución. El orquestador contendrá la composición del dataset, pero la lógica clínica seguirá en los servicios existentes.

Subcomandos propuestos:

```text
python -m app.cli.demo_tenant plan   --dataset aurora-v1
python -m app.cli.demo_tenant create --dataset aurora-v1 --apply
python -m app.cli.demo_tenant status --company-id <uuid>
python -m app.cli.demo_tenant update --company-id <uuid> --dataset aurora-v1 --apply
python -m app.cli.demo_tenant reset  --company-id <uuid> --dataset aurora-v1 --apply
```

Reglas de operación:

- `plan` y `status` son de solo lectura;
- todo comando mutante es dry-run salvo `--apply`;
- ningún comando se ejecuta en startup ni en migraciones;
- `create` usa el aprovisionamiento de Plataforma y no acepta `PLATFORM_ADMIN`;
- `update` solo agrega/corrige entidades deterministas del dataset;
- `reset` nunca ejecuta `DELETE FROM empresas`;
- en producción se exige una confirmación adicional con ambiente, UUID y slug;
- todas las acciones generan auditoría con actor administrativo, versión del dataset y conteos, sin contraseñas ni OTP.

## 5. Identidad inequívoca del tenant demo

No existe actualmente `is_demo` ni metadata empresarial equivalente. Para una única demo controlada no se justifica una migración.

La identificación mínima segura combinará tres condiciones obligatorias:

1. UUID incluido en una allowlist de configuración vacía por defecto, por ejemplo `DENTIA_DEMO_TENANT_IDS`;
2. slug exacto `clinica-dental-aurora-demo`;
3. nombre esperado `Clínica Dental Aurora`.

Un reset requiere que las tres coincidan. El slug por sí solo no autoriza una operación destructiva. Si cualquiera difiere, el comando falla antes de bloquear o modificar filas.

La creación inicial puede generar la empresa sin allowlist porque no borra datos. Antes de habilitar `update` o `reset`, el UUID resultante debe incorporarse explícitamente a la configuración operativa y verificarse con `status`.

Un campo `is_demo` sería conveniente si en el futuro existen múltiples tenants demo autogestionados o una UI de reset. No es necesario para Aurora v1 y no reemplazaría la allowlist operacional.

## 6. Identificadores e idempotencia

Cada objeto demo tendrá una clave lógica estable. El futuro orquestador puede derivar UUIDv5 desde:

```text
<company_uuid>:<dataset_version>:<module>:<logical_key>
```

Ejemplos:

```text
patient:mariana-lopez
appointment:week-current:tuesday:0900:mariana
treatment:andres-endodoncia-46
payment:nicolas-control-01
```

Los UUID deterministas no son secretos; permiten distinguir create/update/no-op sin agregar columnas. También se usarán claves naturales sintéticas donde ya existen restricciones únicas:

- documentos `DEMO-AUR-0001` a `DEMO-AUR-0014` con tipo `Otro`;
- correos bajo un dominio reservado no entregable;
- nombres normalizados de catálogo con prefijo lógico Aurora;
- números y referencias generados por los servicios reales cuando tengan secuencia propia.

El orquestador debe abortar si un UUID esperado existe en otra empresa o si una clave natural esperada pertenece a una fila no reconocida como parte de Aurora. Nunca debe adoptar ni sobrescribir datos desconocidos.

## 7. Estructura base

### Empresa y sede

| Campo | Valor de diseño |
|---|---|
| Nombre | Clínica Dental Aurora |
| Slug | `clinica-dental-aurora-demo` |
| País | Colombia |
| Zona horaria | `America/Bogota` |
| Ciudad | Bogotá |
| Sede | Sede Centro |
| Cupo | 3 odontólogos activos |
| Identificación fiscal | marcador sintético inequívoco; nunca un NIT numérico plausible |
| Contactos | valores no entregables y marcados como demo |

La dirección, teléfono, email institucional, registro profesional y demás campos visibles deben ser sintéticos y no enrutar a terceros. El branding puede usar un logo creado específicamente para Aurora y guardado bajo el prefijo de empresa.

### Usuarios

| Usuario | Roles | Perfil odontológico | Uso |
|---|---|---|---|
| Dra. Valentina Ríos | `ADMINISTRATOR` + `DENTIST_ADMIN` | Activo, Sede Centro | Cuenta principal administrada y atención clínica |
| Dr. Sebastián Torres | `DENTIST` | Activo, Sede Centro | Agenda y casos del segundo profesional |
| Laura Gómez | `SECRETARY` | No aplica | Recepción, agenda, pagos y operación diaria |

Ninguno recibe `PLATFORM_ADMIN`. Las tres cuentas pertenecen únicamente a Aurora y solo se asocian con Sede Centro. Los registros profesionales deben usar valores visibles como sintéticos/no verificables, no números reales.

La cuenta principal consume una plaza odontológica, Sebastián consume otra y Laura no consume plaza.

### Pacientes

Se propone un dataset de 14 pacientes. Los nombres son personas sintéticas sin correspondencia pretendida con una persona real. Cada fila tendrá documento `Otro` con prefijo `DEMO-AUR-`, teléfono deliberadamente no enrutable y correo bajo dominio reservado. Nunca se usarán cédulas, celulares o correos obtenidos de terceros.

| Clave | Nombre visible | Perfil de demostración |
|---|---|---|
| `mariana-lopez` | Mariana López | Historia clínica, evolución, odontograma y plan restaurador |
| `andres-martinez` | Andrés Martínez | Endodoncia/reconstrucción, presupuesto aprobado y pago parcial |
| `sofia-herrera` | Sofía Herrera | Consentimientos electrónico y papel; responsable si se modela como menor |
| `nicolas-castro` | Nicolás Castro | Pago completo, comprobante, control y seguimiento con cita |
| `daniela-ramirez` | Daniela Ramírez | Valoración próxima y presupuesto borrador |
| `mateo-gomez` | Mateo Gómez | Profilaxis atendida |
| `valeria-torres` | Valeria Torres | Restauración pendiente y cita confirmada |
| `samuel-ortega` | Samuel Ortega | Seguimiento vencido |
| `catalina-ruiz` | Catalina Ruiz | Blanqueamiento presupuestado |
| `felipe-vargas` | Felipe Vargas | Cita reprogramada con nueva cita enlazada |
| `laura-mendez` | Laura Méndez | Tratamiento pausado |
| `santiago-pena` | Santiago Peña | Valoración inicial programada |
| `juliana-cardenas` | Juliana Cárdenas | Cita cancelada y seguimiento abierto |
| `tomas-salazar` | Tomás Salazar | Urgencia atendida y evolución firmada |

Las fechas de nacimiento pueden ser fijas porque no vuelven obsoleta la agenda. Deben ser coherentes con el tipo de firmante y nunca futuras. Si Sofía es menor, se crea un responsable igualmente sintético por el flujo normal de responsables.

## 8. Composición funcional del dataset

### 8.1 Agenda

Usar la semana local que contiene la fecha del create/reset y distribuir aproximadamente cuatro citas por día hábil, 20 en total:

- ambos odontólogos;
- horarios entre 08:00 y 17:30;
- tipos existentes: Valoración, Control, Limpieza, Tratamiento y Urgencia;
- días pasados: mayoritariamente `Atendida`, más una `Cancelada`, una `No Asistió` y una `Reprogramada`;
- día actual: combinación temporalmente coherente de `Atendida`, `Confirmada` y `Programada`;
- días futuros: `Confirmada` o `Programada`;
- una cita de sobrecupo con `is_overbook = true` y razón sintética;
- una cita `Reprogramada` enlazada a su nueva cita mediante la relación existente.

No se deben asignar estados futuros incompatibles con la hora ni insertar atenciones para citas no atendidas.

### 8.2 Seguimientos y Dashboard

Los conteos deben emerger de `PatientFollowup` y de su clasificador real:

- 4 `Pendiente por contactar`;
- 6 `Próximo a vencer`;
- 2 `Vencido`;
- 5 `Con cita futura`.

Para obtenerlos correctamente:

- `Vencido`: `followup_date < hoy` y estado abierto;
- `Próximo a vencer`: fecha entre hoy y hoy + 7 días;
- `Pendiente por contactar`: fecha posterior a esa ventana, pero `contact_from <= hoy`;
- `Con cita futura`: estado `Cita programada` y `scheduled_appointment_id` válido.

Cada seguimiento nace de una atención real (`AppointmentCare`) de una cita atendida. No se crean seguimientos huérfanos para llenar tarjetas.

### 8.3 Historia clínica, evoluciones y odontograma

Crear historia clínica para al menos Mariana, Andrés, Sofía, Nicolás y Tomás. Tres casos deben tener distinta profundidad:

- Mariana: anamnesis breve, antecedentes no alarmantes, evolución firmada, plan restaurador y odontograma con caries superficial, restauración existente y una observación no superficial;
- Andrés: diagnóstico y evolución asociados con tratamiento de endodoncia/reconstrucción en una pieza concreta;
- Tomás: evolución firmada de atención de urgencia y control posterior.

Los eventos del odontograma deben usar códigos, superficies, estados y servicios ya soportados. No asignar oclusal a eventos sin superficie ni crear códigos clínicos nuevos. El dato se crea una vez y alimenta las representaciones existentes.

Todo texto debe declarar un caso ficticio, ser breve y clínicamente plausible. Se evitarán prescripciones, dosis o recomendaciones terapéuticas usadas como ejemplo salvo revisión profesional específica.

### 8.4 Catálogo, tratamientos y procedimientos

El catálogo es propio de Aurora. Crear únicamente ítems comunes:

- Profilaxis;
- Restauración en resina;
- Endodoncia;
- Reconstrucción;
- Corona;
- Extracción;
- Blanqueamiento.

Los mapeos con odontograma solo se configuran cuando ya existe un comportamiento aprobado. No se altera ningún catálogo global.

Casos principales:

- Mariana: tratamiento `En ejecución`, restauración realizada y otra pendiente;
- Andrés: tratamiento `En ejecución`, endodoncia realizada, reconstrucción realizada y corona pendiente;
- Catalina: tratamiento `Presupuestado` para blanqueamiento;
- Laura Méndez: tratamiento `Pausado`;
- Daniela: tratamiento o propuesta en `Borrador`.

### 8.5 Presupuestos

Usar las transiciones y versionado reales:

- un presupuesto `Borrador` para Daniela;
- un presupuesto `Aprobado` y vigente para Andrés;
- un presupuesto `En ejecución` o tratamiento parcialmente ejecutado para Mariana, solo si la transición de servicio lo permite;
- opcionalmente una versión previa superseded creada mediante el flujo real para demostrar versionado, no mediante mutación manual.

Los valores serán razonables para una demo colombiana y consistentes entre detalle, total, descuento, pagos y saldo. No se presentarán como tarifas recomendadas por Dentia.

### 8.6 Pagos y comprobantes

Crear mediante el servicio financiero:

- pago parcial de Andrés con saldo pendiente;
- pago completo reciente de Nicolás;
- uno o dos pagos adicionales para que Dashboard/Reportes no estén vacíos.

Todos usan estado `valido`, sede Aurora, tratamiento y paciente de Aurora. Los consecutivos y números de comprobante los genera el flujo real. El PDF de comprobante se renderiza bajo demanda; no se almacena una copia adicional en el seed.

### 8.7 Consentimientos

Preparar como máximo cuatro instancias:

1. borrador;
2. revisado/listo para firma;
3. firmado electrónicamente;
4. firmado en papel y digitalizado.

Reglas obligatorias:

- instalar desde biblioteca oficial compatible con Colombia o crear una plantilla tenant demo; nunca tomar una plantilla de un cliente;
- completar los estados mediante los servicios existentes;
- generar la aceptación electrónica con declaraciones, OTP, firma sintética, manifiesto y PDF reales;
- generar el flujo papel con packet, páginas sintéticas, revisiones y consolidado reales;
- no imprimir tokens, OTP o links en salida persistente;
- capturar todo correo en `DemoEmailSink` y exigir que el destinatario coincida con una dirección interna controlada;
- si el sink no está activo, abortar antes de emitir acceso electrónico.

No se permite insertar directamente una aceptación `SIGNED`, un hash o una ruta de archivo.

### 8.8 Documentos clínicos

Generar solo lo necesario:

- un informe o remisión finalizada para Mariana o Tomás;
- opcionalmente un documento en borrador para contraste.

La finalización debe crear snapshots, número, hash y PDF a través del servicio. No se requieren fotografías ni radiografías. Una receta demo no es necesaria para WEB-2A y se omite para evitar contenido farmacológico innecesario.

## 9. Fechas relativas

La fecha base se calcula al iniciar create/reset en la zona `America/Bogota`:

```text
anchor_date = hoy en America/Bogota
week_start  = lunes de anchor_date
```

Usar offsets declarativos:

```text
appointment.starts_at = week_start + day_offset + local_time
followup.overdue       = anchor_date - 2 días
followup.today         = anchor_date
followup.upcoming      = anchor_date + 3 días
payment.recent         = anchor_date - 1 día
clinical_event.recent  = anchor_date - 7 días
```

La conversión a UTC debe usar `ZoneInfo`, no offsets fijos. Un reset reconstruye agenda, seguimientos y actividad reciente alrededor de la nueva fecha base. Fechas históricas de nacimiento permanecen estables.

## 10. Aislamiento y verificaciones

Antes de cada commit del dataset, ejecutar un auditor de invariantes:

| Control | Verificación |
|---|---|
| Empresa | UUID, slug, nombre y allowlist coinciden |
| Padres | cada paciente, sede, usuario, odontólogo, cita y tratamiento padre pertenece a Aurora |
| Usuarios | ninguna asociación de rol o sede referencia otro tenant |
| Roles | ningún usuario demo tiene `PLATFORM_ADMIN` ni permisos globales |
| Profesionales | dos perfiles activos; cuota 3; ambos vinculados solo a Sede Centro |
| Clínica | historia, evolución y odontograma comparten empresa/paciente correctos |
| Comercial | tratamiento, presupuesto, pago y procedimiento comparten empresa/paciente |
| Consentimientos | plantilla/versión/instancia tenant-scoped; biblioteca global solo como fuente aprobada |
| Archivos | toda ruta resuelta está bajo el root permitido y contiene el UUID de Aurora |
| Correo | cero entregas SMTP; todas las entregas están en el sink controlado |
| Datos | cero documentos, teléfonos o emails provenientes de tenants existentes |
| RIPS | cero filas creadas, actualizadas o eliminadas por Aurora v1 |

El auditor debe hacer consultas negativas contra todos los UUID generados: ninguna fila reconocida por el dataset puede tener otra empresa y ninguna relación Aurora puede apuntar a un padre tenant-scoped externo.

## 11. Diseño de create, update y reset

### Create

1. Verificar ambiente y que no exista el slug.
2. Mostrar plan, conteos y destinatario del email sink.
3. Exigir `--apply` y confirmación de producción cuando corresponda.
4. Crear empresa mediante el aprovisionamiento compartido de Plataforma.
5. Ajustar cupo a 3 por la operación autorizada de Plataforma.
6. Upsert de usuarios, sede y roles.
7. Crear módulos por dependencias usando servicios reales.
8. Generar el conjunto mínimo de archivos.
9. Ejecutar auditor de invariantes.
10. Registrar `DEMO_TENANT_CREATED` con versión y conteos.

### Update

1. Exigir las tres pruebas de identidad demo.
2. Adquirir advisory lock por UUID de empresa y `SELECT ... FOR UPDATE` sobre la empresa.
3. Calcular diff por IDs deterministas.
4. Rechazar filas desconocidas que colisionen con el dataset.
5. Aplicar solo operaciones compatibles y generar artefactos faltantes.
6. Auditar antes/después y verificar invariantes.

No se mutan documentos clínicos o consentimientos finalizados. Si cambia su contenido, se crea una nueva versión/instancia por el flujo normal.

### Reset

El reset preserva:

- empresa Aurora y su UUID;
- Sede Centro y su UUID cuando sea coherente;
- los tres usuarios y sus UUID;
- roles del tenant y catálogo global de permisos;
- auditoría histórica;
- credenciales, salvo rotación solicitada explícitamente.

El reset elimina y recrea únicamente datos operativos del dataset demo. Flujo seguro:

1. dry-run obligatorio con conteo por tabla y archivos;
2. verificar allowlist + UUID + slug + nombre;
3. comprobar que no existen módulos/fuentes fuera del registro Aurora v1; si existen, abortar para revisión;
4. exigir una frase que incluya el UUID y `RESET CLINICA DENTAL AURORA`;
5. verificar referencia de backup operativo reciente;
6. bloquear empresa y adquirir advisory lock;
7. revocar sesiones demo activas;
8. construir manifiesto de archivos y rutas canónicas;
9. mover únicamente directorios tenant-scoped a una cuarentena en el mismo filesystem mediante operación atómica;
10. dentro de una transacción, borrar hijos antes que padres conforme a un registro explícito de dependencias y recrear el dataset;
11. ejecutar invariantes y registrar `DEMO_TENANT_RESET`;
12. confirmar la transacción;
13. borrar cuarentena solo después del commit.

Si falla la transacción, se hace rollback y se restauran los archivos desde cuarentena. Si la limpieza final falla después del commit, se reporta el residuo sintético y se conserva el manifiesto para reintento; no se intenta un borrado amplio.

El registro de borrado debe ser explícito y probado. No usar SQL dinámico del tipo “todas las tablas con `empresa_id`”, `TRUNCATE ... CASCADE`, `DELETE FROM empresas` ni comodines de filesystem.

Orden conceptual de dependencias:

1. entregas, finales, firmas, manifiestos, páginas y demás hijos de consentimientos;
2. instancias, accesos, plantillas tenant e instalaciones demo;
3. items de recetas/documentos y artefactos documentales;
4. detalles/eventos de odontograma y odontogramas;
5. addenda/procedimientos de evolución, evoluciones y componentes de historia clínica;
6. gestiones/seguimientos/atenciones e historial de citas;
7. asociaciones de pagos, pagos, detalles/versiones de presupuesto;
8. procedimientos/eventos/tratamientos y catálogo tenant demo;
9. citas;
10. responsables e historias/pacientes restantes;
11. perfiles odontológicos demo si deben reconstruirse.

Sede, usuarios, roles y empresa permanecen. El orden final debe derivarse y probarse contra el metadata SQLAlchemy vigente antes de implementar.

## 12. Archivos y almacenamiento

Conjunto mínimo recomendado:

- un PDF final de consentimiento electrónico;
- un packet y PDF consolidado de consentimiento en papel;
- un PDF de informe/remisión clínica;
- comprobantes renderizables bajo demanda, sin copia persistida adicional;
- miniaturas/páginas estrictamente necesarias para el consentimiento papel.

No generar cientos de PDFs. No versionar estos artefactos en Git. Los nombres físicos deben ser opacos y las storage keys no deben incluir nombres, documentos ni teléfonos.

Cada create/reset debe informar conteo y SHA-256 sin imprimir paths absolutos, tokens ni identidad sensible. El auditor comprueba que ninguna ruta apunta al UUID de un tenant distinto.

## 13. Política de email

El futuro `DemoEmailSink` debe ser una dependencia explícita del comando y no una variable que cambie globalmente el SMTP de la aplicación:

- deniega por defecto toda entrega;
- acepta solo un destinatario interno configurado fuera del repositorio;
- captura OTP en memoria durante el proceso para completar el flujo demo;
- nunca imprime OTP ni lo guarda en auditoría;
- registra únicamente resultado y destinatario enmascarado;
- aborta si recibe un email de paciente `.invalid` o cualquier destinatario no allowlisted;
- no afecta solicitudes normales de clientes.

No ejecutar el CLI con `APP_ENV=test` contra una base productiva. La supresión debe ser una capacidad específica e inyectada, no un cambio de ambiente.

## 14. Acceso a la demo

No publicar credenciales en la web, repositorio, documentación, screenshots o parámetros CLI.

Política propuesta:

- una cuenta operadora administrada: Dra. Valentina Ríos;
- contraseña aleatoria almacenada en el gestor de secretos del equipo;
- ingreso por la autenticación normal, sin bypass ni login especial;
- `must_change_password` resuelto durante un aprovisionamiento controlado;
- rotación después de una campaña o ante cambio de personal;
- sesiones revisables y revocables con las funciones existentes;
- empresa o cuenta inactivada fuera de ventanas de demo si operativamente conviene;
- Sebastián y Laura pueden mantenerse activos para que las pantallas de usuarios/agenda sean reales, pero no es necesario compartir sus credenciales.

El CLI recibe secretos por entrada oculta o referencia segura, nunca por argumento, archivo versionado o salida estándar.

## 15. Pantallas preparadas para capturas

| Pantalla | Datos necesarios | Composición esperada |
|---|---|---|
| Dashboard | citas del mes/semana, pagos, tratamientos y seguimientos abiertos | métricas no vacías, actividad reciente y acciones prioritarias |
| Agenda | 20 citas relativas, dos odontólogos, estados y tipos variados | semana activa, sin saturación artificial |
| Pacientes | 14 perfiles completos | lista diversa y próxima/última cita visibles |
| Paciente | Mariana como caso principal | resumen, citas, tratamiento y accesos clínicos coherentes |
| Historia clínica | Mariana/Tomás | antecedentes breves y evolución firmada |
| Odontograma | Mariana | hallazgos superficiales, realizado, planificado e informativo sin ambigüedad |
| Tratamiento/presupuesto | Andrés | procedimientos realizados/pendientes, aprobado y pago parcial |
| Consentimiento | Sofía | lista con borrador, pendiente, electrónico firmado y papel finalizado |
| Finanzas | Andrés y Nicolás | pago parcial, pago completo, saldo y comprobantes |
| Seguimientos | mezcla controlada | aproximadamente 4 pendientes, 6 próximos, 2 vencidos y 5 con cita |
| Configuración | tres usuarios y una sede | roles reales, sin administrador de plataforma |

Antes de capturar:

- ejecutar `status` e invariantes;
- confirmar que la fecha visible corresponde a la semana actual;
- ocultar correos, documentos, teléfonos, links y cualquier token aunque sean sintéticos;
- evitar que DevTools, barra de contraseñas o notificaciones muestren secretos;
- comprobar que no haya en pantalla nombres de otros tenants.

## 16. Pruebas requeridas para la implementación

### Unitarias

- UUIDs deterministas y offsets de fecha;
- clasificación de seguimientos produce los conteos esperados;
- el dataset no contiene emails/telefonía/documentos entregables;
- roles no incluyen permisos globales;
- resolución de rutas rechaza escapes y UUID ajenos;
- confirmaciones y allowlist fallan cerradas.

### DB-backed

- create desde cero;
- segundo create es no-op/idempotente;
- update corrige drift permitido sin duplicar;
- reset/recreate conserva empresa, usuarios, roles y auditoría;
- reset rechazado para tenant normal, slug alterado o UUID no allowlisted;
- colisión de UUID/natural key cross-tenant aborta;
- ninguna relación Aurora apunta a padres de otra empresa;
- dos odontólogos consumen dos de tres plazas;
- dashboard y seguimiento arrojan conteos derivados esperados;
- recibos, documentos y consentimientos conservan integridad/hash;
- fallo intermedio hace rollback y restaura cuarentena;
- cero llamadas SMTP;
- cero filas RIPS modificadas.

### Smoke visual

- acceso con cuenta administrada;
- navegación de las ocho capturas prioritarias;
- descarga de documento/consentimiento/comprobante sintético;
- cierre de sesión y revocación de acceso;
- verificación de aislamiento con una cuenta de otro tenant.

## 17. Rollout propuesto

1. Implementar CLI, orquestador, sink e invariantes en rama aislada.
2. Probar create/update/reset en PostgreSQL temporal con storage temporal.
3. Ejecutar suites de seguridad y módulos afectados.
4. Revisión de contenido clínico sintético por odontólogo.
5. Crear Aurora en staging/local y aprobar capturas.
6. Hacer inventario de comandos, actor, backup y allowlist.
7. Solicitar autorización separada para crear Aurora en producción.
8. Ejecutar primero `plan`, revisar conteos y luego `create --apply` en ventana controlada.
9. Verificar invariantes, correo, archivos, healthchecks y acceso.
10. Mantener WEB-2 y RIPS fuera del despliegue de esta capacidad.

## 18. Decisiones y gates

| Gate | Resultado | Justificación |
|---|---|---|
| Estrategia | **DEMO_CLI** | Es explícita, auditable, actualizable y no se acopla a startup ni migraciones. |
| Seguridad | **DEMO_ISOLATION_OK** | El modelo tenant y los servicios ofrecen aislamiento suficiente, condicionado a reutilizar servicios y ejecutar invariantes cross-tenant; no es seguro insertar ORM arbitrario. |
| Reset | **SAFE_RESET_DESIGN_READY** | Quedan definidos identidad triple, dry-run, locks, transacción, orden explícito, cuarentena y rollback. La implementación aún debe probarlos. |
| Producción | **READY_TO_IMPLEMENT_DEMO** | La arquitectura está lista para implementar el tooling; esto no autoriza crear el tenant productivo. El sink y los tests son gates previos obligatorios. |
| Esquema | **NO_SCHEMA_CHANGE_REQUIRED** | UUID allowlisted + slug + nombre permiten una demo única con seguridad suficiente. Reevaluar `is_demo` solo si se generaliza la capacidad. |

## 19. Decisión final

Clínica Dental Aurora debe construirse mediante un CLI dedicado, versionado e idempotente. No se debe usar una migración, fixture de pytest, copia de un tenant ni SQL manual. El tenant se identifica por UUID allowlisted, slug y nombre; todo reset falla cerrado y preserva empresa, accesos y auditoría. Los datos son sintéticos, las fechas operativas son relativas, los archivos son mínimos y tenant-scoped, y los consentimientos finalizados pasan por los servicios reales con correo interceptado.

No crear ni resetear la empresa demo real hasta recibir autorización explícita posterior.

## 20. Implementación WEB-2B

WEB-2B materializa este diseño mediante:

- `app.cli.demo_tenant`, con `plan`, `create`, `status`, `update` y `reset`;
- `DemoTenantOrchestrator`, que reutiliza servicios productivos para empresa, usuarios, pacientes, clínica, odontograma, tratamientos, presupuestos, pagos, consentimientos y documentos;
- `DemoEmailSink`, inyectado únicamente durante el flujo demo y limitado a una empresa y un destinatario explícitos;
- identidad destructiva basada conjuntamente en UUID allowlisted, slug y nombre;
- transacción exterior de base de datos sobre los commits internos de servicios y compensación tenant-scoped de filesystem;
- auditor de invariantes, IDs deterministas, fechas relativas a `America/Bogota` y registro explícito de tablas de reset;
- suite DB-backed para idempotencia, aislamiento, reset, correo y rollback inducido.

No se añadió hook de startup, migración, endpoint público ni valor productivo por defecto. La operación productiva permanece bloqueada hasta una autorización separada y debe seguir el runbook `DEMO-TENANT-OPERATIONS.md`.
