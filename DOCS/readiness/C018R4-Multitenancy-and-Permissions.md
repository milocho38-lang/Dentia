# C018R.4 — CERRADO LOCAL — Aislamiento multiempresa, roles y permisos

Fecha de registro: 2026-07-29.

Estado: **CERRADO LOCALMENTE PARA PILOTO CONTROLADO**.

Nota: el workflow CI quedó versionado y validado por comandos locales equivalentes. La ejecución remota real ocurrirá al abrir PR/push; no se ejecutó push ni CI remoto porque este ticket prohíbe push.

## Veredicto

La brecha P0-3 detectada en C018R.1 queda cerrada técnicamente para piloto controlado:

- existe suite DB-backed real;
- usa PostgreSQL aislado, no SQLite;
- crea Empresa A/B ficticias;
- usa tokens reales y dependencias reales;
- aplica Alembic desde cero;
- ejecuta ataques IDOR y cross-tenant;
- valida roles, sedes, plataforma, finanzas, presupuestos, usuarios, sedes, branding, reportes y descargas;
- mantiene guardrails anti-producción.

## Infraestructura

Archivos principales:

```text
docker-compose.test.yml
backend/requirements-test.txt
backend/scripts/security_characterization_tests.py
backend/scripts/route_security_metrics.py
backend/tests/route_security_registry.py
backend/tests/security_guard.py
backend/tests/conftest.py
backend/tests/factories/world.py
scripts/local/test_dentia_security.sh
.github/workflows/security-tests.yml
```

## Versiones reales

| Paquete | Versión |
| --- | --- |
| FastAPI | `0.115.6` |
| Starlette | `0.41.3` |
| HTTPX | `0.27.2` |
| Pytest | `8.3.4` |

## Registro maestro de rutas

El registro ejecutable está en:

```text
backend/tests/route_security_registry.py
```

Métricas actuales:

| Métrica | Valor |
| --- | ---: |
| Rutas totales | 187 |
| Rutas críticas | 86 |
| DB-backed | 166 |
| Characterized | 18 |
| Not applicable | 3 |
| Pending | 0 |
| Descargas activas | 5 |
| Descargas DB-backed | 5 |
| Mutaciones críticas | 50 |
| Mutaciones críticas DB-backed | 50 |

El registro falla si:

- aparece una ruta privada no registrada/clasificada;
- una ruta crítica queda pendiente;
- una descarga no tiene DB-backed;
- una mutación crítica no tiene contrato DB-backed;
- una ruta `NOT_APPLICABLE` no tiene justificación.

## Cobertura DB-backed

Pruebas actuales:

```text
45 passed
```

Familias cubiertas:

- autenticación efectiva después de cambios de estado;
- usuarios inactivos;
- empresa inactiva;
- roles removidos después de emitir token;
- membresía/sede removida después de emitir token;
- plataforma sin acceso clínico tenant;
- pacientes;
- citas y relaciones cruzadas;
- sedes y alcance restringido;
- documentos clínicos;
- recetas;
- presupuestos;
- presupuesto PDF;
- pagos;
- comprobantes PDF;
- reversión de pagos;
- dashboard financiero;
- cartera/receivables;
- reportes;
- usuarios;
- asignación de roles;
- asignación de sedes;
- empresa;
- branding y assets;
- escalamiento vertical básico.

## Contratos reales observados

Dentia no fuerza uniformidad artificial de códigos HTTP. Se acepta como denegación segura:

- `400` para relaciones inválidas con mensaje genérico;
- `401` para sesión/usuario/empresa/membresía inválida;
- `403` para permiso insuficiente;
- `404` para recurso ajeno/no visible;
- `409` para integridad documental o conflicto de estado.

Regla obligatoria:

- nunca `200` en acceso ajeno;
- nunca datos parciales del tenant B;
- nunca rutas físicas;
- nunca hashes ajenos;
- nunca escrituras parciales.

## Descargas cubiertas

| Descarga | DB-backed |
| --- | --- |
| Receta PDF | Sí |
| Documento clínico PDF | Sí |
| Presupuesto PDF | Sí |
| Comprobante de pago PDF | Sí |
| Branding asset | Sí |

## Mutaciones críticas cubiertas

| Familia | Casos |
| --- | --- |
| Presupuestos | creación cruzada, actualización cruzada, submit, approve, reject, duplicate-version, PDF B, atomicidad |
| Pagos | creación autorizada, tratamiento B, sede B, reversión B, recibo B, rol insuficiente |
| Usuarios | lectura A/B, asignación de roles, usuario B, sede B, autoescalamiento insuficiente |
| Sedes | creación A, lectura B, edición B, atomicidad |
| Empresa/branding | lectura/update A, rol insuficiente, upload asset, no path leak |
| Plataforma | detalle empresa, roles tenant permitidos, usuario B, `PLATFORM_ADMIN` excluido |
| Reportes | tenant scoped, filtro con sede B, rol financiero insuficiente, plataforma denegada |

## Guardrails anti-producción

La suite rechaza:

- `APP_ENV` distinto de `test`;
- ausencia de `DENTIA_TEST_DATABASE_CONFIRMATION`;
- base sin `test`;
- base llamada `dentia`;
- host no local;
- dominios productivos;
- nombres Compose productivos;
- `DATABASE_URL` con `prod`, `production`, `dentiapro.com` u `/opt/apps/dentia`.

## Comandos

```bash
./scripts/local/test_dentia_security.sh --quick
./scripts/local/test_dentia_security.sh --db
./scripts/local/test_dentia_security.sh --coverage
./scripts/local/test_dentia_security.sh --full
```

## Riesgos restantes

No quedan P0/P1 abiertos para la compuerta C018R.4.

## Relación con C018R.2

C018R.2 no reduce la cobertura C018R.4. Agrega hardening operativo alrededor de:

- validación de secretos productivos sin imprimir valores;
- orden seguro de migración en deploy;
- scripts locales con PID validado;
- fechas clínicas por zona horaria;
- anulación visible de recetas/documentos.

La suite C018R.4 debe seguir ejecutándose antes de autorizar piloto o despliegue.

Comando complementario agregado en C018R.2:

```bash
./scripts/local/test_dentia_security.sh --hardening
```

Riesgos P2/P3:

- warnings de deprecación FastAPI/Starlette bajo Python 3.14;
- ampliar cobertura E2E navegador en ticket posterior;
- extender pruebas de reportes/exportaciones cuando existan nuevos formatos CSV/PDF.
