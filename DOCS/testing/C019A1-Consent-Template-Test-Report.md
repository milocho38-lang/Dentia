# C019A.1 — Reporte de pruebas del motor de plantillas

## Cobertura implementada

Las pruebas DB-backed usan PostgreSQL 17 aislado y cubren:

- creación por empresa y código único tenant;
- mismo código permitido entre empresas;
- ciclo borrador, preview, publicación, reemplazo y retiro;
- SHA-256 y snapshot de variables;
- inmutabilidad publicada y control optimista;
- IDOR A/B;
- sede y procedimiento cross-tenant;
- `DENTIST_ADMIN`, `DENTIST`, `SECRETARY` y `PLATFORM_ADMIN`;
- HTML/XSS, enlaces peligrosos, expresiones y variables desconocidas;
- anulación motivada;
- aplicabilidad publicada tenant;
- auditoría sin contenido completo.

La caracterización frontend comprueba filtros, inserción de variables, permisos por estado, acciones de ciclo de vida, doble submit y ausencia de UI de paciente, OTP, QR, firma o portal.

## Resultados

Resultados reales de la ejecución final:

- 49 pruebas aprobadas;
- 0 fallidas;
- migración desde base vacía hasta `20260801_0023` aprobada.
- `test_dentia_security.sh --full`: aprobado;
- 204 rutas, 101 críticas, 183 DB-backed y 0 pendientes;
- `pilot-hardening-tests OK` y 14/14 pruebas de fechas;
- scripts frontend clínico-comerciales, orientación, Dental Inspector y C019A.1: aprobados;
- frontend lint y build: aprobados;
- compileall y `pip check`: aprobados;
- Alembic `0022 → 0023 → 0022 → 0023`: aprobado;
- Alembic head `20260801_0023` y `check` sin operaciones nuevas;
- `git diff --check`: aprobado.

## Hallazgos durante implementación

1. El conflicto de código único ocurría durante el primer `flush`; se amplió el manejo transaccional para devolver `409`.
2. El índice parcial de publicación es inmediato; se fuerza el `flush` de `PUBLISHED → SUPERSEDED` antes de publicar la nueva versión en la misma transacción.

Ambos hallazgos quedaron cubiertos por prueba.

## Riesgos residuales

- No se ha realizado todavía validación jurídica del contenido de ninguna empresa.
- La especialidad no tiene catálogo institucional; C019A.2 deberá decidir si se crea uno antes de automatizar selección.
- Las pruebas frontend son helpers ejecutables y caracterización estructural, no interacción DOM, porque el repositorio no posee Vitest/Jest/Playwright.
- Las advertencias deprecadas de FastAPI/Starlette bajo Python 3.14 son preexistentes y no alteran el resultado.

## Severidad al cierre

- P0: ninguno.
- P1: ninguno.
- P2: validación jurídica pendiente, catálogo formal de especialidades pendiente y ausencia preexistente de pruebas DOM/E2E en frontend.
