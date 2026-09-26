# PERIO-4.1 — Composición clínica compacta del periodontograma

## Razón del rediseño

PERIO-4 demostró el contrato gráfico, la sincronización local y la integridad histórica, pero separaba el SVG de la captura y presentaba cada pieza como una tarjeta de 246 px. Ese patrón hacía difícil reconocer el conjunto como un periodontograma tradicional y permitía ver pocas piezas simultáneamente.

PERIO-4.1 conserva la semántica y el estado clínico de PERIO-1 a PERIO-4, pero cambia exclusivamente la composición frontend: cada arcada es ahora una matriz clínica única, compacta y alineada con su gráfico dental.

## Matriz clínica

Cada arcada usa un eje fijo de 16 posiciones dentales y 48 sitios por cara:

- maxilar: `18 17 16 15 14 13 12 11 | 21 22 23 24 25 26 27 28`;
- mandíbula: `48 47 46 45 44 43 42 41 | 31 32 33 34 35 36 37 38`.

La primera columna, de 176 px, contiene labels clínicos sticky. El área de datos mide 1024 unidades/píxeles lógicos: 64 por pieza y tres columnas de sitio por pieza. El SVG usa exactamente el mismo ancho y las mismas coordenadas, por lo que números, mediciones, dientes y curvas comparten el eje horizontal.

Las piezas ausentes mantienen su columna y FDI; nunca se colapsa el arco. La separación entre hemicuadrantes se marca después de la octava posición.

## Terminología visible

La UI principal usa nombres completos:

- Movilidad;
- Implante;
- Furcación;
- Sangrado al sondaje;
- Placa;
- Supuración;
- Margen gingival;
- Profundidad de sondaje;
- Nivel de inserción.

Los códigos internos `PD`, `GM`, `CAL` y `BOP` permanecen en el modelo y en los algoritmos, pero no son los labels principales. La selección de captura muestra “Profundidad”, “Margen” o “Profundidad + margen”.

## Geometría dental

El gráfico continúa siendo SVG nativo y ahora diferencia familias mediante geometrías propias:

- incisivos: corona estrecha y una raíz;
- caninos: cúspide marcada y raíz larga;
- premolares: corona bicúspide y una o dos raíces según arcada;
- molares: corona amplia y dos o tres raíces sugeridas según arcada.

El maxilar invierte verticalmente la geometría para orientar las raíces en sentido superior. La mandíbula mantiene las raíces en sentido inferior. Los implantes tienen cuerpo roscado y corona simplificada. Los ausentes conservan el espacio con contorno discontinuo y una X.

Furcación mesial/distal se representa mediante marcadores rellenos junto a raíces molares. Movilidad permanece visible en la matriz y en un badge discreto del diente seleccionado.

## Curvas y escala

Cada cara tiene una línea de referencia visible para `Margen gingival = 0`.

- Margen gingival negativo: desplazamiento apical hacia la raíz.
- Margen gingival positivo: desplazamiento coronal.
- Fondo de sondaje: posición del margen más la profundidad de sondaje en dirección apical.
- Nivel de inserción: valor derivado `PD - GM`, mostrado numéricamente sin tercera curva.

El margen gingival usa línea rosada y el fondo de sondaje línea azul. Una profundidad de 4 mm o más produce una ayuda ámbar entre ambas líneas y en la celda, sin inferir diagnóstico.

Valores `null` generan celda vacía e interrupción real de curva. No se interpolan sitios ni se transforma `null` en cero. Los valores fuera de escala se limitan solo en la proyección SVG y conservan el dato real en el detalle accesible.

## Interacción y sincronización

La matriz y el gráfico reciben la misma colección `teeth` derivada del estado local de `RapidPeriodontalEditor`. Cambiar profundidad o margen recalcula el SVG en el mismo render, antes de guardar y sin request al backend.

Se conserva la navegación PERIO-3:

- Enter avanza según el modo de captura;
- Shift+Tab retrocede de forma nativa;
- Backspace en una celda vacía vuelve al objetivo anterior;
- click/tap selecciona pieza o sitio;
- el guardado sigue siendo batch explícito;
- “Cambios sin guardar / Guardado” conserva el contrato vigente.

Un único panel contextual permite cambiar estado, movilidad, furcación y nota de la pieza seleccionada. Esos controles no se repiten en cada columna.

## Estados y marcadores

- Sangrado al sondaje: círculo lleno/vacío.
- Placa: cuadrado lleno/vacío.
- Supuración: rombo lleno/vacío, editable solo para implantes.
- Movilidad: valor `0`–`3` por pieza.
- Furcación: `M●/M○` y `D●/D○` en matriz; relleno visible en raíces.
- Implante: `I` y geometría roscada.
- Ausente: `×`, columna preservada y mediciones deshabilitadas.

Forma, texto y estado accesible acompañan al color.

## Responsive

Desktop prioriza densidad: el área completa de la arcada tiene un ancho mínimo total de 1200 px, incluida la columna de labels. En 1440/1920 px puede verse completa o prácticamente completa según el ancho disponible del workspace.

Tablet y móvil conservan scroll horizontal exclusivamente dentro de la arcada. Los labels permanecen sticky a la izquierda. No existe overflow horizontal global ni zoom/pan complejo.

## Accesibilidad

Números, celdas, piezas y sitios gráficos son operables por teclado. Los inputs exponen pieza, cara, sitio y nombre completo de la medición. Los marcadores booleanos comunican “sí”, “no” y “no evaluado” mediante `aria-label`, además de su forma.

El SVG mantiene `<title>` por sitio y un detalle textual persistente después de seleccionar un punto. Versiones finalizadas e históricas reutilizan la misma composición con controles deshabilitados.

## Integridad histórica

No se modifica backend, esquema, lifecycle, hash ni persistencia. La visualización histórica continúa recibiendo exclusivamente el snapshot seleccionado mediante `historicalPeriodontalExam`; no mezcla datos de la versión actual ni produce escrituras por lectura.

## Pruebas

Las suites `periodontogram-graph-tests.mjs` y `periodontogram-compact-layout-tests.mjs` verifican:

- 16 posiciones por arcada y orden FDI;
- grilla compacta de 48 sitios;
- labels sticky y terminología completa;
- familias incisivo, canino, premolar y molar;
- geometría de implante y espacio de ausente;
- dirección GM maxilar/mandibular;
- movimiento del fondo de sondaje con PD;
- CAL numérico;
- huecos por medición ausente;
- marcadores BOP, placa y supuración;
- movilidad y furcación;
- selección celda/pieza;
- navegación rápida;
- snapshots históricos;
- ausencia de canvas y de diagnóstico automático.

## Fuera de alcance

Comparación de versiones, PDF, voz, 3D, diagnóstico, clasificación periodontal, índices adicionales y modelado óseo avanzado permanecen diferidos.
