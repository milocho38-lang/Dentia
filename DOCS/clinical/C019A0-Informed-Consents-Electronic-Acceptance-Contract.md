# C019A.0 — Contrato funcional, clínico, probatorio y técnico de consentimientos informados y aceptación electrónica

Estado: listo para revisión humana; pendiente de validación jurídica y clínica en Colombia y Chile.

Fecha de documentación: 2026-07-30.

Alcance: documentación, contrato funcional, decisiones, arquitectura objetivo y roadmap. Este documento no implementa modelos, migraciones, endpoints ni interfaz productiva.

> Este documento define el contrato de producto y la evidencia técnica esperada. Los textos clínicos, casos obligatorios y suficiencia jurídica del mecanismo deben ser validados por asesoría jurídica y clínica en Colombia y Chile antes de comercialización abierta.

## Mapa documental y fuente de verdad

Este archivo es el contrato maestro clínico-funcional. Las responsabilidades especializadas se desarrollan sin sustituirlo:

- [Arquitectura, seguridad y threat model](../architecture/C019A0-Consent-Architecture.md).
- [Matriz normativa Colombia/Chile](../compliance/C019A0-Consent-Colombia-Chile.md).
- [Flujos de firma y experiencia de usuario](../ux/C019A0-Consent-Signing-Flows.md).
- [Estrategia futura de pruebas](../testing/C019A0-Consent-Test-Strategy.md).
- [Decisiones, revisores y compuerta para C019A.1](../readiness/C019A0-Consent-Decision-Log.md).

La máquina de estados canónica se mantiene únicamente en la sección 5.3 de este documento. Los demás documentos deben enlazarla y no redefinirla.

## 1. Resumen ejecutivo

Dentia debe soportar consentimientos informados, autorizaciones, rechazos y revocaciones como procesos clínicos y probatorios completos, no como simples PDFs con una imagen de firma.

El producto objetivo debe poder demostrar:

1. quién aceptó, rechazó, retiró o revocó;
2. qué documento exacto revisó;
3. qué versión del documento se utilizó;
4. qué declaraciones aceptó o rechazó;
5. cuándo ocurrió en zona horaria correcta;
6. cómo se verificó la identidad declarada;
7. desde qué canal, sesión o dispositivo ocurrió;
8. que el documento final no fue alterado después;
9. que se entregó o puso a disposición una copia;
10. qué contingencia se usó si hubo firma física o imposibilidad digital.

La fuente de verdad futura no debe ser el PDF aislado. La fuente de verdad debe ser un expediente de consentimiento compuesto por plantilla versionada, instancia, firmantes, evidencias, decisión, PDF final inmutable, hashes, auditoría y eventos de ciclo de vida.

## 2. Inspección del producto actual

La inspección se realizó sobre la arquitectura local existente, especialmente:

- `backend/app/models/company.py`
- `backend/app/models/site.py`
- `backend/app/models/agenda.py`
- `backend/app/models/clinical_document.py`
- `backend/app/models/prescription.py`
- `backend/app/models/audit_event.py`
- `backend/app/core/security_catalog.py`
- `backend/app/core/auth_dependencies.py`
- `backend/app/utils/clinical_dates.py`
- `backend/app/services/clinical_document_service.py`
- `backend/app/services/prescription_service.py`
- `backend/app/services/patient_service.py`
- `backend/app/services/treatment_service.py`
- documentación clínica e integración en `DOCS/clinical/` y `DOCS/integration/`.

### 2.1 Componentes reutilizables

| Capacidad existente | Evidencia local | Uso recomendado en C019 |
| --- | --- | --- |
| Multiempresa | `empresa_id` en pacientes, sedes, documentos, recetas, odontograma, tratamientos y auditoría | Todo consentimiento debe estar estrictamente particionado por empresa. |
| Multisede | `Site` con `zona_horaria`; asignaciones de usuarios y odontólogos por sede | Instancia de consentimiento debe registrar sede clínica cuando aplique. |
| Pacientes | `Patient` con documento, fecha de nacimiento, correo, móvil, estado | Identidad base del paciente. No basta por sí sola como prueba de aceptación. |
| Responsables | `PatientResponsible` con nombre, documento, parentesco, móvil, correo y primario | Base para representantes legales, especialmente menores de edad. Requiere campos probatorios adicionales para aceptación. |
| Menores de edad | `patient_service.is_minor` y validaciones de responsable principal | Regla inicial para exigir representante cuando aplique; debe validarse jurídicamente por país. |
| Historia clínica | `ClinicalRecord`, evoluciones firmadas, adendas, hash | El consentimiento final debe incorporarse al expediente longitudinal, sin modificar evoluciones firmadas. |
| Odontograma | eventos confirmados con hash e histórico | Consentimientos por procedimiento pueden vincularse a diagnóstico, diente, procedimiento o tratamiento. |
| Tratamientos y procedimientos | procedimientos con alcance y trazabilidad clínica-comercial | Consentimientos por procedimiento deben poder relacionarse con tratamiento/procedimiento. |
| Presupuestos | versiones, aprobación, PDF, consecutivo, estado vigente | Buen patrón para versionado e inmutabilidad; no reemplaza consentimiento clínico. |
| Recetas | estados `DRAFT`, `FINALIZED`, `VOIDED`, snapshots, PDF SHA-256 | Patrón reutilizable para PDF final, snapshots e integridad. |
| Documentos clínicos | informes/remisiones/cartas con PDF institucional y anulación | Reutilizable como motor documental, pero no como modelo completo de consentimiento. |
| Auditoría | `auditoria_eventos` con usuario, empresa, acción, resultado, IP y user-agent | Base para trazabilidad interna. Consentimiento requiere además evidencias firmante/dispositivo/canal. |
| Branding | logo, colores, firma profesional y datos institucionales | PDF final debe usar identidad institucional y datos del profesional/sede. |
| Zona horaria | `effective_timezone`, `local_clinical_date`, sede → empresa → `America/Bogota` | Fechas de presentación, aceptación, rechazo, revocación y entrega deben registrar UTC y vista local. |
| Seguridad de sesión | JWT, sesión, `auth_version`, IP/user-agent por request | Útil para aceptación autenticada interna. Para enlaces públicos se requiere mecanismo específico. |
| Storage | patrón de storage por módulo con rutas relativas y validación | Consentimientos finales deben almacenarse fuera de branding y con verificación de hash. |

