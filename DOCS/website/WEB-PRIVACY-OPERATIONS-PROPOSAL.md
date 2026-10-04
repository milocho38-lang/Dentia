# Procedimiento operativo de privacidad para leads de la website

**Estado:** procedimiento manual aprobado el 3 de octubre de 2026 (`America/Bogota`)

**Alcance:** solicitudes de demostración de `dentiapro.com` que no se convierten en clientes

**No autoriza:** ejecutar borrados sin un caso válido, la doble revisión y los controles de este procedimiento; tampoco autoriza jobs, migraciones ni modificación retroactiva de consentimientos

## 1. Decisiones confirmadas

- Responsable del tratamiento del sitio y de los leads: **Camilo Andres Medina Romero**.
- Domicilio informado: **Calle 33B #2BN-83, Cali, Colombia**.
- Teléfono informado: **+57 3106477569**.
- Canal aprobado para solicitudes de privacidad: **dentiapro.notificaciones@gmail.com**.
- Camilo Andres Medina Romero decide las finalidades y el uso de las solicitudes.
- Kimberly Astudillo Sánchez coopera en la operación del canal y del flujo comercial. Esta cooperación no le atribuye por sí sola corresponsabilidad sobre el tratamiento.
- Retención aprobada para solicitudes no convertidas en clientes: **12 meses desde el último contacto**.
- Host contractual confirmado: Hostinger, con hostname `srv1776883.hstgr.cloud`.
- La región física o contractual del alojamiento continúa sin confirmar y no debe inferirse.

El plazo anterior no se extiende automáticamente a contratos, historias clínicas, datos de pacientes, consentimientos clínicos, auditorías de seguridad ni información de clientes. Esas categorías requieren decisiones y políticas propias.

## 2. Estado técnico actual

Actualmente la solicitud y sus metadatos comerciales se conservan en PostgreSQL sin vencimiento automático. Las notas internas también permanecen sin plazo. La aplicación persiste una huella SHA-256 de deduplicación y no dispone de borrado, anonimización, exportación de derechos ni job de retención.

La notificación inicial se entrega mediante Gmail a un destinatario operativo privado. Dentia no administra el buzón mediante API y no puede borrar esa copia desde la aplicación. Los backups contienen copias históricas de PostgreSQL y se rigen por su propia rotación operativa. Los logs del proxy tienen rotación independiente y no forman parte de la ficha comercial del lead.

Por tanto, la regla de 12 meses está aprobada como política, pero **todavía no está automatizada ni puede presentarse como una eliminación automática existente**.

## 3. Criterio de “último contacto”

El vencimiento debe calcularse desde la última comunicación real entre Dentia y la persona, no desde una edición interna. Deben contar:

1. envío de la solicitud inicial por la persona;
2. correo, llamada o mensaje de seguimiento efectivamente realizado por Dentia;
3. respuesta posterior de la persona;
4. demostración realizada o reprogramada con comunicación a la persona;
5. nueva solicitud expresa de continuar la conversación comercial.

No deben reiniciar el plazo por sí solos:

- asignación interna de responsable;
- consulta del lead;
- corrección administrativa;
- nota que no documente una comunicación real;
- ejecución del proceso de retención;
- reintento técnico de notificación.

La implementación actual no tiene un campo inequívoco para todos esos eventos. Para el procedimiento manual, la fecha se determina con la última comunicación bilateral registrada en las notas operativas y en el buzón; si nunca existió contacto posterior, se usa `created_at`. `contacted_at`, `scheduled_at` y `updated_at` sirven como evidencia auxiliar, pero una edición interna no reinicia el plazo. No se deben reinterpretar ni reetiquetar solicitudes históricas sin revisión.

Una futura columna canónica `last_contact_at` facilitaría automatización y reportes, pero no es requisito para aplicar de forma manual el criterio aprobado ni para describirlo con veracidad.

## 4. Flujo para ejercicio de derechos

### 4.1 Recepción

- Canal: `dentiapro.notificaciones@gmail.com`.
- Atención operativa: Camilo Andres Medina Romero y Kimberly Astudillo Sánchez.
- Decisiones sobre alcance, excepciones y respuesta final: Camilo Andres Medina Romero.
- Registrar fecha de recepción, derecho solicitado, identidad del solicitante, alcance, responsable interno, acciones, respuesta y fecha de cierre.

### 4.2 Verificación de identidad

Solicitar únicamente información proporcional. Para un lead de website, el control inicial debe usar el mismo correo registrado y datos suficientes para localizar la solicitud. No pedir documentos de identidad por defecto. Si hay duda razonable, definir un mecanismo adicional antes de revelar o modificar datos.

No enviar datos personales en una respuesta hasta completar la verificación. Toda solicitud sospechosa debe quedar en pausa y documentada, sin negar el derecho automáticamente.

