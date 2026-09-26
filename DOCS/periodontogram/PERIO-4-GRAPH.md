# PERIO-4 — Gráfico periodontal e indicadores visuales

## Alcance

PERIO-4 incorpora una proyección gráfica del estado local del editor periodontal. No introduce persistencia, endpoints, permisos, migraciones, diagnóstico ni una segunda fuente clínica. El guardado continúa siendo el batch explícito de PERIO-2/3.

## Arquitectura SVG

La visualización usa SVG nativo, sin librería gráfica adicional. Cada arcada tiene un `viewBox` estable, ancho responsive y scroll horizontal local cuando el viewport no permite una lectura clínica suficiente. Esta decisión mantiene interacción accesible por sitio, curvas vectoriales, bajo costo para 192 sitios y una ruta futura hacia impresión sin implementar PDF en esta fase.

Las arcadas respetan el recorrido clínico:

- maxilar: `18 → 28`;
- mandíbula: `48 → 38`.

Cada pieza tiene tres coordenadas vestibulares y tres palatinas/linguales. Las piezas naturales muestran corona y raíces simplificadas; los implantes usan cuerpo roscado y marca `I`; los ausentes conservan FDI, pero muestran contorno discontinuo y no generan puntos ni curvas clínicas.

## Modelo geométrico

La línea punteada de cada cara representa `GM = 0`. La escala usa 5 unidades SVG por milímetro y una ventana visual de 6 mm coronales a 12 mm apicales.

- En maxilar, la dirección apical disminuye `y`.
- En mandíbula, la dirección apical aumenta `y`.
- `GM < 0` se desplaza hacia apical/raíz.
- `GM > 0` se desplaza hacia coronal/corona.
- Fondo de sondaje: desplazamiento apical `-GM + PD`.
- CAL permanece derivado como `PD - GM` y se presenta en el detalle; no se dibuja una tercera curva que reduzca legibilidad.

Los valores fuera de la ventana se fijan visualmente en el borde con un indicador `!`; el tooltip y el detalle conservan el valor numérico real. No se modifica ni recorta el dato clínico.

## Curvas y datos incompletos

La línea rosada representa GM y la azul el fondo de sondaje. Una línea solo conecta puntos medidos consecutivos. Un valor `null`, una pieza ausente o una combinación sin PD/GM termina el segmento; no se interpola a través de sitios no evaluados ni se fabrica un cero.

El examen parcial se identifica de forma discreta y mantiene `X/Y` de cobertura. Los denominadores de BOP y placa continúan considerando exclusivamente sitios evaluados según el contrato de PERIO-2.

## Marcadores

- Bolsa `PD >= 4 mm`: banda ámbar entre GM y fondo de sondaje, sin diagnóstico automático.
- BOP verdadero: círculo rojo.
- Placa verdadera: cuadrado violeta.
- Supuración verdadera: rombo verde azulado.
- Movilidad natural: badge `M0`–`M3`.
- Furcación M/D: puntos rellenos independientes en las raíces molares.
- `false`: sin marcador positivo, pero visible como “No” en el detalle.
- `null`: sin marcador y visible como “—/No evaluado”; nunca se trata como falso.

La leyenda combina forma y texto; la interpretación no depende únicamente del color.

## Interacción y sincronización

El gráfico recibe directamente `teeth`, la misma colección derivada del estado local de `RapidPeriodontalEditor`. Cambiar PD, GM, BOP, placa, supuración, estado dental, movilidad o furcación actualiza el SVG antes de guardar. El gráfico no conserva una copia clínica ni dispara requests.

Seleccionar una pieza o sitio actualiza el contexto activo del editor. En un borrador enfoca la medición PD/GM correspondiente al modo de captura; en una versión finalizada o histórica solo cambia la selección de lectura.

## Versiones históricas

`PeriodontogramWorkspace` entrega al editor el examen actualmente visualizado. Para V1/V2 histórica, ese examen se deriva exclusivamente del snapshot congelado mediante `historicalPeriodontalExam`. Por ello, gráfico, indicadores y detalle usan la misma versión y no consultan ni mezclan dientes de la versión vigente.

## Accesibilidad y responsive

Cada pieza y sitio SVG es operable con click, tap, Enter o espacio. Los sitios exponen una etiqueta que incluye pieza, cara, PD, GM, CAL, BOP, placa y supuración. Hover ofrece `<title>` nativo y click/tap abre un detalle textual persistente.

Desktop muestra ambas arcadas completas cuando hay espacio. Tablet y móvil usan scroll horizontal contenido en cada arcada; no fuerzan el gráfico completo a 390 px ni producen overflow global. No se implementa zoom/pan complejo.

## Rendimiento

Los modelos geométricos de las dos arcadas se memoizan a partir de un máximo fijo de 32 dientes/192 sitios. Las derivaciones son lineales y locales; no existe I/O, canvas, listener global ni recálculo backend.

## Pruebas

`periodontogram-graph-tests.mjs` cubre:

- dirección de GM ±2 en maxilar y mandíbula;
- fondo de sondaje y clamp de extremos;
- bolsa en PD 4 y ausencia de bolsa en PD 3;
- diente natural, ausente e implante;
- BOP, placa, supuración, movilidad y furcación;
- semántica `null` frente a `false`;
- cortes de curva sin interpolación;
- CAL y etiquetas accesibles;
- aislamiento gráfico entre snapshot V1 y V2;
- integración con el estado local del editor y la versión seleccionada.

## Diferido

Continúan fuera de alcance comparación/superposición de exámenes, PDF, diagnóstico, hueso alveolar avanzado, voz, zoom complejo, configurador de colores y anotaciones libres sobre SVG.