### 2.2 Capacidades nuevas necesarias

Dentia todavía no posee de forma productiva:

- plantillas de consentimiento versionadas;
- catálogo de tipos de consentimiento/autorización/rechazo/revocación;
- instancias de consentimiento por paciente;
- flujo de aceptación/rechazo por paciente o representante;
- captura manuscrita de firma en pantalla como evidencia no reutilizable;
- mecanismo de enlace público seguro, expirable y de un solo uso;
- verificación explícita de identidad del firmante;
- evidencia técnica del dispositivo/canal;
- PDF final con paquete probatorio;
- registro de entrega o puesta a disposición de copia;
- revocación/retiro como evento posterior;
- flujo de firma física escaneada como contingencia controlada.

### 2.3 Diferencia con documentos clínicos actuales

`documentos_clinicos` resuelve documentos narrativos emitidos por el profesional. Un consentimiento informado requiere además:

- participación activa del paciente, representante o testigo;
- declaraciones explícitas de comprensión y decisión;
- prueba del mecanismo de aceptación;
- evidencia de identidad;
- trazabilidad de presentación previa al acto de aceptación;
- rechazo/revocación;
- copia entregada o disponible;
- potencial pluralidad de firmantes.

Por tanto, C019 no debe modelarse como un simple `documentos_clinicos.document_type = CONSENT`. Puede reutilizar generación PDF, branding, snapshots, hash y auditoría, pero necesita entidades y flujos propios.

## 3. Marco normativo de diseño

Esta sección es criterio de producto, no asesoría jurídica. Toda suficiencia jurídica debe revisarse antes de comercialización abierta.

### 3.1 Colombia

Fuentes de referencia consultadas:

- Ley 527 de 1999, sobre mensajes de datos, comercio electrónico y firmas digitales, publicada en Gestor Normativo de Función Pública.
- Decreto 2364 de 2012, reglamentario de la firma electrónica, publicado por SUIN-Juriscol.

Criterios de diseño derivados:

- tratar el consentimiento electrónico como mensaje de datos conservado íntegramente;
- asegurar equivalencia funcional cuando se requiera escrito, sujeto a validación jurídica;
- registrar integridad, conservación, autoría declarada y trazabilidad;
- usar un mecanismo confiable y apropiado para el caso de uso;
- identificar al firmante y vincularlo con el documento aceptado;
- conservar evidencia de aceptación y acuerdo sobre el mecanismo de firma electrónica;
- diferenciar firma electrónica simple de firma digital certificada.

Pendientes jurídicos Colombia:

- determinar qué consentimientos odontológicos requieren escrito en cada caso;
- definir si la firma manuscrita capturada + OTP/enlace + evidencia técnica es suficiente para cada tipo;
- definir textos obligatorios por procedimiento;
- revisar requisitos de habeas data/autorización de tratamiento de datos personales.

### 3.2 Chile

Fuentes de referencia consultadas:

- Ley 19.799 sobre documentos electrónicos, firma electrónica y servicios de certificación, Biblioteca del Congreso Nacional.
- Ley 20.584 sobre derechos y deberes de las personas en relación con acciones vinculadas a su atención en salud, Biblioteca del Congreso Nacional y Ministerio de Salud de Chile.

Criterios de diseño derivados:

- tratar documentos electrónicos y firma electrónica bajo equivalencia con soporte papel cuando corresponda;
- diferenciar firma electrónica simple y firma electrónica avanzada;
- registrar integridad, autoría y fecha;
- asegurar proceso de información adecuada, suficiente y comprensible;
- soportar otorgamiento y denegación de voluntad;
- permitir constancia escrita en procedimientos que lo requieran.

Pendientes jurídicos Chile:

- clasificar qué procedimientos odontológicos requieren consentimiento escrito;
- definir cuándo una firma electrónica simple es suficiente y cuándo podría exigirse firma electrónica avanzada;
- revisar tratamiento de menores, representantes y testigos;
- revisar textos clínicos obligatorios y conservación en ficha clínica.

## 4. Taxonomía inicial configurable

La taxonomía debe ser configurable por empresa en una fase posterior, pero C019A.1 debe partir con un catálogo estándar Dentia no excesivo.

| Familia | Tipo inicial | Decisión posible | Firmantes típicos | Relación clínica |
| --- | --- | --- | --- | --- |
| Consentimiento clínico | Consentimiento informado general | aceptar / rechazar | paciente o representante | paciente, historia clínica |
| Consentimiento clínico | Consentimiento por procedimiento | aceptar / rechazar | paciente o representante; testigo si aplica | tratamiento, procedimiento, cita, diente/superficie opcional |
| Autorización administrativa | Autorización de tratamiento | aceptar / rechazar | paciente o responsable administrativo | tratamiento, presupuesto opcional |
| Autorización de datos | Autorización de tratamiento de datos | aceptar / rechazar / revocar | titular o representante | paciente |
| Autorización de datos | Autorización de comunicaciones | aceptar / rechazar / revocar | titular o representante | paciente, seguimiento |
| Uso de imagen | Autorización de uso de imágenes | aceptar / rechazar / revocar | paciente o representante | paciente, procedimiento, archivo externo futuro |
| Representación | Consentimiento de representante legal | aceptar / rechazar | representante legal | menor o paciente incapaz según criterio jurídico |
| Rechazo | Rechazo de tratamiento | rechazar | paciente o representante | tratamiento, procedimiento, evolución |
| Revocación | Retiro o revocación del consentimiento | revocar | firmante original o representante válido | consentimiento previo |
| Constancia | Constancia de información entregada | dejar constancia | profesional; paciente opcional | cita, evolución, tratamiento |
| Configurable | Otro documento configurable | según plantilla | según plantilla | flexible |

