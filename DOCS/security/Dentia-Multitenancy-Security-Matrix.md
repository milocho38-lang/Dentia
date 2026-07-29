# Dentia — Matriz de seguridad multiempresa, roles y permisos

Fecha: 2026-07-29.

Esta matriz resume las reglas de aislamiento que protegen a Dentia antes del piloto real. La fuente de verdad técnica sigue siendo el backend; este documento organiza expectativas y cobertura automática.

## Principio principal

La empresa activa nunca debe venir de datos confiados al frontend. El backend deriva el alcance desde sesión/token y valida cada relación antes de leer, crear, modificar, anular, descargar o agregar datos.

## Contrato de denegación segura

Se aceptan estos códigos según el contrato real del endpoint:

- `400`: relación inválida o filtro no autorizado con mensaje genérico;
- `401`: sesión, usuario, empresa o membresía inactiva;
- `403`: permiso insuficiente;
- `404`: recurso no visible o ajeno;
- `409`: conflicto/integridad.

Nunca debe ocurrir:

- `200` en acceso ajeno;
- contenido parcial del tenant B;
- rutas físicas;
- hashes ajenos;
- nombres, números, pacientes, importes o agregados del tenant B;
- escrituras parciales.

## Cobertura actual por familia

| Familia | DB-backed | Contratos principales |
| --- | --- | --- |
| Pacientes | Sí | listado, detalle, actualización B denegada |
| Agenda/citas | Sí | relación paciente B/sede B denegada |
| Sedes | Sí | listado scoped, get/update B denegado |
| Usuarios/roles | Sí | usuario B denegado, roles/sedes B denegados, autoescalamiento bloqueado |
| Plataforma | Sí | empresas permitidas, clínica/finanzas tenant denegadas, `PLATFORM_ADMIN` no asignable desde tenant |
| Branding | Sí | lectura/update A, upload asset A, rol insuficiente, sin path leak |
| Presupuestos | Sí | listado/detalle A, UUID B, mutaciones B, PDF B, atomicidad |
| Pagos/comprobantes | Sí | listado/detalle A, UUID B, creación cruzada, reversión B, recibo B |
| Finanzas/cartera | Sí | dashboard, income, receivables, breakdowns scoped |
| Reportes | Sí | filtros con sede B, finanzas por rol, plataforma denegada |
| Recetas | Sí | PDF A, PDF B, hash mismatch |
| Documentos clínicos | Sí | PDF A, PDF B, path traversal |
| Seguimientos | Characterized | grafo de auth/permisos; no crítico financiero/admin en FIX2 |
| Catálogo de procedimientos | Characterized | grafo de auth/permisos; ampliar DB-backed si se vuelve compuerta crítica |

## Métricas de ruta

| Métrica | Valor |
| --- | ---: |
| Rutas totales | 187 |
| Críticas | 86 |
| DB-backed | 166 |
| Characterized | 18 |
| Not applicable | 3 |
| Pending | 0 |
| Descargas | 5/5 DB-backed |
| Mutaciones críticas | 50/50 DB-backed |

## Actores cubiertos

| Actor | Cobertura |
| --- | --- |
| `PLATFORM_ADMIN` | Gestión plataforma permitida; clínica/finanzas tenant denegadas. |
| Administrador empresa | Gestión tenant A permitida; B denegado. |
| Odontólogo administrador | Acceso clínico/tenant según permisos. |
| Odontólogo | Sin finanzas globales cuando no tiene permiso. |
| Secretaria | Operación limitada; clínica sensible y administración crítica denegadas. |
| Usuario restringido a sede | Solo sede A1. |
| Usuario inactivo | Token rechazado. |
| Empresa/membresía inactiva | Token rechazado. |

## Descargas activas

| Endpoint | Cobertura |
| --- | --- |
| `GET /api/clinical-documents/{document_id}/pdf` | autorizado, B denegado, path traversal |
| `GET /api/prescriptions/{prescription_id}/pdf` | autorizado, B denegado, hash mismatch |
| `GET /api/budgets/{budget_id}/pdf` | autorizado, B denegado |
| `GET /api/payments/{payment_id}/receipt` | autorizado, B denegado, rol insuficiente |
| `GET /api/company/branding/{kind}` | autorizado después de upload, sin path leak |

## Regla para rutas nuevas

Toda nueva ruta privada debe quedar clasificada en `backend/tests/route_security_registry.py`. Si es crítica, debe contar con DB-backed. Si es descarga, debe contar con DB-backed siempre.
