# C019A.0 — Registro de decisiones y preparación para C019A.1

Estado: listo para revisión humana.

Fecha: 2026-07-30.

Documento maestro: [Contrato clínico-funcional C019A.0](../clinical/C019A0-Informed-Consents-Electronic-Acceptance-Contract.md).

Estados permitidos:

- `ADOPTED`: decisión técnica/producto aceptada que no presume suficiencia jurídica ni clínica.
- `PROVISIONAL`: recomendación operativa sujeta a medición o definición posterior.
- `LEGAL_REVIEW_REQUIRED`: no debe cerrarse sin abogado del país aplicable.
- `CLINICAL_REVIEW_REQUIRED`: no debe cerrarse sin odontólogo del país aplicable.

## 1. Las 20 decisiones obligatorias

| ID | Tema | Decisión recomendada | Alternativa | Justificación | Riesgo | Pendiente jurídico | Pendiente clínico | Fase | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D01 | Canal OTP inicial | Correo; SMS post-MVP | SMS o proveedor multicanal desde inicio | reutiliza dato existente y reduce integración inicial | correo comprometido o compartido | determinar fuerza probatoria y consentimiento del canal | confirmar viabilidad con pacientes reales | C019A.3 | `PROVISIONAL` |
| D02 | Vigencia OTP | Política configurable corta; valor exacto no fijado en A.0 | valor global fijo | evita convertir un supuesto en regla jurídica | demasiado corto excluye; largo aumenta abuso | confirmar requisitos/expectativas por país | validar tiempo razonable en consulta | C019A.3 | `PROVISIONAL` |
| D03 | Vigencia del enlace | Configurable por plantilla/canal; valor exacto no fijado | enlace permanente | reduce exposición y permite políticas distintas | expiración durante explicación o enlace robado | confirmar conservación/acceso y reenvío | validar duración operativa | C019A.3 | `PROVISIONAL` |
| D04 | Intentos | Límites separados para OTP, reenvío y token; valores por hardening | intentos ilimitados | mitiga fuerza bruta y abuso | bloqueo legítimo o ataque distribuido | ninguno específico; revisar tratamiento de logs | definir soporte ante bloqueo | C019A.3/A.6 | `PROVISIONAL` |
| D05 | Firma celular/tableta | Dedo o stylus, captura exclusiva por sesión y documento | pad especializado o firma almacenada | accesible, sin compra de hardware, coherente con MVP | el trazo no prueba identidad/capacidad | suficiencia por categoría y país | aceptación de ergonomía y explicación | C019A.4 | `LEGAL_REVIEW_REQUIRED` |
| D06 | Uso de mouse | Solo contingencia en escritorio, identificado en evidencia | prohibir o permitir como canal normal | conserva accesibilidad sin equipararlo al flujo preferido | trazo pobre o cuestionable | valor probatorio | aceptabilidad en clínica | C019A.4 | `PROVISIONAL` |
| D07 | Confirmación profesional | Obligatoria antes de emitir sesión para consentimientos clínicos | emisión por personal administrativo sin revisión | el consentimiento es proceso informativo clínico | falsa constancia o cuello de botella | texto exacto y responsable legal | quién puede confirmar por procedimiento | C019A.2 | `CLINICAL_REVIEW_REQUIRED` |
| D08 | Entrega de copia | Descarga inmediata + enlace seguro; adjunto de correo pendiente | adjuntar siempre PDF o solo papel | minimiza exposición y registra acceso | enlace no usado o correo inseguro | obligación, plazo y canal por país | momento adecuado en flujo | C019A.4 | `LEGAL_REVIEW_REQUIRED` |
| D09 | Rechazo | Decisión de primera clase con constancia propia; nunca consentimiento | tratarlo como cancelación/error | preserva autonomía y trazabilidad | copy intimidatorio o impacto mal aplicado | contenido/firmantes/efectos | consecuencias clínicas y urgencias | C019A.5 | `ADOPTED` |
| D10 | Revocación | Evento posterior; conserva original y genera constancia | editar/eliminar consentimiento original | protege historia e integridad | mostrar como retroactiva indebidamente | revocabilidad y efectos por tipo | impacto en plan clínico | C019A.5 | `ADOPTED` |
| D11 | Contingencia física | Papel firmado + escaneo hasheado como `WET_INK_SCANNED` | suspender atención o etiquetar como firma electrónica | continuidad operativa y clasificación honesta | escaneo ilegible, pérdida del original | custodia, original y retención | casos donde debe usarse | C019A.5 | `LEGAL_REVIEW_REQUIRED` |
| D12 | Representante | Participante separado con snapshot y fundamento; acudiente no equivale automáticamente | reutilizar responsable sin validación | evita suplantar representación y preserva contexto histórico | representación inválida | edades, capacidad y facultades por país | asentimiento y comunicación adaptada | C019A.5 | `LEGAL_REVIEW_REQUIRED` |
| D13 | Plantillas por país | Motor común con políticas/versiones Colombia y Chile separadas | una plantilla universal o motores distintos | evita bifurcar código y permite contenido local | configuración equivocada de país | textos y obligatoriedad | contenido odontológico local | C019A.1 | `ADOPTED` |
| D14 | Hash | SHA-256 de contenido canónico, PDF y archivos persistidos | hash débil o solo PDF | estándar interoperable y disponible | canonicalización inconsistente | ninguno específico; no confundir hash con firma | ninguno | C019A.1/A.4 | `ADOPTED` |
| D15 | QR | Solo enlace opaco; sin paciente, empresa ni clínica sensible | UUID/datos codificados en QR | minimiza exposición y enumeración | fotografía/reuso durante vigencia | privacidad y acuerdo del canal | uso práctico en recepción/consulta | C019A.3 | `ADOPTED` |
| D16 | Auditoría | Eventos append-only + proyección general minimizada | registro mutable o contenido completo en logs | trazabilidad sin duplicar clínica sensible | exceso de datos o evento faltante | retención/acceso | eventos relevantes para revisión clínica | C019A.1–A.6 | `ADOPTED` |
| D17 | Retención | Configurable por país/tipo, sin borrado automático hasta definición legal | plazo global fijo o conservación indefinida automática | evita borrar evidencia o retener sin fundamento | sobre-retención o incumplimiento | plazo, original físico, supresión y litigio | valor clínico histórico | C019A.6 | `LEGAL_REVIEW_REQUIRED` |
| D18 | Storage | Storage clínico segregado por empresa, claves internas, archivos inmutables y hash; incluido en backup | DB base64, ruta pública o storage compartido sin prefijo | seguridad, restore y operación existentes | desincronización DB/archivo | residencia/encargados de datos | ninguno | C019A.4/A.6 | `ADOPTED` |
| D19 | Verificación pública | Página limitada a integridad/estado mediante código opaco; sin contenido clínico ni identidad completa | portal público con PDF/datos o sin verificación | permite comprobar artefacto sin exponer expediente | enumeración y fuga contextual | datos mínimos y legitimación del consultante | utilidad real para clínica/paciente | post-MVP/A.6 | `PROVISIONAL` |
| D20 | Estado mínimo del MVP | C019A.1 implementa solo plantillas/versiones; MVP funcional de firma se completa por fases A.2–A.6 y usa estados canónicos | construir firma/OTP junto con plantillas | reduce riesgo y separa motor documental de identidad/firma | expectativa de módulo “completo” antes de hardening | gate jurídico antes de piloto | gate clínico antes de piloto | C019A.1–A.6 | `ADOPTED` |

