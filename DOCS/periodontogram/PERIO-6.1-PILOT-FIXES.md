# PERIO-6.1 — Correcciones posteriores al piloto clínico

## Objetivo

Este ajuste incorpora exclusivamente el feedback del primer piloto clínico del Periodontograma: habilitar la captura de supuración en implantes, simplificar hallazgos binarios y mejorar el espacio de trabajo sin alterar el lifecycle, los permisos ni los históricos firmados.

## Decisiones clínicas

### Supuración

- Continúa limitada a sitios de piezas con estado `IMPLANT`.
- En implantes se captura con un control binario: marcado significa presente y no marcado significa ausente.
- En dientes naturales y piezas ausentes permanece deshabilitada.
- No se amplía su uso a dientes naturales.

### Sangrado al sondaje, placa y furcación

Para versiones nuevas bajo `PERIODONTAL_EXAM_V3`:

- marcado equivale a `true`;
- no marcado equivale a `false`;
- la interfaz no presenta un tercer estado visible;
- furcación M/D conserva las restricciones de diente natural, presente y molar elegible.

Los campos de base de datos permanecen nullable para poder leer versiones históricas. No se reescriben filas ni snapshots anteriores.

### Indicadores BOP y placa

En `PERIODONTAL_EXAM_V3`, todos los sitios de piezas no ausentes forman el denominador:

```text
BOP % = sitios elegibles con sangrado / sitios elegibles
Placa % = sitios elegibles con placa / sitios elegibles
```

Un hallazgo no marcado se computa como negativo. La cobertura periodontal continúa siendo independiente y se calcula con sitios que tienen tanto profundidad de sondaje como margen gingival.

Las versiones anteriores conservan su snapshot, hash, índices congelados y contrato original. La UI usa esos agregados congelados al consultar una versión histórica.

## Cambios de experiencia de uso

- El Periodontograma ofrece `Expandir periodontograma` para colapsar temporalmente el menú lateral.
- `Mostrar menú` restaura la navegación global.
- Al salir del módulo se restaura el comportamiento normal del layout.
- El workspace del paciente elimina su límite de ancho únicamente en la pestaña Periodontograma.
- El panel de pieza seleccionada permanece sticky bajo el encabezado.
- Seleccionar una pieza maxilar o mandibular actualiza el panel sin desplazar el viewport hacia arriba.
- En tablet y anchos menores se conserva el scroll horizontal local de la matriz; la navegación no depende de hover.

## Compatibilidad e integridad

- No hay migración.
- No cambian RBAC, entitlement, pilot gate ni aislamiento tenant/sede.
- No se reescriben versiones finalizadas.
- Los hashes históricos no cambian.
- Enter, Shift+Tab, Backspace, click directo, batch save, dirty state y gráfico dinámico permanecen vigentes.

## Pruebas

La cobertura incluye:

- supuración seleccionable y persistente en implante;
- rechazo de supuración en diente natural y pieza ausente;
- controles binarios BOP, placa y furcación sin estado visual intermedio;
- denominadores sobre sitios elegibles;
- snapshot e historial inmutables entre V1 y correcciones posteriores;
- expansión/restauración de sidebar;
- panel contextual sticky y selección mandibular dinámica;
- contratos responsive de 1280, 1440, 1920 y scroll local para tablet;
- regresión de captura rápida, versiones históricas y gráfico periodontal.

## Decisiones pendientes

No quedan decisiones clínicas abiertas dentro de PERIO-6.1. Cualquier ampliación de supuración a dientes naturales, comparación entre versiones, PDF, voz o diagnóstico automático requiere un alcance posterior independiente.
