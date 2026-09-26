# PERIO-4.2 — Visibilidad y lectura clínica del gráfico periodontal

## Alcance

PERIO-4.2 conserva sin cambios funcionales la matriz compacta aprobada en
PERIO-4.1 y corrige exclusivamente la integración visual del gráfico. No cambia
el backend, el modelo clínico, el ciclo de vida, los hashes ni las migraciones.

## Causa raíz

El contenedor del SVG declaraba `col-span-48`, pero esa utilidad no existe en el
CSS generado por la configuración Tailwind del frontend. En la grilla compuesta
por una columna de etiquetas y 48 columnas clínicas, el navegador ubicaba el
SVG en una sola columna de sitio. El gráfico sí estaba montado y recibía datos,
pero quedaba comprimido a aproximadamente 1/48 del ancho clínico útil.

Además, un único SVG combinaba las caras vestibular y palatina/lingual entre
ambas matrices, debilitando la relación inmediata entre valores y curvas.

## Corrección

- El wrapper del gráfico usa `grid-column` explícito para ocupar las 48 columnas.
- Matriz y SVG comparten las constantes de 16 piezas, 3 sitios por cara, 48
  columnas, 64 unidades por pieza y 1024 unidades por arcada.
- Cada cara tiene su gráfico inmediatamente después de sus filas clínicas,
  dentro del mismo scroller horizontal.
- El eje X de cada sitio usa 1/6, 1/2 y 5/6 del ancho de su pieza.
- La referencia `Margen gingival 0` queda junto a la unión corona/raíz.
- Margen gingival usa línea continua; fondo de sondaje usa línea discontinua.
- Los sitios sin evaluación y las piezas ausentes interrumpen las curvas.
- Implantes, ausencias, familias dentales, movilidad, furcación, sangrado,
  placa, supuración y profundidades de 4 mm o más conservan representación
  gráfica propia.

## Actualización inmediata e histórico

El SVG se deriva directamente del estado local `drafts`; cambiar margen o
profundidad provoca un nuevo render sin guardar ni consultar el backend. Las
versiones históricas siguen recibiendo exclusivamente los dientes del snapshot
seleccionado y permanecen en modo de solo lectura.

## Revisión clínica pendiente

Las pruebas automatizadas validan geometría, dirección, gaps, integración y
compilación. La aprobación visual final corresponde a la revisión manual del
odontólogo en el preview local.
