# C019A4-LIB1 — Revisión humana de equivalencia

Este paquete permite revisar de forma legible la equivalencia entre el PDF fuente aprobado y las versiones normalizadas en Dentia.

- Resultado inicial de todas las versiones normalizadas: `PENDING`.
- La fuente original se considera aprobada para Colombia y Chile.
- Ninguna versión normalizada queda aprobada automáticamente por este documento.
- Método de extracción: Apple PDFKit vía Swift local, sin OCR.

## Revisión de variantes Colombia y Chile

Cada documento tiene variantes independientes `CO / es-CO` y `CL / es-CL`. El contenido clínico base debe permanecer equivalente; las diferencias esperadas son país, locale, identificador y hash normalizado.

## 01. CERTIFICADO DE ASISTENCIA

- Código: `CERT_ASISTENCIA`
- Categoría: Administrativo
- Páginas fuente: 1–1
- Especialidad: General
- Firmante: `ADMINISTRATIVE_RECORD`
- Resultado: `PENDING`
- Fragmento SHA-256: `2fb5e67fd7048be1374d84d3585e727d136c003cba821ae66b4a36627b3dd3a6`

### Texto fuente relevante

```text
[Página 1]
CERTIFICADO DE ASISTENCIA
Este certificado indica que el usuario _________________, rut: _________________es paciente activo
de la clínica y asistió:
El dia ____ de ________ del __________ a dependencias de la Clinica Dental Seis, ubicada en
Avenida España 105, Curicó.
Se emite el presente documento a solicitud del paciente para los fines que estime convenientes.
______________________________________
CLINICA DENTAL SEIS
```

### Texto normalizado CO / es-CO

```markdown
# Certificado de asistencia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 1]
CERTIFICADO DE ASISTENCIA
Este certificado indica que el usuario _________________, rut: _________________es paciente activo
de la clínica y asistió:
El dia ____ de ________ del __________ a dependencias de la {{company.name}}, ubicada en
{{site.address}}, {{site.city}}.
Se emite el presente documento a solicitud del paciente para los fines que estime convenientes.
______________________________________
{{company.name}}

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `CLINICA DENTAL SEIS` → `{{company.name}}`
- `Clinica Dental Seis` → `{{company.name}}`
- `Avenida España 105, Curicó` → `{{site.address}}, {{site.city}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

No se detectaron líneas por palabra clave; revisar texto completo.

### Referencias institucionales sustituidas

- `CLINICA DENTAL SEIS` → `{{company.name}}`
- `Clinica Dental Seis` → `{{company.name}}`
- `Avenida España 105, Curicó` → `{{site.address}}, {{site.city}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CERT_ASISTENCIA-CO`, país `CO`, locale `es-CO`, hash `0d0382ff24709632b77703dc8d99e9ab6680f6a052c70d51d96a58afe38b3675`.
- CL: id lógico `CERT_ASISTENCIA-CL`, país `CL`, locale `es-CL`, hash `86e993683d311b82dbf3f197f554e65f874c378e90cbea37199ad745f20ba3b3`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 02. CONSENTIMIENTO INFORMADO DE BLANQUEAMIENTO DENTAL

- Código: `CONS_BLANQUEAMIENTO`
- Categoría: Consentimientos clínicos
- Páginas fuente: 2–2
- Especialidad: Estetica
- Firmante: `ADULT_OR_REPRESENTATIVE`
- Resultado: `PENDING`
- Fragmento SHA-256: `497f4db150ef72b142886bb581e21cbbe439d619017a177aeed14929cbd3ec93`

### Texto fuente relevante

```text
[Página 2]
CONSENTIMIENTO BLANQUEAMIENTO DENTAL
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
El blanqueamiento dental es un procedimiento odontológico que tiene por objetivo aclarar el color del
diente utilizando agentes químicos como el peróxido de hidrógeno o carbamida sobre la superficie del
diente. El beneficio principal es la satisfacción del paciente, mejorando la estética de su sonrisa y por
consecuencia su autoestima o comodidad.
El blanqueamiento clínico o en el hogar mediante cubetas y gel blanqueador NO se recomiendan en
embarazadas ni menores de 18 años.
Este procedimiento debe ser realizado en bocas sanas, por lo que, si el paciente presenta alguna
patología como caries, absceso, sensibilidad cervical, fractura, entre otros, deberá resolver sus
patologías antes de realizar el tratamiento.
Dentro de los riesgos de un blanqueamiento está, entre otras, la sensibilidad dental, la cual suele ser
reversible, de forma contraria se podría necesitar tratamiento endodóntico (conducto) y ser derivado.
El resultado del blanqueamiento no es predecible, en promedio se disminuye 4-5 tonos del tono del
paciente. Su durabilidad es variable ya que depende de la alimentación y hábitos del paciente, los
alimentos como café, vino, té, colorantes o hábitos como el cigarro influyen directamente en su
duración, se recomienda evitarlos durante la primera semana posterior al blanqueamiento e idealmente
eliminarlos o disminuirlos.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que este tratamiento consta de dos sesiones necesarias para estabilizar el color y que en
caso de no estar conforme con el resultado y como garantía por este tratamiento puedo solicitar una
tercera sesión, además comprendo que en caso de existir sensibilidad post tratamiento el odontólogo
deberá aplicar un producto desensibilizante como parte de la garantía de dicho tratamiento en
clínica DENTAL SEIS.
Entiendo que estas garantías las perderé si frente a cualquier urgencia sobre dicho tratamiento
consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en
clínica DENTAL SEIS para hacer valer mi garantía como paciente, por lo que pasaré por una
contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si
consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá
devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de blanqueamiento dental

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 2]
CONSENTIMIENTO BLANQUEAMIENTO DENTAL
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
El blanqueamiento dental es un procedimiento odontológico que tiene por objetivo aclarar el color del
diente utilizando agentes químicos como el peróxido de hidrógeno o carbamida sobre la superficie del
diente. El beneficio principal es la satisfacción del paciente, mejorando la estética de su sonrisa y por
consecuencia su autoestima o comodidad.
El blanqueamiento clínico o en el hogar mediante cubetas y gel blanqueador NO se recomiendan en
embarazadas ni menores de 18 años.
Este procedimiento debe ser realizado en bocas sanas, por lo que, si el paciente presenta alguna
patología como caries, absceso, sensibilidad cervical, fractura, entre otros, deberá resolver sus
patologías antes de realizar el tratamiento.
Dentro de los riesgos de un blanqueamiento está, entre otras, la sensibilidad dental, la cual suele ser
reversible, de forma contraria se podría necesitar tratamiento endodóntico (conducto) y ser derivado.
El resultado del blanqueamiento no es predecible, en promedio se disminuye 4-5 tonos del tono del
paciente. Su durabilidad es variable ya que depende de la alimentación y hábitos del paciente, los
alimentos como café, vino, té, colorantes o hábitos como el cigarro influyen directamente en su
duración, se recomienda evitarlos durante la primera semana posterior al blanqueamiento e idealmente
eliminarlos o disminuirlos.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que este tratamiento consta de dos sesiones necesarias para estabilizar el color y que en
caso de no estar conforme con el resultado y como garantía por este tratamiento puedo solicitar una
tercera sesión, además comprendo que en caso de existir sensibilidad post tratamiento el odontólogo
deberá aplicar un producto desensibilizante como parte de la garantía de dicho tratamiento en
clínica {{company.name}}.
Entiendo que estas garantías las perderé si frente a cualquier urgencia sobre dicho tratamiento
consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en
clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una
contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si
consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá
devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`18 años`

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- Dentro de los riesgos de un blanqueamiento está, entre otras, la sensibilidad dental, la cual suele ser
- caso de no estar conforme con el resultado y como garantía por este tratamiento puedo solicitar una
- deberá aplicar un producto desensibilizante como parte de la garantía de dicho tratamiento en
- Entiendo que estas garantías las perderé si frente a cualquier urgencia sobre dicho tratamiento
- clínica DENTAL SEIS para hacer valer mi garantía como paciente, por lo que pasaré por una
- consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_BLANQUEAMIENTO-CO`, país `CO`, locale `es-CO`, hash `e0a6d318a1b95ba48c33437666205efa3102f6e37b5545219f10de82fffa9145`.
- CL: id lógico `CONS_BLANQUEAMIENTO-CL`, país `CL`, locale `es-CL`, hash `a866f7d91dfac7f6d44b2e6a9dfe41988fe4ab68046b54a202722d87f63bf083`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 03. CONSENTIMIENTO INFORMADO DE ORTODONCIA

- Código: `CONS_ORTODONCIA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 3–5
- Especialidad: Ortodoncia
- Firmante: `ADULT_OR_REPRESENTATIVE`
- Resultado: `PENDING`
- Fragmento SHA-256: `1f14b8bfaa782f3dacf4a6842ec756467f7618bf6236c3a4fa696753d9aa9fbf`

### Texto fuente relevante

```text
[Página 3]
CONSENTIMIENTO DE ORTODONCIA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas. El tratamiento de ortodoncia consiste en la
corrección y alineación de los dientes mejorando la oclusión (mordida), función masticatoria, estética y
autoestima del paciente. Esto ocurre mediante la utilización de aparatos metálicos o estéticos ya sean
fijos o removibles. El éxito y resultado final del tratamiento está estrechamente ligado a la colaboración
y responsabilidad del paciente/apoderado, asistir a sus controles mensuales, seguir indicaciones del
dentista y equipo médico, consultar en momentos de urgencia, cuidar hábitos de alimentación e
higiene, entre otros. La ausencia reiterada sin previo aviso a los controles de ortodoncia facultara al
ortodoncista para terminar con el tratamiento y dar el alta disciplinaria al paciente, exonerando de
cualquier responsabilidad futura al especialista. Se me ha explicado que por la longevidad del
tratamiento y su complejidad es posible que durante el mismo tratamiento se necesiten acciones
adicionales de otros especialistas, lo que se deberá presupuestar, asumiendo el costo y no están
incluidos en lo pagado por ortodoncia. (futuras limpiezas, nuevas caries, cambios de obturaciones,
coronas, micro tornillos, implantes, etc.).
A continuación, se indican las condiciones: antes del tratamiento, durante el tratamiento y posterior al
tratamiento.
Antes del tratamiento: Para comenzar un tratamiento de ortodoncia, el paciente debe tener su boca
100% sana, libre de infecciones y tener el alta de la unidad de odontología general y/o algún
especialista en particular. El paciente pasará, primero por un estudio previo a la instalación de
ortodoncia, el llamado estudio de ortodoncia, en la que el odontólogo reunirá toda la información para
planificar y pronosticar el caso clínico. Esta información se puede recabar mediante una anamnesis e
historia clínica, estudio radiográfico (pack de ortodoncia), scanner, exámenes complementarios,
estudio cefalométrico, impresiones preliminares en yeso, montaje en articulador, fotografía clínica,
entre otros. El ortodoncista buscará planificar en número y tiempo de controles, no obstante, en la
práctica pueden ser menos o más controles de los planificados ya que la evolución dental depende en
gran parte de factores directamente relacionados al paciente. Si se extiende el tiempo y resultan más
controles de los planificados, el paciente asumirá el costo de cada control mensual, pues se paga
mensualmente por control activo hasta terminar el tratamiento. Si comencé mi tratamiento en otra
institución, deberé de traer toda la información que pueda (historial clínico) para cambiar de centro
odontológico, asumiendo en la mayoría de los casos que deberé retirar mi ortodoncia antigua, realizar
pack de radiografías de ortodoncia, ser evaluado en la unidad de diagnóstico y odontología general,
recibir presupuestos y plan de tratamiento, realizar todo tipo de tratamiento previo hasta obtener el alta
y luego ser derivado a ortodoncia para estudio e instalación de nuevos aparatos de ortodoncia.
Durante el tratamiento: El paciente deberá utilizar cepillos especiales para limpiar sus dientes y los
aparatos de ortodoncia (cepillo monotip, ortodontic e interproximales). La ausencia a controles de
ortodoncia retrasará el tratamiento en el tiempo planificado y podrá ser necesario agregar acciones
adicionales no contempladas en el presupuesto y diagnóstico inicial. La reposición de un bracket de
ortodoncia desalojado tiene costo adicional, que debe asumir el paciente, ya que se desalojan por

[Página 4]
cuidados, factores biológicos y personales del usuario. Si un bracket se suelta reiteradas veces es
atribuible a no seguir las indicaciones por parte del paciente. Indicaciones especificadas en el
consentimiento como prohibiciones. La urgencia de ortodoncia no tiene costo siempre que el paciente
haya sido responsable con sus controles, por ej. si ocurre el desalojo de un Bracket, la urgencia será
solucionar la molestia o laceración de los tejidos retirando el bracket, pero en ningún caso instalándolo
inmediatamente ya que deberá ser instalado por el especialista en su próximo control, solo el
ortodoncista conoce la posición correcta. En caso de movimiento del arco y/o pinchazo en el extremo
de este con el tejido blando, la urgencia será mover a su posición original el arco o en su defecto cortar
la punta que causa molestias, si necesitará otra acción, deberá esperar a su próximo control. Podrán
ser necesarias extracciones o procedimientos no planificados o previstos en un inicio, los que se
presupuestarán y deberán ser pagados por el paciente. Los cambios no planificados ocurren debido a
que todos los pacientes son distintos y el tratamiento evoluciona según a elementos biológicos,
metabólicos, personales e individuales de cada usuario. Está prohibido comer alimentos duros,
pegajosos y en grandes cantidades (como en bloque) ya que su tamaño puede presionar los aparatos
de ortodoncia y arcos, desalojándolos o rompiéndolos. Alimentos tales como, maní, frutos secos,
chicles, masticables, calugones, morder frutas, se recomienda picarlas o cortarlas en trozos pequeños,
dulces, gomitas, cabritas de maíz, papas fritas, frituras envasadas, entre otros. Está prohibido tener
malos hábitos, onicofagia (morderse las uñas), fumar, no cepillar los dientes mínimos 3 veces al día,
ideal después de cada comida, la mala higiene, morder elementos duros con los dientes como lápices,
cubiertos, no se debe inspeccionar con mondadientes, tenedores, clips, o algún otro elemento los
Brackets para tratar de retirar alimento alojado, para eso se deben utilizar los cepillos
correspondientes. Es frecuente sentir sensibilidad, molestias, dolor, sensación de dientes sueltos,
laceración de mucosas, irritación de tejidos blandos (al comienzo del tratamiento), pellizcar o morderse
labios o mucosa yugal (mejillas), presión dental, dolor articular, dolor muscular, dolor de cabeza,
reabsorción y remodelación radicular (raíces) para lo que es fundamental el seguimiento y control
mediante radiografías, las que deben ser pagadas por el paciente.
Posterior al tratamiento: Terminada la etapa de controles, para finalizar el tratamiento, se debe realizar
el retiro de ortodoncia superior y/o inferior (aparatos metálicos), higienización por arcada (retiro de
composite y pegamento), contención superior e inferior, ya sea fija o removible y controles periódicos
para la contención. El uso de la contención y seguimiento de indicaciones es de exclusiva
responsabilidad del paciente lo que influirá en la mantención del tratamiento de ortodoncia, es decir,
aquellos pacientes que no usan la contención, no siguen indicaciones o no asisten a sus controles de
contención, sus dientes vuelven por naturaleza y genética a desordenarse o enchuecarse, perdiendo
todo el trabajo ganado. Si el paciente necesita utilizar nuevamente ortodoncia para modificar y mejorar
su estética, debe ser todo pagado por el paciente desde el inicio, como si se atendiera por primera vez.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en
clínica DENTAL SEIS, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto
primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica
DENTAL SEIS para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría
dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto
primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución
de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo,
entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento

[Página 5]
correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto
debidamente antes de realizarlo.
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de ortodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 3]
CONSENTIMIENTO DE ORTODONCIA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas. El tratamiento de ortodoncia consiste en la
corrección y alineación de los dientes mejorando la oclusión (mordida), función masticatoria, estética y
autoestima del paciente. Esto ocurre mediante la utilización de aparatos metálicos o estéticos ya sean
fijos o removibles. El éxito y resultado final del tratamiento está estrechamente ligado a la colaboración
y responsabilidad del paciente/apoderado, asistir a sus controles mensuales, seguir indicaciones del
dentista y equipo médico, consultar en momentos de urgencia, cuidar hábitos de alimentación e
higiene, entre otros. La ausencia reiterada sin previo aviso a los controles de ortodoncia facultara al
ortodoncista para terminar con el tratamiento y dar el alta disciplinaria al paciente, exonerando de
cualquier responsabilidad futura al especialista. Se me ha explicado que por la longevidad del
tratamiento y su complejidad es posible que durante el mismo tratamiento se necesiten acciones
adicionales de otros especialistas, lo que se deberá presupuestar, asumiendo el costo y no están
incluidos en lo pagado por ortodoncia. (futuras limpiezas, nuevas caries, cambios de obturaciones,
coronas, micro tornillos, implantes, etc.).
A continuación, se indican las condiciones: antes del tratamiento, durante el tratamiento y posterior al
tratamiento.
Antes del tratamiento: Para comenzar un tratamiento de ortodoncia, el paciente debe tener su boca
100% sana, libre de infecciones y tener el alta de la unidad de odontología general y/o algún
especialista en particular. El paciente pasará, primero por un estudio previo a la instalación de
ortodoncia, el llamado estudio de ortodoncia, en la que el odontólogo reunirá toda la información para
planificar y pronosticar el caso clínico. Esta información se puede recabar mediante una anamnesis e
historia clínica, estudio radiográfico (pack de ortodoncia), scanner, exámenes complementarios,
estudio cefalométrico, impresiones preliminares en yeso, montaje en articulador, fotografía clínica,
entre otros. El ortodoncista buscará planificar en número y tiempo de controles, no obstante, en la
práctica pueden ser menos o más controles de los planificados ya que la evolución dental depende en
gran parte de factores directamente relacionados al paciente. Si se extiende el tiempo y resultan más
controles de los planificados, el paciente asumirá el costo de cada control mensual, pues se paga
mensualmente por control activo hasta terminar el tratamiento. Si comencé mi tratamiento en otra
institución, deberé de traer toda la información que pueda (historial clínico) para cambiar de centro
odontológico, asumiendo en la mayoría de los casos que deberé retirar mi ortodoncia antigua, realizar
pack de radiografías de ortodoncia, ser evaluado en la unidad de diagnóstico y odontología general,
recibir presupuestos y plan de tratamiento, realizar todo tipo de tratamiento previo hasta obtener el alta
y luego ser derivado a ortodoncia para estudio e instalación de nuevos aparatos de ortodoncia.
Durante el tratamiento: El paciente deberá utilizar cepillos especiales para limpiar sus dientes y los
aparatos de ortodoncia (cepillo monotip, ortodontic e interproximales). La ausencia a controles de
ortodoncia retrasará el tratamiento en el tiempo planificado y podrá ser necesario agregar acciones
adicionales no contempladas en el presupuesto y diagnóstico inicial. La reposición de un bracket de
ortodoncia desalojado tiene costo adicional, que debe asumir el paciente, ya que se desalojan por

