# C019A.0 — Estrategia de pruebas de consentimientos

Estado: estrategia futura; no existen todavía suites productivas C019.

Documento maestro: [Contrato clínico-funcional C019A.0](../clinical/C019A0-Informed-Consents-Electronic-Acceptance-Contract.md).

Niveles:

- **P0:** puede causar exposición cross-tenant, decisión falsa, pérdida o alteración probatoria.
- **P1:** rompe flujo clínico, identidad, inmutabilidad o cumplimiento.
- **P2:** degrada operación, UX o trazabilidad sin falsear el expediente.

## 1. Matriz

| Familia | Riesgo | Nivel | Datos de prueba | Resultado esperado | Fase |
| --- | --- | --- | --- | --- | --- |
| Plantillas | edición de contenido publicado | P0 | versión DRAFT/PUBLISHED | publicado inmutable; cambio crea versión | C019A.1 |
| Versiones | instancia cambia al publicar nueva versión | P0 | v1 con instancia, publicar v2 | instancia conserva v1 y hash | C019A.1 |
| Variables | inyección o dato no permitido | P1 | allowlist, variable desconocida, HTML/script | rechazo/sanitización sin ejecución | C019A.1 |
| Estados | transición inválida | P0 | cada par de estados | solo transiciones canónicas | C019A.2 |
| Revisión profesional | firma sin confirmación requerida | P1 | instancia DRAFT | no se emite sesión | C019A.2 |
| OTP | código correcto/incorrecto/vencido | P0 | hashes, reloj controlado | verifica una vez; no filtra código | C019A.3 |
| Intentos OTP | fuerza bruta | P0 | intentos concurrentes | límite atómico y rate limit | C019A.3 |
| Enlace | token opaco/expirado | P0 | tokens A/B, vencidos | no enumera ni cruza tenant | C019A.3 |
| Reenvío | sesiones previas y rotación | P1 | varios reenvíos | política aplicada y auditada | C019A.3 |
| Replay | reutilización tras firma | P0 | mismo token/idempotency key | una sola decisión; respuesta idempotente | C019A.3–A.4 |
| Firma gráfica | reutilización entre instancias | P0 | captura de instancia A en B | imposible/rechazada; vínculo de hash | C019A.4 |
| Firma mouse/dedo | canal registrado | P2 | pointer types | evidencia identifica mecanismo | C019A.4 |
| Sellado | fallo PDF/storage/DB | P0 | fallos inyectados por etapa | no `SIGNED` parcial; compensación | C019A.4 |
| PDF | contenido/version/snapshots | P0 | fixtures completos | PDF exacto, marca correcta, sin secretos | C019A.4 |
| Hash | alteración de byte | P0 | PDF original/modificado | descarga valida original y bloquea alterado | C019A.4 |
| Entrega | descarga/enlace/fallo | P1 | canales y errores | evento exacto sin afirmar entrega fallida | C019A.4 |
| Representante | responsable de otro paciente/empresa | P0 | menor A, responsable B | rechazo sin filtración | C019A.5 |
| Asentimiento | no confundir roles | P1 | menor + representante | eventos y PDF diferenciados | C019A.5 |
| Testigo/intérprete | rol y orden | P1 | participantes múltiples | declaración individual, sin sustitución | C019A.5 |
| Rechazo | mostrado como aceptación | P0 | decisión REJECTED | constancia propia; nunca consentimiento | C019A.5 |
| Revocación | borrar/modificar original | P0 | SIGNED → REVOKED | original intacto, constancia vinculada | C019A.5 |
| Anulación | confundir con revocación | P1 | error administrativo | motivo/actor; decisión original preservada | C019A.5 |
| Contingencia | clasificar escaneo como electrónico | P1 | PDF físico | `WET_INK_SCANNED`, hash y custodio | C019A.5 |
| Multiempresa A/B | IDOR interno | P0 | dos empresas completas | A nunca ve/modifica B | C019A.1–A.6 |
| Sedes | relación cruzada | P0 | sede A/B | validación empresa y alcance | C019A.2 |
| Platform admin | acceso clínico implícito | P0 | token plataforma | denegado salvo mecanismo excepcional aprobado | C019A.2–A.6 |
| Rate limiting | abuso portal/PDF/OTP | P0 | ráfagas por IP/token | límites, backoff y auditoría | C019A.3/A.6 |
| Path traversal | escape storage | P0 | `../`, absoluta, Unicode | rechazo; ninguna lectura/escritura | C019A.4/A.6 |
| Symlink | escape de raíz | P0 | symlink interno a externo | no-follow/resolución segura | C019A.4/A.6 |
| XSS/HTML | script en plantilla/variables | P0 | tags, URLs, CSS | no ejecución en portal/PDF | C019A.1/A.6 |
| Archivos faltantes | DB sin PDF/evidencia | P1 | borrar fixture de storage | error de integridad, no falso éxito | C019A.4/A.6 |
| Hash incorrecto | storage alterado | P0 | reemplazo de archivo | bloqueo y `INTEGRITY_CHECK_FAILED` | C019A.4/A.6 |
| Backup | cobertura DB/storage | P0 | dataset con anexos/firmas | manifiesto completo | C019A.6 |
| Restore | recuperación semántica | P0 | backup aislado | vínculos/hashes/descargas correctos | C019A.6 |
| Colombia | políticas/plantillas | P1 | empresa CO | país, textos y reglas correctos | C019A.1–A.6 |
| Chile | políticas/plantillas | P1 | empresa CL | país, textos y reglas correctos | C019A.1–A.6 |
| Vigencia normativa | norma futura marcada vigente | P1 | Ley 21.719 antes/después 01-12-2026 | política usa fecha efectiva | C019A.1/A.6 |
| DST | fecha local Santiago | P1 | transición DST, backend UTC | UTC/local/zona coherentes | C019A.2/A.6 |
| Bogotá | cierre de día | P1 | medianoche local | fecha clínica correcta | C019A.2 |
| Concurrencia | firma y rechazo simultáneos | P0 | dos requests | exactamente una transición terminal | C019A.4/A.6 |
| Atomicidad | DB final, PDF falla | P0 | fault injection | rollback/estado recuperable | C019A.4/A.6 |
| Auditoría | secretos/datos clínicos en logs | P0 | OTP/token/texto | redacción y allowlist | C019A.3–A.6 |
| Auditoría | evento faltante | P1 | cada transición | actor, tenant, resultado y hashes | C019A.2–A.6 |
| Copia | enlace de descarga de otro firmante | P0 | token cruzado | denegado sin enumeración | C019A.4/A.6 |
| PDF físico | archivo ilegible/incompleto | P1 | páginas faltantes | no cerrar contingencia | C019A.5 |
| Abandono | abandono tratado como decisión | P0 | cerrar navegador | sigue pendiente/expira; nunca firma | C019A.3 |

