# Segundo lote odontograma: resinas (borrador local)

Estado: **8 candidatos preparados y no publicados**. La conexión técnica a onboarding y CLI existe localmente, pero queda deshabilitada por defecto con `PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEED_ENABLED=false`.

## Evidencia de fuente

El Excel autorizado `precios clinicas .xlsx` tiene SHA-256 `1d77bd1c0723fdfaf05e57f78dd4aed15f04eabc95797a2f7589b1446c8de5df`. El 2026-11-08 se materializó localmente desde Library con su identidad `libfile_2ad6417cc23c8191bf73bc32a0be530c`; el archivo local es legible, mide 40.641 bytes y su SHA-256 coincide exactamente. Una revisión independiente había entregado antes las celdas literales C/D/E/F de las filas físicas 290, 291 y 329–334 de `prestaciones `; la lectura local ahora permite verificar directamente esa fuente.

En las ocho filas: nota `por caries o fractura`, alcance `por diente y cara` y precio numérico CLP. No hay fórmulas ni celdas combinadas en esas filas. Los nombres se conservan literalmente en `procedure_catalog_odontogram_resin_8.json`.

## Decisión clínica conservadora

Las ocho filas son restauraciones fotocuradas o composite. El modelo actual ofrece una equivalencia exacta y ya utilizada: seleccionar caries o fractura, mostrar el hallazgo rojo confirmado, registrar `DONE_RESIN` como resultado azul, resolver solo el diagnóstico vinculado y confirmar el resultado al firmar. No se cambia la semántica global ni se usan eventos `PLAN_*`.

Los demás procedimientos con notas clínicas permanecen excluidos. No se inventan mapeos para exodoncia, corona, implante, perno ni combinaciones.

## Precios y alcance

| Fila | Nombre literal | CLP | COP fijo |
|---:|---|---:|---:|
| 290 | Restauración fotocurado pieza temporal: Compuesta Anterior o posterior | 66.000 | 217.000 |
| 291 | Restauración fotocurado pieza temporal: Simple Anterior o posterior | 53.000 | 174.000 |
| 329 | Restauración Cervical (Clase V) | 35.000 | 115.000 |
| 330 | Restauración composite Compleja Posterior (Clase II - tres caras) | 50.000 | 165.000 |
| 331 | Restauración composite Compuesta Anterior (Clase IV) | 50.000 | 165.000 |
| 332 | Restauración composite Compuesta Posterior (Clase II - dos caras) | 45.000 | 148.000 |
| 333 | Restauración composite Simple Anterior (Clase III o V) | 40.000 | 132.000 |
| 334 | Restauración composite Simple Posterior (Clase I - una cara) | 35.000 | 115.000 |

Todos usan `TOOTH_SURFACE`. Los COP son valores fijos derivados con la misma base aprobada del lote inicial; no hay conversión en ejecución.

## Seguridad

- Inserción `ON CONFLICT DO NOTHING` por empresa y nombre normalizado.
- Una colisión no modifica precio, alcance, diagnósticos ni configuración existente.
- Solo las filas insertadas reciben relaciones caries/fractura.
- País ausente o distinto de Chile/Colombia falla antes de insertar.
- La finalización verifica empresa, paciente, vínculo, estado activo, pieza, zona y caras. En procedimientos catalogados también verifica diagnóstico permitido y resultado configurado. La firma lo revalida y falla con rollback ante inconsistencias.
- Los borradores nuevos guardan explícitamente si su configuración es `CATALOG` o `MANUAL`. Los catalogados guardan además el ID de catálogo usado, por lo que una desvinculación posterior falla cerrada.
- Los procedimientos manuales con un único vínculo de diagnóstico conservan el flujo anterior, tanto con `KEEP_ACTIVE` como con `RESOLVE_ON_SIGN`; una asociación manual compartida o inconsistente falla cerrada.
- Los borradores catalogados anteriores a esta protección, sin snapshot, pueden firmarse solo si todavía conservan un catálogo activo cuya configuración completa coincide con diagnóstico, alcance y resultado.
- Un borrador anterior sin snapshot y sin catálogo es ambiguo: no se puede demostrar si siempre fue manual o si perdió su vínculo. Se rechaza sin modificar eventos. Su recuperación requiere revisión clínica y técnica individual del historial/auditoría, y luego recrear de forma explícita la realización; no se corrigen datos automáticamente ni en lote.
- `KEEP_ACTIVE` confirma el resultado realizado al firmar y conserva el diagnóstico de origen confirmado.
- Un procedimiento de catálogo sin resultado predeterminado falla antes de crear el borrador odontográfico.
- La interfaz limita y preselecciona el único resultado configurado; para procedimientos manuales conserva la selección libre previa.
- El dry-run devuelve cantidad a insertar y colisiones con ID, nombre, valor y fila fuente, sin escribir ni agregar auditoría.

## Activación futura