Regla base: no todos los tipos requieren la misma evidencia ni los mismos firmantes. La plantilla debe declarar su política de firmantes y su nivel de evidencia mínimo.

## 5. Contrato funcional

### 5.1 Actores

- Profesional tratante.
- Usuario administrativo autorizado.
- Paciente.
- Representante legal.
- Acudiente: persona de apoyo o contacto; no equivale automáticamente a representante legal.
- Testigo, si corresponde: presencia y declara sobre un acto, sin sustituir por sí mismo la voluntad del paciente.
- Intérprete: facilita comprensión y comunicación; no decide por el paciente.
- Administrador de empresa.
- Auditor autorizado.
- Plataforma, sin acceso a contenido clínico interno salvo soporte explícito y sin romper aislamiento multiempresa.

### 5.2 Definiciones clínicas y documentales

- **Consentimiento informado:** proceso clínico de información, comprensión y decisión libre respecto de una actuación de salud. El documento es evidencia del proceso, no su reemplazo.
- **Autorización:** permiso para una finalidad concreta, clínica, administrativa, de datos, comunicación o imagen. No debe presentarse como consentimiento clínico si su finalidad es distinta.
- **Rechazo:** decisión de no aceptar el acto propuesto. Debe conservarse como decisión propia y nunca mostrarse como consentimiento otorgado.
- **Revocación o retiro:** decisión posterior que deja sin efecto hacia adelante un consentimiento o autorización previamente otorgado, sin borrar el original ni alterar hechos ya ocurridos.
- **Anulación (`VOIDED`):** corrección administrativa motivada por error, duplicidad o defecto de la instancia. No expresa voluntad clínica del paciente y no elimina evidencia.
- **Paciente:** titular de la atención y sujeto principal del proceso de información.
- **Representante legal:** persona con facultad jurídicamente válida para actuar por el paciente en el caso concreto.
- **Acudiente:** acompañante o responsable operativo registrado; requiere validación adicional antes de actuar como representante.
- **Testigo:** tercero que deja constancia del acto según la política aplicable.
- **Intérprete:** tercero que apoya la comunicación y cuya intervención debe quedar registrada.
- **Consentimiento:** decisión del sujeto jurídicamente habilitado.
- **Asentimiento:** participación afirmativa del menor o persona cuya autonomía se ejerce progresivamente; no sustituye automáticamente el consentimiento del representante.
- **Plantilla editable:** definición de trabajo aún no publicada.
- **Versión publicada:** contenido congelado y utilizable para crear instancias; cualquier cambio material crea otra versión.
- **Instancia:** documento concreto asociado a empresa, sede, paciente, versión y contexto clínico.
- **Sesión de firma:** ventana temporal y técnica vinculada a una sola instancia, firmante y canal.
- **Paquete de evidencia:** eventos, hashes, snapshots, método de identidad, tiempos, canal y artefactos que sustentan la decisión.
- **PDF final:** representación inmutable y verificable de la versión, contexto y decisión.
- **Anexo:** archivo vinculado y hasheado, con tipo, origen, autor y fecha; no puede modificar silenciosamente el contenido principal.
- **Entrega:** evento que prueba que una copia fue descargada, puesta a disposición o entregada por un canal registrado.
- **Evento de auditoría:** registro append-only de una acción relevante, sin copiar el contenido clínico completo.
- **Contingencia física:** flujo separado en el que el original probatorio es firmado en papel y se incorpora escaneado.

### 5.3 Máquina de estados canónica

Esta es la única tabla canónica del conjunto C019A.0. `Mutable` significa que el contenido clínico o documental puede cambiar en el mismo registro; los eventos append-only y metadatos operativos controlados no se consideran edición silenciosa.