## 2. Capas de prueba

### Unitarias

- validación de variables;
- transición de estados;
- cálculo temporal;
- hash canónico;
- mapeo de participantes;
- redacción de auditoría;
- policy engine Colombia/Chile.

### Servicios con PostgreSQL

- tenant y sedes;
- constraints e índices;
- control optimista;
- idempotencia;
- carreras terminales;
- publicación de versiones;
- proyecciones vigentes.

### Integración storage/PDF

- escritura atómica;
- paths y symlinks;
- SHA-256;
- archivo faltante/alterado;
- render seguro;
- manifiesto de backup.

### HTTP y seguridad

- permisos;
- IDOR A/B;
- portal público;
- rate limits;
- replay;
- errores anti-enumeración;
- headers de seguridad.

### E2E

- tableta;
- móvil;
- enlace/QR;
- OTP;
- rechazo;
- firma;
- copia;
- revocación;
- contingencia;
- accesibilidad.

### Restore

- backup de DB y storage;
- entorno aislado;
- restore;
- verificación semántica y de hashes;
- descarga de muestra;
- destrucción segura del entorno de prueba.

## 3. Reglas de datos

- Solo empresas/pacientes ficticios.
- Nunca usar `.env.production`, secretos productivos ni VPS.
- Reloj controlable para expiración/DST.
- Storage temporal aislado.
- Tokens y OTP generados para prueba, nunca registrados en claro.
- Fixtures con país, sede y zona horaria explícitos.
- Casos A/B usan IDs reales distintos y relaciones cruzadas maliciosas.

## 4. Gates por fase

| Fase | Gate mínimo |
| --- | --- |
| C019A.1 | versiones inmutables, variables seguras, tenant/roles, publicación |
| C019A.2 | estados, relaciones clínicas, sede/zona, auditoría, platform admin |
| C019A.3 | token opaco, OTP, rate limit, replay, anti-enumeración, abandono |
| C019A.4 | sellado atómico, PDF/hash/storage, firma no reutilizable, copia |
| C019A.5 | representante/asentimiento, rechazo, revocación, anulación, papel |
| C019A.6 | suite completa, concurrencia, restore, DST, Colombia/Chile, piloto |

## 5. Criterio de salida C019A.6

- cero rutas privadas sin caracterizar;
- cero pruebas P0 pendientes;
- cero hallazgos de cross-tenant;
- cero secretos o contenido clínico completo en logs;
- restore de DB + storage verificado;
- hashes de muestra correctos;
- decisiones terminales atómicas;
- revisión jurídica y clínica documentada por país;
- evidencia manual en tablet, móvil y 1366×768;
- riesgos residuales aceptados por responsables humanos.