[Página 4]
cuidados, factores biológicos y personales del usuario. Si un bracket se suelta reiteradas veces es
atribuible a no seguir las indicaciones por parte del paciente. Indicaciones especificadas en el
consentimiento como prohibiciones. La urgencia de ortodoncia no tiene costo siempre que el paciente
haya sido responsable con sus controles, por ej. si ocurre el desalojo de un Bracket, la urgencia será
solucionar la molestia o laceración de los tejidos retirando el bracket, pero en ningún caso instalándolo
inmediatamente ya que deberá ser instalado por el especialista en su próximo control, solo el
ortodoncista conoce la posición correcta. En caso de movimiento del arco y/o pinchazo en el extremo
de este con el tejido blando, la urgencia será mover a su posición original el arco o en su defecto cortar
la punta que causa molestias, si necesitará otra acción, deberá esperar a su próximo control. Podrán
ser necesarias extracciones o procedimientos no planificados o previstos en un inicio, los que se
presupuestarán y deberán ser pagados por el paciente. Los cambios no planificados ocurren debido a
que todos los pacientes son distintos y el tratamiento evoluciona según a elementos biológicos,
metabólicos, personales e individuales de cada usuario. Está prohibido comer alimentos duros,
pegajosos y en grandes cantidades (como en bloque) ya que su tamaño puede presionar los aparatos
de ortodoncia y arcos, desalojándolos o rompiéndolos. Alimentos tales como, maní, frutos secos,
chicles, masticables, calugones, morder frutas, se recomienda picarlas o cortarlas en trozos pequeños,
dulces, gomitas, cabritas de maíz, papas fritas, frituras envasadas, entre otros. Está prohibido tener
malos hábitos, onicofagia (morderse las uñas), fumar, no cepillar los dientes mínimos 3 veces al día,
ideal después de cada comida, la mala higiene, morder elementos duros con los dientes como lápices,
cubiertos, no se debe inspeccionar con mondadientes, tenedores, clips, o algún otro elemento los
Brackets para tratar de retirar alimento alojado, para eso se deben utilizar los cepillos
correspondientes. Es frecuente sentir sensibilidad, molestias, dolor, sensación de dientes sueltos,
laceración de mucosas, irritación de tejidos blandos (al comienzo del tratamiento), pellizcar o morderse
labios o mucosa yugal (mejillas), presión dental, dolor articular, dolor muscular, dolor de cabeza,
reabsorción y remodelación radicular (raíces) para lo que es fundamental el seguimiento y control
mediante radiografías, las que deben ser pagadas por el paciente.
Posterior al tratamiento: Terminada la etapa de controles, para finalizar el tratamiento, se debe realizar
el retiro de ortodoncia superior y/o inferior (aparatos metálicos), higienización por arcada (retiro de
composite y pegamento), contención superior e inferior, ya sea fija o removible y controles periódicos
para la contención. El uso de la contención y seguimiento de indicaciones es de exclusiva
responsabilidad del paciente lo que influirá en la mantención del tratamiento de ortodoncia, es decir,
aquellos pacientes que no usan la contención, no siguen indicaciones o no asisten a sus controles de
contención, sus dientes vuelven por naturaleza y genética a desordenarse o enchuecarse, perdiendo
todo el trabajo ganado. Si el paciente necesita utilizar nuevamente ortodoncia para modificar y mejorar
su estética, debe ser todo pagado por el paciente desde el inicio, como si se atendiera por primera vez.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en
clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto
primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica
{{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría
dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto
primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución
de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo,
entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento

[Página 5]
correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto
debidamente antes de realizarlo.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- y responsabilidad del paciente/apoderado, asistir a sus controles mensuales, seguir indicaciones del
- cualquier responsabilidad futura al especialista. Se me ha explicado que por la longevidad del
- 100% sana, libre de infecciones y tener el alta de la unidad de odontología general y/o algún
- correspondientes. Es frecuente sentir sensibilidad, molestias, dolor, sensación de dientes sueltos,
- labios o mucosa yugal (mejillas), presión dental, dolor articular, dolor muscular, dolor de cabeza,
- responsabilidad del paciente lo que influirá en la mantención del tratamiento de ortodoncia, es decir,
- nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en
- DENTAL SEIS para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría
- primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_ORTODONCIA-CO`, país `CO`, locale `es-CO`, hash `383e210385fe4500f24ddc1c4623a2cd12b61ae2b2fda4cce8702b449826c7b7`.
- CL: id lógico `CONS_ORTODONCIA-CL`, país `CL`, locale `es-CL`, hash `fe363f50afad236f66a6198ee78e7ef0685bf9e1a46ecbda84af418608e561e8`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 04. EXENCIÓN DE GARANTÍA ODONTOLÓGICA

- Código: `CONS_NO_GARANTIA`
- Categoría: Constancias y reconocimientos
- Páginas fuente: 6–6
- Especialidad: General
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `4697cfba4edb0ce8594cf09ac5510f3085d0ca0f52a7a6d6e394abd402f6492c`

### Texto fuente relevante

```text
[Página 6]
CONSENTIMIENTO EXCENCION DE GARANTIA – NO GARANTÍA
PROCEDIMIENTO
_______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del estado de mi salud bucal y posibilidades de tratamiento asociadas.
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
Se me ha explicado que existen otros tratamientos ideales para mi patología, pero por decisión propia
y temas personales acepto realizar el procedimiento descrito anteriormente, del cual asumo todo tipo
de responsabilidad, costos y consecuencias que podrían surgir.
Entiendo que el procedimiento mencionado no se puede garantizar desde su aspecto clínico y
libero de cualquier tipo de responsabilidad a el o los odontólogo(s), clínica DENTAL SEIS y al personal
involucrado en este tratamiento; por lo que en el futuro NO tendré derecho a
garantías, devoluciones, reclamos ni demanda por el mismo.
FIRMA
```

### Texto normalizado CO / es-CO

```markdown
# Exención de garantía odontológica

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 6]
CONSENTIMIENTO EXCENCION DE GARANTIA – NO GARANTÍA
PROCEDIMIENTO
_______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del estado de mi salud bucal y posibilidades de tratamiento asociadas.
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
Se me ha explicado que existen otros tratamientos ideales para mi patología, pero por decisión propia
y temas personales acepto realizar el procedimiento descrito anteriormente, del cual asumo todo tipo
de responsabilidad, costos y consecuencias que podrían surgir.
Entiendo que el procedimiento mencionado no se puede garantizar desde su aspecto clínico y
libero de cualquier tipo de responsabilidad a el o los odontólogo(s), clínica {{company.name}} y al personal
involucrado en este tratamiento; por lo que en el futuro NO tendré derecho a
garantías, devoluciones, reclamos ni demanda por el mismo.
FIRMA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- CONSENTIMIENTO EXCENCION DE GARANTIA – NO GARANTÍA
- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del estado de mi salud bucal y posibilidades de tratamiento asociadas.
- de responsabilidad, costos y consecuencias que podrían surgir.
- libero de cualquier tipo de responsabilidad a el o los odontólogo(s), clínica DENTAL SEIS y al personal
- garantías, devoluciones, reclamos ni demanda por el mismo.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_NO_GARANTIA-CO`, país `CO`, locale `es-CO`, hash `2b207f500cb85773e17ac2985c76e011ad3cbe43125f35bd65daa93ed0431be9`.
- CL: id lógico `CONS_NO_GARANTIA-CL`, país `CL`, locale `es-CL`, hash `87e8e8cdf70c0ddeac763482f2b9a98ac6f6b030341dc03a740c574160cdf637`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 05. CONSENTIMIENTO INFORMADO DE CIRUGÍA ODONTOLÓGICA

- Código: `CONS_CIRUGIA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 7–7
- Especialidad: Cirugia
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `bdc17124e67c715f2053cff0cb3991eb15323a1d3b09278866941489a5f66c6f`

### Texto fuente relevante

```text
[Página 7]
__________________________________________________________________
CONSENTIMIENTO CIRUGÍA
PROCEDIMIENTO
___
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas. Puedo presentar posterior a una cirugía de
forma inmediata o tardía, inflamación, aumento de volumen, dolor, infección, alveolitis húmeda,
alveolitis seca, hemorragia, hematomas o equimosis. Menos frecuente puede ocurrir fractura dental o
de tejido óseo, alteración sensitiva de los nervios de forma temporal o definitiva, traslado o impulsión
de piezas dentales a otros sitios anatómicos (seno maxilar), comunicación buco sinusal por piezas que
tengan íntima relación anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos,
molestias en músculos o articulación temporo mandibular por mantener abierta la boca mucho tiempo,
dificultad para abrir la boca o masticar, fracturas de instrumentos.
Durante el procedimiento, existe la posibilidad de nuevos hallazgos clínicos y patológicos que no se
pudieron predecir mediante el examen clínico y radiográfico, cambiando el curso del tratamiento
inclusive llevando a realizar tratamientos adicionales, como una biopsia, eliminación de una masa
tumoral, enucleación de quistes, o aplicación de injertos e insumos biológicos, etc. Por lo que el
paciente deberá asumir el costo del nuevo presupuesto o la diferencia de este. Si el paciente viene
acompañado mientras está siendo operado, se le explicará a su tutor acompañante.
Se me ha explicado, en caso de faltar o ausentarme sin previo aviso (24 horas antes) a mi hora de
cirugía, los 30.000 de la reserva no serán devueltos, debiendo pagar nuevamente el valor de
reserva por programación de cirugía. De la misma forma si el doctor decide no llevar a cabo la cirugía
por no seguir las instrucciones explicadas en la evaluación de cirugía al NO tomar la pre-medicación
entregada antes del procedimiento quirúrgico o por NO traer/mostrar los exámenes complementarios
requeridos, habiendo sido de mi absoluta responsabilidad. Entiendo como paciente o tutor legal que
debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de
fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de cirugía odontológica

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 7]
__________________________________________________________________
CONSENTIMIENTO CIRUGÍA
PROCEDIMIENTO
___
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas. Puedo presentar posterior a una cirugía de
forma inmediata o tardía, inflamación, aumento de volumen, dolor, infección, alveolitis húmeda,
alveolitis seca, hemorragia, hematomas o equimosis. Menos frecuente puede ocurrir fractura dental o
de tejido óseo, alteración sensitiva de los nervios de forma temporal o definitiva, traslado o impulsión
de piezas dentales a otros sitios anatómicos (seno maxilar), comunicación buco sinusal por piezas que
tengan íntima relación anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos,
molestias en músculos o articulación temporo mandibular por mantener abierta la boca mucho tiempo,
dificultad para abrir la boca o masticar, fracturas de instrumentos.
Durante el procedimiento, existe la posibilidad de nuevos hallazgos clínicos y patológicos que no se
pudieron predecir mediante el examen clínico y radiográfico, cambiando el curso del tratamiento
inclusive llevando a realizar tratamientos adicionales, como una biopsia, eliminación de una masa
tumoral, enucleación de quistes, o aplicación de injertos e insumos biológicos, etc. Por lo que el
paciente deberá asumir el costo del nuevo presupuesto o la diferencia de este. Si el paciente viene
acompañado mientras está siendo operado, se le explicará a su tutor acompañante.
Se me ha explicado, en caso de faltar o ausentarme sin previo aviso (24 horas antes) a mi hora de
cirugía, los 30.000 de la reserva no serán devueltos, debiendo pagar nuevamente el valor de
reserva por programación de cirugía. De la misma forma si el doctor decide no llevar a cabo la cirugía
por no seguir las instrucciones explicadas en la evaluación de cirugía al NO tomar la pre-medicación
entregada antes del procedimiento quirúrgico o por NO traer/mostrar los exámenes complementarios
requeridos, habiendo sido de mi absoluta responsabilidad. Entiendo como paciente o tutor legal que
debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de
fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`24 horas`

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- forma inmediata o tardía, inflamación, aumento de volumen, dolor, infección, alveolitis húmeda,
- tengan íntima relación anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos,
- requeridos, habiendo sido de mi absoluta responsabilidad. Entiendo como paciente o tutor legal que
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_CIRUGIA-CO`, país `CO`, locale `es-CO`, hash `5b446c54e6938bd807479084f0e9159f0708231e3d66bf8294b36a07411748e1`.
- CL: id lógico `CONS_CIRUGIA-CL`, país `CL`, locale `es-CL`, hash `88f4c9cdde722c9877055e47ce3fd585dacb9f756e5887df5cd3017424838467`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 06. CONSENTIMIENTO DE DESTARTRAJE Y OPERATORIA DENTAL

- Código: `CONS_DESTARTRAJE_OPERATORIA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 8–9
- Especialidad: Operatoria
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `28c2523a5302d3cdc11c66880bd7a343e8c8c7ea827ecddeae39565f79539bd6`

### Texto fuente relevante

```text
[Página 8]
CONSENTIMIENTO DESTARTRAJE Y OPERATORIA DENTAL
Declaro haber informado de forma clara y veraz a el / la odontólogo/a tratante respecto a mi estado de
salud general, condiciones médicas u odontológicas, tratamientos previos y actuales, alergias,
cirugías previas y fármacos que utilizo o cualquier otro antecedente. El/la odontólogo/a tratante me ha
informado respecto a mi estado de salud bucal y resuelto mis dudas e inquietudes respecto al mismo.
Me ha explicado también los tratamientos propuestos junto a las ventajas y desventajas, al igual que
los riesgos, beneficios y posibles complicaciones en caso de realizar o no realizar el tratamiento
mencionado. Me ha informado respecto a la posible necesidad de uso de anestésicos, indicación de
fármacos, elementos de higiene u otras indicaciones que pudiesen ser necesarias para lograr los
objetivos del tratamiento.
El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro
dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía mediante el uso
de un instrumento que emite vibraciones y agua en spray. Usualmente el destartraje no es un
procedimiento doloroso, sin embargo, esto es subjetivo por lo que en algunos casos se podrían
presentar sensibilidad dental o molestias durante o posterior al mismo. En ocasiones el depósito de
tártaro también puede ubicarse bajo la encía, necesitando complementar el destartraje supragingival
con uno subgingival. El uso ultrasonido por sí mismo no daña el tejido dental ni tampoco es capaz de
desalojar una obturación (tapadura) o corona antigua que se encuentre en buenas condiciones, si esto
ocurriera significa que ya existe un daño previo, que no se encuentra en buen estado y probablemente
haya perdido su adhesión; en caso de ocurrir, implica la necesidad de realizar el recambio completo de
la obturación, que deberá ser presupuestada y costeada por mí como paciente. La duración de la
limpieza está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un
tratamiento que cuente con algún tipo de garantía posterior.
Las restauraciones (tapaduras) o tratamiento de operatoria permiten restituir parte del diente a través
de un material artificial y un sistema adhesivo biocompatible, como es el caso de cuando se ha sufrido
caries u otras causas. El tratamiento de caries puede generar sensibilidad postoperatoria, que en su
mayoría es reversible y que ocurre debido a múltiples factores como la profundidad de la cavidad,
daño o tratamientos previos, contracción de polimerización del material restaurador, estado de la pulpa
(nervio) del diente u otros. Debido a estos factores dinámicos, incluso utilizando exámenes
radiográficos, no siempre es predecible el estado pulpar del diente y es posible que en algunos
casos la sensibilidad o molestia posterior a la atención no remita y que para resolverlo el diente
necesite un tratamiento endodóntico (tratamiento de conducto), que en ese caso deberá también ser
presupuestado y costeado por el / la paciente.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo/a,
entendiendo también la posibilidad de ser derivado con otro/a especialista para concluir mi
tratamiento exitosamente.
Comprendo que tengo garantías (según plazos indicados en presupuestos) por los tratamientos
realizados en clínica DENTAL SEIS, por lo que si se presenta alguna complicación posterior, es a
quienes primero debo contactar y acudir para ser reevaluado y hacer uso de la misma, para verificar

[Página 9]
posibilidades tratamiento, repitiéndolo o considerando uno distinto si es que el caso lo amerita y que
podría implicar una diferencia a costear sobre el mismo. En caso de ser necesario pasaré por una
evaluación de contraloría a cargo del director de la clínica y no será posible hacer uso de garantías si
es que soy intervenido/a en otro centro dental y perderé todo tipo de cobertura de este tipo o
posibilidades de devolución.
Comprendo y me comprometo como paciente o tutor legal a que debo seguir las indicaciones de mi
odontólogo/a tratante, siendo responsable con estas mismas y/o con el uso de los fármacos prescitos y
asistiendo a los controles que se establezcan con la debida regularidad.
Firma Paciente
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento de destartraje y operatoria dental

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 8]
CONSENTIMIENTO DESTARTRAJE Y OPERATORIA DENTAL
Declaro haber informado de forma clara y veraz a el / la odontólogo/a tratante respecto a mi estado de
salud general, condiciones médicas u odontológicas, tratamientos previos y actuales, alergias,
cirugías previas y fármacos que utilizo o cualquier otro antecedente. El/la odontólogo/a tratante me ha
informado respecto a mi estado de salud bucal y resuelto mis dudas e inquietudes respecto al mismo.
Me ha explicado también los tratamientos propuestos junto a las ventajas y desventajas, al igual que
los riesgos, beneficios y posibles complicaciones en caso de realizar o no realizar el tratamiento
mencionado. Me ha informado respecto a la posible necesidad de uso de anestésicos, indicación de
fármacos, elementos de higiene u otras indicaciones que pudiesen ser necesarias para lograr los
objetivos del tratamiento.
El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro
dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía mediante el uso
de un instrumento que emite vibraciones y agua en spray. Usualmente el destartraje no es un
procedimiento doloroso, sin embargo, esto es subjetivo por lo que en algunos casos se podrían
presentar sensibilidad dental o molestias durante o posterior al mismo. En ocasiones el depósito de
tártaro también puede ubicarse bajo la encía, necesitando complementar el destartraje supragingival
con uno subgingival. El uso ultrasonido por sí mismo no daña el tejido dental ni tampoco es capaz de
desalojar una obturación (tapadura) o corona antigua que se encuentre en buenas condiciones, si esto
ocurriera significa que ya existe un daño previo, que no se encuentra en buen estado y probablemente
haya perdido su adhesión; en caso de ocurrir, implica la necesidad de realizar el recambio completo de
la obturación, que deberá ser presupuestada y costeada por mí como paciente. La duración de la
limpieza está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un
tratamiento que cuente con algún tipo de garantía posterior.
Las restauraciones (tapaduras) o tratamiento de operatoria permiten restituir parte del diente a través
de un material artificial y un sistema adhesivo biocompatible, como es el caso de cuando se ha sufrido
caries u otras causas. El tratamiento de caries puede generar sensibilidad postoperatoria, que en su
mayoría es reversible y que ocurre debido a múltiples factores como la profundidad de la cavidad,
daño o tratamientos previos, contracción de polimerización del material restaurador, estado de la pulpa
(nervio) del diente u otros. Debido a estos factores dinámicos, incluso utilizando exámenes
radiográficos, no siempre es predecible el estado pulpar del diente y es posible que en algunos
casos la sensibilidad o molestia posterior a la atención no remita y que para resolverlo el diente
necesite un tratamiento endodóntico (tratamiento de conducto), que en ese caso deberá también ser
presupuestado y costeado por el / la paciente.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo/a,
entendiendo también la posibilidad de ser derivado con otro/a especialista para concluir mi
tratamiento exitosamente.
Comprendo que tengo garantías (según plazos indicados en presupuestos) por los tratamientos
realizados en clínica {{company.name}}, por lo que si se presenta alguna complicación posterior, es a
quienes primero debo contactar y acudir para ser reevaluado y hacer uso de la misma, para verificar

[Página 9]
posibilidades tratamiento, repitiéndolo o considerando uno distinto si es que el caso lo amerita y que
podría implicar una diferencia a costear sobre el mismo. En caso de ser necesario pasaré por una
evaluación de contraloría a cargo del director de la clínica y no será posible hacer uso de garantías si
es que soy intervenido/a en otro centro dental y perderé todo tipo de cobertura de este tipo o
posibilidades de devolución.
Comprendo y me comprometo como paciente o tutor legal a que debo seguir las indicaciones de mi
odontólogo/a tratante, siendo responsable con estas mismas y/o con el uso de los fármacos prescitos y
asistiendo a los controles que se establezcan con la debida regularidad.
Firma Paciente

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- los riesgos, beneficios y posibles complicaciones en caso de realizar o no realizar el tratamiento
- procedimiento doloroso, sin embargo, esto es subjetivo por lo que en algunos casos se podrían
- tratamiento que cuente con algún tipo de garantía posterior.
- Comprendo que tengo garantías (según plazos indicados en presupuestos) por los tratamientos
- realizados en clínica DENTAL SEIS, por lo que si se presenta alguna complicación posterior, es a
- evaluación de contraloría a cargo del director de la clínica y no será posible hacer uso de garantías si

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_DESTARTRAJE_OPERATORIA-CO`, país `CO`, locale `es-CO`, hash `815553c8e0d9a90ad8187ef3a9cd7a0f621e24a9e170fe71034c5b8ce95a9a59`.
- CL: id lógico `CONS_DESTARTRAJE_OPERATORIA-CL`, país `CL`, locale `es-CL`, hash `dde98b115ba7a59cf0e943c51dfda0b5b934f0179584694b8af281c025819894`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 07. CONSENTIMIENTO INFORMADO DE IMPLANTOLOGÍA

- Código: `CONS_IMPLANTOLOGIA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 10–11
- Especialidad: Implantologia
- Firmante: `ADULT_OR_REPRESENTATIVE`
- Resultado: `PENDING`
- Fragmento SHA-256: `ac950ad4df46f13789bfce79de26ef993878228cc6137354e1bf0f41ab30c5f9`

### Texto fuente relevante