| Ámbito | Estado | Significado | Mutable | Firmable | Descargable | Terminal | Entrada permitida | Salida permitida | Actor autorizado | Auditoría mínima | PDF final | Conservación |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Versión | `DRAFT` | Versión editable, nunca utilizable para instancias clínicas. | Sí | No | No | No | creación | `PUBLISHED`, `VOIDED` | gestor de plantillas autorizado | creación, edición y descarte | No | historial administrativo |
| Versión | `PUBLISHED` | Contenido congelado y habilitado para nuevas instancias. | No | No aplica | Sí, vista controlada | No | `DRAFT` | `SUPERSEDED`, `RETIRED` | publicador autorizado | publicación y hash | Vista versionada | permanente mientras existan instancias |
| Versión | `SUPERSEDED` | Sustituida por una versión publicada posterior. No borra ni altera versiones previas. | No | No aplica | Sí | Sí | `PUBLISHED` | ninguna | sistema/transacción de publicación | sustitución y nueva versión | Sí, histórico | permanente |
| Versión | `RETIRED` | Retirada sin reemplazo; no admite nuevas instancias. | No | No aplica | Sí | Sí | `PUBLISHED` | ninguna | gestor autorizado | retiro y motivo | Sí, histórico | permanente |
| Versión | `VOIDED` | Borrador descartado por error antes de publicación. | No | No aplica | No | Sí | `DRAFT` | ninguna | gestor autorizado | anulación y motivo | No | según política de auditoría |
| Instancia | `DRAFT` | Preparación interna; todavía no presentada. | Sí | No | Solo vista previa con marca de borrador | No | creación | `READY_FOR_REVIEW`, `WET_INK_PENDING`, `VOIDED` | profesional/usuario autorizado | creación y cambios relevantes | No final | según retención de borradores |
| Instancia | `READY_FOR_REVIEW` | Contenido y participantes validados; queda congelada la versión a presentar. | No en contenido | No | Vista previa | No | `DRAFT` | `PENDING_SIGNATURE`, `WET_INK_PENDING`, `VOIDED` | profesional tratante o confirmador autorizado | confirmación profesional | No final | expediente operativo |
| Instancia | `PENDING_SIGNATURE` | Sesión interna o enlace/QR emitido; espera decisión. | No | Sí | Documento a revisar | No | `READY_FOR_REVIEW`, reenvío de `PENDING_SIGNATURE` | `VIEWED`, `SIGNED`, `REJECTED`, `EXPIRED`, `VOIDED` | sistema/usuario autorizado; firmante decide | emisión, reenvío, expiración | No final | expediente y eventos |
| Instancia | `VIEWED` | El firmante abrió o recibió el contenido exacto. | No | Sí | Documento a revisar | No | `PENDING_SIGNATURE` | `SIGNED`, `REJECTED`, `EXPIRED`, `VOIDED` | firmante; sistema registra | visualización y contexto | No final | expediente y eventos |
| Instancia | `SIGNED` | Aceptación registrada; evidencia, hashes y PDF final se sellan atómicamente. | No | No | Sí | Sí, salvo proyección posterior | `PENDING_SIGNATURE`, `VIEWED` | `REVOKED`, `VOIDED` | firmante + servicio transaccional | identidad, decisión, firma, hash, PDF, entrega | Sí, inmutable | permanente según política legal |
| Instancia | `REJECTED` | Rechazo expreso; nunca se presenta como consentimiento otorgado. | No | No | Sí, constancia de rechazo | Sí, salvo `VOIDED` administrativo | `PENDING_SIGNATURE`, `VIEWED` | `VOIDED` | firmante | rechazo, contexto y constancia | Sí, constancia | permanente según política legal |
| Instancia | `EXPIRED` | La sesión o enlace venció sin decisión. | No | No | No final | Sí, salvo nueva instancia | `PENDING_SIGNATURE`, `VIEWED` | ninguna; reenviar crea sesión o instancia según política | sistema | expiración | No | metadatos y auditoría |
| Instancia | `WET_INK_PENDING` | Contingencia iniciada; se espera soporte físico firmado. | Sí, solo metadatos y adjunto previo al cierre | No electrónica | Vista de control | No | `DRAFT`, `READY_FOR_REVIEW` | `WET_INK_SCANNED`, `VOIDED` | profesional/usuario autorizado | inicio, carga, identidad del cargador | No final electrónico | expediente operativo |
| Instancia | `WET_INK_SCANNED` | Original físico firmado incorporado, hasheado y relacionado. No es firma electrónica. | No | No | Sí, copia del soporte/constancia | Sí, salvo `REVOKED` o `VOIDED` | `WET_INK_PENDING` | `REVOKED`, `VOIDED` | usuario autorizado tras control | carga, hash, fecha declarada, custodio | PDF/archivo de contingencia | permanente según política legal |
| Instancia | `REVOKED` | Retiro posterior; conserva íntegros el `SIGNED` o `WET_INK_SCANNED` original y sus efectos históricos. | No | No | Sí, original + constancia | Sí | `SIGNED`, `WET_INK_SCANNED` | `VOIDED` solo por corrección de la revocación | firmante válido y usuario receptor autorizado | identidad, motivo opcional, fecha, vínculo original | Sí, constancia separada | permanente |
| Instancia | `VOIDED` | Corrección administrativa motivada; no equivale a rechazo ni revocación. | No | No | Sí para usuarios autorizados, marcada anulada | Sí | cualquier estado por política estricta | ninguna | rol corrector autorizado | motivo, actor, estado previo y vínculos | Se conserva con marca | permanente si existió evidencia |

Reglas invariantes:

- `SIGNED` nunca vuelve a `DRAFT`.
- La transición a `SIGNED` debe ser atómica: decisión, evidencia, hashes, PDF final y evento de auditoría se confirman juntos o no se confirma nada.
- `REJECTED` nunca se muestra como consentimiento, aceptación o firma.
- `REVOKED` conserva el `SIGNED` o `WET_INK_SCANNED` original; la revocación no es retroactiva salvo conclusión jurídica específica.
- `VOIDED` es corrección administrativa, no decisión clínica.
- `SUPERSEDED` no borra versiones publicadas anteriores ni altera instancias existentes.
- `WET_INK_SCANNED` identifica contingencia física y nunca se rotula como firma electrónica.
- Reenvíos y nuevos OTP son eventos o sesiones nuevas; no hacen retroceder la instancia.
- Los tiempos de expiración y número de intentos son política configurable provisional, no constantes jurídicas.

### 5.4 Flujo digital mínimo

```text
Seleccionar paciente
  → elegir tipo/plantilla versionada
  → relacionar cita/tratamiento/procedimiento si aplica
  → validar paciente/representante/menor
  → generar instancia
  → presentar documento exacto
  → registrar lectura/apertura
  → verificar identidad declarada
  → capturar decisión explícita
  → capturar firma manuscrita de esa sesión, si aplica
  → registrar evidencia técnica
  → generar PDF final
  → calcular hash de contenido y PDF
  → guardar en storage
  → registrar copia entregada/disponible
  → incorporar al expediente del paciente
```

### 5.5 Flujo de rechazo

El rechazo debe ser primera clase, no un error.

```text
Documento presentado
  → paciente/representante rechaza
  → registrar motivo opcional o texto de constancia
  → confirmar comprensión de consecuencias, si la plantilla lo exige
  → generar constancia/PDF de rechazo
  → bloquear solo las acciones que jurídicamente/operativamente dependan del consentimiento
  → mantener expediente y auditoría
```

No debe inventarse consentimiento tácito. Si el paciente rechaza, Dentia debe mostrar claramente el estado.

