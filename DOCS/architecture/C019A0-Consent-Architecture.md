# C019A.0 — Arquitectura de consentimientos informados y aceptación electrónica

Estado: diseño objetivo listo para revisión humana; no implementado.

Fecha: 2026-07-30.

Documento maestro: [Contrato clínico-funcional C019A.0](../clinical/C019A0-Informed-Consents-Electronic-Acceptance-Contract.md).

> Esta arquitectura define controles técnicos y evidencia esperada. No determina por sí misma la suficiencia jurídica de un mecanismo de firma o consentimiento.

## 1. Límites del módulo

El módulo C019 será propietario de:

- plantillas y versiones de consentimiento;
- instancias vinculadas al paciente;
- participantes y roles de firma;
- sesiones de revisión y firma;
- decisiones de firma, rechazo y revocación;
- evidencias técnicas y anexos;
- PDF final y constancias;
- entrega de copia;
- trazabilidad y proyección del estado vigente.

El módulo no será propietario de:

- identidad maestra del paciente o usuario;
- historia clínica completa;
- diagnóstico odontográfico;
- procedimientos, tratamientos o presupuestos;
- pagos o cartera;
- archivos generales sin relación con una instancia;
- autenticación interna general de Dentia;
- servicios de correo/SMS;
- backups globales.

Estas capacidades se referencian mediante identificadores y snapshots mínimos. El consentimiento no duplica ni reescribe la fuente clínica.

## 2. Componentes reutilizables y nuevos

| Área | Reutilizar | Crear |
| --- | --- | --- |
| Tenant | empresa desde sesión, filtros por `empresa_id` | políticas de plantilla/instancia por empresa |
| Sede | sede autorizada y zona horaria | snapshot de sede y política aplicable |
| Paciente | `Patient`, `PatientResponsible`, historia clínica | participantes congelados y representación probatoria |
| Clínica | cita, tratamiento, procedimiento, odontograma, evolución | relaciones opcionales sin duplicar contenido |
| Documentos | branding, render PDF, storage relativo, SHA-256 | paquete final específico de consentimiento |
| Seguridad | permisos, sesión, auditoría, IP/user-agent | portal público, token opaco, OTP, rate limiting |
| Operación | C018R.3 backup/restore y C018R.4 aislamiento | manifiesto semántico de evidencias y verificación |

## 3. Entidades conceptuales

```text
ConsentTemplate
  └── ConsentTemplateVersion
        └── ConsentInstance
              ├── ConsentParticipant
              ├── ConsentSigningSession
              │     ├── ConsentOtpChallenge
              │     └── ConsentDecisionEvent
              ├── ConsentEvidence
              ├── ConsentAttachment
              ├── ConsentDeliveryEvent
              └── ConsentAuditProjection
```

### 3.1 `ConsentTemplate`

Identidad lógica de una familia documental. Puede ser estándar Dentia (`company_id = NULL`) o empresarial. No contiene por sí sola el texto probatorio final.

### 3.2 `ConsentTemplateVersion`

Contenido publicado e inmutable:

- país y política aplicable;
- título y contenido estructurado;
- variables permitidas;
- participantes requeridos;
- secciones clínicas;
- política de evidencia;
- hash canónico;
- autor, fecha y estado.

Las variables deben proceder de una allowlist tipada. No se permite HTML arbitrario, ejecución de plantillas ni acceso a propiedades no declaradas.

### 3.3 `ConsentInstance`

Unidad clínica concreta:

- empresa, sede, paciente y versión;
- contexto clínico opcional;
- fecha clínica y zona horaria;
- decisión y estado proyectado;
- snapshots;
- rutas relativas y hashes finales;
- control optimista de versión.

### 3.4 `ConsentParticipant`

Snapshot del paciente, representante, profesional, testigo o intérprete. Un `PatientResponsible` puede originar el snapshot, pero no prueba por sí solo representación legal.

### 3.5 `ConsentSigningSession`

Sesión temporal ligada a:

- una instancia;
- un participante;
- un canal;
- una versión/hash exactos;
- fecha de creación y expiración;
- token público hasheado;
- estado de consumo.

Una sesión no puede firmar otra instancia ni sobrevivir a un cambio del contenido.

### 3.6 `ConsentOtpChallenge`

Desafío ligado a una sesión. Guarda hash derivado, expiración, contador de intentos y eventos de envío/verificación. Nunca guarda el OTP en texto plano.

