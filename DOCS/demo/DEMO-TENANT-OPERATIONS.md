# WEB-2B — Operación segura de Clínica Dental Aurora

Estado: infraestructura implementada. La creación de Aurora en producción no está autorizada por WEB-2B.

## 1. Alcance

El CLI administra exclusivamente el dataset sintético `aurora-v1` de **Clínica Dental Aurora**. No se ejecuta durante startup, migraciones ni despliegues. Sus operaciones mutantes son dry-run salvo que se agregue `--apply`.

Ejecutar desde `backend/` con el ambiente y `DATABASE_URL` objetivo cargados de forma explícita:

```bash
PYTHONPATH=. python -m app.cli.demo_tenant plan --operation create
```

El plan muestra ambiente, destino de base de datos sin credenciales, operación, conteos esperados y gates. Revisar esta salida antes de cualquier mutación.

Todo comando con `--apply` exige repetir literalmente ese destino saneado mediante:

```text
--confirm-database-target <host:puerto/base>
```

## 2. Secretos y configuración

Los secretos nunca se pasan como argumentos ni se escriben en documentación o logs:

- `DENTIA_DEMO_ADMIN_PASSWORD`: contraseña administrada de la cuenta principal; obligatoria en create.
- `DENTIA_DEMO_ADMIN_EMAIL`: correo de acceso administrado; opcional, con valor sintético no entregable por defecto.
- `DENTIA_DEMO_EMAIL_SINK_RECIPIENT`: único destinatario interno que admite el sink; obligatorio al aplicar.
- `DENTIA_DEMO_TENANT_IDS`: allowlist CSV de UUID. Debe permanecer vacía por defecto y contener el UUID exacto de Aurora antes de update/reset.

Si un secreto obligatorio no está en el ambiente, el CLI solo lo solicita mediante entrada oculta en una terminal interactiva. No imprime contraseñas, OTP ni tokens.

## 3. Create

Dry-run:

```bash
PYTHONPATH=. python -m app.cli.demo_tenant create \
  --actor-user-id <platform-admin-uuid>
```

Aplicación en un entorno no productivo explícito:

```bash
PYTHONPATH=. python -m app.cli.demo_tenant create \
  --actor-user-id <platform-admin-uuid> \
  --confirm-database-target <host:puerto/base> \
  --apply
```

Create reutiliza el aprovisionamiento de Plataforma y luego los servicios de dominio. Si Aurora ya existe, solo puede reconciliarla cuando UUID, slug, nombre y allowlist coinciden; no crea una segunda empresa.

En producción se requieren además:

```text
--confirm-environment PRODUCTION
--confirm-tenant CREATE
```

Esto no constituye autorización para ejecutar el comando. Antes de una creación productiva se necesita autorización operativa posterior, backup verificado y ventana controlada.

## 4. Status

```bash
PYTHONPATH=. python -m app.cli.demo_tenant status \
  --company-id <aurora-uuid>
```

Status no muta DB ni filesystem. Informa identidad, allowlist, conteos, archivos e invariantes sin listar pacientes, correos, documentos, rutas absolutas o secretos.

Después del primer create, incorporar el UUID devuelto a la allowlist operacional y ejecutar status antes de update/reset.

## 5. Update

Dry-run:

```bash
PYTHONPATH=. python -m app.cli.demo_tenant update \
  --company-id <aurora-uuid> \
  --actor-user-id <platform-admin-uuid>
```

Aplicación:

```bash
PYTHONPATH=. python -m app.cli.demo_tenant update \
  --company-id <aurora-uuid> \
  --actor-user-id <platform-admin-uuid> \
  --confirm-database-target <host:puerto/base> \
  --apply
```

Update exige identidad triple y reconcilia el dataset sin duplicarlo. En producción requiere también `--confirm-environment PRODUCTION` y `--confirm-tenant <aurora-uuid>`.

## 6. Reset

Reset preserva empresa, sede base, usuarios, roles, perfiles y auditoría histórica; revoca sesiones y reconstruye únicamente el dataset operativo reconocido. Aborta si detecta datos ajenos al registro Aurora v1 o filas RIPS.

Dry-run:

```bash
PYTHONPATH=. python -m app.cli.demo_tenant reset \
  --company-id <aurora-uuid> \
  --actor-user-id <platform-admin-uuid>
```

Aplicación no productiva:

```bash
PYTHONPATH=. python -m app.cli.demo_tenant reset \
  --company-id <aurora-uuid> \
  --actor-user-id <platform-admin-uuid> \
  --confirm-database-target <host:puerto/base> \
  --confirm-reset "RESET CLINICA DENTAL AURORA <aurora-uuid>" \
  --apply
```

En producción son obligatorios además:

```text
--confirm-environment PRODUCTION
--confirm-tenant <aurora-uuid>
--backup-reference <referencia-verificada>
```

No usar una referencia de backup ficticia. Verificar restaurabilidad según el runbook de backup antes de autorizar reset.

## 7. Barrera de correo

Los consentimientos creados por el orquestador usan `DemoEmailSink` mediante una sobreescritura contextual ligada al UUID exacto de Aurora. El sink:

- rechaza cualquier destinatario distinto al configurado;
- no llama SMTP;
- conserva asunto, destinatario enmascarado, cuerpo redactado y hashes de adjuntos;
- mantiene el OTP solo en memoria durante el flujo automatizado;
- redacta OTP y tokens en la evidencia inspeccionable;
- se desactiva al salir del contexto y no altera el proveedor de otros tenants.

La identidad demo se valida antes del flujo en update/reset. No convertir este mecanismo en un toggle global.

## 8. Transacción, archivos y rollback

El CLI abre una transacción exterior; los commits realizados por servicios quedan contenidos en savepoints. Si una etapa falla antes del commit final:

1. se revierte toda la operación DB;
2. se restauran directorios puestos en cuarentena durante reset;
3. se eliminan archivos nuevos generados por create/update;
4. no se toca ningún directorio cuyo nombre no sea el UUID exacto del tenant objetivo.

Después del commit DB, la limpieza de cuarentena no intenta revertir archivos ni base. Cualquier residuo de cuarentena debe reportarse y limpiarse mediante una intervención controlada, nunca con comodines.

Rollback de producto significa restaurar el backup y la versión de aplicación siguiendo los runbooks oficiales; no ejecutar SQL manual, `TRUNCATE ... CASCADE` ni `DELETE FROM empresas`.

## 9. Verificación posterior

Después de create/update/reset:

1. ejecutar status;
2. confirmar tres usuarios, catorce pacientes, dos odontólogos activos de cupo tres y cuatro consentimientos;
3. verificar agenda de la semana local y seguimientos derivados;
4. comprobar navegación con la cuenta administrada y logout;
5. confirmar que no hay correos SMTP, referencias cross-tenant ni datos RIPS;
6. comprobar documentos y consentimientos sintéticos sin exponer datos en screenshots.

## 10. Prohibiciones

- No ejecutar contra producción sin autorización explícita posterior.
- No agregar el CLI a startup, deploy o migraciones.
- No compartir credenciales ni habilitar acceso anónimo.
- No reutilizar datos de clientes ni copiar tenants.
- No retirar identidad triple, allowlist, frase de reset o referencia de backup.
- No apuntar `APP_ENV=test` a una base productiva.
- No desactivar el sink para completar consentimientos demo.
- No versionar PDFs, firmas, páginas escaneadas ni storage generado.
