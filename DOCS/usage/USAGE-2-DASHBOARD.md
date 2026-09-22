# USAGE-2 — Dashboard Platform Admin de uso y adopción

**Estado:** implementado para validación local

**Fecha:** 2026-09-21

**Dependencia:** USAGE-1 (`platform.usage.view`, catálogo `USAGE_1_V1`)

## 1. Objetivo

USAGE-2 presenta actividad funcional agregada de usuarios piloto para ayudar a entender qué partes de Dentia se están usando. El dashboard no mide desempeño clínico, productividad, calidad ni resultados; tampoco calcula score, ranking, porcentaje de adopción o semáforos.

La pantalla está disponible en:

```text
Platform Admin → Uso y adopción
```

La ruta privada `/administracion/uso-adopcion` y sus APIs exigen `platform.usage.view`. Ese permiso permanece asignado exclusivamente a `PLATFORM_ADMIN` por la migración `20260921_0041`.

## 2. Flujo y layout

El flujo exige contexto antes de consultar métricas:

1. Carga una lista mínima de empresas.
2. Al seleccionar una empresa, carga exclusivamente sus usuarios y sedes.
3. El usuario elige profesional/usuario, sede opcional y periodo.
4. Una sola llamada al endpoint agregado de USAGE-1 obtiene todas las cards, secciones y tendencia.

El layout usa:

- encabezado no evaluativo;
- bloque compacto de filtros;
- hasta seis cards de resumen;
- secciones modulares en dos columnas para pantallas amplias;
- una tendencia semanal de una sola serie seleccionable;
- actividad administrativa visualmente separada;
- estado explícito para métricas no atribuibles.

No existe drill-down hacia pacientes o contenido clínico.

## 3. Filtros

### Empresa

`GET /api/platform/usage/context` devuelve solamente identidad y estado de empresas. No incluye correo, teléfono, dirección ni datos fiscales.

### Usuario / odontólogo y sede

`GET /api/platform/usage/context?company_id={id}` devuelve solo usuarios y sedes de la empresa seleccionada. Por usuario incluye:

- nombre;
- estado activo/inactivo;
- nombres de roles;
- identidad odontológica mínima cuando existe;
- indicador booleano de actividad atribuible para ordenar opciones relevantes.

No devuelve correo, teléfono, documento profesional ni información de pacientes. Los odontólogos activos aparecen primero; luego los usuarios activos con actividad atribuible.

### Periodo

Periodos disponibles:

- últimos 7 días;
- últimos 30 días;
- desde inicio del piloto;
- personalizado.

“Desde inicio del piloto” exige una fecha inicial explícita. No se infiere onboarding porque no existe una fuente canónica. El frontend no solicita métricas mientras falten empresa, usuario o fechas requeridas.

## 4. Cards y módulos

Las seis cards superiores son:

1. última actividad en la zona horaria de la empresa;
2. días activos;
3. citas gestionadas;
4. pacientes únicos con actividad;
5. evoluciones firmadas;
6. tratamientos creados.

Las secciones muestran agregados de Agenda, Pacientes, Historia clínica, Tratamientos, Consentimientos y Ortodoncia. Ortodoncia diferencia entre ausencia de actividad y módulo no habilitado mediante `orthodontics_enabled`. Si existe actividad histórica, se conserva visible incluso cuando el entitlement ya no está activo.

Actividad administrativa contiene únicamente conteos de pagos registrados y reversos, sin montos y sin mezclarlos con actividad clínica.

## 5. Tendencia semanal

El gráfico permite escoger una serie:

- actividad en Agenda;
- pacientes únicos;
- evoluciones firmadas;
- tratamientos;
- consentimientos;
- Ortodoncia.

Solo se dibuja una serie a la vez para evitar un gráfico BI saturado. La visualización es semántica, navegable con el selector nativo y no provoca overflow horizontal global; en tamaños estrechos el scroll queda contenido dentro del gráfico.

## 6. Estados vacíos y métricas no disponibles

Cuando todos los agregados medibles son cero se muestra:

> No se registró actividad de Dentia para este usuario en el periodo seleccionado.

Los ceros de fuentes medibles siguen siendo ceros. Una métrica que Dentia aún no puede atribuir se muestra como **No disponible** junto con la razón técnica. USAGE-2 no convierte una ausencia de fuente en cero.

## 7. Privacidad, cache y RBAC

- Respuestas y UI no incluyen `patient_id`, nombres o documentos de pacientes, diagnósticos, texto clínico, contenido de consentimientos, montos, IP ni user-agent.
- El endpoint contextual evita reutilizar el detalle general de empresa, que contiene PII administrativa innecesaria.
- Backend responde `Cache-Control: no-store, max-age=0` y `Pragma: no-cache`.
- Frontend usa `cache: no-store` y no persiste filtros ni resultados en `localStorage`.
- `PermissionGate` protege la ruta y el backend vuelve a exigir `platform.usage.view`; una URL directa no elude RBAC.
- `ADMINISTRATOR`, `DENTIST_ADMIN`, `DENTIST` y `SECRETARY` reciben `403`.

## 8. Responsive y carga

El diseño prioriza desktop, laptop y tablet. Cards y módulos cambian a una columna o grillas menores sin overflow global. Mientras se consulta el agregado se muestran skeletons; cambios rápidos de filtro cancelan la solicitud anterior mediante `AbortController`.

La selección de empresa carga su contexto una vez. Cada combinación completa de filtros produce una única solicitud agregada, no una llamada por card.

## 9. Pruebas

- DB-backed: contexto mínimo, `no-store`, Platform RBAC, roles tenant denegados y ausencia de PII.
- DB-backed USAGE-1: atribución de actor, aislamiento tenant, periodos, agregados y límites de consultas.
- Frontend: navegación, `PermissionGate`, selectores, periodos rápidos/personalizados, loading, vacío, unsupported, módulos, tendencia, privacidad y helpers de actividad.
- Fixture local sintético: “Odontólogo Piloto”, representado solo por agregados de 30 días (18 citas creadas, 14 completadas, 12 pacientes únicos, 9 evoluciones firmadas, 3 tratamientos, 4 consentimientos y 2 casos ORT).

El fixture vive únicamente bajo `frontend/scripts/fixtures`; no participa en el bundle ni sustituye datos reales del endpoint.
