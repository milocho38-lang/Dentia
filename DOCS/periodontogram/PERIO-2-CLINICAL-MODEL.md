# PERIO-2 — Modelo clínico periodontal, dientes y seis sitios

## Alcance

PERIO-2 incorpora captura periodontal estructurada sobre la foundation versionada de PERIO-1. El alcance se limita a dentición permanente, edición de borradores, derivaciones clínicas deterministas y congelación de snapshots. No incorpora gráfico periodontal final, diagnóstico, comparación longitudinal, PDF ni automatización clínica.

## Dentición y sitios

Cada nueva versión en borrador contiene los 32 dientes permanentes en orden FDI clínico:

`18–11, 21–28, 48–41, 31–38`.

Cada diente inicia como `PRESENT` y dispone de seis sitios, todos sin medir (`null`):

- `BUCCAL_DISTAL`
- `BUCCAL_MID`
- `BUCCAL_MESIAL`
- `LINGUAL_DISTAL`
- `LINGUAL_MID`
- `LINGUAL_MESIAL`

En dientes maxilares la UI presenta la cara lingual como palatina. No se aceptan piezas temporales ni códigos FDI fuera del catálogo permanente.

## Semántica clínica

- Estados: `PRESENT`, `ABSENT`, `IMPLANT`.
- Profundidad de sondaje (PS/PD): entero nullable en milímetros, con rango técnico `0–50`. `0` es una medición real y no significa “sin medir”.
- Margen gingival (MG/GM): entero con signo nullable, con rango técnico `-50–50`. Negativo es apical y positivo coronal.
- Nivel de inserción clínica (NIC/CAL): derivado como `PD - GM`; es `null` si falta una de las dos mediciones.
- Bolsa periodontal visual: derivada cuando `PD >= 4 mm`.
- Sangrado al sondaje y placa: booleanos nullable; `null` no entra en su denominador.
- Supuración: disponible únicamente para implantes en este alcance.
- Movilidad: grado nullable `0–3`, solo para dientes naturales presentes.
- Furcación mesial/distal: presencia nullable, solo para molares permanentes elegibles; PERIO-2 no introduce grados.
- Nota clínica breve por pieza: texto nullable versionado; su contenido no se copia a eventos de auditoría.

Un diente ausente queda excluido de cobertura e índices. Dientes naturales e implantes sí participan. Un sitio cuenta como evaluado para cobertura cuando tiene simultáneamente PD y GM. Se permite finalizar un examen parcial; el snapshot registra explícitamente que su cobertura está incompleta.

## Persistencia y edición

Los datos normalizados se almacenan en:

- `periodontal_teeth`, vinculada a una versión del examen;
- `periodontal_sites`, vinculada al diente y a la misma versión.

La edición se realiza mediante un único PATCH batch por guardado:

`PATCH /api/periodontograms/{exam_id}/draft`

El request exige `row_version`; una versión obsoleta responde `409`. No se hacen requests por celda. Los cambios de estado que implican descartar información clínica requieren `clear_clinical_data=true`; nunca se borran datos silenciosamente.

Los eventos de auditoría registran identificadores y cantidades de dientes/sitios modificados, no los valores clínicos.

## Snapshot e integridad

Al finalizar, `PERIODONTAL_EXAM_V2` congela un JSON determinista con:

- contexto del examen;
- contrato clínico;
- 32 dientes ordenados por FDI;
- seis sitios ordenados por código clínico;
- CAL y bolsa derivados;
- cobertura agregada;
- índices BOP y placa con sus numeradores y denominadores;
- versión de esquema.

El hash SHA-256 se calcula sobre la serialización canónica. Triggers de base de datos impiden insertar, actualizar o eliminar dientes y sitios de una versión `FINALIZED`.

## Correcciones

Una corrección crea una nueva versión `DRAFT` y clona los datos normalizados de la versión finalizada. La versión anterior, su snapshot y su hash permanecen inmutables. La nueva versión puede editarse y finalizarse con un hash independiente.

## API y permisos

PERIO-2 reutiliza la matriz clínica de PERIO-1:

- `periodontogram.view`
- `periodontogram.create`
- `periodontogram.update_draft`
- `periodontogram.finalize`
- `periodontogram.correct`

Solo `DENTIST` y `DENTIST_ADMIN`, con identidad odontológica activa, tenant y sede autorizados, reciben estos permisos. `ADMINISTRATOR`, `SECRETARY` y `PLATFORM_ADMIN` no obtienen acceso clínico por este módulo.

## Rendimiento

Un examen completo materializa 32 dientes y 192 sitios. La lectura clínica recupera dientes y sitios con dos consultas acotadas y los agrupa en memoria; no consulta una vez por pieza o sitio. El guardado agrupa los cambios del usuario en una sola transacción batch y no envía una petición por medición.

## Cobertura de pruebas

Las pruebas focales cubren FDI permanente, seis sitios, `null` frente a cero/falso, fórmula CAL, umbral visual de bolsa, BOP, placa, implantes, supuración, movilidad, furcación, notas por pieza, examen parcial, optimistic locking, corrección V2, hash e inmutabilidad a nivel de base de datos. La suite de seguridad conserva RBAC, tenant y sede.

## Pendientes PERIO-3

PERIO-3 podrá optimizar recorrido clínico, navegación por teclado, captura rápida, autosave controlado y ergonomía del workspace usando los códigos y el batch contract definidos aquí. No debe cambiar la semántica clínica ni reescribir snapshots finalizados.

## Fuera de alcance

PERIO-2 no modifica odontograma, Ortodoncia, RIPS, website, entitlement, seats ni RBAC. Tampoco interpreta automáticamente diagnósticos o decisiones terapéuticas.
