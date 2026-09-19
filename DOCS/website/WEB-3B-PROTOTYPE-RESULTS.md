# WEB-3B — Resultados del prototipo de home compacta

Fecha de validación local final: 2026-09-19

## 1. Alcance

WEB-3B compacta exclusivamente la home pública de Dentia. No modifica la aplicación clínica, backend, RIPS, Ortodoncia, Periodontograma, infraestructura productiva, DNS ni configuración de despliegue.

El prototipo conserva el hero, precios, llamada final a la acción y navegación existentes. El recorrido vertical repetitivo de funcionalidades fue sustituido por un carrusel horizontal único con ocho capacidades reales del producto.

## 2. Estructura comparada

### Antes

- Hero.
- Franja de problema y propuesta de valor.
- Recorrido vertical por funcionalidades con múltiples capturas grandes.
- Bloques adicionales de recorrido, seguridad e implementación.
- Audiencias, precios y llamada final.
- Aproximadamente catorce bandas visuales y diez capturas en la home.

La referencia anterior permanece recuperable en Git desde el estado base del worktree. Sus hashes de contenido eran:

- `website/app/page.tsx`: `32aeb863ef462be35c606b88537b6116e68cf110dbcc7c630a320635d0babbcf`
- `website/app/globals.css`: `73cfefb7e9adabef9db7591541fde7b2c4b9c3a9cd4429ebafaede307ed8b8db`

### Después

1. Hero y franja compacta de transformación.
2. Carrusel de producto.
3. Audiencias: odontólogo independiente y clínica/consultorio.
4. Confianza: seguridad, implementación progresiva y acompañamiento.
5. Validación real en Colombia y Chile.
6. Precios resumidos.
7. Llamada final a demostración.

El resultado reduce la home a siete bandas principales. Las ocho funcionalidades permanecen disponibles dentro de una sola sección horizontal, sin ocultar su texto al HTML inicial.

## 3. Carrusel implementado

El carrusel contiene, en este orden:

1. Agenda organizada.
2. Pacientes en contexto.
3. Historia clínica trazable.
4. Odontograma clínico.
5. Tratamientos conectados.
6. Consentimientos gestionados.
7. Finanzas del paciente.
8. Seguimientos visibles.

Comportamiento:

- cambio automático cada 6 segundos;
- reproducción únicamente cuando la sección está suficientemente visible;
- pausa al pasar el cursor, enfocar un control, iniciar interacción táctil, seleccionar manualmente una diapositiva o cambiar de pestaña;
- controles anterior/siguiente y selectores directos;
- navegación con flechas izquierda/derecha cuando el foco está dentro del carrusel;
- gesto horizontal nativo mediante `scroll-snap`;
- detención del movimiento automático con `prefers-reduced-motion: reduce`;
- loop continuo del slide 8 al 1;
- anuncio accesible de cambios iniciados por el usuario, sin ruido periódico por autoplay.

La interacción manual detiene temporalmente el autoplay durante 10 segundos para evitar que la interfaz contradiga una decisión reciente del visitante. Después se reanuda automáticamente. El botón Pausar/Reanudar mantiene además un control explícito y persistente durante el montaje del componente.

## 4. Capturas utilizadas

Se reutilizan los activos oficiales ya aprobados:

- `home-agenda.png`
- `home-pacientes.png`
- `home-historia-clinica.png`
- `home-odontograma.png`
- `home-tratamientos.png`
- `home-consentimientos.png`
- `home-finanzas.png`
- `home-seguimientos.png`

No se incorporaron imágenes nuevas, datos reales, PII, credenciales ni artefactos generados.

## 5. Medición vertical

WEB-3A estimó la home anterior en aproximadamente:

| Viewport | Home anterior, estimación de fuente | Home compacta, expectativa | Medición DOM |
| --- | ---: | ---: | --- |
| 1440 × 900 | 7.000–8.000 px | 4.500–5.200 px | Pendiente |
| 390 × 844 | 9.000–11.000 px | 6.000–7.000 px | Pendiente |

Estas cifras son estimaciones estructurales, no medidas del DOM. En esta sesión no estuvo disponible un navegador interactivo compatible con la herramienta de inspección, por lo que no se fabricó un resultado de `scrollHeight`.