### 5.6 Flujo de revocación o retiro

```text
Consentimiento finalizado
  → solicitar revocación/retiro
  → identificar firmante o representante válido
  → vincular a consentimiento original
  → registrar fecha clínica y fecha técnica
  → generar evento de revocación
  → generar PDF/constancia de revocación
  → preservar original sin editar
```

La revocación no elimina el consentimiento anterior. Crea un nuevo evento ligado.

### 5.7 Contingencia física

Mientras no exista el módulo electrónico completo, y también como respaldo permanente:

```text
Imprimir o usar formato físico aprobado
  → firmar en papel
  → escanear o fotografiar
  → subir archivo
  → registrar responsable de carga
  → registrar fecha de firma declarada
  → registrar sede y profesional
  → calcular hash del archivo
  → marcar como WET_INK_SCANNED
```

La contingencia debe indicar que la evidencia principal proviene del soporte físico, no de aceptación electrónica.

## 6. Contrato clínico

### 6.1 Contenido mínimo por consentimiento clínico

Cada plantilla clínica debe poder declarar secciones obligatorias:

- identificación de paciente;
- identificación de representante, si aplica;
- profesional o clínica responsable;
- procedimiento o tratamiento;
- diagnóstico o indicación cuando aplique;
- descripción del procedimiento;
- beneficios esperados;
- riesgos frecuentes;
- riesgos relevantes;
- alternativas;
- consecuencias de no realizarlo;
- indicaciones posteriores;
- posibilidad de hacer preguntas;
- declaración de comprensión;
- decisión: aceptar o rechazar;
- fecha y sede;
- país y marco operativo de la empresa.

Los textos clínicos específicos quedan fuera de C019A.0 y deben validarse con asesoría clínica y jurídica.

### 6.2 Menores de edad y representantes

Reglas de producto iniciales:

- si `Patient.birth_date` indica menor de edad, Dentia debe exigir un representante válido para consentimientos que lo requieran;
- reutilizar `PatientResponsible` como base de datos del responsable;
- registrar snapshot del representante al momento de aceptación;
- no depender únicamente del responsable activo actual para probar un consentimiento histórico;
- permitir más de un responsable si la política de plantilla lo exige en el futuro;
- permitir constancia de paciente menor informado/asentimiento solo si se define jurídicamente.

Pendiente jurídico:

- edad y reglas exactas por Colombia/Chile;
- casos en que el menor puede consentir directamente;
- nivel de identificación requerido para representante.

### 6.3 Testigos

El modelo debe soportar testigos aunque no sean obligatorios en el MVP.

Un testigo debe tener:

- nombre;
- tipo/número de documento;
- relación;
- correo/móvil opcional;
- declaración firmada o registrada;
- evidencia de aceptación, si aplica.

La plantilla debe declarar cuándo se requiere testigo.

## 7. Contrato probatorio

### 7.1 Evidencia mínima obligatoria

Cada decisión debe conservar:

- `consent_instance_id`;
- `template_id` y `template_version`;
- hash canónico de plantilla y contenido renderizado;
- hash del PDF final;
- paciente;
- firmante;
- rol del firmante: paciente, representante, testigo, profesional;
- documento de identidad declarado;
- método de verificación;
- declaraciones aceptadas;
- decisión;
- fecha/hora UTC;
- fecha/hora local y zona horaria;
- IP;
- user-agent;
- canal: presencial en clínica, enlace público, usuario autenticado, contingencia física;
- identificador de sesión interna o token público hasheado;
- eventos de apertura/visualización;
- evidencia de firma manuscrita de esa sesión, si aplica;
- constancia de copia entregada o disponible.

### 7.2 Identidad electrónica

El MVP no debe afirmar identidad fuerte si no usa proveedor especializado. Debe registrar el mecanismo usado.

Niveles sugeridos:

- `IN_PERSON_STAFF_CONFIRMED`: personal de clínica verifica presencialmente documento/paciente.
- `AUTHENTICATED_PATIENT_PORTAL`: paciente autenticado en portal futuro.
- `SECURE_LINK_WITH_OTP`: enlace expirable + OTP por canal registrado.
- `SECURE_LINK_ONLY`: enlace expirable sin OTP; evidencia más débil.
- `PHYSICAL_DOCUMENT_UPLOADED`: soporte físico escaneado.
- `ADVANCED_SIGNATURE_PROVIDER`: proveedor externo futuro.

Cada nivel debe mostrar advertencia interna sobre su fuerza probatoria.

### 7.3 Firma manuscrita capturada en pantalla

La firma gráfica capturada:

- pertenece solo a esa instancia;
- no se guarda como firma reutilizable;
- no se ofrece para pegar en documentos futuros;
- se conserva como evidencia asociada al documento exacto;
- debe vincularse a hash de contenido, fecha, firmante y canal;
- por sí sola no prueba identidad.

### 7.4 Integridad e inmutabilidad

Al finalizar:

- congelar snapshots de paciente, representante, empresa, sede, profesional, plantilla y decisión;
- generar PDF final;
- calcular `pdf_sha256`;
- calcular hash de integridad canónico con metadatos probatorios;
- guardar en storage por empresa/instancia;
- impedir edición destructiva;
- toda corrección posterior debe ser adenda, revocación o anulación motivada.

## 8. Arquitectura técnica propuesta

### 8.1 Modelo conceptual futuro

```text
ConsentTemplate
  └── ConsentTemplateVersion
        └── ConsentInstance
              ├── ConsentParticipant
              ├── ConsentDecisionEvent
              ├── ConsentEvidence
              ├── ConsentDeliveryEvent
              ├── ConsentAttachment
              └── ConsentAuditProjection
```

### 8.2 Entidades sugeridas para C019A.1/C019A.2

#### `consent_templates`