```text
[Página 10]
CONSENTIMIENTO IMPLANTOLOGÍA
__________________________________________________________________
PROCEDIMIENTO
___
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
El tratamiento de implantes consiste en la instalación de un tornillo de titanio en el hueso, el que debe
osteointegrarse pudiendo tardar desde 3 a 6 meses antes de ser conectado a través de tornillos
protésicos para continuar con la corona sobre implantes. El implante reemplaza la raíz del diente, por
lo que la instalación del implante por si sola no corresponde al tratamiento final y definitivo. El
tratamiento se completa cuando el o los implantes son rehabilitados mediante una o varias coronas
dentales, luego son controlados en una o varias sesiones por el especialista y entrega el alta.
El implante está fabricado con titanio y es biocompatible con el cuerpo humano. El tornillo de titanio
tiene garantía de por vida y la corona sobre el tornillo de titanio tiene garantía 1 año. Los insumos
biológicos, como injertos y membranas NO tienen garantía debido a que su éxito recae en la
compatibilidad, cicatrización e integración del organismo del paciente (algunos pacientes rechazan el
injerto). En caso de repetir el procedimiento, los insumos biológicos deben ser nuevamente
pagados por el paciente. La garantía se hace efectiva una vez que el tratamiento se encuentra
terminado en su totalidad dentro de los plazos correspondientes. La garantía se mantendrá mientras
el paciente asista a sus controles periódicos, manteniendo los implantes en buen estado, gran parte de
los fallos de este tratamiento ocurren por peri-implantitis asociado a placa bacteriana, es decir por la
higiene y cepillado a diario del paciente o malos hábitos como el cigarro.
A nivel mundial los implantes tienen buena tasa de efectividad, llegando inclusive al 97-98% de éxito al
largo plazo, por el contrario, un 2-3% de los pacientes rechazan los implantes por situaciones
inherentes al procedimiento, ya sea por rechazo de su organismo y sistema inmunológico, deficiente
cicatrización, mal cepillado y mala higiene (infección y placa bacteriana) o malos hábitos de consumo
de cigarro, tabaco y drogas.
Puedo presentar posterior a una cirugía de forma inmediata o tardía, inflamación, aumento de
volumen, dolor, infección, alveolitis húmeda, alveolitis seca, hemorragia, hematomas o
equimosis. Menos frecuente puede ocurrir fractura dental o de tejido óseo, alteración sensitiva de los
nervios de forma temporal o definitiva, traslado o impulsión de piezas dentales a otros sitios
anatómicos (seno maxilar), comunicación buco sinusal por piezas que tengan íntima relación
anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos, molestias en músculos
o articulación temporo mandibular por mantener abierta la boca mucho tiempo, dificultad para abrir la
boca o masticar, fracturas de instrumentos.
Durante el procedimiento, existe la posibilidad de nuevos hallazgos clínicos y patológicos que no se
pueden predecir mediante el examen clínico y radiográfico, cambiando el curso del tratamiento
inclusive llevando a realizar tratamientos adicionales, como una biopsia, eliminación de una masa
tumoral, enucleación de quistes, o aplicación de injertos e insumos biológicos, etc. Por lo que el

[Página 11]
paciente deberá asumir el costo del nuevo presupuesto o la diferencia de este. Si el paciente viene
acompañado mientras está siendo operado, se le explicará a su tutor acompañante.
Se me ha explicado, en caso de faltar o ausentarme sin previo aviso (24 horas antes) a mi hora de
cirugía, los 30.000 de la reserva no serán devueltos, debiendo pagar nuevamente el valor de
reserva por programación de cirugía. De la misma forma si el doctor decide no llevar a cabo la cirugía
por no seguir las instrucciones explicadas en la evaluación y planificación de cirugía al NO tomar la
pre-medicación entregada antes del procedimiento quirúrgico o por NO traer/mostrar los exámenes
complementarios requeridos, habiendo sido de mi absoluta responsabilidad.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de implantología

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 10]
CONSENTIMIENTO IMPLANTOLOGÍA
__________________________________________________________________
PROCEDIMIENTO
___
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
El tratamiento de implantes consiste en la instalación de un tornillo de titanio en el hueso, el que debe
osteointegrarse pudiendo tardar desde 3 a 6 meses antes de ser conectado a través de tornillos
protésicos para continuar con la corona sobre implantes. El implante reemplaza la raíz del diente, por
lo que la instalación del implante por si sola no corresponde al tratamiento final y definitivo. El
tratamiento se completa cuando el o los implantes son rehabilitados mediante una o varias coronas
dentales, luego son controlados en una o varias sesiones por el especialista y entrega el alta.
El implante está fabricado con titanio y es biocompatible con el cuerpo humano. El tornillo de titanio
tiene garantía de por vida y la corona sobre el tornillo de titanio tiene garantía 1 año. Los insumos
biológicos, como injertos y membranas NO tienen garantía debido a que su éxito recae en la
compatibilidad, cicatrización e integración del organismo del paciente (algunos pacientes rechazan el
injerto). En caso de repetir el procedimiento, los insumos biológicos deben ser nuevamente
pagados por el paciente. La garantía se hace efectiva una vez que el tratamiento se encuentra
terminado en su totalidad dentro de los plazos correspondientes. La garantía se mantendrá mientras
el paciente asista a sus controles periódicos, manteniendo los implantes en buen estado, gran parte de
los fallos de este tratamiento ocurren por peri-implantitis asociado a placa bacteriana, es decir por la
higiene y cepillado a diario del paciente o malos hábitos como el cigarro.
A nivel mundial los implantes tienen buena tasa de efectividad, llegando inclusive al 97-98% de éxito al
largo plazo, por el contrario, un 2-3% de los pacientes rechazan los implantes por situaciones
inherentes al procedimiento, ya sea por rechazo de su organismo y sistema inmunológico, deficiente
cicatrización, mal cepillado y mala higiene (infección y placa bacteriana) o malos hábitos de consumo
de cigarro, tabaco y drogas.
Puedo presentar posterior a una cirugía de forma inmediata o tardía, inflamación, aumento de
volumen, dolor, infección, alveolitis húmeda, alveolitis seca, hemorragia, hematomas o
equimosis. Menos frecuente puede ocurrir fractura dental o de tejido óseo, alteración sensitiva de los
nervios de forma temporal o definitiva, traslado o impulsión de piezas dentales a otros sitios
anatómicos (seno maxilar), comunicación buco sinusal por piezas que tengan íntima relación
anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos, molestias en músculos
o articulación temporo mandibular por mantener abierta la boca mucho tiempo, dificultad para abrir la
boca o masticar, fracturas de instrumentos.
Durante el procedimiento, existe la posibilidad de nuevos hallazgos clínicos y patológicos que no se
pueden predecir mediante el examen clínico y radiográfico, cambiando el curso del tratamiento
inclusive llevando a realizar tratamientos adicionales, como una biopsia, eliminación de una masa
tumoral, enucleación de quistes, o aplicación de injertos e insumos biológicos, etc. Por lo que el

[Página 11]
paciente deberá asumir el costo del nuevo presupuesto o la diferencia de este. Si el paciente viene
acompañado mientras está siendo operado, se le explicará a su tutor acompañante.
Se me ha explicado, en caso de faltar o ausentarme sin previo aviso (24 horas antes) a mi hora de
cirugía, los 30.000 de la reserva no serán devueltos, debiendo pagar nuevamente el valor de
reserva por programación de cirugía. De la misma forma si el doctor decide no llevar a cabo la cirugía
por no seguir las instrucciones explicadas en la evaluación y planificación de cirugía al NO tomar la
pre-medicación entregada antes del procedimiento quirúrgico o por NO traer/mostrar los exámenes
complementarios requeridos, habiendo sido de mi absoluta responsabilidad.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`1 año`, `24 horas`, `6 meses`

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- tiene garantía de por vida y la corona sobre el tornillo de titanio tiene garantía 1 año. Los insumos
- biológicos, como injertos y membranas NO tienen garantía debido a que su éxito recae en la
- pagados por el paciente. La garantía se hace efectiva una vez que el tratamiento se encuentra
- terminado en su totalidad dentro de los plazos correspondientes. La garantía se mantendrá mientras
- inherentes al procedimiento, ya sea por rechazo de su organismo y sistema inmunológico, deficiente
- cicatrización, mal cepillado y mala higiene (infección y placa bacteriana) o malos hábitos de consumo
- volumen, dolor, infección, alveolitis húmeda, alveolitis seca, hemorragia, hematomas o
- anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos, molestias en músculos
- complementarios requeridos, habiendo sido de mi absoluta responsabilidad.
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_IMPLANTOLOGIA-CO`, país `CO`, locale `es-CO`, hash `686f9839a85c98727817c20251366df9f57c79306a2c6359a728f14eb6a8b2a0`.
- CL: id lógico `CONS_IMPLANTOLOGIA-CL`, país `CL`, locale `es-CL`, hash `8e7b0830947e16b50383ef9d818ac7373dddcdd227a1ac1fc51566d04d7b4eb4`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 08. CONSENTIMIENTO INFORMADO DE ODONTOPEDIATRÍA

- Código: `CONS_ODONTOPEDIATRIA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 12–13
- Especialidad: Odontopediatria
- Firmante: `REPRESENTATIVE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `01016d9e40ef51ef216ba228cb747f7df8567d8af0669d54c74a769aec1a4079`

### Texto fuente relevante

```text
[Página 12]
CONSENTIMIENTO ODONTOPEDIATRÍA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro
dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía (supragingival)
mediante el uso de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros
y eliminarlos mediante la irrigación a través de agua.
El tártaro en ocasiones se aloja en el tejido subgingival (por debajo de la encía) o tejido radicular del
diente, debiendo ser derivado a la especialidad de periodoncia para un adecuado tratamiento,
presupuestando el destartraje subgingival y pulido radicular según corresponda. El
ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua
(tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba
en buen estado perdiendo su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación
o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del
tratamiento para solucionar el problema.
Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se
podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de
la limpieza está directamente vinculada al cuidado e higiene personal del paciente.
Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial
biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries
puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries,
contracción de polimerización, calor del fresado al eliminar la caries), en otros casos la sensibilidad o
molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo
que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se
puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del
diente.
Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado
por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no
puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una
restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con
sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y
se derivará al paciente (especialidad de rehabilitación oral).
Los tratamientos pulpares en niños (pulpotomía o pulpectomía) ayudan a conservar el diente en su
posición, manteniendo el espacio del diente y dientes vecinos para las futuras erupciones de piezas
permanentes. Aun así, existe una probabilidad de fracaso endodóntico en niños (inherente al trabajo
del odontopediatra), por lo que se tendrá que recurrir a nuevas acciones, por ejemplo, una exodoncia
(extracción), lo que debe ser costeado por el paciente.
En términos generales el acelerado metabolismo y recambio dentario que tienen los niños aumentan la
posibilidad de riesgos y complicaciones inesperadas, como: dolor, inflamación, infección, pulpitis,

[Página 13]
aumentos de volumen, hematomas, equimosis. En caso de presentar fiebre y deshidratación se
recomienda llevar al infante inmediatamente a urgencia médica de alta complejidad (hospital).
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de odontopediatría

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 12]
CONSENTIMIENTO ODONTOPEDIATRÍA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro
dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía (supragingival)
mediante el uso de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros
y eliminarlos mediante la irrigación a través de agua.
El tártaro en ocasiones se aloja en el tejido subgingival (por debajo de la encía) o tejido radicular del
diente, debiendo ser derivado a la especialidad de periodoncia para un adecuado tratamiento,
presupuestando el destartraje subgingival y pulido radicular según corresponda. El
ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua
(tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba
en buen estado perdiendo su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación
o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del
tratamiento para solucionar el problema.
Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se
podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de
la limpieza está directamente vinculada al cuidado e higiene personal del paciente.
Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial
biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries
puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries,
contracción de polimerización, calor del fresado al eliminar la caries), en otros casos la sensibilidad o
molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo
que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se
puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del
diente.
Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado
por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no
puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una
restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con
sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y
se derivará al paciente (especialidad de rehabilitación oral).
Los tratamientos pulpares en niños (pulpotomía o pulpectomía) ayudan a conservar el diente en su
posición, manteniendo el espacio del diente y dientes vecinos para las futuras erupciones de piezas
permanentes. Aun así, existe una probabilidad de fracaso endodóntico en niños (inherente al trabajo
del odontopediatra), por lo que se tendrá que recurrir a nuevas acciones, por ejemplo, una exodoncia
(extracción), lo que debe ser costeado por el paciente.
En términos generales el acelerado metabolismo y recambio dentario que tienen los niños aumentan la
posibilidad de riesgos y complicaciones inesperadas, como: dolor, inflamación, infección, pulpitis,

[Página 13]
aumentos de volumen, hematomas, equimosis. En caso de presentar fiebre y deshidratación se
recomienda llevar al infante inmediatamente a urgencia médica de alta complejidad (hospital).
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del
- Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se
- por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
- posibilidad de riesgos y complicaciones inesperadas, como: dolor, inflamación, infección, pulpitis,
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_ODONTOPEDIATRIA-CO`, país `CO`, locale `es-CO`, hash `c464539ad463cb14c0a051edbeb7323ff638811beda752004b1b8fc31ce5e272`.
- CL: id lógico `CONS_ODONTOPEDIATRIA-CL`, país `CL`, locale `es-CL`, hash `f439d42db89c4fdeba981d491cb15f55d86c79c926ee9a19bdd62c3b14589e34`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 09. RECHAZO DE TRATAMIENTO ODONTOLÓGICO, QUIRÚRGICO O DIAGNÓSTICO

- Código: `RECHAZO_TRATAMIENTO`
- Categoría: Rechazos
- Páginas fuente: 14–14
- Especialidad: General
- Firmante: `ADULT_OR_REPRESENTATIVE`
- Resultado: `PENDING`
- Fragmento SHA-256: `66998f99dd0f6ee1d7f32b655e976b36a07d3293722372e4a691deecae160ddd`

### Texto fuente relevante

```text
[Página 14]
CONSENTIMIENTO DE RECHAZO AL TRATAMIENTO ODONTOLÓGICO, QUIRÚRGICO O
PRUEBAS DIAGNÓSTICAS
Por medio de la presente DECLARO que he sido debidamente informado por el
Dr(a)_____________________, cirujano dentista con cédula de identidad
número_________________ - ___ en relación a la necesidad de someterme a los siguientes
tratamientos o pruebas diagnósticas:
__________________________________________________________________________________
__________________________________________________________________________________
__________________________________
Declaro que he sido debidamente informado y que entiendo los riesgos y beneficios del tratamiento y/o
pruebas diagnósticas recomendadas por el dentista tratante. Declaro que se me han respondido y
aclarado todas mis dudas acerca del tratamiento y/o pruebas diagnósticas recomendadas por el
dentista tratante. Considerando todas las opciones anteriores, aceptando y entendiendo los riesgos y
posibles consecuencias de mi decisión, declaro que no es mi deseo continuar con el tratamiento y/o
pruebas propuestas por el dentista tratante.
NOMBRE PACIENTE:
RUT PACIENTE:
FIRMA:
```

### Texto normalizado CO / es-CO

