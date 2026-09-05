# Dentia public website

Aplicación Next.js independiente para la website comercial pública de Dentia. No contiene rutas ni lógica de la aplicación autenticada.

## Desarrollo local

```bash
cp .env.example .env.local
npm install
npm run dev -- --port 3010
```

Abrir `http://localhost:3010`.

## Variables

- `NEXT_PUBLIC_SITE_URL`: origen del sitio público usado para canonical, sitemap y Open Graph.
- `NEXT_PUBLIC_APP_URL`: origen de la aplicación autenticada. Su valor productivo esperado es `https://app.dentiapro.com`.
- `NEXT_PUBLIC_SITE_INDEXABLE`: usar `true` únicamente cuando el sitio deba ser indexado públicamente.

## Validación

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

El artefacto de producción puede iniciarse con `PORT=3010 npm run start` después del build.

El formulario de demostración no envía ni almacena datos hasta que exista un canal de leads aprobado.
