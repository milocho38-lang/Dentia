# WEB-2E — Website comercial pública de Dentia

## Estado

Implementación preparada en entorno aislado para revisión manual. No publicada.

## Arquitectura

La website se implementa como una aplicación Next.js independiente en `website/`. Tiene su propio manifiesto de dependencias, configuración, build y contenedor. No incorpora rutas comerciales dentro del frontend autenticado ni modifica la aplicación servida en `app.dentiapro.com`.

Esta separación permite revisar, construir y desplegar el sitio público sin acoplar su ciclo de entrega al producto clínico.

## Páginas

- `/`: propuesta de valor, recorrido del producto, capturas reales del tenant demo, seguridad, adopción progresiva y precios iniciales.
- `/producto`: detalle de Agenda, Pacientes, Historia clínica, Odontograma, Tratamientos, Presupuestos, Consentimientos, Finanzas, Seguimientos y Usuarios/sedes.
- `/precios`: planes públicos aprobados para Colombia y Chile.
- `/seguridad`: explicación comercial de controles verificables sin revelar detalles operativos explotables ni atribuir certificaciones inexistentes.
- `/demo`: formulario accesible preparado para revisión visual. El envío permanece deshabilitado porque no existe todavía un canal de leads aprobado.
- `/privacidad` y `/terminos`: rutas marcadas expresamente como pendientes de contenido legal aprobado.

## Assets

La website utiliza los once PNG aprobados en WEB-2D, almacenados en `website/assets/screenshots/`. Los masters se conservan sin alteración y Next.js puede generar derivados optimizados durante el build.

`home-consentimientos.png` se presenta como **Configuración y gestión de consentimientos**. No se describe como captura del acto de firma ni como evidencia de un consentimiento firmado.

El inventario, dimensiones y SHA-256 están documentados en:

- `website/assets/screenshots/README.md`
- `website/assets/screenshots/manifest.txt`

## Variables de entorno

| Variable | Propósito | Preview |
| --- | --- | --- |
| `NEXT_PUBLIC_SITE_URL` | Origen para canonical, sitemap y Open Graph | `http://localhost:3010` |
| `NEXT_PUBLIC_APP_URL` | Origen de la aplicación autenticada | `https://app.dentiapro.com` |
| `NEXT_PUBLIC_SITE_INDEXABLE` | Control explícito de indexación | `false` |

La website no reutiliza `PUBLIC_FRONTEND_URL` de la aplicación autenticada.

## Ejecución local

Desde `website/`:

```bash
cp .env.example .env.local
npm install
npm run dev -- --port 3010
```

El preview queda aislado en `http://localhost:3010`.

## Validación y build

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

El build usa salida `standalone`, por lo que puede ejecutarse fuera del VPS y empaquetarse mediante `website/Dockerfile`.

## SEO y accesibilidad

- Metadata, títulos, descripciones y canonical dependen del origen configurado.
- Open Graph usa el hero aprobado.
- `robots.txt` respeta `NEXT_PUBLIC_SITE_INDEXABLE`; el preview no es indexable por defecto.
- Existe sitemap para las rutas públicas.
- Se incluyen enlace de salto, foco visible, landmarks, headings semánticos, labels de formulario, alt text y menú móvil accesible.
- Se respeta `prefers-reduced-motion`.

## Formulario de demo

No se encontró ni se creó un backend de leads. El formulario no tiene `action`, no ejecuta solicitudes y su botón permanece deshabilitado con una explicación visible. Conectar el envío requerirá una decisión posterior sobre canal, retención, privacidad, antiabuso y operación comercial.

## Deploy futuro

Antes de publicar se requiere:

1. revisión visual manual en escritorio, tablet y móvil;
2. aprobación del contenido legal definitivo;
3. decisión y prueba del canal seguro para solicitudes de demo;
4. definición de variables productivas e indexación;
5. build fuera del VPS y despliegue del contenedor independiente;
6. validación de TLS, redirects, headers, observabilidad y rollback.

No deben cambiarse DNS, proxy, `dentiapro.com` ni `app.dentiapro.com` como parte de esta implementación.

## Rollback conceptual

El sitio público tiene artefacto y contenedor independientes. Un despliegue futuro debe conservar la imagen anterior y permitir que el proxy vuelva al servicio previo sin afectar el contenedor de la aplicación autenticada ni su base de datos.

## Alcance deliberadamente excluido

- publicación productiva;
- RIPS como funcionalidad comercial disponible;
- facturación electrónica, IA, portal del paciente o integraciones futuras no implementadas;
- persistencia de leads;
- afirmaciones de cumplimiento jurídico o certificaciones no verificadas.