## 2. Decisiones por estado

### ADOPTED

- D09 rechazo como decisión de primera clase.
- D10 revocación no destructiva.
- D13 motor común con políticas por país.
- D14 SHA-256.
- D15 QR opaco sin datos clínicos.
- D16 auditoría append-only minimizada.
- D18 storage clínico segregado e íntegro.
- D20 implementación por fases y C019A.1 limitado a plantillas/versiones.

### PROVISIONAL

- D01 correo como OTP inicial.
- D02 vigencia OTP configurable, sin valor final.
- D03 vigencia del enlace configurable, sin valor final.
- D04 límites de intentos/reenvíos, sin cifras finales.
- D06 mouse solo como contingencia.
- D19 verificación pública limitada, post-MVP.

### LEGAL_REVIEW_REQUIRED

- D05 suficiencia de dedo/stylus y paquete de evidencia.
- D08 entrega de copia y canal.
- D11 contingencia física, custodia y original.
- D12 representación, capacidad y menores.
- D17 retención.

### CLINICAL_REVIEW_REQUIRED

- D07 confirmación profesional.

Además, D09, D10 y D13 están adoptadas como arquitectura, pero sus textos, obligatoriedad y efectos concretos siguen sujetos a revisión jurídica y clínica. `ADOPTED` no significa “jurídicamente aprobado”.

## 3. MVP definido

### C019A.1

- plantillas;
- versiones borrador/publicada/sustituida/retirada;
- variables permitidas;
- políticas por país;
- permisos preliminares;
- auditoría;
- preview con marca de borrador;
- sin instancia firmable;
- sin enlace, QR, OTP o firma;
- sin afirmar aprobación jurídica de textos.

### MVP clínico completo antes de piloto

El alcance funcional mínimo se alcanza solo al completar C019A.2–C019A.6:

- instancia clínica;
- revisión profesional;
- decisión digital o contingencia;
- evidencia e integridad;
- PDF y copia;
- rechazo/revocación;
- representantes;
- seguridad, backup y pruebas.

