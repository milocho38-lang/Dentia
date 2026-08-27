# HC1/HC2 — Historia clínica simplificada y tipografía documental

## Decisión funcional

La captura inicial utiliza una anamnesis amplia, un texto libre de hábitos y un texto libre de antecedentes odontológicos. Los campos estructurados anteriores no se eliminan: permanecen disponibles como información histórica separada y se incluyen en la exportación.

Los antecedentes médicos son registros repetibles con nombre, observación opcional, estado activo/inactivo, fecha y autor. Sus transiciones se auditan y los registros activos continúan alimentando las alertas clínicas junto con alergias y medicamentos.

El comportamiento de las evoluciones clínicas no se modifica.

## Exportación

La historia clínica se exporta a PDF desde datos tenant-scoped e incluye institución, paciente, historia inicial, información histórica, antecedentes, alergias, medicamentos, odontograma estructurado, tratamientos/procedimientos sin valores financieros y evoluciones firmadas con sus adendas. La generación es en memoria y registra `CLINICAL_HISTORY_EXPORTED` con formato, tamaño y SHA-256.

La representación actual del odontograma en el PDF agrupa los eventos confirmados por pieza y muestra superficies con etiquetas clínicas legibles. El mapa gráfico de cinco caras queda como mejora futura; esta limitación se conserva únicamente en documentación técnica y no se expone en documentos entregables al paciente.

Los títulos usan el color institucional configurado cuando alcanza contraste de texto AA sobre blanco. Los colores demasiado claros se oscurecen proporcionalmente solo durante el render para conservar su identidad y legibilidad; el valor persistido de la empresa no se altera.

Las fechas de generación se presentan en lenguaje humano y en la zona horaria efectiva de la sede o empresa. Los antecedentes, alergias, medicamentos y superficies se muestran mediante etiquetas humanas y omiten separadores correspondientes a datos ausentes.

Las evoluciones se humanizan exclusivamente durante el render: fecha clínica localizada, identidad profesional canónica y estado legible. Los timestamps, estados y snapshots almacenados permanecen intactos. Las adendas se presentan debajo de su evolución con fecha, profesional, motivo y contenido, sin modificar sus reglas de inmutabilidad.

La información del modelo anterior permanece en la sección `Información histórica preservada`, separada entre datos iniciales, hábitos y antecedentes odontológicos. Un catálogo central traduce las claves conocidas; las claves desconocidas reciben un fallback sin `snake_case`. Solo los valores booleanos inequívocos (`YES/NO`, `TRUE/FALSE`) se presentan como `Sí/No`; todo texto libre se conserva literalmente. Los sentinels técnicos de procedimientos generales no se muestran al paciente.

En antecedentes médicos, `presente` y `estado` conservan semánticas independientes. Solo `presente = SI` junto con `estado = activo` representa un antecedente clínico vigente. Las respuestas `NO` y `DESCONOCIDO` del cuestionario fijo histórico se conservan sin mutación y se muestran en una sección histórica de solo lectura; nunca se presentan como alertas ni como antecedentes positivos en la interfaz o el PDF.

## Tipografía de documentos

Cada empresa elige una tipografía desde una lista cerrada. No se aceptan archivos, CSS, rutas ni URLs. Las familias no incorporadas en ReportLab usan un fallback métrico seguro (Helvetica o Times) y conservan su stack equivalente en la vista previa web.

La configuración se aplica a documentos nuevos. Los PDFs históricos son inmutables y los documentos firmados conservan la tipografía en su snapshot institucional.
