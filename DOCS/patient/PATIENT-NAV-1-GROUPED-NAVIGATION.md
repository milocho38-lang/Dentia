# PATIENT-NAV-1 — Navegación agrupada del paciente

## Problema

El workspace del paciente había acumulado once accesos en una única fila. En resoluciones comunes la navegación requería scroll horizontal, ocultaba módulos y no expresaba la relación entre funciones clínicas, operativas y documentales.

## Jerarquía

La navegación se organiza en dos niveles:

| Grupo principal | Destinos |
| --- | --- |
| Resumen | Resumen del paciente |
| Clínica | Historia clínica, Odontograma, Periodontograma, Ortodoncia |
| Tratamientos | Tratamientos |
| Gestión | Agenda, Finanzas |
| Documentos | Documentos, Consentimientos, Archivos |

Resumen y Tratamientos son accesos directos y no generan una segunda fila vacía. Los demás grupos muestran una fila secundaria compacta con sus destinos visibles.

## Fuente única de verdad

`frontend/lib/patientNavigation.ts` define:

- grupos, orden y etiquetas;
- tab asociado a cada destino;
- permisos existentes;
- módulos sujetos a visibilidad dinámica;
- resolución de grupo desde cualquier tab válido.

`PatientWorkspaceNavigation` se limita a representar la estructura resultante. `PatientDetail` conserva la carga de datos y los resolvers existentes.

## Permisos dinámicos

- Historia clínica, Odontograma, Tratamientos, Agenda, Finanzas y Consentimientos reutilizan sus permisos actuales.
- Periodontograma requiere `periodontogram.view` y respuesta positiva del resolver clínico general, que valida usuario, empresa, identidad odontológica y sede activas.
- Ortodoncia solo aparece cuando el endpoint clínico existente devuelve un workspace accesible, que ya aplica entitlement, assignment, identidad odontológica, tenant y scope.
- Un grupo sin destinos visibles se omite por completo.

No se duplican resolvers ni se muestran módulos bloqueados como opciones inactivas.

## URL, deep links y navegación del navegador

Cada selección escribe el tab en `?tab=<destino>` mediante el router de Next.js. El tab activo siempre se reconstruye desde la URL:

- deep links conservan el grupo y subopción correspondientes;
- Back y Forward restauran el estado visual;
- refresh reconstruye ambos niveles;
- una URL sin tab o con un valor desconocido vuelve a Resumen.

Las URLs y nombres de tabs existentes se mantienen.

## Responsive y accesibilidad

- La fila principal usa controles compactos de al menos 44 px y cabe completa desde desktop/tablet estándar.
- La segunda fila usa controles de al menos 36 px.
- En viewports estrechos cada nivel tiene scroll horizontal local y `overscroll-x-contain`; no se introduce overflow global.
- Los controles son botones nativos, tienen foco visible, `aria-current`, `aria-controls` y nombres accesibles para ambos niveles.
- Los dos niveles tienen jerarquía visual diferente: fondo primario para el grupo y tratamiento ligero para la subopción.

## Pruebas

La suite `patient-grouped-navigation-tests.mjs` cubre:

- cinco grupos y orden aprobado;
- orden de subopciones clínicas, operativas y documentales;
- Tratamientos como acceso directo;
- visibilidad ORT/PERIO y filtrado por permisos;
- omisión de grupos vacíos;
- mapping de deep links a grupos;
- sincronización URL/Back/Forward/refresh por contrato;
- scroll local, alturas y semántica accesible.

Las suites frontend completas y las regresiones específicas de Periodontograma y Ortodoncia verifican que la agrupación no cambia el comportamiento de los módulos.