### 3.7 `ConsentDecisionEvent`

Evento append-only para visualización, firma, rechazo, revocación, anulación y contingencia. Contiene la decisión, actor, tiempo, canal, contenido vinculado y evidencia mínima.

### 3.8 `ConsentEvidence`

Metadatos y artefactos:

- captura gráfica no reutilizable;
- verificación OTP;
- comprobación presencial;
- token público;
- soporte físico;
- hash;
- datos técnicos permitidos.

### 3.9 `ConsentAttachment`

Anexo con nombre lógico, tipo, tamaño, storage key, hash, origen y relación con la instancia. No se almacena como ruta absoluta ni base64 en la tabla principal.

### 3.10 `ConsentDeliveryEvent`

Descarga, enlace seguro, portal o entrega física. No contiene el archivo duplicado.

## 4. Mutabilidad e inmutabilidad

| Elemento | Regla |
| --- | --- |
| Plantilla editable | mutable mientras su versión esté `DRAFT` |
| Versión publicada | inmutable; cambio material crea versión nueva |
| Instancia borrador | mutable con control optimista y auditoría |
| Contenido listo para revisión | congelado antes de emitir sesión |
| Sesión/OTP | append-only en intentos; secretos irreversiblemente hasheados |
| Decisión | append-only |
| Firma gráfica | exclusiva de la instancia y sesión |
| PDF final | inmutable; reemplazo prohibido |
| Hashes | inmutables |
| Revocación/anulación | eventos posteriores; no edición del original |
| Auditoría | append-only |

