# C017G.1 — Informes clínicos, remisiones y cartas

## Propósito

Permitir que el profesional redacte documentos narrativos sencillos desde el Centro Integral del Paciente y genere un PDF institucional inmutable, firmado gráficamente con la identidad configurada de Dentia.

El módulo cubre:

- Remisión.
- Informe clínico.
- Certificado / constancia.
- Carta general.

No cubre recetas, consentimientos informados, adjuntos clínicos, correos, WhatsApp, IA ni firma electrónica avanzada.

## Ubicación funcional

```text
Paciente
  → Documentos
  → Informes y documentos
```

El módulo vive dentro del expediente del paciente para evitar confundirlo con el Centro de Reportes estadístico.

## Flujo aprobado

```text
Nuevo documento
  → seleccionar tipo
  → sede
  → profesional firmante
  → destinatario y asunto
  → contenido narrativo plano
  → guardar borrador
  → previsualizar
  → finalizar
  → descargar PDF almacenado
```

## Estados

- `DRAFT`: editable, sin número definitivo ni PDF inmutable.
- `FINALIZED`: inmutable; genera número, snapshots, hash y PDF almacenado.
- `VOIDED`: conserva el PDF y el histórico; requiere motivo de anulación.

Un documento finalizado no se edita. Para reutilizarlo se duplica como nuevo borrador.

## Inmutabilidad documental

Al finalizar se congelan:

- datos institucionales;
- datos de sede;
- datos del paciente;
- datos del profesional;
- contenido del documento;
- fecha clínica;
- número consecutivo;
- PDF generado;
- hash SHA-256 del PDF;
- hash de integridad del contenido.

Las descargas posteriores devuelven el PDF almacenado, no un PDF regenerado con datos vivos.

## Permisos

Permisos clínicos específicos:

- `clinical_documents.view`
- `clinical_documents.create`
- `clinical_documents.edit_draft`
- `clinical_documents.finalize`
- `clinical_documents.download`
- `clinical_documents.void`

Asignación inicial:

- Odontólogo: ver, crear, editar borrador, finalizar y descargar.
- Odontólogo administrador: todos los anteriores y anular.
- Secretaria, administrador empresarial y administrador de plataforma: sin acceso por defecto al contenido clínico narrativo.

## Auditoría

Eventos mínimos:

- `CLINICAL_DOCUMENT_DRAFT_CREATED`
- `CLINICAL_DOCUMENT_DRAFT_UPDATED`
- `CLINICAL_DOCUMENT_FINALIZED`
- `CLINICAL_DOCUMENT_PDF_DOWNLOADED`
- `CLINICAL_DOCUMENT_DUPLICATED`
- `CLINICAL_DOCUMENT_VOIDED`
- `CLINICAL_DOCUMENT_PDF_INTEGRITY_FAILED`

La auditoría conserva identificadores, resultado y contexto; no debe registrar contenido clínico narrativo completo.

## Reglas de seguridad

- La empresa se deriva de sesión.
- La sede debe estar autorizada para el usuario.
- El paciente debe pertenecer a la empresa activa.
- Las referencias a tratamiento, evolución o cita deben pertenecer al mismo paciente y empresa.
- El PDF no puede descargarse si el hash almacenado no coincide.
- No se permite acceso por `PLATFORM_ADMIN` a contenido clínico de empresas.

## Limitación conocida

El modelo actual de odontólogo no contiene todavía firma, registro profesional y especialidad propios por perfil.

Para C017G.1 se reutiliza la firma gráfica profesional configurada en branding institucional. El PDF deja constancia de que es una firma gráfica para emisión documental y no una firma electrónica avanzada.

Riesgo futuro: crear campos profesionales por odontólogo para soportar firma y registro individual por profesional.