- `id`
- `company_id NULL` para estándar Dentia; no editable por empresa
- `code`
- `name`
- `family`
- `country_scope`
- `is_active`
- `created_at`, `updated_at`

#### `consent_template_versions`

- `id`
- `template_id`
- `version`
- `status`
- `title`
- `body_structured`
- `required_sections`
- `required_participants`
- `evidence_policy`
- `content_hash`
- `effective_from`
- `created_by`
- `created_at`

#### `consent_instances`

- `id`
- `company_id`
- `site_id`
- `patient_id`
- `clinical_record_id NULL`
- `appointment_id NULL`
- `treatment_id NULL`
- `treatment_procedure_id NULL`
- `odontogram_event_id NULL`
- `template_version_id`
- `status`
- `decision`
- `clinical_date`
- `timezone`
- `signed_at`
- `signed_participant_id`
- `revoked_at`
- `voided_at`
- `pdf_storage_path`
- `pdf_sha256`
- `integrity_hash`
- `copy_delivery_status`
- `created_by`
- `updated_by`
- `version`

#### `consent_participants`

- `id`
- `company_id`
- `consent_instance_id`
- `participant_type`: paciente, representante, testigo, profesional
- `patient_id NULL`
- `patient_responsible_id NULL`
- `user_id NULL`
- `name_snapshot`
- `document_type_snapshot`
- `document_snapshot`
- `relationship_snapshot`
- `email_snapshot`
- `mobile_snapshot`
- `identity_verification_method`
- `identity_verification_detail`

#### `consent_decision_events`

- `id`
- `company_id`
- `consent_instance_id`
- `participant_id`
- `event_type`: viewed, signed, rejected, revoked, voided, copy_delivered
- `decision`
- `declarations_snapshot`
- `reason`
- `occurred_at`
- `local_occurred_at`
- `timezone`
- `ip_address`
- `user_agent`
- `channel`
- `session_id NULL`
- `public_token_hash NULL`
- `content_hash`

#### `consent_evidence`

- `id`
- `company_id`
- `consent_instance_id`
- `participant_id NULL`
- `evidence_type`: signature_capture, otp, public_token, identity_check, physical_upload, delivery, system
- `storage_path NULL`
- `sha256 NULL`
- `metadata`
- `created_at`

### 8.3 No almacenar en C019A.1 ni fases posteriores

- firma reutilizable del paciente;
- secretos o tokens en claro;
- imágenes en base64 dentro de tablas principales;
- archivos fuera de storage controlado;
- afirmaciones jurídicas de validez definitiva.

## 9. API objetivo

No implementar en C019A.0. Contrato tentativo:

### Plantillas

- `GET /api/consents/templates`
- `POST /api/consents/templates`
- `POST /api/consents/templates/{template_id}/versions`
- `POST /api/consents/template-versions/{version_id}/publish`

### Instancias internas

- `GET /api/patients/{patient_id}/consents`
- `POST /api/patients/{patient_id}/consents`
- `GET /api/consents/{consent_id}`
- `PATCH /api/consents/{consent_id}/draft`
- `POST /api/consents/{consent_id}/prepare-review`
- `POST /api/consents/{consent_id}/signing-sessions`
- `POST /api/consents/{consent_id}/wet-ink`
- `POST /api/consents/{consent_id}/void`
- `POST /api/consents/{consent_id}/revoke`
- `GET /api/consents/{consent_id}/pdf`

### Aceptación pública futura

- `GET /api/public/consents/{token}`
- `POST /api/public/consents/{token}/viewed`
- `POST /api/public/consents/{token}/sign`
- `POST /api/public/consents/{token}/reject`

Reglas de seguridad:

- tokens de un solo uso o vida corta;
- guardar solo hash del token;
- no exponer otros pacientes;
- rate limit;
- expiración;
- auditoría;
- no usar sesión de empresa para acceso público;
- no permitir cambio de documento después de emitir enlace.

## 10. Permisos propuestos

- `consents.view`
- `consents.create`
- `consents.edit_draft`
- `consents.send`
- `consents.facilitate_in_person`
- `consents.issue_signing_session`
- `consents.download`
- `consents.void`
- `consents.revoke`
- `consents.templates.manage`
- `consents.audit`

Asignación sugerida:

| Rol | Permisos |
| --- | --- |
| `DENTIST_ADMIN` | todos los permisos de consentimientos dentro de empresa/sedes autorizadas |
| `DENTIST` | view, create, edit_draft propio, facilitate_in_person propio, issue_signing_session propio, download, revoke según política |
| `ADMINISTRATOR` | administración no clínica: templates.manage administrativo, view metadata; no contenido clínico sensible salvo combinación con rol clínico |
| `SECRETARY` | create operativo, send, view metadata y facilitate_in_person solo si la política lo autoriza; nunca decide por el paciente y no accede a contenido clínico sensible detallado salvo permiso explícito |
| `PLATFORM_ADMIN` | sin acceso a contenido interno de consentimientos de empresas |

No ampliar permisos clínicos por conveniencia.

## 11. Auditoría mínima

Eventos:

- `CONSENT_TEMPLATE_CREATED`
- `CONSENT_TEMPLATE_VERSION_CREATED`
- `CONSENT_TEMPLATE_VERSION_PUBLISHED`
- `CONSENT_INSTANCE_CREATED`
- `CONSENT_REVIEW_LINK_CREATED`
- `CONSENT_VIEWED`
- `CONSENT_SIGNED`
- `CONSENT_REJECTED`
- `CONSENT_PDF_DOWNLOADED`
- `CONSENT_COPY_DELIVERED`
- `CONSENT_REVOKED`
- `CONSENT_VOIDED`
- `CONSENT_WET_INK_SCANNED`
- `CONSENT_ACCESS_DENIED`
- `CONSENT_INTEGRITY_CHECK_FAILED`

No registrar texto clínico completo en auditoría general. Guardar IDs, hashes, resultado, actor, canal, IP, user-agent, sede, empresa y timestamps.

