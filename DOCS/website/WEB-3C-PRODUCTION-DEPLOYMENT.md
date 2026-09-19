# WEB-3C — Publicación de la home compacta

**Fecha:** 2026-09-19

**Alcance:** website pública de Dentia

**Commit anterior y rollback de código:** `e9271e94ca5a51eeea1839c58bc9eec179992bc2`

**Commit WEB-3C:** el commit `feat(website): compact home with product carousel` que contiene este documento

El SHA del commit no se incrusta dentro del propio commit porque ese valor depende del contenido del documento. El registro operativo de la publicación debe reportar el SHA completo, la ejecución exacta de CI y la ruta de backup generada por el procedimiento oficial.

## Alcance publicado

- home pública compactada según WEB-3A;
- un único carrusel de ocho funcionalidades;
- autoplay cada 6 segundos y loop continuo;
- pausa por hover, foco, pestaña oculta y movimiento reducido;
- pausa temporal de 10 segundos después de interacción manual;
- navegación anterior/siguiente, selectores directos, teclado y swipe nativo;
- responsive, SEO y accesibilidad preservados;
- documentación y contratos automatizados de WEB-3A/WEB-3B.

No forman parte de WEB-3C la aplicación clínica, backend, base de datos, Alembic, RIPS, Ortodoncia, Periodontograma, AdminPH, DNS, TLS, NPM ni variables productivas.

## Validación local previa

Sobre el snapshot candidato se ejecutaron satisfactoriamente:

```text
npm test
npm run lint
npm run typecheck
npm run build
git diff --check
```

Resultados relevantes:

- `site-contract-tests OK`;
- `official-screenshots 11/11`;
- `carousel-autoplay-tests OK`;
- 12 rutas estáticas generadas por Next.js;
- sin errores de lint, TypeScript ni whitespace.

## CI y condición de despliegue

El despliegue solo se autoriza si GitHub Actions termina en verde para el SHA exacto del commit WEB-3C. Un fallo de CI bloquea el despliegue; no se permiten exclusiones, `continue-on-error` ni cambios de cobertura para ocultarlo.

## Backup y despliegue

Se usa exclusivamente `scripts/production/deploy_dentia.sh`. El procedimiento:

1. valida la configuración productiva sin imprimir secretos;
2. crea y verifica un backup completo de PostgreSQL y storage;
3. exige un repositorio productivo limpio;
4. actualiza `master` por fast-forward;
5. reconstruye imágenes;
6. ejecuta Alembic como no-op para este cambio sin esquema;
7. recrea y valida backend, frontend y website;
8. registra en `.run/` el commit anterior, el nuevo commit y el backup usado.

La ruta exacta del backup y el resultado del deploy se conservan en el registro operativo del servidor y en el informe final de WEB-3C. No se copian datos del backup ni información sensible a Git.

## Verificaciones productivas requeridas

Después del deploy se comprueba:

- `https://dentiapro.com` y `https://app.dentiapro.com` en HTTP 200;
- backend y PostgreSQL saludables;
- AdminPH y NPM saludables;
- cero OOM y reinicios inesperados;
- HTML nuevo enlazado a CSS y JavaScript hashed vigentes;
- CSS, chunks, screenshots, imágenes optimizadas e iconos en HTTP 200 y con MIME correcto;
- cache de assets hashed sin mezcla entre HTML y bundles de versiones diferentes;
- hero, carrusel, audiencias, confianza, validación, precios, CTA y footer presentes;
- un solo `h1`, canonical, robots, sitemap y contenido funcional indexable;
- skip link, labels, foco visible, teclado y reduced motion;
- contratos responsive para 320, 390 y 430 px sin overflow global.

La comprobación visual final aprobada por Camilo para WEB-3B/WEB-3B.2 es la referencia de aceptación del diseño. En producción se valida que se estén sirviendo esos mismos artefactos y contratos, sin introducir cambios adicionales.

## Cache

No se desactiva el cache productivo. Los recursos `_next/static` conservan nombres con hash y cache inmutable; el HTML debe referenciar los hashes del build desplegado. Solo se consideraría una invalidación puntual si se detectara una mezcla real entre HTML y assets de builds distintos.

## Rollback

Al no existir migración ni cambio de datos, el rollback de código consiste en volver por el procedimiento oficial al commit:

```text
e9271e94ca5a51eeea1839c58bc9eec179992bc2
```

El backup creado por el deploy queda disponible como protección adicional, pero no debe restaurarse para un rollback exclusivamente visual salvo que exista una causa independiente y expresamente verificada.