```markdown
# Rechazo de tratamiento odontológico, quirúrgico o diagnóstico

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 14]
CONSENTIMIENTO DE RECHAZO AL TRATAMIENTO ODONTOLÓGICO, QUIRÚRGICO O
PRUEBAS DIAGNÓSTICAS
Por medio de la presente DECLARO que he sido debidamente informado por el
Dr(a)_____________________, cirujano dentista con cédula de identidad
número_________________ - ___ en relación a la necesidad de someterme a los siguientes
tratamientos o pruebas diagnósticas:
__________________________________________________________________________________
__________________________________________________________________________________
__________________________________
Declaro que he sido debidamente informado y que entiendo los riesgos y beneficios del tratamiento y/o
pruebas diagnósticas recomendadas por el dentista tratante. Declaro que se me han respondido y
aclarado todas mis dudas acerca del tratamiento y/o pruebas diagnósticas recomendadas por el
dentista tratante. Considerando todas las opciones anteriores, aceptando y entendiendo los riesgos y
posibles consecuencias de mi decisión, declaro que no es mi deseo continuar con el tratamiento y/o
pruebas propuestas por el dentista tratante.
NOMBRE PACIENTE:
RUT PACIENTE:
FIRMA:

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- CONSENTIMIENTO DE RECHAZO AL TRATAMIENTO ODONTOLÓGICO, QUIRÚRGICO O
- Declaro que he sido debidamente informado y que entiendo los riesgos y beneficios del tratamiento y/o
- dentista tratante. Considerando todas las opciones anteriores, aceptando y entendiendo los riesgos y

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `RECHAZO_TRATAMIENTO-CO`, país `CO`, locale `es-CO`, hash `1877a15a6dd7f160f69ee68fa1b0d279ad6881f412210d19646009f1de7323db`.
- CL: id lógico `RECHAZO_TRATAMIENTO-CL`, país `CL`, locale `es-CL`, hash `00ecdae91b4e9e6e50806d1e80c0ec639e5bdcff2011cb0492de4dc298cd3a44`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 10. CONSENTIMIENTO INFORMADO DE DESTARTRAJE

- Código: `CONS_DESTARTRAJE`
- Categoría: Consentimientos clínicos
- Páginas fuente: 15–15
- Especialidad: Periodoncia
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `2c7e9414c2a4dbb6e81d0970619071c86b5a40b87abeba872d72878bc70d8d5c`

### Texto fuente relevante

```text
[Página 15]
CONSENTIMIENTO INFORMADO DE DESTARTRAJE
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro
dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía (supragingival)
mediante el uso de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros
y eliminarlos mediante la irrigación a través de agua.
El tártaro en ocasiones se aloja en el tejido subgingival (por debajo de la encía) o tejido radicular del
diente, debiendo ser derivado a la especialidad de periodoncia para un adecuado tratamiento,
presupuestando el destartraje subgingival y pulido radicular según corresponda.
El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua
(tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba
en buen estado perdiendo su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación
o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del
tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el
dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o
posterior al tratamiento.
La duración de la limpieza está directamente vinculada al cuidado e higiene personal del
paciente. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
La duración de la limpieza está directamente vinculada al cuidado e higiene bucal personal, por lo
tanto no es un tratamiento que cuente con algún tipo de garantía posterior.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de destartraje

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 15]
CONSENTIMIENTO INFORMADO DE DESTARTRAJE
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro
dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía (supragingival)
mediante el uso de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros
y eliminarlos mediante la irrigación a través de agua.
El tártaro en ocasiones se aloja en el tejido subgingival (por debajo de la encía) o tejido radicular del
diente, debiendo ser derivado a la especialidad de periodoncia para un adecuado tratamiento,
presupuestando el destartraje subgingival y pulido radicular según corresponda.
El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua
(tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba
en buen estado perdiendo su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación
o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del
tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el
dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o
posterior al tratamiento.
La duración de la limpieza está directamente vinculada al cuidado e higiene personal del
paciente. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
La duración de la limpieza está directamente vinculada al cuidado e higiene bucal personal, por lo
tanto no es un tratamiento que cuente con algún tipo de garantía posterior.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del
- tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el
- dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o
- tanto no es un tratamiento que cuente con algún tipo de garantía posterior.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_DESTARTRAJE-CO`, país `CO`, locale `es-CO`, hash `8abfa3f055c16f6021fabd244b927db3f01ed81b0336459c86cdfb9c691b8f34`.
- CL: id lógico `CONS_DESTARTRAJE-CL`, país `CL`, locale `es-CL`, hash `e54d820d68238a8fc52bdeaa35bc770483f075c637ff29e2a6412a7c32bfb192`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 11. CONSENTIMIENTO INFORMADO DE ENDODONCIA

- Código: `CONS_ENDODONCIA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 16–17
- Especialidad: Endodoncia
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `e78e071ec73d670e43e5013b66e007b145c3f522d3f9232a1d3d49de74073822`

### Texto fuente relevante

```text
[Página 16]
CONSENTIMIENTO INFORMADO DE ENDODONCIA
PROCEDIMIENTO
__________________________________________________________________
_____
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He
entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
El tratamiento endodóntico (de conducto) consiste en la eliminación y extracción del tejido pulpar
(nervio dental) rellenando con un material biocompatible los canales radiculares, para esto se ingresa a
través del diente, eliminando el tejido infectado por caries, fracturas o por indicación de rehabilitación
(anclar un perno/poste). El tejido pulpar se elimina utilizando limas endodónticas, antimicrobianos o
irrigando con hipoclorito y otros elementos que mejoren la desinfección de los conductos radiculares.
El tratamiento puede ser sobre una pulpa vital o necrótica (necrosis pulpar). Los retratamientos tienen
un pronóstico de éxito reservado ya que son dientes que ya fueron tratados anteriormente y presentan
mayor desgaste de tejido dentario. En ocasiones el tratamiento fracasa y el diente se deberá extraer,
llevando el tratamiento a buscar otros caminos como implantes o prótesis.
El tratamiento endodóntico corresponde al 50% del tratamiento final, ya que, una vez terminado
el tratamiento de conducto, la corona dental se cierra y obtura con un material provisorio dentro de los
que usualmente son fermín y vidrio ionómero, este doble sellado corresponde a un tratamiento
provisorio y temporal que con el tiempo se infiltra hacia el interior del diente pudiendo volverse a
infectar los canales radiculares. El tratamiento endodóntico se garantiza cuando el diente se
ha rehabilitado definitivamente dentro de 30 días terminando la endodoncia, ya sea con una
obturación simple o restauración indirecta (endocorona, incrustación, corona).
Durante el procedimiento pueden ocurrir situaciones inherentes al operador (tratante), tales como,
fractura de limas endodónticas por fatiga de material, fractura dentaria o radicular por debilitamiento de
sus paredes producto del avance de caries o infección, aparición de quistes radiculares por avance de
la infección desde el diente al hueso, para esto se deberá realizar una cirugía apical o exodoncia
(según corresponda), debiendo asumir el costo el paciente, perforaciones o falsas vías desde el diente
al periodonto, inyección y extravasación de hipoclorito a los tejidos que rodean al diente, pudiendo
producir incluso quemaduras lo que se suele proteger con aislación absoluta para evitar que esto
suceda, dolores, sensibilidad o molestias posterior al término de la endodoncia reversibles o
irreversibles, desalojo del cemento temporal entre sesiones, conductos calcificados o pulpolitos que
imposibiliten realizar el tratamiento endodóntico.
Me han explicado que a pesar de terminar la endodoncia y estar correctamente realizada, el
tratamiento podría no funcionar debido a la persistencia de inflamación/infección por bacterias
resistentes. Entiendo que debo seguir las indicaciones de mi tratante, siendo responsable con las
indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda
tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e

[Página 17]
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de endodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 16]
CONSENTIMIENTO INFORMADO DE ENDODONCIA
PROCEDIMIENTO
__________________________________________________________________
_____
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He
entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
El tratamiento endodóntico (de conducto) consiste en la eliminación y extracción del tejido pulpar
(nervio dental) rellenando con un material biocompatible los canales radiculares, para esto se ingresa a
través del diente, eliminando el tejido infectado por caries, fracturas o por indicación de rehabilitación
(anclar un perno/poste). El tejido pulpar se elimina utilizando limas endodónticas, antimicrobianos o
irrigando con hipoclorito y otros elementos que mejoren la desinfección de los conductos radiculares.
El tratamiento puede ser sobre una pulpa vital o necrótica (necrosis pulpar). Los retratamientos tienen
un pronóstico de éxito reservado ya que son dientes que ya fueron tratados anteriormente y presentan
mayor desgaste de tejido dentario. En ocasiones el tratamiento fracasa y el diente se deberá extraer,
llevando el tratamiento a buscar otros caminos como implantes o prótesis.
El tratamiento endodóntico corresponde al 50% del tratamiento final, ya que, una vez terminado
el tratamiento de conducto, la corona dental se cierra y obtura con un material provisorio dentro de los
que usualmente son fermín y vidrio ionómero, este doble sellado corresponde a un tratamiento
provisorio y temporal que con el tiempo se infiltra hacia el interior del diente pudiendo volverse a
infectar los canales radiculares. El tratamiento endodóntico se garantiza cuando el diente se
ha rehabilitado definitivamente dentro de 30 días terminando la endodoncia, ya sea con una
obturación simple o restauración indirecta (endocorona, incrustación, corona).
Durante el procedimiento pueden ocurrir situaciones inherentes al operador (tratante), tales como,
fractura de limas endodónticas por fatiga de material, fractura dentaria o radicular por debilitamiento de
sus paredes producto del avance de caries o infección, aparición de quistes radiculares por avance de
la infección desde el diente al hueso, para esto se deberá realizar una cirugía apical o exodoncia
(según corresponda), debiendo asumir el costo el paciente, perforaciones o falsas vías desde el diente
al periodonto, inyección y extravasación de hipoclorito a los tejidos que rodean al diente, pudiendo
producir incluso quemaduras lo que se suele proteger con aislación absoluta para evitar que esto
suceda, dolores, sensibilidad o molestias posterior al término de la endodoncia reversibles o
irreversibles, desalojo del cemento temporal entre sesiones, conductos calcificados o pulpolitos que
imposibiliten realizar el tratamiento endodóntico.
Me han explicado que a pesar de terminar la endodoncia y estar correctamente realizada, el
tratamiento podría no funcionar debido a la persistencia de inflamación/infección por bacterias
resistentes. Entiendo que debo seguir las indicaciones de mi tratante, siendo responsable con las
indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda
tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e

[Página 17]
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`30 días`

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He
- irrigando con hipoclorito y otros elementos que mejoren la desinfección de los conductos radiculares.
- sus paredes producto del avance de caries o infección, aparición de quistes radiculares por avance de
- la infección desde el diente al hueso, para esto se deberá realizar una cirugía apical o exodoncia
- suceda, dolores, sensibilidad o molestias posterior al término de la endodoncia reversibles o
- tratamiento podría no funcionar debido a la persistencia de inflamación/infección por bacterias
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_ENDODONCIA-CO`, país `CO`, locale `es-CO`, hash `8145b2e32fa38c9c0811a9c97da53895ca5876e442d0720a004db474e2ee0d68`.
- CL: id lógico `CONS_ENDODONCIA-CL`, país `CL`, locale `es-CL`, hash `a6fa83c3aa9212f8b6dc5a735ed177b6be20471e2cb7d735d004b49a28fe1eb8`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 12. CONSENTIMIENTO INFORMADO DE OBTURACIÓN DIRECTA

- Código: `CONS_OBTURACION_DIRECTA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 18–18
- Especialidad: Operatoria
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `8fe02ff4b36dad59c4870e67c4b0534432e7284666a0b98a10942bec40b8c9ea`

### Texto fuente relevante

```text
[Página 18]
CONSENTIMIENTO INFORMADO DE OBTURACIÓN DIRECTA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial
biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries
puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries,
contracción de polimerización, calor del fresado al eliminar la caries), en otros casos la sensibilidad o
molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo
que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se
puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del
diente.
Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado
por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no
puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una
restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con
sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y
se derivará al paciente (especialidad de rehabilitación oral).
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de obturación directa

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 18]
CONSENTIMIENTO INFORMADO DE OBTURACIÓN DIRECTA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial
biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries
puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries,
contracción de polimerización, calor del fresado al eliminar la caries), en otros casos la sensibilidad o
molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo
que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se
puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del
diente.
Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado
por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no
puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una
restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con
sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y
se derivará al paciente (especialidad de rehabilitación oral).
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_OBTURACION_DIRECTA-CO`, país `CO`, locale `es-CO`, hash `9db3c60a62a6964eff4c220707a3642cd1ef0781a0fa97124e8613c9e7d5929d`.
- CL: id lógico `CONS_OBTURACION_DIRECTA-CL`, país `CL`, locale `es-CL`, hash `b9ae9dacfd41933a7fa55a4dc7395bf0325b66d9ac065a43937af7f5a36577fb`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 13. CONSENTIMIENTO INFORMADO DE OBTURACIÓN DIRECTA CON BASE CAVITARIA

- Código: `CONS_OBTURACION_BASE`
- Categoría: Consentimientos clínicos
- Páginas fuente: 19–19
- Especialidad: Operatoria
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `d5ec927c2f9ffcaa844b13f0c265bc82f115c6108385c3360fda6c6486b8b9d1`

### Texto fuente relevante

```text
[Página 19]
CONSENTIMIENTO INFORMADO DE OBTURACION DIRECTA CON BASE CAVITARIA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial
biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries
profunda además de la obturación de resina necesitara un sellado hermético con una base cavitaria,
cemento protector pulpo-dentinario que proporciona un excelente aislamiento térmico, químico y
eléctrico. Una barrera antibacteriana y antitoxinas. En algunos casos se puede realizar en dos
sesiones para evaluar cómo se comporta el diente post eliminación de la caries profunda dejando la
cavidad sellada con la base cavitaria y obturada con un material provisorio para posteriormente realizar
la obturación de resina compuesta. El tratamiento de caries profunda puede generar sensibilidad
postoperatoria la que en su mayoría es reversible (avance de caries, contracción de polimerización,
calor del fresado al eliminar la caries). Cuando la caries ha sido un daño progresivo el sellado
hermético puede reactivar procesos infecciosos, donde la sensibilidad o molestia es irreversible y se
deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo que siendo un tratamiento
adicional deberá ser costeado por el paciente, ya que en ocasiones no se puede predecir con el
examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del diente.
Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado
por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no
puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una
restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con
sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y
se derivará al paciente (especialidad de rehabilitación oral).
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes
de realizarlo.
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de obturación directa con base cavitaria

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 19]
CONSENTIMIENTO INFORMADO DE OBTURACION DIRECTA CON BASE CAVITARIA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial
biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries
profunda además de la obturación de resina necesitara un sellado hermético con una base cavitaria,
cemento protector pulpo-dentinario que proporciona un excelente aislamiento térmico, químico y
eléctrico. Una barrera antibacteriana y antitoxinas. En algunos casos se puede realizar en dos
sesiones para evaluar cómo se comporta el diente post eliminación de la caries profunda dejando la
cavidad sellada con la base cavitaria y obturada con un material provisorio para posteriormente realizar
la obturación de resina compuesta. El tratamiento de caries profunda puede generar sensibilidad
postoperatoria la que en su mayoría es reversible (avance de caries, contracción de polimerización,
calor del fresado al eliminar la caries). Cuando la caries ha sido un daño progresivo el sellado
hermético puede reactivar procesos infecciosos, donde la sensibilidad o molestia es irreversible y se
deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo que siendo un tratamiento
adicional deberá ser costeado por el paciente, ya que en ocasiones no se puede predecir con el
examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del diente.
Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado
por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no
puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una
restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con
sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y
se derivará al paciente (especialidad de rehabilitación oral).
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes
de realizarlo.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_OBTURACION_BASE-CO`, país `CO`, locale `es-CO`, hash `fed82d86b2ac8d49b6a49cca08ff85197984d3aa0c40c86242cabe17aca2407e`.
- CL: id lógico `CONS_OBTURACION_BASE-CL`, país `CL`, locale `es-CL`, hash `e1a57cfbb7a29f48c9e8221beaec0122eaddbc07f252ba2261ebc8883cc83b87`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 14. CONSENTIMIENTO INFORMADO DE PERIODONCIA

- Código: `CONS_PERIODONCIA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 20–20
- Especialidad: Periodoncia
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `b88f1fc357c6e995d261fbb6fd0d4a9333574a9e376b5ceedc25aa5fd7c7cbe8`

### Texto fuente relevante

```text
[Página 20]
CONSENTIMIENTO INFORMADO DE PERIODONCIA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
El tratamiento periodontal consiste en la remoción del tártaro dental (sarro) adherido a la superficie del
diente o los tejidos de soporte (periodonto). Se busca la eliminación de la infección, inflamación,
sangrado y conservar la mayor cantidad de tejido óseo y dental. Esto se consigue mediante un
destartraje supragingival, subgingival, pulido/alisado radicular y pulido coronario. Se puede realizar un
tratamiento no quirúrgico (convencional) o quirúrgico. Por lo general se utilizan curetas y/o la aplicación
de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros y eliminarlos
mediante la irrigación a través de agua, adicional a esto se emplean antimicrobianos, antibióticos o
medicamentos para ayudar a que el sistema elimine la infección.
El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua
(tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba
en buen estado desde el inicio, y perdió su correcta adhesión. Si se llega a desalojar alguna
obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los
gastos adicionales del tratamiento para solucionar el problema.
Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se
podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de
la limpieza está directamente vinculada al cuidado diario e higiene personal del paciente, debiendo
siempre volver a sus controles para mantener una buena salud oral.
Se me ha explicado que posterior al tratamiento periodontal, la enfermedad se puede reagudizar
presentando inflamación, aumento de volumen o nuevas infecciones, además mis dientes pueden
quedar con movilidad o mayor grado de movilidad del que tenían ya que siempre estuvieron así, y
estaban aparentemente firmes a causa de la infección y tártaro (sarro), debido a esto es posible que
necesite exodoncias (extracciones) y elementos protésicos adicionales, los que no contempla el
tratamiento periodontal, estos serán presupuestados y derivados al especialista. Comprendo que la
evolución y recuperación de mi enfermedad no se puede predecir ya que depende en gran parte de mi
sistema inmune y organismo.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener. Comprendo que la duración de la limpieza y éxito de mi tratamiento
periodontal está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un
tratamiento que cuente con algún tipo de garantía posterior.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de periodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 20]
CONSENTIMIENTO INFORMADO DE PERIODONCIA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
El tratamiento periodontal consiste en la remoción del tártaro dental (sarro) adherido a la superficie del
diente o los tejidos de soporte (periodonto). Se busca la eliminación de la infección, inflamación,
sangrado y conservar la mayor cantidad de tejido óseo y dental. Esto se consigue mediante un
destartraje supragingival, subgingival, pulido/alisado radicular y pulido coronario. Se puede realizar un
tratamiento no quirúrgico (convencional) o quirúrgico. Por lo general se utilizan curetas y/o la aplicación
de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros y eliminarlos
mediante la irrigación a través de agua, adicional a esto se emplean antimicrobianos, antibióticos o
medicamentos para ayudar a que el sistema elimine la infección.
El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua
(tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba
en buen estado desde el inicio, y perdió su correcta adhesión. Si se llega a desalojar alguna
obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los
gastos adicionales del tratamiento para solucionar el problema.
Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se
podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de
la limpieza está directamente vinculada al cuidado diario e higiene personal del paciente, debiendo
siempre volver a sus controles para mantener una buena salud oral.
Se me ha explicado que posterior al tratamiento periodontal, la enfermedad se puede reagudizar
presentando inflamación, aumento de volumen o nuevas infecciones, además mis dientes pueden
quedar con movilidad o mayor grado de movilidad del que tenían ya que siempre estuvieron así, y
estaban aparentemente firmes a causa de la infección y tártaro (sarro), debido a esto es posible que
necesite exodoncias (extracciones) y elementos protésicos adicionales, los que no contempla el
tratamiento periodontal, estos serán presupuestados y derivados al especialista. Comprendo que la
evolución y recuperación de mi enfermedad no se puede predecir ya que depende en gran parte de mi
sistema inmune y organismo.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener. Comprendo que la duración de la limpieza y éxito de mi tratamiento
periodontal está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un
tratamiento que cuente con algún tipo de garantía posterior.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- diente o los tejidos de soporte (periodonto). Se busca la eliminación de la infección, inflamación,
- sangrado y conservar la mayor cantidad de tejido óseo y dental. Esto se consigue mediante un
- medicamentos para ayudar a que el sistema elimine la infección.
- obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los
- Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se
- presentando inflamación, aumento de volumen o nuevas infecciones, además mis dientes pueden
- estaban aparentemente firmes a causa de la infección y tártaro (sarro), debido a esto es posible que
- tratamiento que cuente con algún tipo de garantía posterior.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_PERIODONCIA-CO`, país `CO`, locale `es-CO`, hash `fb31e061f65a8e347b6e5ce95c8141fa3126fb01365f83b0bd8d45f48bf44820`.
- CL: id lógico `CONS_PERIODONCIA-CL`, país `CL`, locale `es-CL`, hash `9e00fc62cc84df4e75a7a1a756a7eb80930a71c31de5cf2e37920578afae1535`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 15. CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL PRÓTESIS FIJA

- Código: `CONS_PROTESIS_FIJA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 21–21
- Especialidad: Rehabilitacion Oral
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `701f62dbebb333907bcd4b5e601bf1be51019142c043a53a6ed6108d4549fe2f`

### Texto fuente relevante

```text
[Página 21]
CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL PRÓTESIS FIJA
PROCEDIMIENTO(S) _______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
La rehabilitación oral busca devolver dientes perdidos mediante el uso de elementos artificiales
protésicos, dentro de las prótesis fijas se encuentran las endo-coronas, coronas (prótesis fija unitaria) o
puentes (prótesis fija plural). Estas pueden ser realizadas con metal, metal-cerámicas o libres de
metal, apoyándose de pernos metálicos intra-conducto o postes de fibra de vidrios, entre otros
elementos.
Durante el procedimiento o posterior a la instalación protésica fija, pueden ocurrir eventos inherentes al
tratante los que son propios de la técnica en sí, tales como, fracturas de tejido dental, fracturas de
paredes o piso del diente, fractura radicular, fractura coronaria, fractura de postes o pernos intra-
conductos, desalojos de provisorios entre sesiones, caries futuras por mala higiene y dieta cariogénica,
fractura coronaria de prótesis fija porcelana, cerámica o metal, inflamación de los tejidos blandos
circundantes, infecciones, fatiga de material.
Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del paciente,
este deberá de pagar los costos adicionales que signifiquen corregir y mejorar el tratamiento.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica CLINICA SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica CLINICA SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de rehabilitación oral prótesis fija

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 21]
CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL PRÓTESIS FIJA
PROCEDIMIENTO(S) _______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
La rehabilitación oral busca devolver dientes perdidos mediante el uso de elementos artificiales
protésicos, dentro de las prótesis fijas se encuentran las endo-coronas, coronas (prótesis fija unitaria) o
puentes (prótesis fija plural). Estas pueden ser realizadas con metal, metal-cerámicas o libres de
metal, apoyándose de pernos metálicos intra-conducto o postes de fibra de vidrios, entre otros
elementos.
Durante el procedimiento o posterior a la instalación protésica fija, pueden ocurrir eventos inherentes al
tratante los que son propios de la técnica en sí, tales como, fracturas de tejido dental, fracturas de
paredes o piso del diente, fractura radicular, fractura coronaria, fractura de postes o pernos intra-
conductos, desalojos de provisorios entre sesiones, caries futuras por mala higiene y dieta cariogénica,
fractura coronaria de prótesis fija porcelana, cerámica o metal, inflamación de los tejidos blandos
circundantes, infecciones, fatiga de material.
Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del paciente,
este deberá de pagar los costos adicionales que signifiquen corregir y mejorar el tratamiento.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica CLINICA SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica CLINICA SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- circundantes, infecciones, fatiga de material.
- Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
- director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del paciente,
- Comprendo que tengo garantías por los tratamientos realizados en clínica CLINICA SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_PROTESIS_FIJA-CO`, país `CO`, locale `es-CO`, hash `27823b87674a5e35402b6dafc46d0c2bf9647effbef8b1481bb3cf6ce50da620`.
- CL: id lógico `CONS_PROTESIS_FIJA-CL`, país `CL`, locale `es-CL`, hash `821beee94bef47fd3d41fddac9664adb9d0aa747ad980fced2ae35ecf6d616c2`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 16. CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL PRÓTESIS REMOVIBLE

- Código: `CONS_PROTESIS_REMOVIBLE`
- Categoría: Consentimientos clínicos
- Páginas fuente: 22–23
- Especialidad: Rehabilitacion Oral
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `acab89092fc1240d9866a456e88ae57b7f55ee2a10562152cd997bf57e7600e4`

### Texto fuente relevante

```text
[Página 22]
CONSENTIMIENTO DE REHABILITACIÓN ORAL PRÓTESIS REMOVIBLE
PROCEDIMIENTO(S) _______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
La rehabilitación oral busca devolver dientes perdidos mediante el uso de elementos artificiales
protésicos, dentro de las prótesis removibles se encuentra la prótesis total, prótesis parcial de base
acrílica, parcial de base metálica, prótesis valplast o termoplástica, prótesis inmediata/temporal o
provisoria, entre otras.
Una prótesis de base metálica presenta mejor resistencia y estabilidad que una de base acrílica, se
afirma de los dientes (pilares) a través de retenedores (ganchos), por lo que se necesita un mínimo de
tejido óseo (hueso) y dientes para su confección, los dientes móviles o con enfermedad periodontal no
son buenos pilares para sostener elementos protésicos. Las prótesis acrílicas tienen más acrílico y se
usan cuando no hay muchos dientes, por lo que su soporte esta dado más que nada en su relación
con la cantidad de hueso. El paladar es un soporte primario, por lo que en general se utiliza como
soporte y el evitarlo hace que la prótesis pueda no quedar bien diseñada, presentando molestias.
Existe una baja cantidad de pacientes que, a pesar del buen diseño y fabricación de una prótesis,
siguiendo los pasos al pie de la letra en su fabricación, preservando correctamente los tejidos e
instalándola como corresponde, el paciente no la soportará y la rechazará por temas de confort y
comodidad, esto es ajeno al trabajo del odontólogo, por lo que no existirá devolución de dinero y la
opción más recomendada será implantología.
Para la fabricación de una prótesis, al menos se necesitan 4 sesiones o más, cada sesión con
diferencia de 7 a 10 días. Por lo que no es un procedimiento rápido. La rapidez del odontólogo está en
estrecha relación al trabajo externo y envío de los laboratorios, lo que no es responsabilidad directa del
odontólogo o clínica DENTAL SEIS
Si el paciente necesita extracciones previas a su prótesis removible, esto aumentara el tiempo de
espera, ya que el hueso se demora en cicatrizar 3 meses, por lo que se podría, según evaluación del
clínico, comenzar con las primeras etapas e impresiones para la prótesis después de 4-6 semanas de
las extracciones, el tiempo aumenta en pacientes con cicatrización lenta o enfermedades no
controladas.
Mientras cicatriza el tejido óseo, es posible utilizar prótesis temporal, provisoria e inmediata, las que se
instalan al mismo momento de la extracción dental, entendiendo que, son prótesis diseñadas solo
como emergencia y con uso limitado, las que deberán ser ajustadas constantemente hasta que
cicatrice el tejido óseo (hueso) y se pueda comenzar con la etapa de una prótesis definitiva. Una
prótesis inmediata o provisoria y una prótesis definitiva son procedimientos independientes por lo que
el paciente debe pagar cada prótesis independientemente. La prótesis inmediata/temporal NO
reemplaza una prótesis definitiva.
Durante el procedimiento o posterior a la instalación protésica removible, pueden ocurrir eventos
inherentes al tratante los que son propios de la técnica en sí o su uso, tales como, fracturas de tejido