La [máquina de estados canónica](../clinical/C019A0-Informed-Consents-Electronic-Acceptance-Contract.md#53-máquina-de-estados-canónica) gobierna versiones e instancias. Este documento no define una segunda lista.

## 5. Contrato API objetivo

No implementado en C019A.0. Los nombres definitivos deben seguir las convenciones reales del backend.

### 5.1 Plantillas y versiones

- listar plantillas visibles por empresa/país;
- crear plantilla empresarial;
- crear/editar versión borrador;
- validar variables y secciones;
- publicar versión atómicamente;
- sustituir o retirar una versión;
- obtener vista previa marcada como borrador.

### 5.2 Instancias internas

- listar consentimientos de un paciente dentro del tenant;
- crear instancia;
- editar borrador con `version`;
- confirmar revisión profesional;
- emitir/reemitir sesión;
- iniciar contingencia física;
- cargar y cerrar soporte físico;
- revocar o anular con motivo;
- descargar PDF/constancia con verificación de integridad.

### 5.3 Portal público

- resolver token opaco;
- obtener contenido mínimo de la instancia;
- registrar visualización;
- solicitar/verificar OTP;
- firmar o rechazar;
- descargar copia mediante autorización acotada.

### 5.4 Reglas transversales

- empresa siempre derivada de sesión en API interna;
- `company_id`, `patient_id`, `site_id` y relaciones se vuelven a validar;
- token público no revela UUID ni tenant;
- respuesta pública no enumera pacientes;
- errores no distinguen token inexistente, vencido o de otro tenant cuando esa diferencia facilite enumeración;
- comandos terminales usan idempotency key y transacción;
- la transición a `SIGNED` o `REJECTED` sella evidencia y PDF de forma atómica;
- los datasets son paginados;
- toda descarga verifica autorización, storage key y hash.

## 6. Multiempresa y sede

Reglas obligatorias:

1. Toda entidad clínica de consentimiento lleva `company_id`.
2. Toda consulta interna filtra por empresa efectiva antes de resolver el ID.
3. La sede debe pertenecer a la empresa y estar dentro del alcance del usuario.
4. Paciente, cita, tratamiento, procedimiento y profesional relacionados deben pertenecer a la misma empresa.
5. `PLATFORM_ADMIN` no obtiene acceso clínico implícito.
6. El portal público resuelve tenant exclusivamente a través del hash del token y la instancia; nunca acepta empresa del cliente.
7. Storage usa prefijo interno por empresa sin exponerlo.
8. Auditoría guarda empresa y sede, pero no contenido clínico completo.

Zona horaria:

- persistir instantes en UTC;
- persistir la zona IANA usada;
- mostrar por sede, luego empresa, luego `America/Bogota`;
- registrar también fecha clínica cuando corresponda;
- probar Bogotá, Santiago y cambios DST de Santiago.

## 7. Storage, integridad y archivos

Estructura conceptual:

```text
clinical/consents/{company_internal_key}/{instance_internal_key}/
  final.pdf
  evidence/
  attachments/
  wet-ink/
```

Los nombres reales deben ser generados por el servidor. Nunca incorporar directamente nombre de paciente, documento, email, token ni texto del usuario.

Controles:

- rutas relativas normalizadas;
- allowlist de raíz y tipo de archivo;
- rechazo de `..`, rutas absolutas y separadores alternos;
- protección frente a symlinks;
- tamaño y MIME validados con contenido;
- antivirus futuro para anexos;
- permisos mínimos;
- escritura temporal + `fsync`/rename atómico según capacidad del storage;
- SHA-256 calculado desde bytes persistidos;
- verificación antes de descarga;
- no sobreescritura de artefactos finales;
- ausencia de secretos en QR, nombre o metadata pública.

## 8. Auditoría

La auditoría general registra:

- evento;
- actor interno o participante;
- empresa/sede;
- IDs de instancia, versión, sesión y evidencia;
- transición anterior/nueva;
- resultado;
- canal;
- IP/user-agent permitidos;
- timestamp UTC y zona;
- hashes;
- motivo de corrección cuando aplica.

No registra:

- OTP en claro;
- token público en claro;
- imagen de firma en payload de auditoría;
- cuerpo completo de la plantilla;
- diagnóstico o observación clínica completa;
- credenciales;
- rutas físicas del servidor.

Los eventos de dominio son la fuente probatoria; `auditoria_eventos` es una proyección complementaria, no un sustituto.

## 9. Backup y restauración

Integración futura obligatoria con:

- [C018R.3 — Backup completo y restore](../readiness/C018R3-Complete-Backup-and-Restore.md).
- [Runbook de backup y restauración](../operations/Dentia-Backup-Restore-Runbook.md).
- [Runbook de storage persistente](../operations/Dentia-Persistent-Storage-Runbook.md).

El backup debe cubrir coordinadamente:

- tablas y relaciones;
- PDFs finales;
- capturas y anexos;
- soportes físicos;
- manifiesto de storage;
- hashes.

El restore debe verificar:

- ausencia de archivos faltantes o extraños;
- coincidencia de hashes;
- aislamiento por empresa;
- vínculos DB/storage;
- capacidad de descargar una copia histórica;
- conservación de estados terminales;
- evidencia de restore sin imprimir datos clínicos.

La retención y borrado legal no se fija aquí; requiere decisión jurídica por país.

## 10. Portal público, enlace y QR

El enlace usa un token aleatorio de entropía suficiente y solo se guarda su hash. El QR codifica el enlace opaco, no datos clínicos ni identificadores internos.

Controles:

- expiración configurable;
- consumo y replay controlados;
- rotación al reenviar;
- invalidación de sesiones anteriores según política;
- rate limiting por token/IP/contexto;
- respuestas anti-enumeración;
- `Cache-Control: no-store`;
- `Referrer-Policy: no-referrer`;
- CSP estricta;
- sin indexación;
- no analytics de terceros;
- validación CSRF/origin donde aplique;
- protección frente a clickjacking;
- cierre explícito de sesión.

## 11. OTP

Decisión provisional inicial: correo. SMS queda post-MVP.

El OTP:

- se genera criptográficamente;
- se vincula a sesión, participante y propósito;
- se persiste solo como hash derivado;
- tiene expiración e intentos configurables;
- usa comparación constante;
- consume o invalida el desafío al verificar;
- limita reenvíos;
- no se incluye en logs;
- no se considera identidad fuerte por sí solo;
- no convierte la firma gráfica en firma avanzada.

Los valores exactos de vigencia e intentos están pendientes en el [Decision Log](../readiness/C019A0-Consent-Decision-Log.md).

## 12. Generación PDF

Para `SIGNED`, `REJECTED`, `REVOKED` y `WET_INK_SCANNED` según corresponda:

1. resolver snapshots y contenido exacto;
2. renderizar con motor documental controlado;
3. incluir versión, decisión y evidencia resumida;
4. generar bytes;
5. calcular SHA-256;
6. persistir de forma atómica;
7. confirmar evento terminal y storage en una operación compensable;
8. verificar hash en descarga.

No se incorporan secretos, tokens, OTP, rutas físicas ni metadata innecesaria.

Una firma gráfica se muestra únicamente si pertenece a esa instancia y participante. Nunca se recupera como “firma del paciente” reutilizable.

## 13. Threat model

| Amenaza | Activo | Vector | Impacto | Control requerido | Riesgo residual |
| --- | --- | --- | --- | --- | --- |
| IDOR/cross-tenant | instancias y PDFs | IDs manipulados | exposición clínica | tenant desde sesión, filtros DB, pruebas A/B | error futuro en endpoint nuevo |
| Enumeración pública | identidad/estado | tokens o errores | privacidad | token opaco, mensajes uniformes, rate limit | inferencia por canal externo |
| Robo de enlace | decisión | correo/dispositivo comprometido | firma no autorizada | OTP, expiración, alertas, evidencia de canal | seguridad del correo del paciente |
| Replay | firma/descarga | reutilización de token/OTP | duplicidad o acceso | nonce, consumo, idempotencia, rotación | carreras no cubiertas |
| Fuerza bruta OTP | identidad declarada | intentos masivos | suplantación | límite por sesión/IP, backoff, bloqueo | ataques distribuidos |
| Firma reutilizada | autoría | pegar imagen previa | evidencia falsa | captura ligada a sesión/hash; no biblioteca | captura visual imitada |
| Alteración de PDF | integridad | reemplazo en storage | evidencia inválida | storage inmutable, SHA-256, verificación | compromiso privilegiado de storage |
| Race/atomicidad | estado | dos firmas o firma+rechazo | contradicción | lock/version, transacción, idempotency key | fallas entre DB y storage |
| XSS/HTML | firmante | plantilla o variables | robo de sesión | contenido estructurado, sanitización, CSP | librería de render vulnerable |
| Path traversal | storage | nombre/anexo | lectura/escritura arbitraria | claves del servidor, normalización, allowlist | bug de librería |
| Symlink | storage | enlace malicioso local | escape de raíz | no-follow, resolución segura, permisos | actor con acceso al host |
| Malware | anexos | archivo cargado | compromiso usuario | MIME/tamaño, descarga segura, antivirus futuro | zero-day |
| Exceso de auditoría | datos sensibles | logs | filtración | allowlist de campos, redacción | error humano |
| Abuso `PLATFORM_ADMIN` | clínica tenant | permiso global | acceso indebido | denegación explícita y tests | soporte excepcional mal gobernado |
| QR con datos | privacidad | captura pública | exposición | solo URL opaca | fotografía del QR vigente |
| Ingeniería social | voluntad | texto/canal engañoso | aceptación no informada | branding, resumen, contacto, revisión profesional | coacción fuera del sistema |
| DoS | portal/PDF | requests masivos | indisponibilidad | rate limit, colas, límites de render | ataque volumétrico |
| Backup incompleto | evidencia | DB sin storage | pérdida probatoria | backup coordinado y restore test | ventana entre respaldos |
| Hash incorrecto | integridad | algoritmo/bytes distintos | falso fallo o falsa confianza | bytes persistidos, formato versionado | migración futura |
| Cambio normativo | cumplimiento | política obsoleta | producto inadecuado | revisión periódica por país | intervalo de detección |

## 14. Riesgos residuales

- OTP por correo no prueba por sí solo identidad legal.
- La firma gráfica no determina capacidad, comprensión ni ausencia de coacción.
- La seguridad final depende del correo/dispositivo del firmante.
- DB y filesystem no comparten transacción nativa; se requiere patrón de staging/compensación.
- La retención puede diferir por país y tipo documental.
- Menores, capacidad, asentimiento y representación requieren validación específica.
- Chile tiene una reforma de protección de datos con vigencia diferida al 1 de diciembre de 2026; debe planificarse sin tratarla como vigente el 30 de julio de 2026.
- La suficiencia de firma electrónica simple o avanzada depende del caso y de revisión jurídica.

## 15. Invariantes para implementación

1. Un estado clínico real, múltiples representaciones.
2. Una versión publicada nunca cambia.
3. Una sesión firma un único hash.
4. Ningún secreto se persiste en claro.
5. Ningún ID proporcionado evita la validación tenant.
6. Ningún QR contiene datos clínicos.
7. Ningún PDF final se sobreescribe.
8. Ninguna revocación o anulación borra el original.
9. Ninguna contingencia física se etiqueta como firma electrónica.
10. Ningún administrador de plataforma recibe contenido clínico por su rol global.
