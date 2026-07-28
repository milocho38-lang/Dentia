# C017G.2 — Recetario odontológico

## Propósito

Permitir que el odontólogo cree recetas odontológicas ordinarias desde el expediente del paciente, con medicamentos estructurados y PDF institucional histórico.

El módulo cubre recetas ordinarias de práctica odontológica. No implementa medicamentos controlados, recetario oficial, firma electrónica avanzada, MIPRES, ROE, dispensación, inventario farmacéutico ni autorización de aseguradores.

## Ubicación funcional

```text
Paciente
  → Documentos
  → Recetas
```

Las recetas se muestran separadas de informes clínicos, presupuestos, comprobantes y archivos externos.

## Flujo aprobado

```text
Nueva receta
  → seleccionar sede y profesional
  → agregar medicamentos estructurados
  → revisar alertas clínicas
  → guardar borrador
  → previsualizar
  → confirmar revisión clínica
  → finalizar
  → descargar PDF almacenado
```

## Estados

- `DRAFT`: editable, sin consecutivo definitivo, sin validez para dispensación.
- `FINALIZED`: inmutable; genera consecutivo, snapshots, PDF y hash.
- `VOIDED`: conserva histórico y PDF; requiere motivo.

Una receta finalizada no se edita. Para corregirla se duplica como nuevo borrador.

## Ítems de medicamento

Cada receta contiene uno o varios medicamentos con campos estructurados:

- nombre genérico / principio activo;
- marca opcional;
- forma farmacéutica;
- concentración;
- dosis;
- vía;
- frecuencia;
- duración;
- cantidad total;
- unidad;
- indicaciones.

El nombre genérico es el campo principal. Dentia no recomienda marcas ni medicamentos.

## Alertas clínicas

Antes de finalizar se muestran alergias y medicamentos activos provenientes de Historia Clínica.

Reglas:

- Dentia no bloquea por inferencias automáticas en este MVP.
- Dentia no calcula dosis.
- Dentia no valida interacciones.
- El profesional debe confirmar que revisó alergias, medicamentos actuales y antecedentes relevantes.

## Profesional y firma

La receta requiere profesional activo, autorizado para la sede y con perfil odontológico.

Para finalizar se requiere:

- firma gráfica configurada;
- registro profesional configurado.

La firma gráfica no equivale a firma digital certificada.

## Consecutivo

El consecutivo es empresarial e independiente:

```text
RX-000001
RX-000002
```

Se asigna al finalizar y no se consume en borradores.

## Inmutabilidad

Al finalizar se congelan:

- empresa y sede;
- paciente;
- responsable legal cuando corresponda;
- profesional;
- medicamentos;
- indicaciones;
- alertas clínicas revisadas;
- PDF;
- SHA-256;
- hash de integridad.

Las descargas posteriores retornan el PDF almacenado, no un PDF regenerado desde datos vivos.

## Permisos

- `prescriptions.view`
- `prescriptions.create`
- `prescriptions.edit_draft`
- `prescriptions.finalize`
- `prescriptions.download`
- `prescriptions.void`

Asignación inicial:

- Odontólogo: ver, crear, editar borrador, finalizar y descargar.
- Odontólogo administrador: todos los anteriores y anular.
- Administrador no clínico, secretaria y administrador de plataforma: sin acceso por defecto al contenido de recetas.

## Auditoría

Eventos:

- `PRESCRIPTION_DRAFT_CREATED`
- `PRESCRIPTION_DRAFT_UPDATED`
- `PRESCRIPTION_FINALIZED`
- `PRESCRIPTION_PDF_DOWNLOADED`
- `PRESCRIPTION_DUPLICATED`
- `PRESCRIPTION_VOIDED`
- `PRESCRIPTION_PDF_INTEGRITY_FAILED`

La auditoría no debe registrar el contenido completo de la receta salvo identificadores y contexto necesario.

## Restricciones regulatorias

Dentia no sustituye recetarios oficiales exigidos para medicamentos controlados.

El PDF no constituye una receta electrónica certificada.

Dentia no recomienda medicamentos, no calcula dosis y no valida interacciones farmacológicas.