La publicación necesitaría una nueva autorización. El despliegue inicial debe conservar `PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEED_ENABLED=false`. Solo una activación posterior y explícita hace que nuevas clínicas de Chile o Colombia reciban el lote; país ausente/no soportado conserva el alta sin inferir moneda ni insertar este lote.

Para una clínica existente, la CLI es dry-run por defecto:

```bash
cd backend
python -m app.cli.seed_odontogram_resin_catalog \
  --company-id <UUID_EMPRESA> \
  --actor-id <UUID_USUARIO_ACTIVO_DE_LA_MISMA_EMPRESA>
```

La salida enumera únicamente colisiones del catálogo, sin pacientes. No escribe filas ni auditoría. **La escritura mediante CLI está deshabilitada:** `--actor-id` es un dato aportado por quien invoca el proceso y no autentica su identidad real, aunque el UUID corresponda a un administrador con `procedure_catalog.manage`. Por ello `--apply` siempre termina sin escribir ni auditar. Habilitar backfill exigirá otro mecanismo de ejecución que obtenga una identidad autenticada y autorización vigente, y requerirá revisión y autorización separadas. La idempotencia y preservación de colisiones del servicio se mantienen probadas para onboarding transaccional, pero no se presentan como una capacidad CLI disponible.

### Backfill autenticado preparado localmente

Para clínicas existentes se preparó una vía administrativa tenant-scoped que no acepta `company_id` ni `actor_id`. Tiene una compuerta independiente, apagada por defecto: `PROCEDURE_CATALOG_ODONTOGRAM_RESIN_BACKFILL_ENABLED=false`. Con la compuerta apagada, preview y apply responden como no disponibles sin escribir ni auditar:

- `GET /api/procedure-catalog/odontogram-resin-batch/preview`
- `POST /api/procedure-catalog/odontogram-resin-batch/apply`

Ambas rutas obtienen empresa, usuario y sesión exclusivamente del token autenticado y exigen el permiso vigente `procedure_catalog.manage`. El apply exige la versión y el SHA-256 inmutable devueltos por preview, además de la confirmación literal `APPLY_ODONTOGRAM_RESIN_BATCH`; cualquier diferencia obliga a repetir el preview. La empresa se bloquea transaccionalmente y, después del lock, se bloquean y revalidan las asignaciones de rol, roles, concesiones y permisos antes de insertar. Así, una revocación concurrente se serializa con la aplicación y todo reintento posterior queda rechazado. La auditoría conserva empresa, usuario, sesión autenticada, IP, agente, versión, digest, moneda, insertados, colisiones y vínculos.

Las tres compuertas son independientes y `false` por defecto: onboarding (`PROCEDURE_CATALOG_ODONTOGRAM_RESIN_SEED_ENABLED`), backfill API (`PROCEDURE_CATALOG_ODONTOGRAM_RESIN_BACKFILL_ENABLED`) y CLI, cuyo `--apply` permanece incondicionalmente deshabilitado.

Esta vía permanece solo local y no implica habilitación ni autorización productiva. Conserva nombres/precios/configuración de cualquier colisión y nunca recibe identificadores de pacientes.

## Validación integrada aislada

El 2026-11-03 se ejecutó una validación tipo staging sobre PostgreSQL 17 efímero, migrado desde vacío hasta `20261102_0052`, con datos exclusivamente sintéticos:

1. Ambos flags odontográficos explícitamente `false`: health respondió correctamente; preview quedó cerrado sin escritura ni auditoría.
2. Se habilitó solo el gate API dentro del proceso de prueba: clínica Chile mostró CLP, 7 inserciones y una colisión preservada; clínica Colombia mostró COP y 8 inserciones.
3. Apply autenticado y reintento: Chile insertó 7 y luego 0; Colombia insertó 8. Los valores de la colisión no cambiaron y cada intento produjo su auditoría autenticada.
4. Se repitieron onboarding CL/CO, rollback ante manifiesto inválido, revocación concurrente y reintentos concurrentes.
5. Resultado focal integrado: 9 pruebas aprobadas; focal total: 52; suite backend completa: 493. Frontend lint, TypeScript y build webpack (33 páginas) aprobaron.

El intento visual con CUA no pudo continuar: el Mac seguía bloqueado y el desbloqueo automático falló. No se usaron producción ni datos reales.

La búsqueda de solo lectura en configuración, scripts y documentación del repositorio no encontró un ambiente staging persistente identificado y autorizado para esta tarea. Las únicas referencias aplicables eran el entorno efímero descrito arriba y menciones genéricas de staging. No se intentó conectar, desplegar ni modificar ningún ambiente persistente.

La prueba integrada usa `monkeypatch` para fijar y restaurar automáticamente ambos flags. Se ejecutó además un orden explícito —integración con gate habilitado, seguido de gate apagado y auditoría— y las tres pruebas aprobaron, descartando dependencia de orden. La auditoría comprobó usuario, sesión, IP y agente HTTP no vacíos.

## Inventario productivo de compatibilidad legacy