### 4.3 Búsqueda y alcance

Localizar, sin exponer información de otras personas:

- fila de `demo_requests`;
- notas de `demo_request_notes`;
- estado y responsable comercial;
- huella de deduplicación asociada;
- eventos de auditoría vinculados al identificador del lead;
- copia de notificación en Gmail;
- copias contenidas temporalmente en backups;
- logs solo cuando la solicitud y la capacidad técnica permitan relacionarlos de forma fiable.

### 4.4 Respuesta y evidencia

Conservar evidencia mínima de:

- recepción y verificación;
- búsquedas realizadas;
- decisión y fundamento;
- sistemas afectados;
- acciones ejecutadas y fecha;
- respuesta entregada;
- excepciones o copias pendientes de expirar.

Esa evidencia no debe recrear todo el contenido eliminado. Debe conservarse bajo una política separada para cumplimiento y defensa de solicitudes de derechos, aún por aprobar.

## 5. Retención y eliminación

### 5.1 Leads no convertidos

Una revisión periódica debe identificar solicitudes cuyo `last_contact_at` haya superado 12 meses y que sigan sin conversión ni obligación de conservación aplicable. La ejecución debe:

1. bloquear nuevas acciones comerciales sobre el registro durante la revisión;
2. comprobar estado, último contacto y ausencia de conversión;
3. revisar si existe una solicitud de derechos, controversia, obligación legal o incidente abierto;
4. eliminar o anonimizar notas internas que identifiquen al prospecto;
5. eliminar o anonimizar los datos personales del lead;
6. inutilizar la huella de deduplicación para que no permanezca vinculable al registro eliminado;
7. eliminar la copia operativa en Gmail y sus ubicaciones equivalentes, incluidas papelera o archivo según la política aprobada del buzón;
8. registrar evidencia mínima no reconstructiva de la ejecución;
9. permitir que las copias de backup expiren por su rotación normal, con controles para no restaurarlas como datos activos.

Debe elegirse expresamente entre borrado físico y anonimización irreversible. La columna actual `deleted_at` solo oculta lógicamente el lead y no satisface por sí sola una eliminación de datos personales.

### 5.2 Conversión a cliente

Cuando un lead se convierte, la regla de 12 meses deja de gobernar únicamente esa ficha comercial. Antes de conservar o trasladar datos debe definirse:

- qué datos pasan al expediente contractual del cliente;
- con qué finalidad y fundamento;
- qué campos del lead se eliminan por duplicados o innecesarios;
- qué plazos contractuales, tributarios o probatorios aplican.

La conversión no autoriza reutilización ilimitada ni mezcla con datos clínicos.

### 5.3 Auditoría y seguridad

Los eventos actuales no incluyen email, teléfono, mensaje ni IP pública en claro. Su retención debe decidirse separadamente por finalidad de seguridad y trazabilidad. Si se conserva el identificador técnico de una solicitud eliminada, debe evaluarse que no permita reconstruir o volver a vincular al titular.

### 5.4 Gmail

La aplicación no controla el buzón. Se necesita un procedimiento del administrador de la cuenta que contemple búsqueda, etiquetas, archivo, papelera, copias y plazo de eliminación definitiva. No debe afirmarse que borrar la fila de PostgreSQL elimina el correo.

### 5.5 Backups

El script productivo conserva por defecto los **30 paquetes verificados más recientes**, no 30 días. La configuración productiva no sobreescribe ese valor. En la inspección del 4 de octubre de 2026 existían 30 paquetes, desde `dentia_20260730_014653` hasta `dentia_20261004_005537`. No existe cron o timer identificado para crear backups periódicos: se generan en despliegues y ejecuciones manuales. El último backup de despliegue puede quedar protegido frente a la poda, por lo que el tiempo calendario real depende de la frecuencia de despliegues.

No se propone modificar backups históricos individualmente. La operación debe mantener:

- duración y rotación aprobada;
- acceso restringido;
- no uso ordinario de copias expiradas;
- registro de solicitudes de supresión pendientes en backups;
- reaplicación del borrado o anonimización si una copia se restaura;
- eliminación final al expirar la rotación.

La política pública puede explicar que las copias residuales se mantienen temporalmente hasta su rotación y que, si se restaura una copia, la supresión se reaplica antes de devolver el dato a uso ordinario. No debe prometer que todas las copias desaparecen exactamente al día 365: la rotación actual está definida por cantidad de paquetes, no por días.

## 6. Procedimiento manual aprobado

Este procedimiento no afirma que exista una acción automática. Fue aprobado como runbook acotado para atender solicitudes y vencimientos, siempre con doble revisión antes de eliminar:

1. **Registrar el caso:** asignar identificador interno, fecha, solicitante, alcance y operador; no copiar el contenido completo del lead al registro de control.
2. **Verificar identidad:** usar el correo registrado y una comprobación proporcional. No entregar ni borrar datos ante una coincidencia dudosa.
3. **Resolver el universo:** localizar el lead por email normalizado; identificar notas, auditoría técnica y notificación en Gmail sin consultar información de terceros.
4. **Determinar último contacto:** usar la última comunicación bilateral documentada; si no existe, usar `created_at`. Anotar las fuentes consultadas y la fecha resultante.
5. **Aplicar gates:** confirmar que no es cliente convertido y que no existe reclamación, incidente u obligación documentada que exija conservación limitada.
6. **Aplicar doble revisión:** Camilo Andres Medina Romero decide acceso, corrección, supresión o excepción; antes de una supresión, Camilo Andres Medina Romero y Kimberly Astudillo Sánchez revisan identidad, alcance, fuentes consultadas y objetivo exacto. Ninguna de las dos personas ejecuta la eliminación mientras exista desacuerdo o información incompleta.
7. **Ejecutar por sistema:**
   - Gmail: localizar la notificación exacta y moverla a eliminación conforme al procedimiento aprobado del buzón;
   - PostgreSQL: usar exclusivamente un comando o script previamente revisado, probado con datos sintéticos, limitado al UUID exacto y ejecutado dentro de transacción; eliminar primero notas y luego datos personales/lead, o aplicar la anonimización irreversible aprobada;
   - huella: eliminarla o volverla irreversiblemente no vinculable junto con el lead;
   - auditoría: conservar solo el evento técnico no reconstructivo si existe fundamento aprobado;
   - backups: no modificar paquetes históricos individualmente; registrar el UUID como supresión pendiente hasta que los paquetes correspondientes expiren por la rotación de los 30 paquetes verificados más recientes y reaplicar la supresión antes de devolver a uso ordinario cualquier backup restaurado.
8. **Verificar:** ejecutar consultas de solo lectura que confirmen ausencia o anonimización en tablas activas, ausencia de la copia operativa en Gmail y registro de la obligación sobre backups.
9. **Responder y cerrar:** comunicar el resultado, las excepciones y las copias que desaparecerán por rotación; conservar evidencia mínima del trámite sin recrear los datos eliminados.

El paso 7 sobre PostgreSQL requiere preparar para cada ejecución un comando o script seguro, revisado por ambas personas y probado primero con datos sintéticos. Hasta completar ese gate para un caso concreto puede recibirse, verificarse y documentarse la solicitud, pero no debe declararse completada una supresión de base de datos.

## 7. Excepciones

Una excepción no debe aplicarse automáticamente. Camilo debe revisar y documentar si existe una obligación legal, reclamación, prevención de fraude, incidente de seguridad o necesidad de defensa que justifique conservar una parte limitada por más tiempo.

La excepción debe indicar datos afectados, fundamento, acceso permitido, nueva fecha de revisión y criterio de cierre. No debe utilizarse para extender indefinidamente toda la ficha comercial.

## 8. Mejoras futuras recomendadas

Sin ejecutar todavía:

1. añadir `last_contact_at` y reglas exactas de actualización;
2. definir estados y casos que bloquean la depuración;
3. decidir borrado físico frente a anonimización irreversible;
4. diseñar operación idempotente para lead, notas y huella;
5. documentar manejo de auditoría y evidencia mínima;
6. aprobar procedimiento de Gmail;
7. confirmar rotación real de backups y restauración con reaplicación de bajas;
8. añadir vista previa, conteos, doble confirmación y registro de ejecución;
9. crear pruebas de aislamiento, autorización, antigüedad, excepciones y restauración;
10. ejecutar primero un reporte de solo lectura y revisión humana antes de cualquier eliminación.

Estas mejoras permiten automatizar y reducir errores, pero no son condición para publicar una política veraz que describa un procedimiento manual. Antes de afirmar que una supresión fue ejecutada sí debe existir un comando seguro y probado para PostgreSQL y un procedimiento aprobado para Gmail.

## 9. Gates de operación

- Texto legal consolidado, aprobado y publicado con su versión y fecha de vigencia.
- Región de Hostinger confirmada documentalmente o declarada como desconocida, sin afirmar una localización no verificada.
- Para cada supresión: procedimiento manual preparado, revisado por ambas personas y ensayado con datos sintéticos antes de operar sobre el UUID exacto.
- Propietario y suplente del canal de privacidad definidos.
- Plazo de respuesta legal confirmado para cada jurisdicción aplicable.
- Política de evidencia de derechos aprobada.
- Tratamiento de Gmail, backups, logs y auditoría descrito sin prometer eliminación automática.
- Texto público distingue la regla de 12 meses del ciclo residual de backups.

La herramienta automática, la columna adicional y los jobs son mejoras posteriores. No bloquean por sí solos la publicación del texto si la operación manual queda aprobada y el sitio no afirma capacidades inexistentes.