## 12. PDF final

El PDF final debe contener:

- branding institucional;
- datos de empresa y sede;
- datos de paciente;
- datos de representante/testigo si aplica;
- datos del profesional;
- tipo y versión de plantilla;
- contenido exacto aceptado/rechazado;
- declaraciones;
- decisión;
- fecha/hora local y zona horaria;
- mecanismo de identificación;
- firma manuscrita capturada, si aplica;
- sección de evidencia técnica resumida;
- hash o código de verificación;
- nota de alcance: firma electrónica simple o contingencia, según el caso;
- constancia de copia.

No debe incluir secretos, tokens en claro ni datos técnicos excesivos que faciliten abuso.

## 13. Entrega de copia

Debe registrarse uno o varios eventos:

- descarga inmediata;
- envío manual registrado;
- puesta a disposición en portal futuro;
- entrega física;
- correo/SMS futuro.

En C019A.1 no debe integrarse correo/SMS real. C019A.3 solo podrá incorporar el canal expresamente autorizado y probado.

## 14. UX objetivo

Ubicación inicial:

```text
Paciente
  → Documentos
  → Consentimientos
```

Flujo interno:

```text
Nuevo consentimiento
  → tipo/plantilla
  → relación clínica
  → firmantes
  → revisar documento
  → elegir canal
  → aceptar/rechazar
  → PDF final / constancia
```

Estados visibles, traducidos desde la máquina canónica:

- borrador;
- listo para revisión;
- pendiente de firma;
- visto;
- firmado;
- rechazado;
- enlace vencido;
- revocado;
- anulado;
- contingencia física pendiente;
- soporte físico incorporado.

Alertas UX:

- menor sin representante válido;
- plantilla sin versión activa;
- documento expirado;
- consentimiento requerido rechazado;
- consentimiento revocado;
- firma física pendiente de subir;
- PDF final no disponible;
- hash fallido.

## 15. Integración con módulos Dentia

### Pacientes

Consentimientos se listan en expediente. Deben usar paciente y responsables como base, con snapshots históricos.

### Agenda

Una cita puede requerir o recomendar consentimiento por procedimiento, pero no debe bloquear urgencias salvo regla configurada.

### Tratamientos y procedimientos

Un procedimiento planificado puede sugerir consentimiento. No debe cambiar reglas económicas ni aprobar presupuestos.

### Odontograma

Los eventos odontográficos pueden contextualizar un consentimiento por pieza/procedimiento, pero no debe duplicarse evidencia clínica.

### Evoluciones

La evolución puede referenciar consentimientos vigentes. No modificar evoluciones firmadas. Si se firma una evolución sin consentimiento recomendado, registrar alerta/constancia si la política lo exige.

### Documentos clínicos y recetas

Reutilizar motor documental y patrones de PDF/hash, pero mantener entidad propia de consentimiento.

### Reportes

Futuro: métricas agregadas de consentimientos pendientes, aceptados, rechazados, revocados y contingencias físicas, sin exponer contenido clínico sensible.

### Backups semánticos

Consentimientos finales, evidencias y PDFs deben quedar incluidos en verificación de backup/restore de storage clínico.

## 16. Roadmap aprobado para revisión

- **C019A.0 — Contrato y decisiones:** contrato maestro, arquitectura, cumplimiento, UX, estrategia de pruebas, decision log y compuerta humana.
- **C019A.1 — Plantillas y versiones:** modelo, publicación inmutable, variables permitidas, permisos y auditoría; sin OTP ni firma.
- **C019A.2 — Instancias y flujo clínico:** creación desde paciente, relaciones clínicas, revisión profesional y estados internos.
- **C019A.3 — Enlace, QR, portal y OTP:** acceso público opaco, sesiones, expiración, rate limiting, replay e identidad declarada.
- **C019A.4 — Firma, evidencia, PDF y copia:** captura por sesión, sellado atómico, SHA-256, storage, descarga y entrega.
- **C019A.5 — Menores, representantes, rechazo, revocación y contingencia:** políticas por país, asentimiento, testigos/intérpretes y soporte físico.
- **C019A.6 — Hardening, backup, pruebas y piloto:** seguridad, IDOR, restore semántico, concurrencia, DST y validación de piloto.

## 17. Pruebas obligatorias futuras

### Multiempresa

- empresa A no ve consentimientos de B;
- token público de A no accede a B;
- storage por empresa.

### Menores y representantes

- menor exige representante si plantilla lo requiere;
- snapshot de representante queda congelado;
- cambio posterior de responsable no altera histórico.

### Versionado

- plantilla activa no se edita destructivamente;
- nueva versión no altera consentimientos anteriores;
- PDF indica versión usada.

### Decisiones

- aceptación genera PDF/hash;
- rechazo genera constancia;
- revocación conserva original;
- anulación exige motivo.

### Evidencia

- IP/user-agent/canal/fecha/zona horaria;
- hash de PDF;
- hash de contenido;
- token no se guarda en claro;
- firma capturada no se reutiliza.

### Zona horaria

- Bogotá;
- Santiago;
- empresa multisede;
- backend en UTC.

### Seguridad

- permisos por rol;
- `PLATFORM_ADMIN` sin contenido clínico interno;
- enlaces expirados;
- replay de token rechazado;
- rate limit;
- descarga verifica integridad.

## 18. Riesgos y decisiones pendientes

1. Validación jurídica Colombia/Chile sobre suficiencia de firma electrónica simple por tipo de consentimiento.
2. Definición clínica de plantillas odontológicas por procedimiento.
3. Política de menores, asentimiento y representantes.
4. Necesidad de testigos en casos específicos.
5. Requisitos de firma electrónica avanzada en Chile para casos particulares.
6. Nivel mínimo de identidad para enlaces remotos.
7. Canal de entrega de copia: manual, correo, portal o SMS.
8. Conservación de evidencia técnica y política de retención.
9. Acceso de secretaria a contenido vs. metadata.
10. Estrategia de proveedor externo si se requiere firma avanzada.