[Página 23]
dental (piezas pilares), fracturas de paredes o piso del diente, fractura radicular, fractura coronaria,
fractura de ganchos metálicos, caries futuras por mala higiene y dieta cariogénica, fractura coronaria
de prótesis fija donde se engancha el retenedor (alambre que afirma la prótesis), inflamación de los
tejidos blandos circundantes, infecciones, dolor, incomodidad, fatiga de material, fractura de prótesis o
dientes artificiales, desalojo de dientes protésicos.
Luego de una instalación protésica, si el paciente la utiliza por primera vez, es normal sentir
incomodidad o cambios en la forma de comer o hablar, por lo que se recomienda practicar en casa,
leyendo en voz alta 10 minutos al día, comer cosas livianas y acostumbrarse a ellas. Si presenta dolor,
inflamación, ulceras o erosiones, debe suspender su uso, agendar una visita al especialista y utilizar la
prótesis 24 horas antes de su hora (todo el día), ideal dormir con ella sólo esa vez, de esta forma se
marcarán las zonas de sobre compresión para realizar desgastes precisos sobre la prótesis,
eliminando las molestias.
Recuerde que NO debe dormir con la prótesis (NUNCA), ya que puede generar inflamaciones, los
tejidos no descansan y proliferan hongos. Es frecuente la estomatitis sub-protésica por el mal diseño
de estas y utilizarlas sin descanso.
Las prótesis removibles no son eternas, se recomienda rebasar y ajustar las prótesis una vez por año,
e idealmente cambiarlas cuando se comiencen a sentir sueltas, esto es debido a que con el tiempo el
hueso o dientes (donde se soporta una prótesis) comienzan a reabsorberse o cambian biológicamente
de forma natural por lo que una prótesis ya no funcionará de la misma forma. Recuerde, no solo
higienizar sus dientes, sino también la prótesis, todos los días.
Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del paciente,
este deberá de pagar los costos adicionales que signifiquen corregir y mejorar el tratamiento.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de rehabilitación oral prótesis removible

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 22]
CONSENTIMIENTO DE REHABILITACIÓN ORAL PRÓTESIS REMOVIBLE
PROCEDIMIENTO(S) _______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
La rehabilitación oral busca devolver dientes perdidos mediante el uso de elementos artificiales
protésicos, dentro de las prótesis removibles se encuentra la prótesis total, prótesis parcial de base
acrílica, parcial de base metálica, prótesis valplast o termoplástica, prótesis inmediata/temporal o
provisoria, entre otras.
Una prótesis de base metálica presenta mejor resistencia y estabilidad que una de base acrílica, se
afirma de los dientes (pilares) a través de retenedores (ganchos), por lo que se necesita un mínimo de
tejido óseo (hueso) y dientes para su confección, los dientes móviles o con enfermedad periodontal no
son buenos pilares para sostener elementos protésicos. Las prótesis acrílicas tienen más acrílico y se
usan cuando no hay muchos dientes, por lo que su soporte esta dado más que nada en su relación
con la cantidad de hueso. El paladar es un soporte primario, por lo que en general se utiliza como
soporte y el evitarlo hace que la prótesis pueda no quedar bien diseñada, presentando molestias.
Existe una baja cantidad de pacientes que, a pesar del buen diseño y fabricación de una prótesis,
siguiendo los pasos al pie de la letra en su fabricación, preservando correctamente los tejidos e
instalándola como corresponde, el paciente no la soportará y la rechazará por temas de confort y
comodidad, esto es ajeno al trabajo del odontólogo, por lo que no existirá devolución de dinero y la
opción más recomendada será implantología.
Para la fabricación de una prótesis, al menos se necesitan 4 sesiones o más, cada sesión con
diferencia de 7 a 10 días. Por lo que no es un procedimiento rápido. La rapidez del odontólogo está en
estrecha relación al trabajo externo y envío de los laboratorios, lo que no es responsabilidad directa del
odontólogo o clínica {{company.name}}
Si el paciente necesita extracciones previas a su prótesis removible, esto aumentara el tiempo de
espera, ya que el hueso se demora en cicatrizar 3 meses, por lo que se podría, según evaluación del
clínico, comenzar con las primeras etapas e impresiones para la prótesis después de 4-6 semanas de
las extracciones, el tiempo aumenta en pacientes con cicatrización lenta o enfermedades no
controladas.
Mientras cicatriza el tejido óseo, es posible utilizar prótesis temporal, provisoria e inmediata, las que se
instalan al mismo momento de la extracción dental, entendiendo que, son prótesis diseñadas solo
como emergencia y con uso limitado, las que deberán ser ajustadas constantemente hasta que
cicatrice el tejido óseo (hueso) y se pueda comenzar con la etapa de una prótesis definitiva. Una
prótesis inmediata o provisoria y una prótesis definitiva son procedimientos independientes por lo que
el paciente debe pagar cada prótesis independientemente. La prótesis inmediata/temporal NO
reemplaza una prótesis definitiva.
Durante el procedimiento o posterior a la instalación protésica removible, pueden ocurrir eventos
inherentes al tratante los que son propios de la técnica en sí o su uso, tales como, fracturas de tejido

[Página 23]
dental (piezas pilares), fracturas de paredes o piso del diente, fractura radicular, fractura coronaria,
fractura de ganchos metálicos, caries futuras por mala higiene y dieta cariogénica, fractura coronaria
de prótesis fija donde se engancha el retenedor (alambre que afirma la prótesis), inflamación de los
tejidos blandos circundantes, infecciones, dolor, incomodidad, fatiga de material, fractura de prótesis o
dientes artificiales, desalojo de dientes protésicos.
Luego de una instalación protésica, si el paciente la utiliza por primera vez, es normal sentir
incomodidad o cambios en la forma de comer o hablar, por lo que se recomienda practicar en casa,
leyendo en voz alta 10 minutos al día, comer cosas livianas y acostumbrarse a ellas. Si presenta dolor,
inflamación, ulceras o erosiones, debe suspender su uso, agendar una visita al especialista y utilizar la
prótesis 24 horas antes de su hora (todo el día), ideal dormir con ella sólo esa vez, de esta forma se
marcarán las zonas de sobre compresión para realizar desgastes precisos sobre la prótesis,
eliminando las molestias.
Recuerde que NO debe dormir con la prótesis (NUNCA), ya que puede generar inflamaciones, los
tejidos no descansan y proliferan hongos. Es frecuente la estomatitis sub-protésica por el mal diseño
de estas y utilizarlas sin descanso.
Las prótesis removibles no son eternas, se recomienda rebasar y ajustar las prótesis una vez por año,
e idealmente cambiarlas cuando se comiencen a sentir sueltas, esto es debido a que con el tiempo el
hueso o dientes (donde se soporta una prótesis) comienzan a reabsorberse o cambian biológicamente
de forma natural por lo que una prótesis ya no funcionará de la misma forma. Recuerde, no solo
higienizar sus dientes, sino también la prótesis, todos los días.
Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del paciente,
este deberá de pagar los costos adicionales que signifiquen corregir y mejorar el tratamiento.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`10 días`, `24 horas`, `3 meses`, `6 semanas`

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- estrecha relación al trabajo externo y envío de los laboratorios, lo que no es responsabilidad directa del
- tejidos blandos circundantes, infecciones, dolor, incomodidad, fatiga de material, fractura de prótesis o
- leyendo en voz alta 10 minutos al día, comer cosas livianas y acostumbrarse a ellas. Si presenta dolor,
- Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
- director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del paciente,
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_PROTESIS_REMOVIBLE-CO`, país `CO`, locale `es-CO`, hash `0f3c63f04609c20eb2aa820157b5ec30865afddb24fcb8480a1e98e884a8b530`.
- CL: id lógico `CONS_PROTESIS_REMOVIBLE-CL`, país `CL`, locale `es-CL`, hash `743ce176f90970865261753b31e426f305a1f84349237582940ff4c2e472e51d`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 17. CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL SOBRE IMPLANTES

- Código: `CONS_REHAB_IMPLANTES`
- Categoría: Consentimientos clínicos
- Páginas fuente: 24–25
- Especialidad: Rehabilitacion Oral
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `f2178af952800b4ee633ae3bedc0346efe2d11266820654c5e88a19282783f52`

### Texto fuente relevante

```text
[Página 24]
CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL SOBRE IMPLANTES
PROCEDIMIENTO(S) _______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
La rehabilitación oral sobre implantes busca devolver dientes perdidos mediante el uso de elementos
artificiales protésicos que se anclan a través de tornillos o se cementan en los implantes de titanio
integrados al hueso.
Dentro de las prótesis sobre implantes, se encuentran; coronas unitarias o plurales sobre implantes
(cementadas o atornilladas), sobredentaduras (removibles sobre implantes), prótesis hibridas (fijas)
atornilladas sobre implantes.
Para la fabricación de una corona o prótesis sobre implantes, al menos se necesitan 4 sesiones o más,
cada sesión con diferencia de 7 a 10 días. Por lo que no es un procedimiento rápido. La rapidez del
odontólogo está en estrecha relación al stock de insumos (empresa externa de implantes), avances de
los laboratorios (externos) y envíos por empresas de transporte nacional (Chilexpress o correos),
situaciones que no son responsabilidad directa del odontólogo o clínica DENTAL SEIS.
Posterior a la cirugía el implante puede quedar con una inclinación no favorable e imposible de
predecir por lo que se necesitará otro tipo de sistema de pernos lo que me podría llevar a tener que
pagar un costo adicional a lo ya presupuestado, de la misma forma algún diente provisional extra o
cualquier acción necesaria que favorezca el resultado final del tratamiento.
Si el paciente necesita extracciones previas a su tratamiento final, esto aumentará el tiempo de espera,
ya que el hueso se demora en cicatrizar 3 meses, será criterio del especialista cuando avanzar con las
siguientes etapas, el tiempo aumenta en pacientes con cicatrización lenta o enfermedades no
controladas.
Mientras cicatriza el tejido óseo, es posible utilizar prótesis temporal, provisoria e inmediata, las que se
instalan en el mismo momento de la extracción dental o aplicación de injertos, entendiendo que, son
prótesis diseñadas sólo como emergencia y con uso limitado, las que deberán ser ajustadas
constantemente hasta que cicatrice el tejido óseo (hueso) y se pueda comenzar con la etapa de una
prótesis definitiva. Una prótesis inmediata o provisoria y una prótesis definitiva son procedimientos
distintos por lo que el paciente debe pagar cada prótesis independientemente. La prótesis inmediata/
temporal NO reemplaza una prótesis definitiva sobre implantes.
Durante el procedimiento o posterior a la instalación de la rehabilitación sobre implantes, pueden
ocurrir eventos inherentes al odontólogo los que son propios de la técnica en sí o por su uso, tales
como, des-osteointegración de implantes (no se integró correctamente), desalojo de dientes
protésicos, fractura coronaria de la cerámica sobre implantes, fractura o desalojo de los tornillos y
aditamentos de implantología, fractura parcial o total de prótesis hibridas o sobredentaduras,
inflamación, dolor o molestias, incomodidad.

[Página 25]
Luego de una instalación protésica removible, si el paciente la utiliza por primera vez, es normal sentir
incomodidad o cambios en la forma de comer o hablar, por lo que se recomienda practicar en casa,
leyendo en voz alta 10 minutos al día, comer cosas livianas y acostumbrarse a ellas. Si presenta dolor,
inflamación, ulceras o erosiones, debe suspender su uso, agendar una visita al especialista y utilizar la
prótesis 24 horas antes de su hora (todo el día), ideal dormir con ella sólo esa vez, de esta forma se
marcarán las zonas de sobre compresión para realizar desgastes precisos sobre la prótesis,
eliminando las molestias.
Recuerde que NO debe dormir con la prótesis removible sobre implantes (NUNCA), ya que puede
generar inflamaciones, los tejidos no descansan y proliferan hongos. Es frecuente la estomatitis sub-
protésica por el mal diseño de estas y/o utilizarlas sin descanso.
Recuerde, no solo higienizar sus dientes, sino también, los implantes y la prótesis removible sobre
implantes, todos los días. En el caso de las prótesis fijas atornilladas, debe asistir periódicamente a
“desmontar, mantener y limpieza”, la que sólo puede realizar el odontólogo especialista.
Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del
paciente, este deberá de pagar los costos adicionales que signifiquen corregir y mejorar el
tratamiento.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de rehabilitación oral sobre implantes

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 24]
CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL SOBRE IMPLANTES
PROCEDIMIENTO(S) _______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
La rehabilitación oral sobre implantes busca devolver dientes perdidos mediante el uso de elementos
artificiales protésicos que se anclan a través de tornillos o se cementan en los implantes de titanio
integrados al hueso.
Dentro de las prótesis sobre implantes, se encuentran; coronas unitarias o plurales sobre implantes
(cementadas o atornilladas), sobredentaduras (removibles sobre implantes), prótesis hibridas (fijas)
atornilladas sobre implantes.
Para la fabricación de una corona o prótesis sobre implantes, al menos se necesitan 4 sesiones o más,
cada sesión con diferencia de 7 a 10 días. Por lo que no es un procedimiento rápido. La rapidez del
odontólogo está en estrecha relación al stock de insumos (empresa externa de implantes), avances de
los laboratorios (externos) y envíos por empresas de transporte nacional (Chilexpress o correos),
situaciones que no son responsabilidad directa del odontólogo o clínica {{company.name}}.
Posterior a la cirugía el implante puede quedar con una inclinación no favorable e imposible de
predecir por lo que se necesitará otro tipo de sistema de pernos lo que me podría llevar a tener que
pagar un costo adicional a lo ya presupuestado, de la misma forma algún diente provisional extra o
cualquier acción necesaria que favorezca el resultado final del tratamiento.
Si el paciente necesita extracciones previas a su tratamiento final, esto aumentará el tiempo de espera,
ya que el hueso se demora en cicatrizar 3 meses, será criterio del especialista cuando avanzar con las
siguientes etapas, el tiempo aumenta en pacientes con cicatrización lenta o enfermedades no
controladas.
Mientras cicatriza el tejido óseo, es posible utilizar prótesis temporal, provisoria e inmediata, las que se
instalan en el mismo momento de la extracción dental o aplicación de injertos, entendiendo que, son
prótesis diseñadas sólo como emergencia y con uso limitado, las que deberán ser ajustadas
constantemente hasta que cicatrice el tejido óseo (hueso) y se pueda comenzar con la etapa de una
prótesis definitiva. Una prótesis inmediata o provisoria y una prótesis definitiva son procedimientos
distintos por lo que el paciente debe pagar cada prótesis independientemente. La prótesis inmediata/
temporal NO reemplaza una prótesis definitiva sobre implantes.
Durante el procedimiento o posterior a la instalación de la rehabilitación sobre implantes, pueden
ocurrir eventos inherentes al odontólogo los que son propios de la técnica en sí o por su uso, tales
como, des-osteointegración de implantes (no se integró correctamente), desalojo de dientes
protésicos, fractura coronaria de la cerámica sobre implantes, fractura o desalojo de los tornillos y
aditamentos de implantología, fractura parcial o total de prótesis hibridas o sobredentaduras,
inflamación, dolor o molestias, incomodidad.

[Página 25]
Luego de una instalación protésica removible, si el paciente la utiliza por primera vez, es normal sentir
incomodidad o cambios en la forma de comer o hablar, por lo que se recomienda practicar en casa,
leyendo en voz alta 10 minutos al día, comer cosas livianas y acostumbrarse a ellas. Si presenta dolor,
inflamación, ulceras o erosiones, debe suspender su uso, agendar una visita al especialista y utilizar la
prótesis 24 horas antes de su hora (todo el día), ideal dormir con ella sólo esa vez, de esta forma se
marcarán las zonas de sobre compresión para realizar desgastes precisos sobre la prótesis,
eliminando las molestias.
Recuerde que NO debe dormir con la prótesis removible sobre implantes (NUNCA), ya que puede
generar inflamaciones, los tejidos no descansan y proliferan hongos. Es frecuente la estomatitis sub-
protésica por el mal diseño de estas y/o utilizarlas sin descanso.
Recuerde, no solo higienizar sus dientes, sino también, los implantes y la prótesis removible sobre
implantes, todos los días. En el caso de las prótesis fijas atornilladas, debe asistir periódicamente a
“desmontar, mantener y limpieza”, la que sólo puede realizar el odontólogo especialista.
Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del
paciente, este deberá de pagar los costos adicionales que signifiquen corregir y mejorar el
tratamiento.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`10 días`, `24 horas`, `3 meses`

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- situaciones que no son responsabilidad directa del odontólogo o clínica DENTAL SEIS.
- inflamación, dolor o molestias, incomodidad.
- leyendo en voz alta 10 minutos al día, comer cosas livianas y acostumbrarse a ellas. Si presenta dolor,
- Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y
- director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_REHAB_IMPLANTES-CO`, país `CO`, locale `es-CO`, hash `ab5540ac6eccfc3e0fe127423ff133fbb6195caf96f28cec9fb257397c561ce6`.
- CL: id lógico `CONS_REHAB_IMPLANTES-CL`, país `CL`, locale `es-CL`, hash `1b3df0071c3cfb4e5bcc399dba7f09773dcb774aa199fc1cfa684cbdcd1da2c3`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 18. APROBACIÓN ESTÉTICA DE REHABILITACIÓN ORAL

- Código: `CONS_APROBACION_ESTETICA`
- Categoría: Constancias y reconocimientos
- Páginas fuente: 26–26
- Especialidad: Rehabilitacion Oral
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `e48a95e0cab02e987bc1b3a97af4a2a84e4920fd75c5db89434b34c38cc60fb9`

### Texto fuente relevante

```text
[Página 26]
CONSENTIMIENTO DE REHABILITACION ORAL APROBACIÓN ESTÉTICA
E N R E L A C I O N A L
PROCEDIMIENTO:
_______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
Acepto y apruebo en color, forma, tamaño, posición y diseño mi tratamiento protésico fijo y/o
removible por lo que autorizo a terminar definitivamente este proceso. Consiento enviar a
terminar el trabajo al laboratorio y me encuentro conforme con el resultado estético final.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA
```

### Texto normalizado CO / es-CO

```markdown
# Aprobación estética de rehabilitación oral

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 26]
CONSENTIMIENTO DE REHABILITACION ORAL APROBACIÓN ESTÉTICA
E N R E L A C I O N A L
PROCEDIMIENTO:
_______________________________________________________________
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
Acepto y apruebo en color, forma, tamaño, posición y diseño mi tratamiento protésico fijo y/o
removible por lo que autorizo a terminar definitivamente este proceso. Consiento enviar a
terminar el trabajo al laboratorio y me encuentro conforme con el resultado estético final.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_APROBACION_ESTETICA-CO`, país `CO`, locale `es-CO`, hash `a40fa497757cb8d1f2a55723f743b800908dc3e4b0572e160f0098abc6f1b58e`.
- CL: id lógico `CONS_APROBACION_ESTETICA-CL`, país `CL`, locale `es-CL`, hash `12d9000724e7b30173097592c0f9a219b211332581a4dcfde07d6b05eac4c515`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 19. CONSENTIMIENTO INFORMADO DE URGENCIA ODONTOLÓGICA

- Código: `CONS_URGENCIA`
- Categoría: Consentimientos clínicos
- Páginas fuente: 27–27
- Especialidad: Urgencia
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `9eb0ccb7e006257f1a8dc00e485b194e9178eb04e088e2dbf10a302127318d93`

### Texto fuente relevante

```text
[Página 27]
CONSENTIMIENTO DE URGENCIA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
Asisto por urgencia odontológica y luego de una evaluación clínica complementada con imágenes
r a d i o g r á fi c a s t e n g o c o m o p o s i b l e
diagnóstico_________________________________________________________
Y p a r a s o l u c i o n a r m i u r g e n c i a a c e p t o e l t r a t a m i e n t o d e
_______________________________________________.
Comprendo que el tratamiento de urgencia no es definitivo solo ayuda a disminuir temporalmente la
infección, cuadro clínico o dolor por lo que luego, deberé realizar un diagnóstico integral y ser derivado
a la especialidad correspondiente quien me entregará el tratamiento definitivo. Existe la posibilidad que
la urgencia dental sobrepase la capacidad de resolución del centro dental debiendo ser derivado a
nivel hospitalario o establecimientos de alta complejidad.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de urgencia odontológica

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 27]
CONSENTIMIENTO DE URGENCIA
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
Asisto por urgencia odontológica y luego de una evaluación clínica complementada con imágenes
r a d i o g r á fi c a s t e n g o c o m o p o s i b l e
diagnóstico_________________________________________________________
Y p a r a s o l u c i o n a r m i u r g e n c i a a c e p t o e l t r a t a m i e n t o d e
_______________________________________________.
Comprendo que el tratamiento de urgencia no es definitivo solo ayuda a disminuir temporalmente la
infección, cuadro clínico o dolor por lo que luego, deberé realizar un diagnóstico integral y ser derivado
a la especialidad correspondiente quien me entregará el tratamiento definitivo. Existe la posibilidad que
la urgencia dental sobrepase la capacidad de resolución del centro dental debiendo ser derivado a
nivel hospitalario o establecimientos de alta complejidad.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- infección, cuadro clínico o dolor por lo que luego, deberé realizar un diagnóstico integral y ser derivado
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_URGENCIA-CO`, país `CO`, locale `es-CO`, hash `ea0e040a62bfb380cdaf94e074d325df5aa13fddbbba8c07c987a3ad3a687bb8`.
- CL: id lógico `CONS_URGENCIA-CL`, país `CL`, locale `es-CL`, hash `9a730374c30634ce75a60e9f4baf076c00371edd7920c5b16cf2c37aaf0fd82e`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 20. CONSENTIMIENTO INFORMADO DE ÓXIDO NITROSO

- Código: `CONS_OXIDO_NITROSO`
- Categoría: Consentimientos clínicos
- Páginas fuente: 28–29
- Especialidad: Sedacion
- Firmante: `ADULT_OR_REPRESENTATIVE`
- Resultado: `PENDING`
- Fragmento SHA-256: `201ae64cb40358f98d98c3ea9d3fe6b2272954735e2e13b6dc2be0a7a66c52c3`

### Texto fuente relevante

```text
[Página 28]
CONSENTIMIENTO INFORMADO DE ÓXIDO NITROSO
Yo ________________________________, RUT: _____________________ como paciente o en
calidad de tutor legal del paciente __________________________________,
RUT:________________________, declaro lo siguiente:
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos, óxido nitroso y del procedimiento a realizar,
entendiendo que:
El nivel de sedación es mínimo a moderado de tipo inhalatoria intranasal con óxido nitroso/oxígeno,
respecto al óxido nitroso, entiendo y acepto que:
• En ocasiones proporciona relajación y/o risa.
• Seré sometido al uso de óxido nitroso por un especialista calificado y certificado.
• Estaré despierto y completamente consciente de mi entorno.
• Seré capaz de responder a preguntas y seguir instrucciones de mi tratante.
• El O. Nitroso tiene contraindicaciones y no debo estar resfriado ni enfermo, tampoco mis vías
respiratorias deben estar infectadas con algún patógeno ni recientemente debo haberme
realizado una cirugía del oído medio.
• El O.N se utiliza en pacientes para el control del dolor, ansiedad, miedo o paciente con
necesidades especiales.
Las posibles complicaciones por el uso de óxido nitroso son las siguientes
• Náuseas y vómitos, siendo la complicación más usual, pero de baja frecuencia. Por esto siendo
ADULTO, NO debo comer 8 horas antes del procedimiento alimentos grasos, 6 horas
alimentos sólidos ni ingerir líquidos 2 horas antes y para los LACTANTES, seguir un ayuno de
4 horas para sólidos y 2 horas para líquidos. Recordar que la leche se considera dentro del
ítem de alimento sólido.
• Hormigueo en dedos, mejilla, labios, lengua, cuello, hombros y/o cabeza, siendo pasajero
• Calor, rubor o enrojecimiento, siendo un efecto pasajero y temporal
• Sensación de estar “fuera del cuerpo”, flotando, ido o volando, siendo un efecto pasajero.
• Sentir lentitud al hablar o movilizar alguna estructura del cuerpo, siendo momentáneo.
• Al terminar el procedimiento o en su fase final, posibles temblores o movimientos involuntarios,
los que son completamente transitorios y una vez recuperado se detienen.
Es posible que la sensación que me produzca el uso de óxido nitroso sea desagradable y estimule mi
actividad y función motora, lo que puede llevar a suspender la atención y procedimiento por parte de
mi profesional tratante o mía. En algunos casos inclusive, se puede complementar con alguna otra

