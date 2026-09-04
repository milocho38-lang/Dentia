# WEB-1B — Dominio canónico `app.dentiapro.com`

**Estado:** implementación preparada; publicación y cambio productivo pendientes de autorización.

## Objetivo

Convertir `https://app.dentiapro.com` en el origen canónico para las nuevas URL públicas generadas por Dentia, manteniendo temporalmente `https://dentiapro.com` como segundo host funcional para compatibilidad con enlaces históricos.

WEB-1B no publica la web comercial, no redirige globalmente el dominio raíz y no modifica DNS, TLS ni Nginx Proxy Manager.

## Estado anterior

- `dentiapro.com` y `app.dentiapro.com` sirven la misma aplicación mediante HTTPS y HTTP/2.
- Cada host mantiene su propia cookie `dentia_refresh` host-only.
- `PUBLIC_FRONTEND_URL=https://dentiapro.com` controla las URL públicas nuevas generadas por el backend.
- Los accesos históricos a consentimientos almacenan el hash del token y su ruta; no requieren reescribir una URL persistida para seguir disponibles en el host raíz.

## Auditoría de referencias

| Referencia | Clasificación WEB-1B | Decisión |
| --- | --- | --- |
| `.env.production.example` | Debe cambiar | Documentar `https://app.dentiapro.com` como valor canónico. |
| `consent_access_service.py` | Ya parametrizada | Conserva `settings.public_frontend_url`; no requiere cambio. |
| `consent_production_readiness.py` | Debe cambiar | Exigir el nuevo origen canónico en el gate productivo. |
| `validate_dentia_production_config.sh` | Debe cambiar | Validar el nuevo valor antes de backup/deploy. |
| `treatment_service.py` | Debe cambiar | Evitar un QR fijo al root y consumir la configuración canónica. |
| `scripts/dentia.env.example` y `dentia_common.sh` | Debe permanecer temporalmente | `DENTIA_DOMAIN_URL` es un healthcheck del root durante la transición. |
| Guardas de bases de prueba que contienen `dentiapro.com` | Deben permanecer | Identifican destinos productivos prohibidos para tests; no expresan canonicalidad web. |
| Documentación WEB-0.x y WEB-1A | Documentación histórica | No reescribir decisiones ni evidencias anteriores. |
| `www.dentiapro.com` | Futura WEB-2 | Fuera de alcance. |

## Cambio preparado

La configuración productiva objetivo es:

```text
PUBLIC_FRONTEND_URL=https://app.dentiapro.com
```

El cambio afecta exclusivamente la construcción de nuevas URL públicas server-side y los QR que consumen esa configuración. En particular, una nueva sesión de acceso a consentimiento debe devolver:

```text
https://app.dentiapro.com/consentimiento/<token>
```

No cambia:

- `/api`, que continúa same-origin;
- las rutas frontend;
- cookies host-only;
- autenticación, rotación o replay protection;
- tokens o documentos históricos;
- base de datos;
- Alembic;
- configuración de DNS/NPM.

## Compatibilidad legacy

`https://dentiapro.com` continúa sirviendo el mismo frontend y enviando `/api` al mismo backend. Por ello, los enlaces históricos con ruta `/consentimiento/<token>` permanecen resolubles desde el root mientras dure la transición.

No se migran, reemiten ni reescriben tokens históricos.

## Secuencia productiva autorizable

1. Publicar el commit aislado de WEB-1B.
2. Confirmar GitHub Actions en verde.
3. Registrar commit, configuración y estado productivo anterior.
4. Crear y verificar el backup oficial.
5. Cambiar únicamente `PUBLIC_FRONTEND_URL` en el archivo productivo protegido.
6. Ejecutar el procedimiento oficial de deploy/restart con el commit de WEB-1B.
7. Verificar Alembic `20260801_0035 (head)`, salud, logs, puertos y ambos hosts.
8. Generar un acceso nuevo de consentimiento y comprobar dominio app en URL y QR.
9. Abrir un enlace histórico mediante el root.

## Rollback

El rollback no requiere cambios de base de datos:

1. Restaurar en el archivo productivo protegido:

   ```text
   PUBLIC_FRONTEND_URL=https://dentiapro.com
   ```

2. Volver al commit de aplicación anterior mediante el procedimiento oficial.
3. Recrear backend/frontend con la configuración restaurada.
4. Verificar root, app, auth y consentimientos.

El backup previo al cambio canónico protege la base y el storage, aunque WEB-1B no los modifica.

## Validaciones requeridas después de publicar

- configuración productiva válida con el dominio app;
- nuevas URL y QR en `app.dentiapro.com`;
- enlaces históricos funcionales en el root;
- autenticación independiente por host;
- ausencia de CORS y puertos internos filtrados;
- root, app y AdminPH saludables;
- cero errores nuevos en frontend, backend y proxy.

WEB-2 no se inicia automáticamente al cerrar WEB-1B.
