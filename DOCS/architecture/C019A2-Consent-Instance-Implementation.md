# C019A.2 — Implementación de instancias de consentimiento

## Arquitectura aplicada

```text
Plantilla tenant publicada e inmutable
             ↓
motor de aplicabilidad C019A.1
             ↓
contexto clínico validado por empresa/sede
             ↓
ConsentInstance + ConsentInstanceProcedure snapshots
             ↓
revisión profesional
             ↓
READY_FOR_REVIEW sellado
             ↓
C019A.3 podrá crear sesión y PENDING_SIGNATURE
```

No existe una segunda fuente de verdad para plantillas ni contenido editable posterior al sellado.

## Modelo y migración

La revisión `20260801_0024`, dependiente de `20260801_0023`, crea:

- `consentimiento_instancia_consecutivos`: contador transaccional por empresa.
- `consentimiento_instancias`: contexto, estado, versión exacta, contenido, variables, hashes, revisión y anulación.
- `consentimiento_instancia_procedimientos`: asociación explícita y snapshot ordenado de catálogo/procedimiento de tratamiento.

Las FKs usan `RESTRICT` para historia esencial y `SET NULL` solo en vínculos operativos que pueden desaparecer. No hay cascadas destructivas ni datos clínicos sembrados.

## Resolución segura

La resolución usa exclusivamente el allowlist de `VARIABLE_CATALOG` y reemplazo por expresión regular de identificadores registrados. No hay `eval`, acceso dinámico a atributos ni contenido arbitrario enviado por frontend.

Se reutilizan `calculate_age`, `effective_timezone`, `clinical_date_or_local_default` y `find_applicable_published_templates`. Los campos inexistentes en el modelo real —diagnóstico y número de plan del tratamiento, especialidad o registro individual cuando no están configurados— permanecen nulos y se reportan como faltantes; no se infieren de observaciones.

## Snapshots y hashes

La instancia conserva:

- contenido exacto y número de versión de plantilla;
- valores resueltos;
- identidad de paciente, empresa, sede y profesional;
- tratamiento y procedimientos;
- fecha clínica, zona horaria y timestamp UTC.

Al confirmar se calculan SHA-256 de plantilla, contenido y contexto, más un `integrity_hash` canónico. Toda lectura de una instancia sellada vuelve a comprobar los cuatro valores y responde `409` si detecta alteración.

## API

- `POST /api/consent-instances/applicable-templates`
- `GET|POST /api/consent-instances`
- `POST /api/consent-instances/batch`
- `GET|PATCH /api/consent-instances/{id}`
- `POST /api/consent-instances/{id}/resolve`
- `POST /api/consent-instances/{id}/preview`
- `POST /api/consent-instances/{id}/professional-confirm`
- `POST /api/consent-instances/{id}/mark-pending-signature` — reservado, responde `409`.
- `POST /api/consent-instances/{id}/void`
- `GET /api/consent-instances/{id}/audit`

La creación batch usa una sola transacción. Ningún payload acepta empresa, estado, hashes o contenido sustitutivo.

## Seguridad y auditoría

Todos los accesos derivan empresa de la sesión y cruzan empresa, sede autorizada, paciente, cita, tratamiento, procedimientos, profesional y plantilla. La confirmación requiere permiso clínico, perfil odontológico activo y que el usuario sea el profesional seleccionado.

Se auditan creación, selección de plantilla, resolución, preview, actualización de contexto, confirmación profesional, sellado y anulación. El detalle evita texto completo, identidad documental, tokens y secretos.

## Contrato para C019A.3

C019A.3 deberá crear la sesión de firma de forma atómica y solo entonces transicionar `READY_FOR_REVIEW → PENDING_SIGNATURE`. Deberá reutilizar los snapshots y hashes, sin re-renderizar la plantilla ni modificar esta instancia.

## Integración implementada por C019A.3

La emisión crea una sesión de acceso persistente y transiciona atómicamente a `PENDING_SIGNATURE`. El portal vuelve a verificar los cuatro hashes antes de mostrar el snapshot; no modifica contenido, variables ni contexto sellado. Revocación y reemisión operan sobre el canal técnico, no sobre la historia clínica de la instancia.