[Página 29]
técnica de sedación o control de estímulos para llevar a cabo la intervención, lo que me será explicado
previamente a mi o a mi tutor legal.
Aunque el uso del óxido nitroso se considera una práctica segura y eficaz, siempre debo informar en
caso de estar embarazada al personal de salud para recibir el tratamiento indicado.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes
de realizarlo.
Firma _____________________ CURICÓ ___ de
_______del _____
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de óxido nitroso

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 28]
CONSENTIMIENTO INFORMADO DE ÓXIDO NITROSO
Yo ________________________________, RUT: _____________________ como paciente o en
calidad de tutor legal del paciente __________________________________,
RUT:________________________, declaro lo siguiente:
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos, óxido nitroso y del procedimiento a realizar,
entendiendo que:
El nivel de sedación es mínimo a moderado de tipo inhalatoria intranasal con óxido nitroso/oxígeno,
respecto al óxido nitroso, entiendo y acepto que:
• En ocasiones proporciona relajación y/o risa.
• Seré sometido al uso de óxido nitroso por un especialista calificado y certificado.
• Estaré despierto y completamente consciente de mi entorno.
• Seré capaz de responder a preguntas y seguir instrucciones de mi tratante.
• El O. Nitroso tiene contraindicaciones y no debo estar resfriado ni enfermo, tampoco mis vías
respiratorias deben estar infectadas con algún patógeno ni recientemente debo haberme
realizado una cirugía del oído medio.
• El O.N se utiliza en pacientes para el control del dolor, ansiedad, miedo o paciente con
necesidades especiales.
Las posibles complicaciones por el uso de óxido nitroso son las siguientes
• Náuseas y vómitos, siendo la complicación más usual, pero de baja frecuencia. Por esto siendo
ADULTO, NO debo comer 8 horas antes del procedimiento alimentos grasos, 6 horas
alimentos sólidos ni ingerir líquidos 2 horas antes y para los LACTANTES, seguir un ayuno de
4 horas para sólidos y 2 horas para líquidos. Recordar que la leche se considera dentro del
ítem de alimento sólido.
• Hormigueo en dedos, mejilla, labios, lengua, cuello, hombros y/o cabeza, siendo pasajero
• Calor, rubor o enrojecimiento, siendo un efecto pasajero y temporal
• Sensación de estar “fuera del cuerpo”, flotando, ido o volando, siendo un efecto pasajero.
• Sentir lentitud al hablar o movilizar alguna estructura del cuerpo, siendo momentáneo.
• Al terminar el procedimiento o en su fase final, posibles temblores o movimientos involuntarios,
los que son completamente transitorios y una vez recuperado se detienen.
Es posible que la sensación que me produzca el uso de óxido nitroso sea desagradable y estimule mi
actividad y función motora, lo que puede llevar a suspender la atención y procedimiento por parte de
mi profesional tratante o mía. En algunos casos inclusive, se puede complementar con alguna otra

[Página 29]
técnica de sedación o control de estímulos para llevar a cabo la intervención, lo que me será explicado
previamente a mi o a mi tutor legal.
Aunque el uso del óxido nitroso se considera una práctica segura y eficaz, siempre debo informar en
caso de estar embarazada al personal de salud para recibir el tratamiento indicado.
Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo
responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado
nuevas dudas que pueda tener.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes
de realizarlo.
Firma _____________________ CURICÓ ___ de
_______del _____

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`2 horas`, `4 horas`, `6 horas`, `8 horas`

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos, óxido nitroso y del procedimiento a realizar,
- • El O. Nitroso tiene contraindicaciones y no debo estar resfriado ni enfermo, tampoco mis vías
- • El O.N se utiliza en pacientes para el control del dolor, ansiedad, miedo o paciente con
- Las posibles complicaciones por el uso de óxido nitroso son las siguientes
- • Náuseas y vómitos, siendo la complicación más usual, pero de baja frecuencia. Por esto siendo
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_OXIDO_NITROSO-CO`, país `CO`, locale `es-CO`, hash `9be01c92cbee762264e0aa0475a432d34ed455ccfb74dc7aea9a647f14b598a1`.
- CL: id lógico `CONS_OXIDO_NITROSO-CL`, país `CL`, locale `es-CL`, hash `afa1909c56f66991a49cd8260c3e64ce68235865ea11497df6eb88e1c2aa3535`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 21. CONSENTIMIENTO INFORMADO DE PLANO DE RELAJACIÓN Y ESTABILIZACIÓN

- Código: `CONS_PLANO_RELAJACION`
- Categoría: Consentimientos clínicos
- Páginas fuente: 30–30
- Especialidad: Rehabilitacion Oral
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `e5aa91ab43e432a2a7a3346ffecdc8b6972a21ab9472d639a1063fa2a1697025`

### Texto fuente relevante

```text
[Página 30]
CONSENTIMIENTO INFORMADO DE PLANO DE RELAJACION Y ESTABILIZACIÓN
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
El plano de relajación o estabilización oclusal consiste en un dispositivo interoclusal de acrílico
que cubre los dientes para protegerlos de desgastes excesivos no funcionales. El plano NO
resuelve por sí solo el bruxismo ya que se necesita un enfoque multidisciplinario y otros
tratamientos.
El plano se debe utilizar durante la noche mientras se duerme y en ocasiones durante el día
(según corresponda), en caso de molestias se debe asistir con el odontólogo tratante para
modificar y ajustar el plano de relajación. Debo seguir las indicaciones de mi tratante en cuanto
al tiempo y forma de uso. Es normal y transitorio sentir salivación excesiva o incomodidad los
primeros días. Cada día se debe higienizar el plano utilizando agua de la llave y un cepillo duro
(EXCLUSIVO PARA EL PLANO), además en el comercio venden pastillas efervescentes para
limpiar estos elementos protésicos. Me comprometo a remover el plano de mi boca utilizando
ambas manos y guardándolo adecuadamente para evitar su pérdida o fractura y debo asistir a
los controles que mi odontólogo indique.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE
```

### Texto normalizado CO / es-CO

```markdown
# Consentimiento informado de plano de relajación y estabilización

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 30]
CONSENTIMIENTO INFORMADO DE PLANO DE RELAJACION Y ESTABILIZACIÓN
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
El plano de relajación o estabilización oclusal consiste en un dispositivo interoclusal de acrílico
que cubre los dientes para protegerlos de desgastes excesivos no funcionales. El plano NO
resuelve por sí solo el bruxismo ya que se necesita un enfoque multidisciplinario y otros
tratamientos.
El plano se debe utilizar durante la noche mientras se duerme y en ocasiones durante el día
(según corresponda), en caso de molestias se debe asistir con el odontólogo tratante para
modificar y ajustar el plano de relajación. Debo seguir las indicaciones de mi tratante en cuanto
al tiempo y forma de uso. Es normal y transitorio sentir salivación excesiva o incomodidad los
primeros días. Cada día se debe higienizar el plano utilizando agua de la llave y un cepillo duro
(EXCLUSIVO PARA EL PLANO), además en el comercio venden pastillas efervescentes para
limpiar estos elementos protésicos. Me comprometo a remover el plano de mi boca utilizando
ambas manos y guardándolo adecuadamente para evitar su pérdida o fractura y debo asistir a
los controles que mi odontólogo indique.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_PLANO_RELAJACION-CO`, país `CO`, locale `es-CO`, hash `dd251ff72030081ac461ec2d8d3752a55b196ed0d8e58826a599ec5fd4703ffa`.
- CL: id lógico `CONS_PLANO_RELAJACION-CL`, país `CL`, locale `es-CL`, hash `b5c3a5560db1c1580656d8f9f834f26392f41819cab499584ce85dcbc52b7dad`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 22. RETIRO ANTICIPADO DE ORTODONCIA Y PACIENTE EXTERNO

- Código: `CONS_RETIRO_ORTODONCIA`
- Categoría: Constancias y reconocimientos
- Páginas fuente: 31–31
- Especialidad: Ortodoncia
- Firmante: `ADULT_SELF`
- Resultado: `PENDING`
- Fragmento SHA-256: `cb72c1293a0ffa5fd13d33ce5ba10ef07ebe6130d55ee59d36d8f1df1c618ed7`

### Texto fuente relevante

```text
[Página 31]
CONSENTIMIENTO INFORMADO DE RETIRO ORTODONCIA ANTICIPADO Y PACIENTE
EXTERNO
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
Por diferentes motivos personales y voluntariamente indico mi deseo de terminar el tratamiento de
ortodoncia anticipadamente, comprendo plenamente los riesgos de terminar voluntariamente el
proceso antes de tiempo y las consecuencias que pueda traer en el futuro, el odontólogo me ha
explicado y resuelto todas mis dudas e inquietudes por lo que libero de toda responsabilidad al
profesional y a la clínica dental, entendiendo que, no voy a completar el tratamiento como
corresponde.
Siendo un paciente de clínica externa, donde instalé y realicé mi tratamiento en otra clínica ajena a
CLINICA SEIS. Decido por motivos personales no seguir con el tratamiento y voluntariamente darle
término anticipado, liberando de toda responsabilidad al personal, a la doctora que retirara mi
ortodoncia y clínica DENTAL SEIS ya que esta es MI decisión completamente voluntaria.
Reitero que acepto las condiciones y consecuencias de la decisión que he tomado.
Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica DENTAL SEIS para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE
```

### Texto normalizado CO / es-CO

```markdown
# Retiro anticipado de ortodoncia y paciente externo

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 31]
CONSENTIMIENTO INFORMADO DE RETIRO ORTODONCIA ANTICIPADO Y PACIENTE
EXTERNO
El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades
sistémicas, hábitos y consumo de alcohol o drogas.
Por diferentes motivos personales y voluntariamente indico mi deseo de terminar el tratamiento de
ortodoncia anticipadamente, comprendo plenamente los riesgos de terminar voluntariamente el
proceso antes de tiempo y las consecuencias que pueda traer en el futuro, el odontólogo me ha
explicado y resuelto todas mis dudas e inquietudes por lo que libero de toda responsabilidad al
profesional y a la clínica dental, entendiendo que, no voy a completar el tratamiento como
corresponde.
Siendo un paciente de clínica externa, donde instalé y realicé mi tratamiento en otra clínica ajena a
CLINICA SEIS. Decido por motivos personales no seguir con el tratamiento y voluntariamente darle
término anticipado, liberando de toda responsabilidad al personal, a la doctora que retirara mi
ortodoncia y clínica {{company.name}} ya que esta es MI decisión completamente voluntaria.
Reitero que acepto las condiciones y consecuencias de la decisión que he tomado.
Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que
perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e
intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi
garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis
garantías sobre el tratamiento y no existirá devolución de dinero.
Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo
la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente,
asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes
de realizarlo.
FIRMA PACIENTE

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

No se detectaron valores, porcentajes o plazos explícitos por patrón automático.

### Riesgos y advertencias detectadas

- El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y
- complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que:
- ortodoncia anticipadamente, comprendo plenamente los riesgos de terminar voluntariamente el
- explicado y resuelto todas mis dudas e inquietudes por lo que libero de toda responsabilidad al
- término anticipado, liberando de toda responsabilidad al personal, a la doctora que retirara mi
- Comprendo que tengo garantías por los tratamientos realizados en clínica DENTAL SEIS, los que
- garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica
- garantías sobre el tratamiento y no existirá devolución de dinero.

### Referencias institucionales sustituidas

- `DENTAL SEIS` → `{{company.name}}`

### Revisión de variantes Colombia y Chile

- CO: id lógico `CONS_RETIRO_ORTODONCIA-CO`, país `CO`, locale `es-CO`, hash `69085805835f941db68b264f7dce0ecfbd5fe8c80bcf6fa3712afe47c8768c62`.
- CL: id lógico `CONS_RETIRO_ORTODONCIA-CL`, país `CL`, locale `es-CL`, hash `cfb9b47ceb28389ce13c2f1df972bf5ec06b0d8ad2b50246b831bf439891549e`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 23. INDICACIONES DE CIRUGÍA

- Código: `IND_CIRUGIA`
- Categoría: Indicaciones
- Páginas fuente: 32–32
- Especialidad: Cirugia
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `cfc5ff21bbab0c7760b04072f0699e3baebb1505f1b91b3286dfcdab6db8f2f6`

### Texto fuente relevante

```text
[Página 32]
INDICACIONES CIRUGÍA
• Morder gasa por 45 minutos, luego remover con delicadeza y desecharla.
• En caso de hemorragia o sangrado espontáneo poner nueva gasa en la zona afectada.
• No escupir, no enjuagarse con ningún enjuague bucal o líquido.
• No comer mientras dure el efecto de la anestesia.
• Dieta blanda y fría las primeras 48 horas, luego aumentar de a poco la consistencia y
temperatura de alimentos.
• Comer o masticar por el lado contrario a la cirugía.
• Estornudar o toser con la boca abierta.
• No aspirar, no succionar, no utilizar bombillas o popotes.
• No fumar por 7 días.
• No hacer deportes por 7 días.
• Reposo relativo por 3 días.
• Dormir semi sentado, la cabeza debe estar por sobre los pies.
• Cepillado normal, pero sin tocar el área afectada, para enjuagarse mueva la cabeza y para
escupir sólo abra la boca y permita que el líquido caiga por sí solo. NO escupir y NO
enjuagarse.
• Hielo local no directo. Cubra con un paño el hielo y aplique en la zona afectada.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de cirugía

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 32]
INDICACIONES CIRUGÍA
• Morder gasa por 45 minutos, luego remover con delicadeza y desecharla.
• En caso de hemorragia o sangrado espontáneo poner nueva gasa en la zona afectada.
• No escupir, no enjuagarse con ningún enjuague bucal o líquido.
• No comer mientras dure el efecto de la anestesia.
• Dieta blanda y fría las primeras 48 horas, luego aumentar de a poco la consistencia y
temperatura de alimentos.
• Comer o masticar por el lado contrario a la cirugía.
• Estornudar o toser con la boca abierta.
• No aspirar, no succionar, no utilizar bombillas o popotes.
• No fumar por 7 días.
• No hacer deportes por 7 días.
• Reposo relativo por 3 días.
• Dormir semi sentado, la cabeza debe estar por sobre los pies.
• Cepillado normal, pero sin tocar el área afectada, para enjuagarse mueva la cabeza y para
escupir sólo abra la boca y permita que el líquido caiga por sí solo. NO escupir y NO
enjuagarse.
• Hielo local no directo. Cubra con un paño el hielo y aplique en la zona afectada.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`3 días`, `48 horas`, `7 días`

### Riesgos y advertencias detectadas

- • En caso de hemorragia o sangrado espontáneo poner nueva gasa en la zona afectada.
- • No comer mientras dure el efecto de la anestesia.
- • Seguir receta indicada. Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_CIRUGIA-CO`, país `CO`, locale `es-CO`, hash `efb9f8931dff7710c78e55fc45b46f38f3974aecd13c56f4830c34e7fc2b6f57`.
- CL: id lógico `IND_CIRUGIA-CL`, país `CL`, locale `es-CL`, hash `01ed3ab265645bd02631be72cef5be408aec587eb49400d7bfd92eaddf3c91a5`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 24. INDICACIONES DE CIRUGÍA DE IMPLANTES

- Código: `IND_CIRUGIA_IMPLANTES`
- Categoría: Indicaciones
- Páginas fuente: 33–33
- Especialidad: Implantologia
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `a43c3b28603fce8b17b99dfd0a5df976bf61f80ce4de169afd940fe842a4f1b6`

### Texto fuente relevante

```text
[Página 33]
INDICACIONES CIRUGÍA DE IMPLANTES
Reposo absoluto el primer y segundo día. Reposo relativo los días siguientes, mientras haya malestar.
No agacharse, no hacer fuerzas, permanecer sentado o semisentado, incluso en las dos primeras
noches. Suspender actividades deportivas si las realiza por 1 semana al menos.
Alimentación blanda: comidas picadas o molidas. Evitar alimentos que dejen residuos, y los que
fermentan, como masas y azúcares.
No fumar por al menos una semana.
Higiene cuidadosa. Cepillar cuidadosamente las áreas dentadas no involucradas en la cirugía. La
herida y los puntos, limpiarla con un algodón empapado en un colutorio con clorhexidina 0.12%, como
Perioaid u Oralgene.
En el caso de haberse indicado antibióticos, mantener rigurosamente su dosis y frecuencia por los
días indicados. No puede suspenderse sin consulta.
Los analgésicos y anti-inflamatorios prescritos pueden espaciarse en la medida que las molestias
vayan disminuyendo, hasta suprimirse totalmente.
Durante el primer y segundo día, aplicar hielo (NUNCA DIRECTO) en una bolsa sobre la parte de la
cara operada, en intervalos de 10 minutos por 10 minutos.
Asistir al control y retiro de sutura a los 14 días.
Avisar al cirujano Dr.(a) de presentar hemorragias severas u otras anomalías que pudieran sugerir
complicaciones, asistir a la clínica.
Si tiene hematoma es normal y puede demorar unos 10 a 15 días en remitir.
Comprendo que debo seguir las siguientes indicaciones entregadas por mi odontólogo tratante:
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de cirugía de implantes

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 33]
INDICACIONES CIRUGÍA DE IMPLANTES
Reposo absoluto el primer y segundo día. Reposo relativo los días siguientes, mientras haya malestar.
No agacharse, no hacer fuerzas, permanecer sentado o semisentado, incluso en las dos primeras
noches. Suspender actividades deportivas si las realiza por 1 semana al menos.
Alimentación blanda: comidas picadas o molidas. Evitar alimentos que dejen residuos, y los que
fermentan, como masas y azúcares.
No fumar por al menos una semana.
Higiene cuidadosa. Cepillar cuidadosamente las áreas dentadas no involucradas en la cirugía. La
herida y los puntos, limpiarla con un algodón empapado en un colutorio con clorhexidina 0.12%, como
Perioaid u Oralgene.
En el caso de haberse indicado antibióticos, mantener rigurosamente su dosis y frecuencia por los
días indicados. No puede suspenderse sin consulta.
Los analgésicos y anti-inflamatorios prescritos pueden espaciarse en la medida que las molestias
vayan disminuyendo, hasta suprimirse totalmente.
Durante el primer y segundo día, aplicar hielo (NUNCA DIRECTO) en una bolsa sobre la parte de la
cara operada, en intervalos de 10 minutos por 10 minutos.
Asistir al control y retiro de sutura a los 14 días.
Avisar al cirujano Dr.(a) de presentar hemorragias severas u otras anomalías que pudieran sugerir
complicaciones, asistir a la clínica.
Si tiene hematoma es normal y puede demorar unos 10 a 15 días en remitir.
Comprendo que debo seguir las siguientes indicaciones entregadas por mi odontólogo tratante:

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`1 semana`, `14 días`, `15 días`

### Riesgos y advertencias detectadas

- complicaciones, asistir a la clínica.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_CIRUGIA_IMPLANTES-CO`, país `CO`, locale `es-CO`, hash `814675c3a2f3f0aef79b3735c6b2eea4589f31936c59072d8b920788d46ad6d6`.
- CL: id lógico `IND_CIRUGIA_IMPLANTES-CL`, país `CL`, locale `es-CL`, hash `f7efcbbeccf1bb6fcd83c8bddbd115af033a57a2ce14539a391b0dd9c59fac41`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 25. INDICACIONES DE ENDODONCIA