No se compran pads especializados en el MVP. SMS y proveedor de firma avanzada quedan post-MVP salvo conclusión jurídica que los convierta en requisito.

## 4. Criterios objetivos para autorizar C019A.1

- [ ] Taxonomía aprobada provisionalmente por producto.
- [ ] Máquina de estados única aceptada y enlazada.
- [ ] Modelo conceptual coherente, sin usar `documentos_clinicos` como sustituto.
- [ ] D13, D14, D16, D18 y D20 aceptadas.
- [ ] Reglas de plantillas/versiones adoptadas.
- [ ] Allowlist de variables definida por tipo y país.
- [ ] Reglas de publicación, sustitución y retiro definidas.
- [ ] Empresa derivada de sesión y sede validada.
- [ ] Plantillas estándar vs. empresariales definidas.
- [ ] Permisos preliminares y `PLATFORM_ADMIN` sin acceso clínico.
- [ ] Auditoría de publicación definida sin contenido clínico completo.
- [ ] No hay pregunta jurídica que bloquee exclusivamente construir el motor de plantillas.
- [ ] OTP, enlace, QR y firma quedan expresamente fuera de C019A.1.
- [ ] Validación clínica inicial de categorías Colombia.
- [ ] Validación clínica inicial de categorías Chile.
- [ ] Textos y plantillas permanecen marcados “borrador/no aprobados”.
- [ ] No se publica un catálogo clínico como legalmente suficiente.
- [ ] Pruebas de inmutabilidad, XSS, tenant y variables están especificadas.

Autorizar C019A.1 no autoriza firma electrónica, portal público ni piloto.

## 5. Preguntas para abogado Colombia

| ID | Pregunta | Decisión |
| --- | --- | --- |
| CO-L01 | ¿Para cuáles procedimientos odontológicos debe constar por escrito el consentimiento? Liste categorías cerradas. | D07/D13 |
| CO-L02 | ¿Un paquete de enlace/OTP por correo, firma gráfica, hash, IP, user-agent y evidencia de presentación es admisible para cada categoría? Sí/no/condiciones. | D01/D05 |
| CO-L03 | ¿Qué texto debe constituir acuerdo sobre el mecanismo de firma electrónica bajo Decreto 2364? | D05 |
| CO-L04 | ¿Cuándo se requiere firma digital/certificada o proveedor especializado? | D05 |
| CO-L05 | ¿Qué copia debe entregarse y en qué plazo/canal? | D08 |
| CO-L06 | ¿Debe conservarse el original físico después de escanearlo y por cuánto tiempo? | D11/D17 |
| CO-L07 | ¿Qué prueba mínima acredita la representación y cuándo un responsable registrado no basta? | D12 |
| CO-L08 | ¿Cómo aplicar Resolución 309 de 2025 a odontología general por edad, autonomía y riesgo? | D12 |
| CO-L09 | ¿Qué consentimientos/autorizaciones son revocables y con qué efecto temporal? | D10 |
| CO-L10 | ¿Cuánto conservar cada evidencia, sesión fallida, PDF y evento de auditoría? | D17 |
| CO-L11 | ¿Qué datos mínimos puede exponer una verificación pública sin vulnerar reserva clínica/datos personales? | D19 |
| CO-L12 | ¿Puede C019A.1 operar con textos expresamente marcados como borradores internos sin firma? | D20 |

## 6. Preguntas para abogado Chile

| ID | Pregunta | Decisión |
| --- | --- | --- |
| CL-L01 | ¿Qué procedimientos odontológicos quedan en la regla escrita del artículo 14 de Ley 20.584? | D07/D13 |
| CL-L02 | ¿Cuándo basta firma electrónica simple y cuándo se requiere avanzada bajo Ley 19.799? | D05 |
| CL-L03 | ¿OTP por correo + firma gráfica + evidencia técnica satisface autenticidad para los casos escritos? Sí/no/condiciones. | D01/D05 |
| CL-L04 | ¿Qué copia debe entregarse y por qué canal/plazo? | D08 |
| CL-L05 | ¿Qué requisitos aplican a papel escaneado y conservación del original? | D11/D17 |
| CL-L06 | ¿Quién representa a menores o personas sin capacidad y cómo se documenta? | D12 |
| CL-L07 | ¿Cómo debe registrarse asentimiento y desde qué criterios de autonomía? | D12 |
| CL-L08 | ¿Qué efectos tiene el rechazo y la revocación por familia documental? | D09/D10 |
| CL-L09 | ¿Cuál es la retención mínima de consentimiento, evidencia técnica y ficha clínica? | D17 |
| CL-L10 | ¿Qué preparación exige Ley 21.719 antes de su vigencia del 01-12-2026 sin aplicarla anticipadamente? | D17/D19 |
| CL-L11 | ¿Qué datos mínimos admite una verificación pública? | D19 |
| CL-L12 | ¿Puede C019A.1 construir solo el motor de plantillas con textos no publicados como jurídicamente aprobados? | D20 |

