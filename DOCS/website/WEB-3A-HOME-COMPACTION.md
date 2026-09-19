# WEB-3A — Compactación de la home pública y carrusel horizontal

**Estado:** arquitectura aprobada e implementada en WEB-3B/WEB-3B.2

**Fecha:** 2026-09-17

**Decisión recomendada:** **B. Compactar con un carrusel principal**

**Alcance revisado:** home pública de [dentiapro.com](https://dentiapro.com/), implementación Next.js de `website/app/page.tsx`, estilos globales, componentes compartidos y once capturas oficiales de Clínica Dental Aurora.

La home productiva se verificó en modo lectura y se contrastó con el código limpio del sitio. No se realizó una medición visual automatizada porque el navegador interactivo no estaba disponible; las alturas son estimaciones basadas en la estructura y CSS actuales y deberán confirmarse en el prototipo WEB-3B.

## 1. Problema detectado

La home comunica correctamente el producto, pero repite el mismo recorrido funcional en tres niveles:

1. El hero enumera agenda, pacientes, historia clínica, tratamientos, consentimientos, pagos y seguimiento.
2. `Un flujo continuo` vuelve a mostrar esas siete etapas.
3. La sección `story-stack` desarrolla nuevamente los módulos en siete filas verticales con nueve capturas.

La repetición no es principalmente de copy literal, sino de intención. El visitante entiende pronto que Dentia conecta la operación, pero debe recorrer varios miles de píxeles antes de llegar a seguridad, implementación, validación real, precios y CTA final.

Hallazgos concretos:

- existen ocho secciones `<section>` principales después del header;
- la sección narrativa central contiene siete filas grandes, por lo que la página se percibe como catorce bandas de contenido antes del footer;
- la home renderiza diez capturas: hero más nueve dentro del relato;
- dos filas muestran pares de capturas, reduciendo su legibilidad;
- el bloque de problema, el flujo y las filas funcionales compiten por explicar la misma idea;
- precios y CTA aparecen correctamente fuera de elementos interactivos, pero llegan tarde por la longitud previa;
- en móvil las siete filas se apilan y multiplican el desplazamiento vertical.

No se recomienda convertir toda la página en un desplazamiento horizontal. Eso afectaría orientación, accesibilidad, SEO, uso móvil y descubrimiento de precios/CTA.

## 2. Objetivo

Crear una home que se sienta más rápida, visual y propia de un SaaS sin sacrificar información esencial.

Resultados buscados:

- explicar qué es Dentia en el primer viewport;
- sustituir repetición vertical por exploración horizontal controlable;
- mantener contenido comercial completo y rastreable;
- conservar precios y CTA como destinos estables;
- reutilizar las capturas reales aprobadas sin hacerlas ilegibles;
- mantener una experiencia funcional sin autoplay ni JavaScript;
- no anunciar Ortodoncia ni Periodontograma hasta autorización comercial.

## 3. Análisis de la home actual

### 3.1 Inventario

| Orden | Bloque actual | Contenido | Evaluación |
|---:|---|---|---|
| 1 | Hero | Propuesta, dos CTA, validación y dashboard | Mantener; ya responde qué es, para quién y qué conecta |
| 2 | Menos fragmentación | Problema y transformación en tres tarjetas | Mantener, pero compactar a una franja de valor |
| 3 | Un flujo continuo | Siete etapas en tarjetas pequeñas | Integrar al carrusel; hoy anticipa lo que se repite debajo |
| 4 | Story stack | Independiente, clínica y cinco historias funcionales adicionales | Reemplazar por audiencia + carrusel principal |
| 5 | Seguridad | Panel y cinco controles | Compactar dentro de tres tarjetas de confianza |
| 6 | Implementación/estado | Dos tarjetas grandes | Agrupar con seguridad y acompañamiento |
| 7 | Precios | Colombia, Chile y enlace | Mantener estable; reducir padding y copy repetido |
| 8 | CTA final | Solicitar demostración | Mantener estable |

### 3.2 Densidad y longitud

La combinación de padding vertical de hasta `7.5rem`, siete filas narrativas y gaps de hasta `8rem` hace que la sección central domine la página. Con el contenedor y proporciones actuales se estima:

- desktop 1440 px: aproximadamente 7.000–8.000 px de documento, incluido footer;
- móvil 390 px: aproximadamente 9.000–11.000 px, por el apilamiento de copy y capturas;
- sección narrativa central: cerca de 40–50 % de la altura total.

La propuesta reduce catorce bandas visuales efectivas a siete secciones principales. La reducción esperada es de 35–45 % en desktop y 30–40 % en móvil. Son objetivos de prototipo, no cifras de aceptación rígidas.

### 3.3 Contenido que no debe perderse

- operación conectada de punta a punta;
- utilidad para independiente y clínica;
- historia clínica y odontograma;
- consentimientos electrónicos y en papel;
- pagos, saldos y comprobantes;
- seguimiento de controles;
- multiempresa y permisos;
- seguridad, implementación progresiva y acompañamiento;
- validación con prácticas de Colombia y Chile;
- precios y solicitud de demo.

## 4. Nueva arquitectura propuesta

Se recomiendan siete secciones de contenido, además de navegación y footer:

1. **Hero vertical:** mensaje, CTA y dashboard.
2. **Problema → resultado:** franja compacta de transformación.
3. **Todo conectado en Dentia:** único carrusel funcional con ocho módulos.
4. **Para quién es:** dos tarjetas, independiente y clínica.
5. **Por qué Dentia:** seguridad, implementación y acompañamiento; validación Colombia/Chile integrada.
6. **Precios:** dos tarjetas compactas y enlace estable.
7. **CTA final:** solicitud de demostración.

La página `/producto` conserva el detalle profundo y las capturas complementarias. La home presenta el valor y permite explorar sin convertirse en un catálogo exhaustivo.

### Recomendación final

**Opción B — compactar con un carrusel principal.**

Razones:

- elimina la repetición entre journey y siete historias verticales;
- permite usar capturas grandes en lugar de pares pequeños;
- preserva una lectura vertical predecible para hero, audiencias, confianza, precios y CTA;
- reduce peso cognitivo frente a dos carruseles;
- requiere un solo patrón interactivo que probar y hacer accesible;
- mantiene `/producto` como lugar natural para una experiencia visual más extensa.

## 5. Secciones que permanecen verticales

### Navegación

Mantener sticky header, enlaces Producto/Precios/Seguridad/Demo, inicio de sesión y CTA. No introducir navegación horizontal global.

### Hero

Mantener:

- eyebrow `Gestión odontológica conectada`;
- titular `Toda tu consulta odontológica en un solo lugar.`;
- CTA principal `Solicitar demostración`;
- CTA secundario `Conocer Dentia`;
- línea de validación Colombia/Chile;
- dashboard real como visual principal.

El hero no debe ser un slide. Es el ancla de orientación y conversión.

### Problema → resultado

Mantener el contraste `Información dispersa → Dentia → Una sola operación`, pero reducirlo a una franja compacta. El párrafo largo puede resumirse a una frase. En móvil se apila verticalmente sin autoplay.

### Audiencias

Mantener dos tarjetas visibles simultáneamente en desktop:

- `Odontólogo independiente`;
- `Clínica o consultorio`.

En móvil se apilan. No necesitan carrusel porque comparar las dos opciones aporta valor y solo existen dos.

### Confianza

Mantener tres tarjetas compactas:

- Seguridad;
- Implementación;
- Acompañamiento.

La validación con prácticas reales aparece como una línea o badge debajo: `En validación con odontólogos de Colombia y Chile`. No se inventan testimonios.

### Precios y CTA

Permanecen siempre visibles y fuera del carrusel. El visitante no debe esperar una transición ni recorrer slides para encontrarlos.

## 6. Secciones que pasan a carrusel

Un único carrusel reemplaza:

- el bloque `Un flujo continuo`;
- las historias verticales de agenda/independiente, contexto clínico, plan y ejecución, consentimientos, finanzas y seguimientos;
- parte de la explicación modular repetida en el hero.

La tarjeta `Para clínicas`, basada en Configuración, pasa a la sección de audiencias. Seguridad e implementación pasan a la sección de confianza. No se incluyen en el carrusel funcional.

El carrusel contiene una lista horizontal de módulos. Todo el contenido permanece en el DOM y puede recorrerse manualmente aunque JavaScript o autoplay no estén disponibles.

## 7. Wireframe textual

```text
NAV STICKY
Dentia | Producto | Precios | Seguridad | Demo | Iniciar sesión

HERO — vertical
Gestión odontológica conectada
Toda tu consulta odontológica en un solo lugar.
Subtítulo breve
[Solicitar demostración] [Conocer Dentia]
Validación Colombia / Chile
                          [Dashboard real]

PROBLEMA → RESULTADO — compacto
[Información dispersa] → [Dentia] → [Una sola operación]

TODO CONECTADO EN DENTIA — carrusel único
Navegación directa: Agenda · Pacientes · Historia · Odontograma ·
Tratamientos · Consentimientos · Finanzas · Seguimiento

┌────────────────────────────────────────────────────────────┐
│ Título + beneficio breve          Screenshot grande real   │
│ [Conocer el producto]                                      │
└────────────────────────────────────────────────────────────┘
[Anterior] [1 de 8] [Pausar/Reanudar] [Siguiente]

PARA QUIÉN ES — estable
[Odontólogo independiente] [Clínica / consultorio]

POR QUÉ DENTIA — estable
[Seguridad] [Implementación] [Acompañamiento]
En validación con odontólogos reales · Colombia · Chile

PRECIOS — estable
[Colombia] [Chile]
[Ver precios]

CTA FINAL — estable
Conoce cómo funcionaría Dentia en tu práctica.
[Solicitar demostración]

FOOTER
```

## 8. Carrusel 1 — Todo conectado en Dentia

### Estructura de cada slide

- eyebrow opcional de una o dos palabras;
- título de máximo 4–6 palabras;
- beneficio de máximo 2–3 líneas;
- una sola captura grande;
- enlace estable a `/producto` o a su ancla, sin CTA diferente por slide;
- indicador de posición y controles fuera del área que se mueve.

### Slides propuestos

| # | Título | Beneficio breve propuesto | Captura |
|---:|---|---|---|
| 1 | Agenda organizada | Visualiza citas y disponibilidad con el contexto necesario para atender. | `home-agenda.png` |
| 2 | Pacientes en contexto | Encuentra rápidamente la información administrativa y clínica de cada paciente. | `home-pacientes.png` |
| 3 | Historia clínica trazable | Registra evoluciones y consulta una línea de tiempo clínica clara. | `home-historia-clinica.png` |
| 4 | Odontograma clínico | Consulta hallazgos y tratamientos por pieza y superficie. | `home-odontograma.png` |
| 5 | Tratamientos conectados | Mantén visible lo planeado, realizado, pendiente y presupuestado. | `home-tratamientos.png` |
| 6 | Consentimientos gestionados | Prepara plantillas y acompaña el proceso documental desde Dentia. | `home-consentimientos.png` |
| 7 | Finanzas del paciente | Registra pagos, consulta saldos y conserva comprobantes. | `home-finanzas.png` |
| 8 | Seguimientos visibles | Identifica controles pendientes, próximos, vencidos o programados. | `home-seguimientos.png` |

Precisiones:

- `home-consentimientos.png` se describe como configuración y gestión, no como captura de firma;
- `home-presupuesto.png` permanece disponible en `/producto`; no se comprime junto a tratamientos dentro de la misma slide;
- `home-configuracion.png` se usa en la tarjeta de clínica, no en el carrusel;
- el dashboard permanece únicamente en el hero;
- Ortodoncia y Periodontograma quedan fuera.

## 9. Carrusel 2 — Decisión

No se recomienda un segundo carrusel `Así se ve Dentia en el día a día` en la home.

Sería redundante porque:

- usaría las mismas capturas del carrusel funcional;
- obligaría al visitante a aprender dos controles idénticos;
- aumentaría timers, movimiento y complejidad accesible;
- reduciría el ahorro vertical conseguido;
- competiría con `/producto`, que ya contiene el detalle visual.

Si en el futuro existen videos cortos, testimonios reales o casos de uso distintos de las funcionalidades, puede evaluarse una segunda experiencia. No debe crearse solo para reutilizar screenshots.

## 10. Autoplay

Comportamiento final aprobado:

- intervalo de **6 segundos**, dentro del rango aprobado de 5–7 segundos;
- inicia únicamente cuando el carrusel entra sustancialmente en viewport;
- mantiene un loop continuo del slide 8 al 1;
- pausa al pasar el puntero, enfocar un elemento, tocar/arrastrar, cambiar de pestaña o usar cualquier control;
- después de interacción manual reanuda automáticamente tras **10 segundos** sin interacción;
- `Pausar/Reanudar` permanece visible y conserva su estado mientras la sección esté montada;
- con `prefers-reduced-motion: reduce`, autoplay inicia desactivado y el cambio manual es instantáneo;
- sin JavaScript, la lista sigue siendo desplazable manualmente.

El autoplay es mejora opcional, no requisito para acceder al contenido.

## 11. Controles

Controles persistentes y fuera del contenido móvil:

- flecha `Anterior`;
- flecha `Siguiente`;
- botón `Pausar` / `Reanudar`;
- indicador textual `1 de 8`;
- ocho selectores directos con nombre accesible, presentados como labels cortos en desktop y puntos/botones en móvil;
- swipe/trackpad sobre la pista horizontal;
- teclas de flecha cuando el foco está dentro del carrusel;
- foco visible y área táctil mínima de 44 × 44 px.

El cambio automático no mueve el foco. `Anterior` y `Siguiente` siguen el mismo loop circular del autoplay, mientras `Pausar/Reanudar` conserva el control explícito del visitante.

## 12. Desktop

En anchos grandes:

- slide activa en layout de dos columnas, copy 35–40 % y screenshot 60–65 %;
- altura estable basada en la captura para evitar saltos;
- puede verse una pequeña porción de la siguiente tarjeta como pista de horizontalidad, sin reducir legibilidad;
- navegación de módulos encima o debajo, no superpuesta a la imagen;
- controles alineados al extremo inferior;
- máximo ancho igual al contenedor actual de 1240 px;
- screenshot sin pares ni miniaturas.

El carrusel no ocupa toda la altura del viewport ni secuestra la rueda vertical. Trackpad horizontal y controles son mejoras; el scroll vertical de la página sigue siendo normal.

## 13. Mobile

En móvil:

- una slide ocupa aproximadamente 88–92 % del ancho y deja asomar la siguiente;
- copy encima de la captura para conservar legibilidad;
- pista con `scroll-snap-type: x mandatory` o `proximity`, `overflow-x: auto` y contención horizontal;
- swipe nativo, sin interceptar el gesto vertical;
- controles de 44 px o más y estado `n de 8`;
- labels directos se convierten en una fila desplazable o puntos con nombres accesibles;
- screenshots mantienen proporción y no fijan una altura excesiva;
- autoplay se pausa al primer gesto táctil;
- ninguna regla aplica `overflow-x` al `body` ni provoca scroll horizontal global.

Las tarjetas de audiencia se apilan y las tres tarjetas de confianza pueden usar una cuadrícula de una columna. Precios continúa visible como sección normal.

## 14. Accesibilidad

Contrato mínimo:

- región con nombre, por ejemplo `aria-label="Funcionalidades principales de Dentia"`;
- encabezado `<h2>` estable y slides como lista semántica;
- `aria-roledescription="carrusel"` solo como complemento, no sustituto de semántica;
- botones nativos con labels completos;
- orden de tabulación predecible;
- autoplay pausado al foco y control de pausa siempre disponible;
- `aria-live="off"` durante avance automático para no interrumpir lectores de pantalla;
- anuncio discreto de posición solo tras interacción manual;
- ninguna información exclusiva del color, movimiento o screenshot;
- alt text específico ya aprobado para cada captura;
- contenido funcional utilizable con CSS/JS deshabilitado de forma razonable;
- reduced motion desactiva autoplay y smooth scrolling.

Los slides no deben contener múltiples enlaces repetidos que conviertan la navegación por teclado en ocho CTA idénticos. Un enlace estable `Ver todas las funcionalidades` puede permanecer fuera del track.

## 15. SEO

- El título y copy de cada módulo se renderizan del lado del servidor y permanecen en el DOM.
- No cargar el contenido textual bajo demanda al activar una slide.
- Mantener un único `<h1>` en el hero y un `<h2>` para la sección; cada slide usa `<h3>`.
- No usar imágenes como sustituto del texto indexable.
- Mantener metadata, canonical, sitemap y enlaces actuales.
- No ocultar slides inactivas con técnicas que eliminen su contenido del árbol de accesibilidad/DOM sin una alternativa.
- El carrusel no debe cambiar URLs ni generar páginas duplicadas.
- `/producto` continúa como destino detallado y enlazable.

La compactación elimina repetición sin reducir la cobertura semántica de agenda, pacientes, historia clínica, odontograma, tratamientos, consentimientos, finanzas y seguimiento.

## 16. Performance

El repositorio actual no incluye una librería de carruseles y no necesita agregarla.

Implementación recomendada para WEB-3B:

- componente React pequeño para índice, timer y pausa;
- CSS scroll snap para la pista;
- `IntersectionObserver` para ejecutar autoplay solo en viewport;
- `visibilitychange` para detener timers en background;
- `Next/Image`, ya usado por `ProductScreenshot`;
- solo hero con `priority`; slides con lazy loading;
- `sizes` específico para ancho de slide;
- sin duplicar imágenes para un loop infinito;
- no precargar las ocho capturas a máxima resolución;
- evitar listeners globales permanentes;
- medir LCP, CLS e INP antes y después.

El carrusel debe ser una mejora progresiva. Si falla el JavaScript, la pista horizontal y controles nativos de scroll siguen permitiendo explorar.

## 17. Screenshots a reutilizar

| Asset | Uso propuesto | Estado |
|---|---|---|
| `hero-dashboard.png` | Hero | Mantener |
| `home-agenda.png` | Slide Agenda | Carrusel |
| `home-pacientes.png` | Slide Pacientes | Carrusel; actualmente no aparece en home |
| `home-historia-clinica.png` | Slide Historia clínica | Carrusel |
| `home-odontograma.png` | Slide Odontograma | Carrusel |
| `home-tratamientos.png` | Slide Tratamientos | Carrusel |
| `home-presupuesto.png` | Detalle en `/producto` | No duplicar en home |
| `home-consentimientos.png` | Slide Consentimientos | Carrusel con descripción exacta de gestión/configuración |
| `home-finanzas.png` | Slide Finanzas | Carrusel |
| `home-seguimientos.png` | Slide Seguimientos | Carrusel |
| `home-configuracion.png` | Tarjeta Clínica/consultorio | Estática |

Las once capturas siguen siendo oficiales y útiles. La compactación cambia su distribución, no sus archivos ni su aprobación de privacidad.

## 18. Copy que se mantiene

Mantener sin cambio funcional, sujeto solo a corrección editorial menor:

- `Toda tu consulta odontológica en un solo lugar.`
- `Gestión odontológica conectada`.
- `Solicitar demostración`.
- `Conocer Dentia`.
- `En validación con prácticas odontológicas reales en Colombia y Chile.`
- idea central `Tu consulta no debería depender de cinco herramientas diferentes.`
- mensajes diferenciados para independiente y clínica;
- afirmaciones verificables de seguridad: roles, separación entre organizaciones, HTTPS y trazabilidad;
- precios iniciales públicos para Colombia y Chile;
- CTA final `Conoce cómo funcionaría Dentia en tu práctica.`

No agregar Ortodoncia, Periodontograma, IA, RIPS ni testimonios no aprobados.

## 19. Copy que conviene acortar

Propuestas para aprobación editorial; no son copy final:

| Bloque | Actual | Dirección de compactación |
|---|---|---|
| Hero | Párrafo de dos líneas largas con siete módulos | Mantener módulos, reducir a una frase de resultado y una de audiencia |
| Problema | Párrafo extenso más tres tarjetas | Una frase de problema y la transformación visual |
| Independiente | Lista de módulos repetida | Beneficio: operar la consulta sin fragmentación, incluso sin secretaria |
| Clínica | Usuarios, permisos, sedes y empresa en una frase larga | Beneficio: crecer con equipo y sedes bajo controles de acceso |
| Consentimientos | Dos párrafos más nota de imagen | Una frase funcional; nota de captura como caption breve |
| Seguridad | Párrafo más lista de cinco | Tarjeta resumen y enlace a `/seguridad`; conservar tres controles clave |
| Implementación | Dos tarjetas con headings largos | `Implementación progresiva` y `Acompañamiento real`, máximo 2–3 líneas |
| Precios | Introducción y dos descripciones semejantes | Heading, una frase y dos tarjetas con país/precio |

El carrusel debe evitar frases genéricas como “solución integral” y conservar beneficios concretos.

## 20. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Autoplay molesto | rechazo y pérdida de lectura | 6 s, pausas contextuales, pausa manual explícita y reduced motion |
| Información escondida | menor comprensión/SEO | todo el contenido en DOM, navegación directa y enlace a Producto |
| Capturas ilegibles | carrusel decorativo | una captura grande por slide y no pares |
| Doble carrusel redundante | más complejidad y movimiento | un único carrusel funcional |
| Scroll horizontal global | mala UX móvil | overflow solo en track, pruebas 320–430 px |
| Teclado confuso | barrera accesible | botones nativos, foco visible y orden estable |
| Ocho imágenes pesadas | LCP/INP degradados | Next/Image, lazy loading, sizes y sin loop duplicado |
| Timer en background | consumo y cambios inesperados | IntersectionObserver y visibilitychange |
| Copy comercial no aprobado | promesas incorrectas | reutilizar copy vigente y aprobar cualquier reducción |
| Anunciar módulos no disponibles | expectativa falsa | excluir Ortodoncia y Periodontograma |
| Exceso de compactación | pérdida de claridad | mantener secciones estables y validar con usuarios |

## 21. Roadmap de implementación

### WEB-3B — Prototipo aislado

- crear estructura compacta en entorno local;
- componente de carrusel ligero sin dependencia externa;
- usar las ocho slides y assets aprobados;
- implementar pausa, controles, swipe y reduced motion;
- no publicar.

### WEB-3B.1 — Validación visual y de contenido

- revisar desktop 1440/1366, tablet y móvil 390/320;
- confirmar copy acortado con Camilo;
- validar legibilidad de screenshots y altura estable;
- medir altura total real y comparar con baseline;
- validar autoplay activo por defecto con pausa accesible.

### WEB-3C — Publicación controlada

- commit aislado y CI verde;
- backup y rollback registrados;
- despliegue de la website sin modificar la aplicación clínica;
- verificación de assets, accesibilidad, SEO, cache y salud productiva.

### WEB-3D — Seguimiento posterior

- observar métricas de rendimiento y conversión;
- evaluar mejoras comerciales futuras con evidencia;
- mantener `app.dentiapro.com` fuera de cambios de la website.

### Gates para iniciar WEB-3B

- aprobar la recomendación de un solo carrusel;
- aprobar las ocho funcionalidades y su orden;
- aprobar el comportamiento de autoplay;
- aprobar la dirección de compactación del copy;
- confirmar que Ortodoncia y Periodontograma siguen fuera de la home.