- Código: `IND_ENDODONCIA`
- Categoría: Indicaciones
- Páginas fuente: 34–34
- Especialidad: Endodoncia
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `0157e0233b4756840962f73febaf5c6c3789e18e316168d8b3f802517c5b609b`

### Texto fuente relevante

```text
[Página 34]
INDICACIONES ENDODONCIA
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de
la anestesia. Espere 2 horas antes de comer.
• Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado
endodóntico. Lo importante es realizar la obturación final antes del primer mes de
terminada la endodoncia.
• Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede
desalojar la obturación provisoria al usar hilo dental o con el cepillado.
• Es normal sentir sensibilidad localizada en el diente las primeras 48 horas.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES BLANQUEAMIENTO
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros.
• Evite alimentos muy fríos los primeros días.
• No fumar.
• En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar
pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave.
APLICACIÓN DE FLUOR BARNIZ
• No toque el barniz o sus dientes con los dedos
• No comer por 3 horas.
• No tomar agua por 1 hora.
• No cepillar los dientes por 12 horas.
• Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo.
• Cambiar cepillo por uno nuevo.
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de endodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 34]
INDICACIONES ENDODONCIA
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de
la anestesia. Espere 2 horas antes de comer.
• Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado
endodóntico. Lo importante es realizar la obturación final antes del primer mes de
terminada la endodoncia.
• Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede
desalojar la obturación provisoria al usar hilo dental o con el cepillado.
• Es normal sentir sensibilidad localizada en el diente las primeras 48 horas.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES BLANQUEAMIENTO
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros.
• Evite alimentos muy fríos los primeros días.
• No fumar.
• En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar
pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave.
APLICACIÓN DE FLUOR BARNIZ
• No toque el barniz o sus dientes con los dedos
• No comer por 3 horas.
• No tomar agua por 1 hora.
• No cepillar los dientes por 12 horas.
• Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo.
• Cambiar cepillo por uno nuevo.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`1 hora`, `12 horas`, `2 horas`, `3 horas`, `48 horas`

### Riesgos y advertencias detectadas

- la anestesia. Espere 2 horas antes de comer.
- • Seguir receta indicada. Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_ENDODONCIA-CO`, país `CO`, locale `es-CO`, hash `271a3a6b4bf7e197d1895b6bf48ad9ee01501055d7fbf5874568ee67cf944e72`.
- CL: id lógico `IND_ENDODONCIA-CL`, país `CL`, locale `es-CL`, hash `0bb48d494fdd954c6fe3aec557f19af4503e83ffa7b42f1b0c8aa3b3efc99d3f`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 26. INDICACIONES DE BLANQUEAMIENTO

- Código: `IND_BLANQUEAMIENTO`
- Categoría: Indicaciones
- Páginas fuente: 34–34
- Especialidad: Estetica
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `0157e0233b4756840962f73febaf5c6c3789e18e316168d8b3f802517c5b609b`

### Texto fuente relevante

```text
[Página 34]
INDICACIONES ENDODONCIA
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de
la anestesia. Espere 2 horas antes de comer.
• Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado
endodóntico. Lo importante es realizar la obturación final antes del primer mes de
terminada la endodoncia.
• Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede
desalojar la obturación provisoria al usar hilo dental o con el cepillado.
• Es normal sentir sensibilidad localizada en el diente las primeras 48 horas.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES BLANQUEAMIENTO
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros.
• Evite alimentos muy fríos los primeros días.
• No fumar.
• En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar
pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave.
APLICACIÓN DE FLUOR BARNIZ
• No toque el barniz o sus dientes con los dedos
• No comer por 3 horas.
• No tomar agua por 1 hora.
• No cepillar los dientes por 12 horas.
• Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo.
• Cambiar cepillo por uno nuevo.
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de blanqueamiento

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 34]
INDICACIONES ENDODONCIA
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de
la anestesia. Espere 2 horas antes de comer.
• Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado
endodóntico. Lo importante es realizar la obturación final antes del primer mes de
terminada la endodoncia.
• Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede
desalojar la obturación provisoria al usar hilo dental o con el cepillado.
• Es normal sentir sensibilidad localizada en el diente las primeras 48 horas.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES BLANQUEAMIENTO
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros.
• Evite alimentos muy fríos los primeros días.
• No fumar.
• En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar
pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave.
APLICACIÓN DE FLUOR BARNIZ
• No toque el barniz o sus dientes con los dedos
• No comer por 3 horas.
• No tomar agua por 1 hora.
• No cepillar los dientes por 12 horas.
• Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo.
• Cambiar cepillo por uno nuevo.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`1 hora`, `12 horas`, `2 horas`, `3 horas`, `48 horas`

### Riesgos y advertencias detectadas

- la anestesia. Espere 2 horas antes de comer.
- • Seguir receta indicada. Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_BLANQUEAMIENTO-CO`, país `CO`, locale `es-CO`, hash `61e8a75cc493a077a2b21d330615064b9485a4a4462f96b155abb88ff6ccea58`.
- CL: id lógico `IND_BLANQUEAMIENTO-CL`, país `CL`, locale `es-CL`, hash `78c1d8ee7a7b3b8175183bd06c085bd1eb86813741c34b6c4b4d494fc8ddc5d4`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 27. APLICACIÓN DE FLÚOR BARNIZ

- Código: `IND_FLUOR_BARNIZ`
- Categoría: Indicaciones
- Páginas fuente: 34–34
- Especialidad: Odontopediatria
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `0157e0233b4756840962f73febaf5c6c3789e18e316168d8b3f802517c5b609b`

### Texto fuente relevante

```text
[Página 34]
INDICACIONES ENDODONCIA
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de
la anestesia. Espere 2 horas antes de comer.
• Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado
endodóntico. Lo importante es realizar la obturación final antes del primer mes de
terminada la endodoncia.
• Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede
desalojar la obturación provisoria al usar hilo dental o con el cepillado.
• Es normal sentir sensibilidad localizada en el diente las primeras 48 horas.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES BLANQUEAMIENTO
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros.
• Evite alimentos muy fríos los primeros días.
• No fumar.
• En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar
pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave.
APLICACIÓN DE FLUOR BARNIZ
• No toque el barniz o sus dientes con los dedos
• No comer por 3 horas.
• No tomar agua por 1 hora.
• No cepillar los dientes por 12 horas.
• Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo.
• Cambiar cepillo por uno nuevo.
```

### Texto normalizado CO / es-CO

```markdown
# Aplicación de flúor barniz

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 34]
INDICACIONES ENDODONCIA
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de
la anestesia. Espere 2 horas antes de comer.
• Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado
endodóntico. Lo importante es realizar la obturación final antes del primer mes de
terminada la endodoncia.
• Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede
desalojar la obturación provisoria al usar hilo dental o con el cepillado.
• Es normal sentir sensibilidad localizada en el diente las primeras 48 horas.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES BLANQUEAMIENTO
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros.
• Evite alimentos muy fríos los primeros días.
• No fumar.
• En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar
pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave.
APLICACIÓN DE FLUOR BARNIZ
• No toque el barniz o sus dientes con los dedos
• No comer por 3 horas.
• No tomar agua por 1 hora.
• No cepillar los dientes por 12 horas.
• Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo.
• Cambiar cepillo por uno nuevo.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`1 hora`, `12 horas`, `2 horas`, `3 horas`, `48 horas`

### Riesgos y advertencias detectadas

- la anestesia. Espere 2 horas antes de comer.
- • Seguir receta indicada. Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_FLUOR_BARNIZ-CO`, país `CO`, locale `es-CO`, hash `205af77e899aa6ff7b4fb18e2f990c97b1d303ccbfa0ddd237d43d8871360d70`.
- CL: id lógico `IND_FLUOR_BARNIZ-CL`, país `CL`, locale `es-CL`, hash `ce2735354d9726165e71c069921a35170c5cdbb8d3bb7de8337c2a0c7f01ee38`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 28. INDICACIONES DE OBTURACIONES EN RESINA

- Código: `IND_OBTURACIONES_RESINA`
- Categoría: Indicaciones
- Páginas fuente: 35–36
- Especialidad: Operatoria
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `f7b8b445c639aa73d1306a3fa9d38ae8d3db845345c6d648fbdd27ac56e9b770`

### Texto fuente relevante

```text
[Página 35]
INDICACIONES DE OBTURACIONES – RESINA
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES PARA DESTARTRAJE (LIMPIEZA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Utilizar cepillo de corte recto de cerdas suaves.
• La limpieza no suelta dientes ni desaloja obturaciones.
INDICACIONES GENERALES ODONTOPEDIATRIA
• Utiliza cepillos y pasta dental acorde a la edad del paciente
• En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental,
mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado.
• En escolares motiva y supervisa el cepillado individual del paciente.
• Cuida la alimentación de tu hijo, mantén una alimentación saludable.
• Realiza controles periódicos.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
OBTURACIONES – RESINA

[Página 36]
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES ORTODONCIA
• Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
periodo de adaptación de tus dientes
• Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y
cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos.
• No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar
en trozos pequeños, etc.)
• No comer alimentos pegajosos (calugas, chicle, masticables, etc.)
• No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar.
• No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente
• Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES PERIODONCIA
DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• No fumar por 72 horas.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Usar cepillo suave
• La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la
obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados
falsamente por el sarro.
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de obturaciones en resina

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 35]
INDICACIONES DE OBTURACIONES – RESINA
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES PARA DESTARTRAJE (LIMPIEZA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Utilizar cepillo de corte recto de cerdas suaves.
• La limpieza no suelta dientes ni desaloja obturaciones.
INDICACIONES GENERALES ODONTOPEDIATRIA
• Utiliza cepillos y pasta dental acorde a la edad del paciente
• En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental,
mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado.
• En escolares motiva y supervisa el cepillado individual del paciente.
• Cuida la alimentación de tu hijo, mantén una alimentación saludable.
• Realiza controles periódicos.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
OBTURACIONES – RESINA

[Página 36]
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES ORTODONCIA
• Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
periodo de adaptación de tus dientes
• Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y
cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos.
• No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar
en trozos pequeños, etc.)
• No comer alimentos pegajosos (calugas, chicle, masticables, etc.)
• No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar.
• No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente
• Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES PERIODONCIA
DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• No fumar por 72 horas.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Usar cepillo suave
• La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la
obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados
falsamente por el sarro.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`48 horas`, `72 horas`

### Riesgos y advertencias detectadas

- • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
- • Seguir receta indicada. Tomar medicamentos según prescripción.
- • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
- • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
- • Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_OBTURACIONES_RESINA-CO`, país `CO`, locale `es-CO`, hash `7e4a9f831b3b76c31d83f0fc7094d0edd439c85af5620aa5f9f26ed1da6159f3`.
- CL: id lógico `IND_OBTURACIONES_RESINA-CL`, país `CL`, locale `es-CL`, hash `1606a62d98784a7e4357045bc84a41725c4a1cd43e119dc03c460de5300fec1d`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 29. INDICACIONES PARA DESTARTRAJE

- Código: `IND_DESTARTRAJE`
- Categoría: Indicaciones
- Páginas fuente: 35–35
- Especialidad: Periodoncia
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `5900d00db99eb8383240b20a20610f3efbc4a670ce926de0b873b7c82fcf8b9d`

### Texto fuente relevante

```text
[Página 35]
INDICACIONES DE OBTURACIONES – RESINA
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES PARA DESTARTRAJE (LIMPIEZA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Utilizar cepillo de corte recto de cerdas suaves.
• La limpieza no suelta dientes ni desaloja obturaciones.
INDICACIONES GENERALES ODONTOPEDIATRIA
• Utiliza cepillos y pasta dental acorde a la edad del paciente
• En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental,
mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado.
• En escolares motiva y supervisa el cepillado individual del paciente.
• Cuida la alimentación de tu hijo, mantén una alimentación saludable.
• Realiza controles periódicos.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
OBTURACIONES – RESINA
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones para destartraje

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 35]
INDICACIONES DE OBTURACIONES – RESINA
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES PARA DESTARTRAJE (LIMPIEZA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Utilizar cepillo de corte recto de cerdas suaves.
• La limpieza no suelta dientes ni desaloja obturaciones.
INDICACIONES GENERALES ODONTOPEDIATRIA
• Utiliza cepillos y pasta dental acorde a la edad del paciente
• En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental,
mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado.
• En escolares motiva y supervisa el cepillado individual del paciente.
• Cuida la alimentación de tu hijo, mantén una alimentación saludable.
• Realiza controles periódicos.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
OBTURACIONES – RESINA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`48 horas`

### Riesgos y advertencias detectadas

- • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
- • Seguir receta indicada. Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_DESTARTRAJE-CO`, país `CO`, locale `es-CO`, hash `74b9d107985ba2ee589be9f06cc6a224305610e95ec85b80a6e055c7a9c42c93`.
- CL: id lógico `IND_DESTARTRAJE-CL`, país `CL`, locale `es-CL`, hash `d9e4ce9c5b09a2694821a03c2acb426e000bfff9fa80a78bf7047c9f84e2e44e`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 30. INDICACIONES GENERALES DE ODONTOPEDIATRÍA

- Código: `IND_ODONTOPEDIATRIA_GENERAL`
- Categoría: Indicaciones
- Páginas fuente: 35–35
- Especialidad: Odontopediatria
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `5900d00db99eb8383240b20a20610f3efbc4a670ce926de0b873b7c82fcf8b9d`

### Texto fuente relevante

```text
[Página 35]
INDICACIONES DE OBTURACIONES – RESINA
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES PARA DESTARTRAJE (LIMPIEZA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Utilizar cepillo de corte recto de cerdas suaves.
• La limpieza no suelta dientes ni desaloja obturaciones.
INDICACIONES GENERALES ODONTOPEDIATRIA
• Utiliza cepillos y pasta dental acorde a la edad del paciente
• En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental,
mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado.
• En escolares motiva y supervisa el cepillado individual del paciente.
• Cuida la alimentación de tu hijo, mantén una alimentación saludable.
• Realiza controles periódicos.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
OBTURACIONES – RESINA
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones generales de odontopediatría

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 35]
INDICACIONES DE OBTURACIONES – RESINA
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES PARA DESTARTRAJE (LIMPIEZA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Utilizar cepillo de corte recto de cerdas suaves.
• La limpieza no suelta dientes ni desaloja obturaciones.
INDICACIONES GENERALES ODONTOPEDIATRIA
• Utiliza cepillos y pasta dental acorde a la edad del paciente
• En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental,
mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado.
• En escolares motiva y supervisa el cepillado individual del paciente.
• Cuida la alimentación de tu hijo, mantén una alimentación saludable.
• Realiza controles periódicos.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
OBTURACIONES – RESINA

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`48 horas`

### Riesgos y advertencias detectadas

- • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
- • Seguir receta indicada. Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_ODONTOPEDIATRIA_GENERAL-CO`, país `CO`, locale `es-CO`, hash `7e05ad9501bea22d2a8291f7a93be75c34583dc8878e4362ff51febbe5738b93`.
- CL: id lógico `IND_ODONTOPEDIATRIA_GENERAL-CL`, país `CL`, locale `es-CL`, hash `ed9efcde41ae677027c2d9964152326ff7912f707878a732b1b0084d3625f8a8`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 31. INDICACIONES DE ORTODONCIA

- Código: `IND_ORTODONCIA`
- Categoría: Indicaciones
- Páginas fuente: 36–36
- Especialidad: Ortodoncia
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `fcf2f5e3e88d47a7a29956925efeeb2c5e45e0451d2a3abbd5bb3ff3b5ae2d75`

### Texto fuente relevante

```text
[Página 36]
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES ORTODONCIA
• Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
periodo de adaptación de tus dientes
• Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y
cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos.
• No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar
en trozos pequeños, etc.)
• No comer alimentos pegajosos (calugas, chicle, masticables, etc.)
• No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar.
• No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente
• Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES PERIODONCIA
DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• No fumar por 72 horas.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Usar cepillo suave
• La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la
obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados
falsamente por el sarro.
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de ortodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 36]
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES ORTODONCIA
• Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
periodo de adaptación de tus dientes
• Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y
cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos.
• No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar
en trozos pequeños, etc.)
• No comer alimentos pegajosos (calugas, chicle, masticables, etc.)
• No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar.
• No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente
• Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES PERIODONCIA
DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• No fumar por 72 horas.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Usar cepillo suave
• La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la
obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados
falsamente por el sarro.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`48 horas`, `72 horas`

### Riesgos y advertencias detectadas

- • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
- • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
- • Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_ORTODONCIA-CO`, país `CO`, locale `es-CO`, hash `837bf38eeefe7193dd40532c6c3eccdf4bea25dbe2691f045630ea9b40c69454`.
- CL: id lógico `IND_ORTODONCIA-CL`, país `CL`, locale `es-CL`, hash `35da88170c7394f06f7a4eb439ab7d02bc479b2d03e576b86b03ec3d99923f69`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 32. INDICACIONES DE PERIODONCIA

- Código: `IND_PERIODONCIA`
- Categoría: Indicaciones
- Páginas fuente: 36–37
- Especialidad: Periodoncia
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `51dbb0db7eb3032180ec538b326519ef2ea013f8c2048d28191d616c65be1469`

### Texto fuente relevante

```text
[Página 36]
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES ORTODONCIA
• Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
periodo de adaptación de tus dientes
• Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y
cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos.
• No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar
en trozos pequeños, etc.)
• No comer alimentos pegajosos (calugas, chicle, masticables, etc.)
• No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar.
• No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente
• Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES PERIODONCIA
DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• No fumar por 72 horas.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Usar cepillo suave
• La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la
obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados
falsamente por el sarro.

[Página 37]
• Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su
tratante si esto sucede.
• Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde.
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la
anestesia.
INDICACIONES PREOPERATORIAS -CIRUGÍA MENOR MAXILOFACIAL
Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local
A continuación le entregamos las recomendaciones e instrucciones que deben seguir los pacientes
que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad,
eficacia y correcto desarrollo del procedimiento quirúrgico ambulatorio.
I. Requisitos Generales del Paciente
• Ayuno: No es necesario ayuno. Se recomienda evitar comidas pesadas al menos 2 horas
antes del procedimiento.
Debe consumir un desayuno o colación ligera si la cirugía es en la mañana/tarde, pues pasará
un par de horas antes de poder comer luego de la anestesia.
• Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación
contraria del equipo médico. Si Ud. toma anticoagulantes o antiagregantes, debe haber sido
evaluado previamente por el cirujano y/o hematología si corresponde. Llevar una lista de
medicamentos actuales.
• Higiene oral: Realizar higiene oral habitual antes de asistir al procedimiento.
• Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria
aguda, herpes oral activo o descompensación de enfermedades crónicas, debe comunicarse
con anticipación para reagendar la cirugía.
• Acompañante: Es recomendable asistir con un acompañante, especialmente si el paciente es
de edad avanzada o con antecedentes médicos relevantes.
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de periodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 36]
• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola,
té).
• Evite fumar por 24-48 horas.
• En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
a control con su tratante.
• En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante.
INDICACIONES ORTODONCIA
• Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
periodo de adaptación de tus dientes
• Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y
cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos.
• No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar
en trozos pequeños, etc.)
• No comer alimentos pegajosos (calugas, chicle, masticables, etc.)
• No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar.
• No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente
• Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES PERIODONCIA
DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA)
• Diariamente realice una correcta higiene dental, mínimo 3 veces al día.
• No fumar por 72 horas.
• En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar
pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin
enjuagarse.
• Usar cepillo suave
• La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la
obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados
falsamente por el sarro.

[Página 37]
• Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su
tratante si esto sucede.
• Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde.
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la
anestesia.
INDICACIONES PREOPERATORIAS -CIRUGÍA MENOR MAXILOFACIAL
Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local
A continuación le entregamos las recomendaciones e instrucciones que deben seguir los pacientes
que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad,
eficacia y correcto desarrollo del procedimiento quirúrgico ambulatorio.
I. Requisitos Generales del Paciente
• Ayuno: No es necesario ayuno. Se recomienda evitar comidas pesadas al menos 2 horas
antes del procedimiento.
Debe consumir un desayuno o colación ligera si la cirugía es en la mañana/tarde, pues pasará
un par de horas antes de poder comer luego de la anestesia.
• Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación
contraria del equipo médico. Si Ud. toma anticoagulantes o antiagregantes, debe haber sido
evaluado previamente por el cirujano y/o hematología si corresponde. Llevar una lista de
medicamentos actuales.
• Higiene oral: Realizar higiene oral habitual antes de asistir al procedimiento.
• Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria
aguda, herpes oral activo o descompensación de enfermedades crónicas, debe comunicarse
con anticipación para reagendar la cirugía.
• Acompañante: Es recomendable asistir con un acompañante, especialmente si el paciente es
de edad avanzada o con antecedentes médicos relevantes.

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`2 horas`, `48 horas`, `72 horas`

### Riesgos y advertencias detectadas

- • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir
- • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un
- • Tomar medicamentos según prescripción.
- • Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su
- • Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde.
- anestesia.
- Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local
- que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad,
- un par de horas antes de poder comer luego de la anestesia.
- • Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación
- medicamentos actuales.
- • Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_PERIODONCIA-CO`, país `CO`, locale `es-CO`, hash `de9fa0cc60bb6598d58e437fe115b80bc1bdcaa9fa4b78e494bba7bb106659bc`.
- CL: id lógico `IND_PERIODONCIA-CL`, país `CL`, locale `es-CL`, hash `986e9fc217019bac6ed1575180a2638c3555331009654a7f2fdce998e3d7d87c`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 33. INDICACIONES PREOPERATORIAS DE CIRUGÍA MENOR MAXILOFACIAL