## 7. Preguntas para odontólogo Colombia

| ID | Pregunta | Decisión |
| --- | --- | --- |
| CO-C01 | Seleccione procedimientos que siempre requieren consentimiento escrito en su práctica. | D07/D13 |
| CO-C02 | ¿Quién debe confirmar que se explicaron riesgos y alternativas: tratante, odontólogo administrador u otro? | D07 |
| CO-C03 | ¿En qué momento del flujo debe quedar listo para firma: valoración, plan, cita o antes del procedimiento? | D07 |
| CO-C04 | ¿Una tableta compartida es operativamente viable y cómo se protege privacidad? | D05 |
| CO-C05 | ¿Cuánto tiempo razonable necesita el paciente para revisar enlace remoto? | D03 |
| CO-C06 | ¿Qué situaciones justifican papel y qué control de legibilidad necesita? | D11 |
| CO-C07 | ¿Cómo se documenta clínicamente el rechazo sin coacción? | D09 |
| CO-C08 | ¿Qué alertas debe generar una revocación antes de un procedimiento? | D10 |
| CO-C09 | ¿Qué categorías y textos iniciales deben validar especialistas? | D13 |
| CO-C10 | ¿Qué papel debe tener el asentimiento del menor en odontología? | D12 |

## 8. Preguntas para odontólogo Chile

| ID | Pregunta | Decisión |
| --- | --- | --- |
| CL-C01 | Seleccione procedimientos quirúrgicos, invasivos o de riesgo relevante que requieren escrito. | D07/D13 |
| CL-C02 | ¿Quién confirma profesionalmente la información antes de firma? | D07 |
| CL-C03 | ¿En qué momento se presenta y cuánto tiempo debe poder revisarse? | D03/D07 |
| CL-C04 | ¿Tableta y celular son viables en consulta y recepción? | D05 |
| CL-C05 | ¿Cuándo usar papel por contingencia? | D11 |
| CL-C06 | ¿Qué información debe incluir el rechazo en ficha clínica? | D09 |
| CL-C07 | ¿Qué alerta clínica necesita una revocación? | D10 |
| CL-C08 | ¿Qué categorías odontológicas y lenguaje requieren adaptación chilena? | D13 |
| CL-C09 | ¿Cómo participan menores y acompañantes en explicación/asentimiento? | D12 |
| CL-C10 | ¿La copia inmediata por descarga satisface el flujo práctico o se necesita impresión? | D08 |

## 9. Riesgos que bloquean fases posteriores, no C019A.1

- suficiencia de OTP/firma: bloquea C019A.3/A.4;
- menores/representación: bloquea activación de esas políticas en C019A.5;
- retención: bloquea piloto C019A.6;
- textos clínicos: bloquea publicación de plantillas clínicas, no el motor de borradores;
- firma avanzada: bloquea categorías que la requieran, no el versionado.

## 10. Veredicto

**C019A.0 — LISTO PARA REVISIÓN HUMANA**

Condicionado a:

- revisión jurídica Colombia;
- revisión jurídica Chile;
- revisión clínica Colombia;
- revisión clínica Chile.

No está jurídicamente aprobado y no autoriza implementación más allá de C019A.1 cuando se cumpla la compuerta de la sección 4.

## 11. Actualización técnica C019A.3

Se implementó localmente el canal de revisión con correo OTP como decisión provisional y configurable. Esto no resuelve la suficiencia jurídica del mecanismo ni autoriza aceptación o firma. Los valores operativos y la compuerta para C019A.4 constan en `C019A3-Consent-Access-Decision-Update.md`.

## 12. Actualización técnica C019A.4

Se implementó el mecanismo técnico provisional para adulto actuando en nombre propio, evidencia, PDF y copia. Permanece bloqueado en producción y no resuelve las preguntas jurídicas D01/D05/D08/D12/D17. La compuerta está en `C019A4-Consent-Acceptance-Decision-Update.md`.

## C019A4-LIB1

Decisión: la biblioteca oficial se implementa como catálogo global desacoplado. La instalación exacta conserva contenido Dentia; las copias editables pasan a responsabilidad de la clínica. Documentos especiales no se ofrecen como consentimientos comunes.
# Actualización C019A.5 — 2026-08-07

- Dentia adopta un canal manuscrito separado de la aceptación electrónica.
- Un mismo snapshot clínico alimenta ambos canales, pero sus evidencias nunca se mezclan.
- Elegir papel revoca accesos electrónicos activos; el packet impreso queda congelado.
- `SIGNED` solo se asigna al canal papel cuando la copia completa fue verificada y sellada.
- La clínica conserva el original físico; Dentia conserva la copia digitalizada y evidencia técnica sin fijar un periodo legal universal.