## 19. Decisión C019A.0

Dentia debe implementar consentimientos informados como módulo propio, integrado al expediente clínico y al sistema documental, con evidencia probatoria explícita. El módulo debe reutilizar patrones actuales de empresa/sede/paciente/responsables/PDF/hash/auditoría, pero no debe reducirse a documentos clínicos narrativos ni a una imagen de firma pegada en PDF.

C019A.0 queda **listo para revisión humana**, no jurídicamente aprobado. El inicio de C019A.1 queda sujeto a la compuerta definida en el [registro de decisiones](../readiness/C019A0-Consent-Decision-Log.md).

## 20. Fuentes normativas consultadas

- Colombia — Ley 527 de 1999, Gestor Normativo Función Pública: <https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4276>
- Colombia — Decreto 2364 de 2012, SUIN-Juriscol: <https://www.suin-juriscol.gov.co/viewDocument.asp?ruta=Decretos%2F1442265>
- Colombia — Ley 23 de 1981, Gestor Normativo Función Pública: <https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=68760>
- Colombia — Ley Estatutaria 1751 de 2015, SUIN-Juriscol: <https://www.suin-juriscol.gov.co/viewDocument.asp?id=30019746>
- Colombia — Resolución 1995 de 1999, Ministerio de Salud: <https://www.minsalud.gov.co/Normatividad_Nuevo/RESOLUCI%C3%93N%201995%20DE%201999.pdf>
- Colombia — Resolución 309 de 2025, SUIN-Juriscol: <https://www.suin-juriscol.gov.co/viewDocument.asp?ruta=Resolucion%2F30054600>
- Chile — Ley 19.799, Biblioteca del Congreso Nacional: <https://www.bcn.cl/leychile/Navegar?idNorma=196640>
- Chile — Ley 20.584, Biblioteca del Congreso Nacional: <https://www.leychile.cl/leychile/navegar?idNorma=1039348>
- Chile — Decreto 31 de 2012, Ministerio de Salud, Biblioteca del Congreso Nacional: <https://www.bcn.cl/leychile/navegar?i=1046012>
- Chile — Carta de derechos y deberes de los pacientes, Ministerio de Salud: <https://www.minsal.cl/derechos-y-deberes-de-los-pacientes/>

Fecha de consulta: 2026-07-30. La matriz, alcance y advertencias de vigencia están en [C019A0-Consent-Colombia-Chile.md](../compliance/C019A0-Consent-Colombia-Chile.md).

## 21. Auditoría editorial y matriz de trazabilidad

Brechas detectadas en la consolidación inicial y corregidas en C019A.0-FINAL:

- aceptación, finalización y contingencia física tratadas como estados separados sin una semántica terminal única;
- ausencia de distinción explícita entre representante, acudiente, testigo e intérprete;
- falta de separación entre consentimiento, autorización, rechazo, revocación y anulación;
- arquitectura, threat model, cumplimiento, UX y pruebas concentrados en un solo documento;
- decisiones de OTP, firma, entrega, retención y contingencia sin estado formal;
- roadmap antiguo C033A/C047A potencialmente contradictorio;
- falta de compuerta objetiva para C019A.1;
- referencias normativas sin matriz de alcance, vigencia y preguntas jurídicas;
- falta de listas separadas para revisores humanos por país y disciplina.

Trazabilidad final:

| Requisito C019A.0 | Fuente de verdad |
| --- | --- |
| propósito, taxonomía y filosofía clínica | secciones 1, 4 y 6 de este contrato |
| consentimiento, autorización, rechazo, revocación y anulación | sección 5.2 |
| paciente, representante, acudiente, testigo e intérprete | secciones 5.1, 5.2 y 6 |
| consentimiento vs. asentimiento | secciones 5.2 y 6.2 |
| plantilla, versión, instancia, sesión, evidencia, PDF, anexos y entrega | secciones 5.2, 7 y 8; arquitectura secciones 3–4 |
| estados, transiciones, actores, PDF y conservación | sección 5.3, máquina canónica única |
| identidad electrónica y firma no reutilizable | secciones 7.2–7.4; arquitectura secciones 10–12 |
| campos obligatorios y datos que nunca se guardan | secciones 6.1, 7.1 y 8.3; arquitectura secciones 3 y 8 |
| token opaco, OTP hasheado y QR sin datos clínicos | arquitectura secciones 10–11 |
| multiempresa, sedes y `PLATFORM_ADMIN` | secciones 2, 8 y 10; arquitectura sección 6 |
| storage, PDF, hash y atomicidad | secciones 7, 8 y 12; arquitectura secciones 7 y 12 |
| auditoría append-only | sección 11; arquitectura sección 8 |
| backup y restore C018R.3/C018R.4 | arquitectura secciones 2, 6 y 9 |
| portal público y contrato API | sección 9; arquitectura secciones 5 y 10 |
| threat model y riesgos residuales | arquitectura secciones 13–14 |
| Colombia/Chile y vigencia normativa | matriz de cumplimiento |
| flujo presencial, remoto, rechazo, revocación y papel | documento de UX |
| pruebas P0/P1/P2 y fases | estrategia de pruebas |
| 20 decisiones y estados de revisión | Decision Log |
| preguntas a abogados/odontólogos | Decision Log, secciones 5–8 |
| roadmap C019A.0–C019A.6 | sección 16 y `DOCS/D005 - ROADMAP DESARROLLO.md` |
| criterios para iniciar C019A.1 | Decision Log, sección 4 |

Regla editorial: si una implementación futura cambia una decisión canónica, debe actualizar primero el documento propietario y luego sus enlaces; no se copiará una segunda máquina de estados ni se presentará una recomendación jurídica como aprobación.