- Código: `IND_PREOP_CIRUGIA_MAXILOFACIAL`
- Categoría: Indicaciones
- Páginas fuente: 37–38
- Especialidad: Cirugia Maxilofacial
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `7d0adfe529eb2e3444364f720d58ccbdc174daa6ab98bedc6e5d06c85fded9ac`

### Texto fuente relevante

```text
[Página 37]
• Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su
tratante si esto sucede.
• Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde.
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la
anestesia.
INDICACIONES PREOPERATORIAS -CIRUGÍA MENOR MAXILOFACIAL
Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local
A continuación le entregamos las recomendaciones e instrucciones que deben seguir los pacientes
que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad,
eficacia y correcto desarrollo del procedimiento quirúrgico ambulatorio.
I. Requisitos Generales del Paciente
• Ayuno: No es necesario ayuno. Se recomienda evitar comidas pesadas al menos 2 horas
antes del procedimiento.
Debe consumir un desayuno o colación ligera si la cirugía es en la mañana/tarde, pues pasará
un par de horas antes de poder comer luego de la anestesia.
• Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación
contraria del equipo médico. Si Ud. toma anticoagulantes o antiagregantes, debe haber sido
evaluado previamente por el cirujano y/o hematología si corresponde. Llevar una lista de
medicamentos actuales.
• Higiene oral: Realizar higiene oral habitual antes de asistir al procedimiento.
• Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria
aguda, herpes oral activo o descompensación de enfermedades crónicas, debe comunicarse
con anticipación para reagendar la cirugía.
• Acompañante: Es recomendable asistir con un acompañante, especialmente si el paciente es
de edad avanzada o con antecedentes médicos relevantes.

[Página 38]
II. Pacientes Embarazadas y en Lactancia
• Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad,
preferentemente en el segundo trimestre del embarazo (semanas 14 a 28). Se debe informar al
equipo tratante sobre la edad gestacional. Se evitarán fármacos contraindicados durante la
gestación. El uso de anestésicos locales con vasoconstrictor está permitido en dosis
controladas. Evitar posición supina prolongada durante el procedimiento para prevenir
síndrome de hipotensión supina. Se recomienda asistencia con acompañante.
• Pacientes en Lactancia: La mayoría de los anestésicos locales (como la lidocaína) y
antibióticos de uso habitual (como amoxicilina) son compatibles con la lactancia. Si se
prescriben analgésicos o antibióticos, consultar siempre la compatibilidad con lactancia. Si se
indican medicamentos poco compatibles, se puede realizar extracción de leche previa para
alimentar al lactante en las horas posteriores.
III. Documentación Necesaria
• Exámenes complementarios (si fueron solicitados previamente como scanner o panorámica
si los realizó en otro centro).
IV. Consideraciones Específicas para el Procedimiento
• Vestimenta y otros: Ropa cómoda y fácil de remover. Evitar maquillaje, uñas pintadas, alhajas
o accesorios en cara/cuello. Barba recortada 1 cm máximo, para lograr una adecuada
desinfección.
• Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales.
INDICACIONES REHABILITACION ORAL
Prótesis removible parcial o total
• Mantenga una buena higiene bucal (dientes, mucosas, lengua), al menos 3 veces al día e ideal
después de cada comida.
• Mantenga una buena higiene de su prótesis removible, cepille su prótesis con un cepillo
independiente, utilice otro para sus dientes.
• Lave su prótesis con jabón líquido neutro o de glicerina bajo el chorro de agua.
• No cepille su prótesis con pasta dental ya que puede rayar la superficie por las partículas
abrasivas que podría tener.
• Semanalmente limpie su prótesis con tabletas efervescentes de limpieza profunda.
• No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos.
• Al retirar su prótesis puede mantenerla en un vaso con agua (temperatura normal) para evitar
su deformación con el calor. No usar nunca agua hirviendo ya que puede deformar su
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones preoperatorias de cirugía menor maxilofacial

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 37]
• Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su
tratante si esto sucede.
• Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde.
• Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la
anestesia.
INDICACIONES PREOPERATORIAS -CIRUGÍA MENOR MAXILOFACIAL
Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local
A continuación le entregamos las recomendaciones e instrucciones que deben seguir los pacientes
que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad,
eficacia y correcto desarrollo del procedimiento quirúrgico ambulatorio.
I. Requisitos Generales del Paciente
• Ayuno: No es necesario ayuno. Se recomienda evitar comidas pesadas al menos 2 horas
antes del procedimiento.
Debe consumir un desayuno o colación ligera si la cirugía es en la mañana/tarde, pues pasará
un par de horas antes de poder comer luego de la anestesia.
• Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación
contraria del equipo médico. Si Ud. toma anticoagulantes o antiagregantes, debe haber sido
evaluado previamente por el cirujano y/o hematología si corresponde. Llevar una lista de
medicamentos actuales.
• Higiene oral: Realizar higiene oral habitual antes de asistir al procedimiento.
• Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria
aguda, herpes oral activo o descompensación de enfermedades crónicas, debe comunicarse
con anticipación para reagendar la cirugía.
• Acompañante: Es recomendable asistir con un acompañante, especialmente si el paciente es
de edad avanzada o con antecedentes médicos relevantes.

[Página 38]
II. Pacientes Embarazadas y en Lactancia
• Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad,
preferentemente en el segundo trimestre del embarazo (semanas 14 a 28). Se debe informar al
equipo tratante sobre la edad gestacional. Se evitarán fármacos contraindicados durante la
gestación. El uso de anestésicos locales con vasoconstrictor está permitido en dosis
controladas. Evitar posición supina prolongada durante el procedimiento para prevenir
síndrome de hipotensión supina. Se recomienda asistencia con acompañante.
• Pacientes en Lactancia: La mayoría de los anestésicos locales (como la lidocaína) y
antibióticos de uso habitual (como amoxicilina) son compatibles con la lactancia. Si se
prescriben analgésicos o antibióticos, consultar siempre la compatibilidad con lactancia. Si se
indican medicamentos poco compatibles, se puede realizar extracción de leche previa para
alimentar al lactante en las horas posteriores.
III. Documentación Necesaria
• Exámenes complementarios (si fueron solicitados previamente como scanner o panorámica
si los realizó en otro centro).
IV. Consideraciones Específicas para el Procedimiento
• Vestimenta y otros: Ropa cómoda y fácil de remover. Evitar maquillaje, uñas pintadas, alhajas
o accesorios en cara/cuello. Barba recortada 1 cm máximo, para lograr una adecuada
desinfección.
• Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales.
INDICACIONES REHABILITACION ORAL
Prótesis removible parcial o total
• Mantenga una buena higiene bucal (dientes, mucosas, lengua), al menos 3 veces al día e ideal
después de cada comida.
• Mantenga una buena higiene de su prótesis removible, cepille su prótesis con un cepillo
independiente, utilice otro para sus dientes.
• Lave su prótesis con jabón líquido neutro o de glicerina bajo el chorro de agua.
• No cepille su prótesis con pasta dental ya que puede rayar la superficie por las partículas
abrasivas que podría tener.
• Semanalmente limpie su prótesis con tabletas efervescentes de limpieza profunda.
• No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos.
• Al retirar su prótesis puede mantenerla en un vaso con agua (temperatura normal) para evitar
su deformación con el calor. No usar nunca agua hirviendo ya que puede deformar su

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`2 horas`

### Riesgos y advertencias detectadas

- • Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su
- • Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde.
- anestesia.
- Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local
- que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad,
- un par de horas antes de poder comer luego de la anestesia.
- • Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación
- medicamentos actuales.
- • Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria
- • Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad,
- indican medicamentos poco compatibles, se puede realizar extracción de leche previa para
- desinfección.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_PREOP_CIRUGIA_MAXILOFACIAL-CO`, país `CO`, locale `es-CO`, hash `15687e57fd720f14591e01c6038a91ab441c3f1a849add79fb3b248cd958f11d`.
- CL: id lógico `IND_PREOP_CIRUGIA_MAXILOFACIAL-CL`, país `CL`, locale `es-CL`, hash `b1cffe6b32c7eb7d8eac695e8c2b343eb5e944f9db6a4e48eb2c2180a9cabf4d`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 34. INDICACIONES DE REHABILITACIÓN ORAL

- Código: `IND_REHABILITACION_ORAL`
- Categoría: Indicaciones
- Páginas fuente: 38–39
- Especialidad: Rehabilitacion Oral
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `141d1acfd4641ccda3d23655f1f2a84979a18970e4deefea336afaac7a43d15a`

### Texto fuente relevante

```text
[Página 38]
II. Pacientes Embarazadas y en Lactancia
• Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad,
preferentemente en el segundo trimestre del embarazo (semanas 14 a 28). Se debe informar al
equipo tratante sobre la edad gestacional. Se evitarán fármacos contraindicados durante la
gestación. El uso de anestésicos locales con vasoconstrictor está permitido en dosis
controladas. Evitar posición supina prolongada durante el procedimiento para prevenir
síndrome de hipotensión supina. Se recomienda asistencia con acompañante.
• Pacientes en Lactancia: La mayoría de los anestésicos locales (como la lidocaína) y
antibióticos de uso habitual (como amoxicilina) son compatibles con la lactancia. Si se
prescriben analgésicos o antibióticos, consultar siempre la compatibilidad con lactancia. Si se
indican medicamentos poco compatibles, se puede realizar extracción de leche previa para
alimentar al lactante en las horas posteriores.
III. Documentación Necesaria
• Exámenes complementarios (si fueron solicitados previamente como scanner o panorámica
si los realizó en otro centro).
IV. Consideraciones Específicas para el Procedimiento
• Vestimenta y otros: Ropa cómoda y fácil de remover. Evitar maquillaje, uñas pintadas, alhajas
o accesorios en cara/cuello. Barba recortada 1 cm máximo, para lograr una adecuada
desinfección.
• Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales.
INDICACIONES REHABILITACION ORAL
Prótesis removible parcial o total
• Mantenga una buena higiene bucal (dientes, mucosas, lengua), al menos 3 veces al día e ideal
después de cada comida.
• Mantenga una buena higiene de su prótesis removible, cepille su prótesis con un cepillo
independiente, utilice otro para sus dientes.
• Lave su prótesis con jabón líquido neutro o de glicerina bajo el chorro de agua.
• No cepille su prótesis con pasta dental ya que puede rayar la superficie por las partículas
abrasivas que podría tener.
• Semanalmente limpie su prótesis con tabletas efervescentes de limpieza profunda.
• No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos.
• Al retirar su prótesis puede mantenerla en un vaso con agua (temperatura normal) para evitar
su deformación con el calor. No usar nunca agua hirviendo ya que puede deformar su

[Página 39]
prótesis. Los elementos protésicos deben ser controlados cada 6 meses o 1 año para realizar
ajustes y rebasados.
Prótesis fija (carillas, incrustaciones, coronas, coronas sobre implantes)
• No comer alimentos muy duros (masticar hielo, frutos secos). Evitar malos hábitos: comerse las
uñas, abrir botellas con los dientes.
• Evitar alimentos que puedan teñir la cerámica.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES ODONTOPEDIATRIA TRAUMA DENTOALVEOLAR
• REALIZAR CEPILLADO CON CEPILLO SUAVE DESPUÉS DE CADA COMIDA
• UTILIZAR CLORHEXIDINA 0,12% CON COTONITO O GASA EN LA ZONA POR 10-15
DIAS
• DIETA BLANCA POR 10 DÍAS
• EVITAR USO DE CHUPETE, MAMADERA O BOMBILLAS.
• UTILIZAR BÁLSAMO LABIAL EN CASO DE HERIDA EN EL LABIO
• DEBE VOLVER A CONTROL Y TRATAMIENTO
• INDICACIONES:
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de rehabilitación oral

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 38]
II. Pacientes Embarazadas y en Lactancia
• Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad,
preferentemente en el segundo trimestre del embarazo (semanas 14 a 28). Se debe informar al
equipo tratante sobre la edad gestacional. Se evitarán fármacos contraindicados durante la
gestación. El uso de anestésicos locales con vasoconstrictor está permitido en dosis
controladas. Evitar posición supina prolongada durante el procedimiento para prevenir
síndrome de hipotensión supina. Se recomienda asistencia con acompañante.
• Pacientes en Lactancia: La mayoría de los anestésicos locales (como la lidocaína) y
antibióticos de uso habitual (como amoxicilina) son compatibles con la lactancia. Si se
prescriben analgésicos o antibióticos, consultar siempre la compatibilidad con lactancia. Si se
indican medicamentos poco compatibles, se puede realizar extracción de leche previa para
alimentar al lactante en las horas posteriores.
III. Documentación Necesaria
• Exámenes complementarios (si fueron solicitados previamente como scanner o panorámica
si los realizó en otro centro).
IV. Consideraciones Específicas para el Procedimiento
• Vestimenta y otros: Ropa cómoda y fácil de remover. Evitar maquillaje, uñas pintadas, alhajas
o accesorios en cara/cuello. Barba recortada 1 cm máximo, para lograr una adecuada
desinfección.
• Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales.
INDICACIONES REHABILITACION ORAL
Prótesis removible parcial o total
• Mantenga una buena higiene bucal (dientes, mucosas, lengua), al menos 3 veces al día e ideal
después de cada comida.
• Mantenga una buena higiene de su prótesis removible, cepille su prótesis con un cepillo
independiente, utilice otro para sus dientes.
• Lave su prótesis con jabón líquido neutro o de glicerina bajo el chorro de agua.
• No cepille su prótesis con pasta dental ya que puede rayar la superficie por las partículas
abrasivas que podría tener.
• Semanalmente limpie su prótesis con tabletas efervescentes de limpieza profunda.
• No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos.
• Al retirar su prótesis puede mantenerla en un vaso con agua (temperatura normal) para evitar
su deformación con el calor. No usar nunca agua hirviendo ya que puede deformar su

[Página 39]
prótesis. Los elementos protésicos deben ser controlados cada 6 meses o 1 año para realizar
ajustes y rebasados.
Prótesis fija (carillas, incrustaciones, coronas, coronas sobre implantes)
• No comer alimentos muy duros (masticar hielo, frutos secos). Evitar malos hábitos: comerse las
uñas, abrir botellas con los dientes.
• Evitar alimentos que puedan teñir la cerámica.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES ODONTOPEDIATRIA TRAUMA DENTOALVEOLAR
• REALIZAR CEPILLADO CON CEPILLO SUAVE DESPUÉS DE CADA COMIDA
• UTILIZAR CLORHEXIDINA 0,12% CON COTONITO O GASA EN LA ZONA POR 10-15
DIAS
• DIETA BLANCA POR 10 DÍAS
• EVITAR USO DE CHUPETE, MAMADERA O BOMBILLAS.
• UTILIZAR BÁLSAMO LABIAL EN CASO DE HERIDA EN EL LABIO
• DEBE VOLVER A CONTROL Y TRATAMIENTO
• INDICACIONES:

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`1 año`, `10 DÍAS`, `15
DIAS`, `6 meses`

### Riesgos y advertencias detectadas

- • Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad,
- indican medicamentos poco compatibles, se puede realizar extracción de leche previa para
- desinfección.
- • Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales.
- • No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos.
- • Seguir receta indicada. Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_REHABILITACION_ORAL-CO`, país `CO`, locale `es-CO`, hash `245699c7ddebee66ebc437129bf5b98a8c03c7c60f6c11ced56229f565decd0e`.
- CL: id lógico `IND_REHABILITACION_ORAL-CL`, país `CL`, locale `es-CL`, hash `291dd4fb7244ab65ad28823cf2f6f68e376f43f3b467359b4ff87b2a353a4c06`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.

## 35. INDICACIONES DE ODONTOPEDIATRÍA TRAUMA DENTOALVEOLAR

- Código: `IND_TRAUMA_DENTOALVEOLAR`
- Categoría: Indicaciones
- Páginas fuente: 39–39
- Especialidad: Odontopediatria
- Firmante: `NO_SIGNATURE_REQUIRED`
- Resultado: `PENDING`
- Fragmento SHA-256: `49258ec94b4b23800e772b1706e0487eff66cef998b1af87d70b8c7cd2983c73`

### Texto fuente relevante

```text
[Página 39]
prótesis. Los elementos protésicos deben ser controlados cada 6 meses o 1 año para realizar
ajustes y rebasados.
Prótesis fija (carillas, incrustaciones, coronas, coronas sobre implantes)
• No comer alimentos muy duros (masticar hielo, frutos secos). Evitar malos hábitos: comerse las
uñas, abrir botellas con los dientes.
• Evitar alimentos que puedan teñir la cerámica.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES ODONTOPEDIATRIA TRAUMA DENTOALVEOLAR
• REALIZAR CEPILLADO CON CEPILLO SUAVE DESPUÉS DE CADA COMIDA
• UTILIZAR CLORHEXIDINA 0,12% CON COTONITO O GASA EN LA ZONA POR 10-15
DIAS
• DIETA BLANCA POR 10 DÍAS
• EVITAR USO DE CHUPETE, MAMADERA O BOMBILLAS.
• UTILIZAR BÁLSAMO LABIAL EN CASO DE HERIDA EN EL LABIO
• DEBE VOLVER A CONTROL Y TRATAMIENTO
• INDICACIONES:
```

### Texto normalizado CO / es-CO

```markdown
# Indicaciones de odontopediatría trauma dentoalveolar

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Colombia
Clínica: {{company.name}}
Sede: {{site.name}}
Dirección de sede: {{site.address}}, {{site.city}}
Profesional responsable: {{professional.full_name}}

## Texto del documento fuente

[Página 39]
prótesis. Los elementos protésicos deben ser controlados cada 6 meses o 1 año para realizar
ajustes y rebasados.
Prótesis fija (carillas, incrustaciones, coronas, coronas sobre implantes)
• No comer alimentos muy duros (masticar hielo, frutos secos). Evitar malos hábitos: comerse las
uñas, abrir botellas con los dientes.
• Evitar alimentos que puedan teñir la cerámica.
• Seguir receta indicada. Tomar medicamentos según prescripción.
• Seguir indicaciones de especialista.
• En caso de urgencia asistir a clínica o centro asistencial.
INDICACIONES ODONTOPEDIATRIA TRAUMA DENTOALVEOLAR
• REALIZAR CEPILLADO CON CEPILLO SUAVE DESPUÉS DE CADA COMIDA
• UTILIZAR CLORHEXIDINA 0,12% CON COTONITO O GASA EN LA ZONA POR 10-15
DIAS
• DIETA BLANCA POR 10 DÍAS
• EVITAR USO DE CHUPETE, MAMADERA O BOMBILLAS.
• UTILIZAR BÁLSAMO LABIAL EN CASO DE HERIDA EN EL LABIO
• DEBE VOLVER A CONTROL Y TRATAMIENTO
• INDICACIONES:

## Firma

Paciente o responsable: ______________________________

Profesional: {{professional.full_name}}
Registro profesional: {{professional.license_number}}
```

### Variables introducidas

`company.name`, `document.clinical_date`, `patient.document_number`, `patient.document_type`, `patient.full_name`, `professional.full_name`, `professional.license_number`, `site.address`, `site.city`, `site.name`

### Líneas eliminadas o sustituidas

- No se detectaron referencias institucionales sustituidas.

### Cambios de formato

- Transformación a Markdown restringido Dentia.
- Encabezado Dentia agregado con variables institucionales.
- Saltos de página representados como etiquetas `[Página N]`.

### Diferencias textuales

```diff
Sin diferencias relevantes entre el cuerpo fuente normalizado y el cuerpo Dentia.
```

### Valores, porcentajes y plazos detectados

`1 año`, `10 DÍAS`, `15
DIAS`, `6 meses`

### Riesgos y advertencias detectadas

- • Seguir receta indicada. Tomar medicamentos según prescripción.

### Referencias institucionales sustituidas

No se detectaron referencias institucionales fuente en este fragmento.

### Revisión de variantes Colombia y Chile

- CO: id lógico `IND_TRAUMA_DENTOALVEOLAR-CO`, país `CO`, locale `es-CO`, hash `a5b68a1ca60367bc3999156be33e98a2ef796f3a267007b677e0a78b9243dda4`.
- CL: id lógico `IND_TRAUMA_DENTOALVEOLAR-CL`, país `CL`, locale `es-CL`, hash `80b741d9a555e93a55e54b388c9f56475c8ac45eac6d17661da5c87ceea07e60`.
- Hashes distintos: sí
- Fallback: no se usa; cada variante conserva país y locale propios.

### Observaciones

- Pendiente registrar revisión odontológica y jurídica de equivalencia.
- No aprobar si la revisión humana encuentra cambios en riesgos, consecuencias, contraindicaciones, porcentajes, medicamentos, montos, plazos, garantías, derechos u obligaciones.
