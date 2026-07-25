# C017F.1 — Evolución clínica simplificada

## Decisión funcional

La evolución clínica narrativa pasa a ser el campo principal para crear y editar evoluciones nuevas en Dentia.

El odontólogo puede registrar la atención escribiendo en una sola caja:

```text
Evolución clínica
```

No es obligatorio distribuir la narración entre motivo, subjetivo, objetivo, evaluación, procedimiento, indicaciones y recomendaciones.

## Modelo de datos

Se agrega el campo nullable:

```text
evoluciones_clinicas.texto_evolucion
```

Nombre de aplicación:

```text
evolution_text
```

Los campos estructurados históricos permanecen intactos y no se eliminan.

## Compatibilidad histórica

Las evoluciones antiguas sin `evolution_text` siguen mostrándose con sus campos históricos.

No se migran automáticamente.

No se concatenan destructivamente.

No se recalculan hashes históricos.

## Formulario

El formulario principal muestra:

- fecha y hora clínica;
- sede;
- odontólogo;
- tratamiento vinculado;
- campo principal `Evolución clínica`;
- procedimientos vinculados;
- información adicional opcional colapsada;
- próximo control opcional colapsado.

## Información adicional

Los campos estructurados permanecen disponibles como información adicional opcional:

- motivo;
- subjetivo;
- objetivo / examen;
- evaluación;
- procedimiento realizado;
- anestesia;
- materiales;
- medicamentos administrados;
- hallazgos;
- complicaciones;
- indicaciones;
- recomendaciones;
- observaciones.

## Firma e integridad

Para evoluciones nuevas, el hash incluye `evolution_text` además de los campos que ya participaban en la carga canónica.

Las evoluciones históricas firmadas no se modifican ni se recalculan.

## Procedimientos y odontograma

La simplificación no cambia:

- procedimientos vinculados;
- eventos odontográficos en borrador;
- confirmación odontográfica al firmar;
- resolución de diagnóstico cuando aplique;
- auditoría;
- inmutabilidad posterior a la firma.

## Próximo control

El próximo control sigue siendo estructurado y opcional.

Solo se diligencia cuando la evolución requiere seguimiento.

## Plan de pruebas

- crear evolución con una sola narrativa;
- guardar borrador;
- reabrir y continuar editando;
- firmar;
- verificar hash;
- verificar que evoluciones antiguas sin narrativa muestran campos históricos;
- verificar que campos vacíos no aparecen en vista firmada;
- verificar procedimientos vinculados;
- verificar cambios odontográficos pendientes y confirmación al firmar;
- verificar próximo control opcional;
- verificar permisos y multiempresa.
