# C019A.3-FIX1 — Triage de dependencias frontend

Fecha de evaluación: 2026-08-01. Comando: `npm --prefix frontend audit --omit=dev --json`.

## Decisión ejecutiva

Se actualizó `next` y `eslint-config-next` de 15.5.19 a 15.5.22. Esto elimina los advisories directos de Next corregidos en 15.5.21. También se actualizó el PostCSS directo de build a 8.5.18.

El reporte conserva tres entradas `high` porque Next 15.5.22 incluye PostCSS 8.4.31 y Sharp 0.34.5. No se aplicaron overrides incompatibles: los vectores restantes no son alcanzables con la configuración actual de Dentia, pero deben reevaluarse en cada actualización de Next.

## Matriz

| Paquete / advisory | Relación y versión | Severidad | Runtime / navegador / portal | Vector necesario y explotabilidad en Dentia | Versión corregida | Acción y evidencia |
|---|---|---:|---|---|---|---|
| Next `GHSA-m99w-x7hq-7vfj` — DoS Server Actions | Directa; 15.5.19 → 15.5.22 | High | Servidor; App Router | Requería una Server Action. No existen directivas `use server`, pero la ruta pública justificaba eliminar el rango vulnerable. | 15.5.21 | **Corregir ahora: hecho.** 15.5.22 está fuera del rango afectado. |
| Next `GHSA-89xv-2m56-2m9x` — SSRF Server Actions | Directa; 15.5.19 → 15.5.22 | High | Servidor | Requería Server Actions y control de headers Host. No hay Server Actions; se actualizó igualmente. | 15.5.21 | **Corregir ahora: hecho.** |
| Next `GHSA-p9j2-gv94-2wf4` — SSRF en rewrites | Directa; 15.5.19 → 15.5.22 | High | Servidor; alcanzaba rutas públicas | Requería hostname de destino construido con entrada de request. Dentia usa `API_PROXY_TARGET` fijo de proceso, nunca un segmento de URL; se actualizó igualmente. | 15.5.21 | **Corregir ahora: hecho.** |
| Next `GHSA-68g3-v927-f742` — cache confusion | Directa; 15.5.19 → 15.5.22 | Moderate | Servidor/cache | Request con body y comportamiento de caché afectado. Portal fuerza `no-store`; además se eliminó el rango vulnerable. | 15.5.21 | **Corregir ahora: hecho.** |
| Next `GHSA-4633-3j49-mh5q` — cache confusion UTF-8 | Directa; 15.5.19 → 15.5.22 | Moderate | Servidor/cache | Body UTF-8 inválido y caché. Portal/API usan `no-store`; versión corregida instalada. | 15.5.21 | **Corregir ahora: hecho.** |
| Next `GHSA-4c39-4ccg-62r3` — payload Server Action Edge | Directa; 15.5.19 → 15.5.22 | Moderate | Edge runtime | Requería Server Actions en Edge; Dentia no usa ambas. | 15.5.21 | **Corregir ahora: hecho.** |
| Next `GHSA-q8wf-6r8g-63ch` — DoS Image Optimization SVG | Directa; 15.5.19 → 15.5.22 | Moderate | Servidor de imágenes | Requería Image Optimization con SVG. No hay `next/image`; versión corregida instalada. | 15.5.21 | **Corregir ahora: hecho.** |
| Next `GHSA-955p-x3mx-jcvp` — divulgación Server Functions | Directa; 15.5.19 → 15.5.22 | Moderate | Servidor | Requería Server Functions; no existen en Dentia. | 15.5.21 | **Corregir ahora: hecho.** |
| PostCSS `GHSA-qx2v-qp2m-jg93` — XSS `</style>` | Directa build 8.5.18 (corregida); transitiva Next 8.4.31 | Moderate | Build, no bundle del navegador | Requiere CSS controlado por atacante procesado y embebido en `<style>`. Consentimientos se renderizan como nodos React escapados; no aceptan CSS ni `dangerouslySetInnerHTML`. | 8.5.10 | **Mitigado / P2 transitivo.** PostCSS directo actualizado; copia de Next no recibe CSS no confiable. |
| PostCSS `GHSA-6g55-p6wh-862q` — lectura arbitraria por source map | Directa build 8.5.18; transitiva Next 8.4.31 | High | Build/servidor, no navegador | Requiere CSS atacante con `sourceMappingURL` procesado por PostCSS. Solo CSS versionado del repositorio entra al build; usuarios y portal no suministran CSS. | 8.5.12 | **Aceptar temporalmente con mitigación / P2.** No hacer override interno sin soporte de Next. |
| PostCSS `GHSA-r28c-9q8g-f849` — traversal `.map` | Directa build 8.5.18; transitiva Next 8.4.31 | High | Build/servidor, no navegador | Requiere CSS no confiable y un path `.map`. Dentia no ofrece carga o procesamiento de CSS del usuario. | 8.5.18 | **Aceptar temporalmente con mitigación / P2.** Dependencia directa corregida. |
| Sharp `GHSA-f88m-g3jw-g9cj` — libvips | Transitiva opcional de Next; 0.34.5 | High | Servidor, no bundle | Requiere procesar una imagen no confiable. No existen imports `next/image`, configuración remota ni Image Optimization en el portal; el QR es SVG generado en el navegador por `qrcode.react`. | 0.35.0 | **Aceptar temporalmente con mitigación / P2.** Bloquear piloto si se incorpora procesamiento de imágenes antes de actualizar. |

## QR y contenido clínico

`qrcode.react@4.2.0` no aparece en `npm audit`. Recibe únicamente la URL opaca y produce SVG en el navegador. El contenido del consentimiento no se convierte en HTML libre: se divide y representa como texto React, por lo que no alcanza PostCSS ni Sharp.

## Compuerta

P0: 0. P1 aplicables después del parche: 0. P2: dos dependencias transitivas reportadas por npm, actualmente no alcanzables. La aceptación temporal deja de ser válida si Dentia incorpora CSS suministrado por usuarios, `next/image`, optimización de imágenes o cargas gráficas procesadas por Next.
