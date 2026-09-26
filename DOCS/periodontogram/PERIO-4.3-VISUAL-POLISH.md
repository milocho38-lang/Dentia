# PERIO-4.3 — Pulido visual final del gráfico periodontal

## Objetivo

Mejorar la legibilidad clínica del gráfico periodontal sin alterar la matriz de captura, el modelo, el API, el lifecycle, el versionado ni la seguridad definidos en PERIO-1 a PERIO-4.2.

## Problemas visuales corregidos

- Las líneas clínicas tenían demasiado peso frente a los dientes y marcadores.
- La etiqueta del margen gingival cero competía con el área anatómica del gráfico.
- Los marcadores simultáneos de sangrado, placa y supuración podían superponerse.
- Las siluetas dentales eran pequeñas respecto del área útil disponible.
- Movilidad y furcación necesitaban una posición más inequívoca.
- La leyenda no explicitaba implantes ni furcación.

## Ajustes aplicados

### Curvas clínicas

- Margen gingival: línea continua rosa oscuro de 1,6 px.
- Fondo de sondaje: línea azul discontinua de 1,6 px.
- Extremos y uniones redondeados.
- Los puntos aislados usan un radio discreto de 1,9 px.
- Los segmentos continúan cortándose ante valores nulos; no se interpola información clínica ausente.
- La ayuda visual de bolsas de 4 mm o más conserva su semántica y usa una banda ámbar más tenue.

### Referencia de margen gingival

La línea `Margen gingival = 0` permanece dentro del SVG como referencia horizontal, pero su texto visible se trasladó al gutter izquierdo de cada fila gráfica. Así no cubre dientes ni curvas.

### Dientes y marcadores

- Dientes naturales e implantes aumentaron 12 %, dentro del rango aprobado.
- Se mantienen siluetas diferenciadas para incisivos, caninos, premolares y molares.
- Los implantes conservan una forma y color propios.
- Las piezas ausentes permanecen discretas y sin mediciones clínicas.
- Sangrado, placa y supuración ocupan carriles verticales distintos y usan formas diferentes.
- Movilidad se ubica hacia corona y furcación hacia raíces para reducir ambigüedad.

### Leyenda

La única leyenda del periodontograma incluye:

- Margen gingival.
- Fondo de sondaje.
- Sangrado al sondaje.
- Placa.
- Supuración.
- Bolsa ≥ 4 mm.
- Implante.
- Furcación.

## Antes y después conceptual

| Aspecto | Antes | PERIO-4.3 |
| --- | --- | --- |
| Curvas | Mayor peso visual y quiebres dominantes | Trazos finos con uniones redondeadas y los mismos puntos clínicos |
| Sitios sin dato | Gap real | Gap real, sin suavizado ni interpolación |
| Referencia GM=0 | Texto sobre el área anatómica | Texto en el gutter y línea de referencia dentro del gráfico |
| Dientes | Presencia visual reducida | Escala 1,12 conservando centro X y alineación clínica |
| Hallazgos por sitio | Marcadores próximos entre sí | Carriles verticales y formas independientes |
| Movilidad/furcación | Cercanas a otros hallazgos | Movilidad hacia corona y furcación hacia raíces |
| Leyenda | Cobertura parcial | Una leyenda estable con los ocho elementos aprobados |

## Responsive

- A 1280, 1440 y 1920 px se conserva la misma grilla clínica; el contenedor aprovecha el ancho disponible sin alterar las 48 posiciones por cara.
- En tablet, la arcada mantiene un ancho clínico mínimo de 1200 px y utiliza scroll horizontal local compartido por matriz y gráfico.
- Los labels permanecen sticky en un gutter de 176 px y no se desplazan sobre las primeras columnas.
- La interacción táctil utiliza los mismos hit targets del SVG y no depende de `hover`.

## Contratos preservados

- La grilla mantiene 48 columnas de sitios y scroll horizontal compartido por arco.
- El gráfico usa exactamente los mismos dientes del borrador o de la versión histórica mostrada.
- Selección por clic, tap, Enter y barra espaciadora sigue activa.
- La consulta de versiones históricas continúa estrictamente en solo lectura.
- No se modificaron backend, persistencia, snapshots, hashes, lifecycle, RBAC ni aislamiento tenant.
- No se agregaron dependencias.

## Validación

El contrato automatizado verifica peso y continuidad de líneas, ubicación del margen cero, escala dental, separación de marcadores, leyenda única, alineación con la matriz, interacción por teclado y compatibilidad histórica. La aprobación visual final requiere revisión manual del preview de producción a 1280, 1440, 1920 y ancho tablet.
