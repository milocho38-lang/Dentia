# PERIO-6.2 — Ajustes finales del piloto

## Alcance

PERIO-6.2 incorpora tres ajustes confirmados durante la segunda revisión del piloto: supuración en dientes naturales, mejor aprovechamiento horizontal en el modo expandido y un panel contextual sticky más compacto. No cambia lifecycle, RBAC, piloto, snapshots históricos ni almacenamiento.

## Semántica clínica de supuración

La supuración se registra por sitio como hallazgo binario en piezas `PRESENT` e `IMPLANT`:

- marcado: presente (`true`);
- no marcado: ausente (`false`);
- pieza `ABSENT`: no aplica y permanece `null`.

No se calcula un porcentaje global de supuración. El marcador existente se representa tanto en dientes naturales como en implantes. BOP, placa y furcación conservan exactamente la semántica binaria aprobada en PERIO-6.1.

El modelo ya disponía de `periodontal_sites.suppuration`; la limitación estaba en servicio y UI, por lo que no se requiere migración. Las nuevas versiones continúan usando `PERIODONTAL_EXAM_V3`, cuyo contrato declara `PRESENT_OR_IMPLANT_BINARY`. V1/V2 y sus hashes permanecen intactos y no se reinterpretan.

## Panel contextual compacto

El sticky utiliza una sola identificación, `Pieza <FDI>`, y organiza en dos líneas compactas:

- pieza/sitio activo, modo de captura y acción de guardado;
- estado dental, movilidad, furcación y acceso colapsado a la nota clínica.

Los indicadores se trasladaron al encabezado no sticky de la matriz. La nota no reserva altura mientras está cerrada. En desktop el objetivo contractual del panel cerrado es no superar 120 px; en tablet se permite envolver los controles en dos filas.

## Fit horizontal

El ajuste solo se activa con `Expandir periodontograma`:

- ancho mínimo clínico: 1120 px;
- gutter de etiquetas: 144 px;
- ancho máximo: 1600 px para evitar expansión excesiva en 1920 px;
- ancho normal: conserva 1200 px;
- scroll horizontal local: permanece disponible para 1280 px y viewports menores.

La reducción efectiva de las columnas clínicas es cercana al 5 %, sin alterar alturas de controles, navegación por teclado ni alineación matriz/gráfico.

## Regresiones cubiertas

- supuración natural e implante: selección, persistencia, snapshot e histórico;
- rechazo de datos de sitio en piezas ausentes;
- marcador gráfico de supuración en diente natural e implante;
- BOP, placa y furcación continúan binarios;
- panel sticky compacto, selección mandibular y nota colapsada;
- fit contractual de las 16 piezas a 1440 px en modo expandido;
- scroll local compartido y gráfico sincronizado;
- captura PD/GM, CAL, teclado, dirty state y batch save;
- timestamps sintéticos de USAGE anclados al periodo fijo de prueba.

## Compatibilidad

- Sin migración.
- Sin cambios de permisos, gate, tenant/sede o datos productivos.
- Sin reescritura de versiones finalizadas.
- Sin cambios en comparison, PDF, voz, diagnósticos o indicadores nuevos.