El 2026-11-03 se ejecutó una única consulta agregada y de solo lectura en PostgreSQL productivo, agrupando exclusivamente por acción de diagnóstico y presencia de catálogo. No se seleccionaron IDs de empresa, paciente, tratamiento, procedimiento ni evento. Resultado: **0** borradores `PROCEDURE_PERFORMED` en estado `DRAFT` con `source_odontogram_event_id` informado. Por tanto, en ese instante no había borradores legacy potencialmente bloqueados por la nueva revalidación. Este conteo es temporal y debe repetirse antes de una publicación futura si ha transcurrido tiempo.

## Conciliación complementaria de las otras 76 filas

Esta conciliación **no es V2 y no sustituye V2**. Una búsqueda local amplia y dos búsquedas acotadas por título en Library no localizaron el manifiesto V2. `EXACT_MANIFEST_RECONCILIATION.md` corresponde al lote inicial de 173 y tampoco es V2. El archivo complementario queda deliberadamente desconectado de runtime:

`backend/app/library_data/procedure_catalog_odontogram_additional_76_review.json`

El Excel local y `source-reconciliation-76.json` coincidieron en las 304 celdas C–F de las 76 filas: nombre, nota, alcance y precio. No hubo diferencias, fórmulas ni celdas combinadas que intersectaran esas filas. La revisión externa del paquete registra además 608 celdas cotejadas sin diferencias; se conserva como evidencia atribuida y no se presenta como una segunda ejecución local.

### Resultado conservador actualizado

- **6 restauraciones preparadas en borrador desconectado:** filas 277, 278, 287, 288, 289 y 316. Usan diagnóstico explícito caries/fractura y resultado `DONE_RESIN`; 288–289 no se restringen a fractura por su nombre.
- **6 reglas `NO_CHANGE` preparadas:** remineralización 279 y paquetes 222–226. Cada paquete conserva un único nombre y precio; no crea sitios ni multiplica el valor por el número de implantes.
- **8 retratamientos preparados en borrador desconectado:** filas 206–213. Exigen una endodoncia previa defectuosa ya registrada, representada como zigzag azul; nunca fabrican el antecedente. La firma válida agrega `DONE_ENDO` y compensa únicamente ese marcador cuando se usa `RESOLVE_ON_SIGN`.
- **Pulpotomía 197 y corona sobre implante 519 tienen regla clínica resuelta, pero aún requieren implementación técnica.** En 519 el profesional selecciona el diente; no se fabrica ni reemplaza el implante existente.
- **La única correspondencia específica aún no resuelta es la fila 328, Reparación de Carilla.** Se mantiene sin resultado automático porque la fuente no determina inequívocamente restauración versus carilla realizada.
- **Las demás familias tienen reglas clínicas conciliadas, pero su soporte técnico fiel todavía no está implementado.** Permanecen desconectadas y no ejecutables.

### Brechas comprobadas del motor actual

| Familia | Capacidad existente | Razón de bloqueo |
|---|---|---|
| Exodoncia | `PLAN_EXTRACTION` y `DONE_EXTRACTION` | El resultado actual se renderiza como ausencia, no como X azul distinta de ausencia previa. |
| Corona / incrustación | `PLAN_CROWN` y `DONE_CROWN` | Los colores y el símbolo actuales no cumplen círculo rojo pendiente y azul realizado dentro del flujo protegido. |
| Endodoncia / pulpectomía | `PLAN_ENDO` y `DONE_ENDO` | Falta verificar línea roja/azul separada de diagnóstico y restauración; pulpotomía exige círculo oclusal sin raíz. |
| Retratamiento | Borrador local con `FIND_ENDO_DEFECTIVE` y `DONE_ENDO` | Implementado localmente: zigzag azul previo existente, transición firmada a línea normal, revalidación de vínculo y compensación exacta. Aún no está conectado a runtime de carga. |
| Carilla | `FIND_VENEER` | Representa carilla preexistente, no carilla pendiente roja y realizada azul; diseño de sonrisa exige seis objetivos sin multiplicar el precio. |
| Implante / corona sobre implante | Códigos plan/realizado de implante y corona | El flujo catalogado admite un resultado predeterminado; debe conservarse independientemente el implante existente. |
| Perno | Sin código propio | No puede sustituirse por implante. |
| Diastema | Resultado de restauración disponible | No existe un diagnóstico/origen aprobado; no se inventa caries para abrir el flujo. |

Los precios COP del manifiesto complementario son valores fijos calculados una sola vez con la misma base aprobada del lote preparado (`1 CLP = 3,291243 COP`, observada 2026-11-03 03:33 UTC, redondeo HALF_UP al millar). No hay conversión en ejecución ni actualización de precios existentes.

### Estado de activación

El manifiesto complementario declara `connected_to_runtime=false`, `onboarding_enabled=false`, `backfill_api_enabled=false`, `cli_apply_enabled=false` y `production_authorized=false`. El borrador ejecutable de 20 filas tampoco está importado por bootstrap, endpoint o CLI. Las pruebas fijan hashes, nombres literales, precios fijos, colisiones e idempotencia; esto no autoriza ni activa carga alguna.