La medición final debe realizarse con el preview local en los dos viewports indicados, una vez cargadas las imágenes, ejecutando en la consola:

```js
await document.fonts.ready;
await Promise.all(
  [...document.images].map((image) =>
    image.complete
      ? Promise.resolve()
      : new Promise((resolve) => {
          image.addEventListener("load", resolve, { once: true });
          image.addEventListener("error", resolve, { once: true });
        }),
  ),
);

({
  viewport: `${window.innerWidth}x${window.innerHeight}`,
  scrollHeight: document.documentElement.scrollHeight,
});
```

El gate de reducción vertical medida permanece pendiente hasta registrar ambos valores reales.

## 6. Responsive y accesibilidad

Se implementaron reglas para 320, 390, 430, 1024, 1280, 1440 y 1920 px mediante un layout fluido y breakpoints existentes. En móvil:

- cada slide ocupa casi todo el ancho y deja visible una fracción del siguiente;
- el desplazamiento horizontal queda contenido dentro del carrusel;
- los controles se apilan sin alterar el orden de lectura;
- no se fuerza scroll horizontal sobre la página.

Accesibilidad incluida:

- jerarquía única de `h1` y títulos de sección;
- región del carrusel etiquetada;
- controles con nombres accesibles;
- estado activo comunicado con `aria-current`;
- navegación por teclado;
- foco visible heredado del sistema visual;
- contenido textual completo disponible en el DOM;
- alternativa de movimiento reducido.

Camilo aprobó la revisión visual final, la longitud de la home, las proporciones, el carrusel, el autoplay y la navegación manual. El contrato de swipe permanece cubierto por la pista nativa con `scroll-snap` y los controles táctiles.

## 7. SEO y rendimiento

- Las ocho descripciones están renderizadas en el HTML; no dependen de una llamada posterior.
- Se conserva un único `h1` y enlaces internos a Producto, Seguridad, Precios y Demo.
- No se agregaron librerías de carrusel ni dependencias de runtime.
- Las capturas reutilizan el componente optimizado de imágenes del sitio.
- El autoplay usa un único temporizador y se suspende fuera del viewport o con la página oculta.

## 8. Validaciones ejecutadas

| Validación | Resultado |
| --- | --- |
| `npm test` | PASS — `site-contract-tests OK`, 11/11 capturas oficiales y `carousel-autoplay-tests OK` |
| `npm run lint` | PASS |
| `npm run typecheck` | PASS |
| `npm run build` | PASS — 12 rutas estáticas generadas |
| `npm audit` | 0 vulnerabilidades reportadas tras instalar dependencias locales |
| `git diff --check -- website DOCS/website` | PASS |
| Preview local `/` | HTTP 200 |

Los contratos automatizados verifican las ocho diapositivas, intervalo de 6 segundos, pausa por visibilidad/hover/foco/interacción, teclado, `aria-live`, movimiento reducido, `scroll-snap` y pista visual del siguiente slide en móvil.

## 9. Riesgos residuales

- Medir `scrollHeight` real en 1440 × 900 y 390 × 844.
- Observar métricas productivas de rendimiento y uso del carrusel después del despliegue.
- Mantener el monitoreo de overflow en navegadores móviles sin cambiar el diseño aprobado sin una nueva revisión.

## 10. Estado

- `WEB_3B_CAROUSEL_IMPLEMENTED`
- `WEB_3B_AUTOPLAY_PASS`
- `WEB_3B_MANUAL_NAVIGATION_PASS`
- `WEB_3B_MOBILE_SWIPE_CONTRACT_PASS`
- `WEB_3B_REDUCED_MOTION_PASS`
- `WEB_3B_KEYBOARD_PASS`
- `WEB_3B_SEO_STRUCTURE_PASS`
- `WEB_3B_BUILD_PASS`
- `WEB_3B_VERTICAL_REDUCTION_MEASUREMENT_PENDING`
- `WEB_3B_RESPONSIVE_VISUAL_REVIEW_PASS`
- `WEB_3B_CAMILO_APPROVAL_PASS`
- `READY_FOR_WEB_3C`

No se hizo commit, push ni deploy.
