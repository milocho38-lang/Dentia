# C019A4-LIB1-NORM3 — Revisión humana de normalización v2

Este informe separa el texto fuente de procedencia y el contenido normalizado destinado al paciente.

- Esquema: `LIB1_NORM_V2`
- Documentos: 35
- Variantes: 70
- CO: 35
- CL: 35
- Estados: {'BLOCKED': 66, 'NEEDS_REVIEW': 4}

## Contrato

- `source_text`: evidencia de procedencia, no editable, nunca destinada al paciente.
- `normalized_content_v2`: Markdown restringido para paciente, sin marcadores de página ni bloques de firma manuscrita.
- Ninguna variante queda aprobada automáticamente; todas requieren revisión humana de equivalencia.

## CERT_ASISTENCIA — CO / es-CO

- Título: Certificado de asistencia
- Tipo: CERTIFICATE
- Páginas fuente: [1]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 12
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:CERTIFICATE']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Certificado de asistencia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CERTIFICADO DE ASISTENCIA Este certificado indica que el usuario _________________, rut: _________________es paciente activo de la clínica y asistió: El dia ____ de ________ del __________ a dependencias de la {{company.name}}, ubicada en {{site.address}}, {{site.city}}. Se emite el presente documento a solicitud del paciente para los fines que estime convenientes. {{company.name}}

```

## CERT_ASISTENCIA — CL / es-CL

- Título: Certificado de asistencia
- Tipo: CERTIFICATE
- Páginas fuente: [1]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 12
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:CERTIFICATE']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Certificado de asistencia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Certificado de asistencia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CERTIFICADO DE ASISTENCIA Este certificado indica que el usuario _________________, rut: _________________es paciente activo de la clínica y asistió: El dia ____ de ________ del __________ a dependencias de la {{company.name}}, ubicada en {{site.address}}, {{site.city}}. Se emite el presente documento a solicitud del paciente para los fines que estime convenientes. {{company.name}}

```

## CONS_BLANQUEAMIENTO — CO / es-CO

- Título: Consentimiento informado de blanqueamiento dental
- Tipo: INFORMED_CONSENT
- Páginas fuente: [2]
- Estado: **BLOCKED**
- Compatibilidad firmante: `REPRESENTATIVE_REQUIRED`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 42
- Frases de representante: ['menores', 'paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:REPRESENTATIVE_REQUIRED', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de blanqueamiento dental

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO BLANQUEAMIENTO DENTAL El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: El blanqueamiento dental es un procedimiento odontológico que tiene por objetivo aclarar el color del diente utilizando agentes químicos como el peróxido de hidrógeno o carbamida sobre la superficie del diente. El beneficio principal es la satisfacción del paciente, mejorando la estética de su sonrisa y por consecuencia su autoestima o comodidad. El blanqueamiento clínico o en el hogar mediante cubetas y gel blanqueador NO se recomiendan en embarazadas ni menores de 18 años. Este procedimiento debe ser realizado en bocas sanas, por lo que, si el paciente presenta alguna patología como caries, absceso, sensibilidad cervical, fractura, entre otros, deberá resolver sus patologías antes de realizar el tratamiento. Dentro de los riesgos de un blanqueamiento está, entre otras, la sensibilidad dental, la cual suele ser reversible, de forma contraria se podría necesitar tratamiento endodóntico (conducto) y ser derivado. El resultado del blanqueamiento no es predecible, en promedio se disminuye 4-5 tonos del tono del paciente. Su durabilidad es variable ya que depende de la alimentación y hábitos del paciente, los alimentos como café, vino, té, colorantes o hábitos como el cigarro influyen directamente en su duración, se recomienda evitarlos durante la primera semana posterior al blanqueamiento e idealmente eliminarlos o disminuirlos. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que este tratamiento consta de dos sesiones necesarias para estabilizar el color y que en caso de no estar conforme con el resultado y como garantía por este tratamiento puedo solicitar una tercera sesión, además comprendo que en caso de existir sensibilidad post tratamiento el odontólogo deberá aplicar un producto desensibilizante como parte de la garantía de dicho tratamiento en clínica {{company.name}}. Entiendo que estas garantías las perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_BLANQUEAMIENTO — CL / es-CL

- Título: Consentimiento informado de blanqueamiento dental
- Tipo: INFORMED_CONSENT
- Páginas fuente: [2]
- Estado: **BLOCKED**
- Compatibilidad firmante: `REPRESENTATIVE_REQUIRED`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 42
- Frases de representante: ['menores', 'paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:REPRESENTATIVE_REQUIRED', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de blanqueamiento dental

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de blanqueamiento dental

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO BLANQUEAMIENTO DENTAL El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: El blanqueamiento dental es un procedimiento odontológico que tiene por objetivo aclarar el color del diente utilizando agentes químicos como el peróxido de hidrógeno o carbamida sobre la superficie del diente. El beneficio principal es la satisfacción del paciente, mejorando la estética de su sonrisa y por consecuencia su autoestima o comodidad. El blanqueamiento clínico o en el hogar mediante cubetas y gel blanqueador NO se recomiendan en embarazadas ni menores de 18 años. Este procedimiento debe ser realizado en bocas sanas, por lo que, si el paciente presenta alguna patología como caries, absceso, sensibilidad cervical, fractura, entre otros, deberá resolver sus patologías antes de realizar el tratamiento. Dentro de los riesgos de un blanqueamiento está, entre otras, la sensibilidad dental, la cual suele ser reversible, de forma contraria se podría necesitar tratamiento endodóntico (conducto) y ser derivado. El resultado del blanqueamiento no es predecible, en promedio se disminuye 4-5 tonos del tono del paciente. Su durabilidad es variable ya que depende de la alimentación y hábitos del paciente, los alimentos como café, vino, té, colorantes o hábitos como el cigarro influyen directamente en su duración, se recomienda evitarlos durante la primera semana posterior al blanqueamiento e idealmente eliminarlos o disminuirlos. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que este tratamiento consta de dos sesiones necesarias para estabilizar el color y que en caso de no estar conforme con el resultado y como garantía por este tratamiento puedo solicitar una tercera sesión, además comprendo que en caso de existir sensibilidad post tratamiento el odontólogo deberá aplicar un producto desensibilizante como parte de la garantía de dicho tratamiento en clínica {{company.name}}. Entiendo que estas garantías las perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_ORTODONCIA — CO / es-CO

- Título: Consentimiento informado de ortodoncia
- Tipo: INFORMED_CONSENT
- Páginas fuente: [3, 4, 5]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 5
- Líneas de firma eliminadas: 4
- Párrafos unidos: 91
- Frases de representante: ['apoderado', 'paciente o tutor legal']
- Términos locales: ['cabritas', 'garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
ort

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

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
consentimient

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de ortodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE ORTODONCIA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. El tratamiento de ortodoncia consiste en la corrección y alineación de los dientes mejorando la oclusión (mordida), función masticatoria, estética y autoestima del paciente. Esto ocurre mediante la utilización de aparatos metálicos o estéticos ya sean fijos o removibles. El éxito y resultado final del tratamiento está estrechamente ligado a la colaboración y responsabilidad del paciente/apoderado, asistir a sus controles mensuales, seguir indicaciones del dentista y equipo médico, consultar en momentos de urgencia, cuidar hábitos de alimentación e higiene, entre otros. La ausencia reiterada sin previo aviso a los controles de ortodoncia facultara al ortodoncista para terminar con el tratamiento y dar el alta disciplinaria al paciente, exonerando de cualquier responsabilidad futura al especialista. Se me ha explicado que por la longevidad del tratamiento y su complejidad es posible que durante el mismo tratamiento se necesiten acciones adicionales de otros especialistas, lo que se deberá presupuestar, asumiendo el costo y no están incluidos en lo pagado por ortodoncia. (futuras limpiezas, nuevas caries, cambios de obturaciones, coronas, micro tornillos, implantes, etc.). A continuación, se indican las condiciones: antes del tratamiento, durante el tratamiento y posterior al tratamiento. Antes del tratamiento: Para comenzar un tratamiento de ortodoncia, el paciente debe tener su boca 100% sana, libre de infecciones y tener el alta de la unidad de odontología general y/o algún especialista en particular. El paciente pasará, primero por un estudio previo a la instalación de ortodoncia, el llamado estudio de ortodoncia, en la que el odontólogo reunirá toda la información para planificar y pronosticar el caso clínico. Esta información se puede recabar mediante una anamnesis e historia clínica, estudio radiográfico (pack de ortodoncia), scanner, exámenes complementarios, estudio cefalométrico, impresiones preliminares en yeso, montaje en articulador, fotografía clínica, entre otros. El ortodoncista buscará planificar en número y tiempo de controles, no obstante, en la práctica pueden ser menos o más controles de los planificados ya que la evolución dental depende en gran parte de factores directamente relacionados al paciente. Si se extiende el tiempo y resultan más controles de los planificados, el paciente asumirá el costo de cada control mensual, pues se paga mensualmente por control activo hasta terminar el tratamiento. Si comencé mi tratamiento en otra institución, deberé de traer toda la información que pueda (historial clínico) para cambiar de centro odontológico, asumiendo en la mayoría de los casos que deberé retirar mi ortodoncia antigua, realizar pack de radiografías de ortodoncia, ser evaluado en la unidad de diagnóstico y odontología general, recibir presupuestos y plan de tratamiento, realizar todo tipo de tratamiento previo hasta obtener el alta y luego ser derivado a ortodoncia para estudio e instalación de nuevos aparatos de ortodoncia. Durante el tratamiento: El paciente deberá utilizar cepillos especiales para limpiar sus dientes y los aparatos de ortodoncia (cepillo monotip, ortodontic e interproximales). La ausencia a controles de ortodoncia retrasará el tratamiento en el tiempo planificado y podrá ser necesario agregar acciones adicionales no contempladas en el presupuesto y diagnóstico inicial. La reposición de un bracket de ortodoncia desalojado tiene costo adicional, que debe asumir el paciente, ya que se desalojan por

cuidados, factores biológicos y personales del usuario. Si un bracket se suelta reiteradas veces es atribuible a no seguir las indicaciones por parte del paciente. Indicaciones especificadas en el consentimiento como prohibiciones. La urgencia de ortodoncia no tiene costo siempre que el paciente haya sido responsa

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_ORTODONCIA — CL / es-CL

- Título: Consentimiento informado de ortodoncia
- Tipo: INFORMED_CONSENT
- Páginas fuente: [3, 4, 5]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 5
- Líneas de firma eliminadas: 4
- Párrafos unidos: 91
- Frases de representante: ['apoderado', 'paciente o tutor legal']
- Términos locales: ['cabritas', 'garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
ort

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

```markdown
# Consentimiento informado de ortodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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
consentimiento c

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de ortodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE ORTODONCIA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. El tratamiento de ortodoncia consiste en la corrección y alineación de los dientes mejorando la oclusión (mordida), función masticatoria, estética y autoestima del paciente. Esto ocurre mediante la utilización de aparatos metálicos o estéticos ya sean fijos o removibles. El éxito y resultado final del tratamiento está estrechamente ligado a la colaboración y responsabilidad del paciente/apoderado, asistir a sus controles mensuales, seguir indicaciones del dentista y equipo médico, consultar en momentos de urgencia, cuidar hábitos de alimentación e higiene, entre otros. La ausencia reiterada sin previo aviso a los controles de ortodoncia facultara al ortodoncista para terminar con el tratamiento y dar el alta disciplinaria al paciente, exonerando de cualquier responsabilidad futura al especialista. Se me ha explicado que por la longevidad del tratamiento y su complejidad es posible que durante el mismo tratamiento se necesiten acciones adicionales de otros especialistas, lo que se deberá presupuestar, asumiendo el costo y no están incluidos en lo pagado por ortodoncia. (futuras limpiezas, nuevas caries, cambios de obturaciones, coronas, micro tornillos, implantes, etc.). A continuación, se indican las condiciones: antes del tratamiento, durante el tratamiento y posterior al tratamiento. Antes del tratamiento: Para comenzar un tratamiento de ortodoncia, el paciente debe tener su boca 100% sana, libre de infecciones y tener el alta de la unidad de odontología general y/o algún especialista en particular. El paciente pasará, primero por un estudio previo a la instalación de ortodoncia, el llamado estudio de ortodoncia, en la que el odontólogo reunirá toda la información para planificar y pronosticar el caso clínico. Esta información se puede recabar mediante una anamnesis e historia clínica, estudio radiográfico (pack de ortodoncia), scanner, exámenes complementarios, estudio cefalométrico, impresiones preliminares en yeso, montaje en articulador, fotografía clínica, entre otros. El ortodoncista buscará planificar en número y tiempo de controles, no obstante, en la práctica pueden ser menos o más controles de los planificados ya que la evolución dental depende en gran parte de factores directamente relacionados al paciente. Si se extiende el tiempo y resultan más controles de los planificados, el paciente asumirá el costo de cada control mensual, pues se paga mensualmente por control activo hasta terminar el tratamiento. Si comencé mi tratamiento en otra institución, deberé de traer toda la información que pueda (historial clínico) para cambiar de centro odontológico, asumiendo en la mayoría de los casos que deberé retirar mi ortodoncia antigua, realizar pack de radiografías de ortodoncia, ser evaluado en la unidad de diagnóstico y odontología general, recibir presupuestos y plan de tratamiento, realizar todo tipo de tratamiento previo hasta obtener el alta y luego ser derivado a ortodoncia para estudio e instalación de nuevos aparatos de ortodoncia. Durante el tratamiento: El paciente deberá utilizar cepillos especiales para limpiar sus dientes y los aparatos de ortodoncia (cepillo monotip, ortodontic e interproximales). La ausencia a controles de ortodoncia retrasará el tratamiento en el tiempo planificado y podrá ser necesario agregar acciones adicionales no contempladas en el presupuesto y diagnóstico inicial. La reposición de un bracket de ortodoncia desalojado tiene costo adicional, que debe asumir el paciente, ya que se desalojan por

cuidados, factores biológicos y personales del usuario. Si un bracket se suelta reiteradas veces es atribuible a no seguir las indicaciones por parte del paciente. Indicaciones especificadas en el consentimiento como prohibiciones. La urgencia de ortodoncia no tiene costo siempre que el paciente haya sido responsable

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_NO_GARANTIA — CO / es-CO

- Título: Exención de garantía odontológica
- Tipo: NO_WARRANTY_ACKNOWLEDGEMENT
- Páginas fuente: [6]
- Estado: **BLOCKED**
- Compatibilidad firmante: `FUTURE_WORKFLOW`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 6
- Párrafos unidos: 18
- Frases de representante: No detectadas
- Términos locales: ['garantía', 'GARANTIA', 'garantías']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:NO_WARRANTY_ACKNOWLEDGEMENT', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Exención de garantía odontológica

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO EXCENCION DE GARANTIA – NO GARANTÍA PROCEDIMIENTO El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del estado de mi salud bucal y posibilidades de tratamiento asociadas. He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Se me ha explicado que existen otros tratamientos ideales para mi patología, pero por decisión propia y temas personales acepto realizar el procedimiento descrito anteriormente, del cual asumo todo tipo de responsabilidad, costos y consecuencias que podrían surgir. Entiendo que el procedimiento mencionado no se puede garantizar desde su aspecto clínico y libero de cualquier tipo de responsabilidad a el o los odontólogo(s), clínica {{company.name}} y al personal involucrado en este tratamiento; por lo que en el futuro NO tendré derecho a garantías, devoluciones, reclamos ni demanda por el mismo.

```

## CONS_NO_GARANTIA — CL / es-CL

- Título: Exención de garantía odontológica
- Tipo: NO_WARRANTY_ACKNOWLEDGEMENT
- Páginas fuente: [6]
- Estado: **BLOCKED**
- Compatibilidad firmante: `FUTURE_WORKFLOW`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 6
- Párrafos unidos: 18
- Frases de representante: No detectadas
- Términos locales: ['garantía', 'GARANTIA', 'garantías']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:NO_WARRANTY_ACKNOWLEDGEMENT', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Exención de garantía odontológica

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Exención de garantía odontológica

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO EXCENCION DE GARANTIA – NO GARANTÍA PROCEDIMIENTO El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del estado de mi salud bucal y posibilidades de tratamiento asociadas. He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Se me ha explicado que existen otros tratamientos ideales para mi patología, pero por decisión propia y temas personales acepto realizar el procedimiento descrito anteriormente, del cual asumo todo tipo de responsabilidad, costos y consecuencias que podrían surgir. Entiendo que el procedimiento mencionado no se puede garantizar desde su aspecto clínico y libero de cualquier tipo de responsabilidad a el o los odontólogo(s), clínica {{company.name}} y al personal involucrado en este tratamiento; por lo que en el futuro NO tendré derecho a garantías, devoluciones, reclamos ni demanda por el mismo.

```

## CONS_CIRUGIA — CO / es-CO

- Título: Consentimiento informado de cirugía odontológica
- Tipo: INFORMED_CONSENT
- Páginas fuente: [7]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 6
- Párrafos unidos: 43
- Frases de representante: ['tutor', 'paciente o tutor legal']
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de cirugía odontológica

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO CIRUGÍA PROCEDIMIENTO ___ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Puedo presentar posterior a una cirugía de forma inmediata o tardía, inflamación, aumento de volumen, dolor, infección, alveolitis húmeda, alveolitis seca, hemorragia, hematomas o equimosis. Menos frecuente puede ocurrir fractura dental o de tejido óseo, alteración sensitiva de los nervios de forma temporal o definitiva, traslado o impulsión de piezas dentales a otros sitios anatómicos (seno maxilar), comunicación buco sinusal por piezas que tengan íntima relación anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos, molestias en músculos o articulación temporo mandibular por mantener abierta la boca mucho tiempo, dificultad para abrir la boca o masticar, fracturas de instrumentos. Durante el procedimiento, existe la posibilidad de nuevos hallazgos clínicos y patológicos que no se pudieron predecir mediante el examen clínico y radiográfico, cambiando el curso del tratamiento inclusive llevando a realizar tratamientos adicionales, como una biopsia, eliminación de una masa tumoral, enucleación de quistes, o aplicación de injertos e insumos biológicos, etc. Por lo que el paciente deberá asumir el costo del nuevo presupuesto o la diferencia de este. Si el paciente viene acompañado mientras está siendo operado, se le explicará a su tutor acompañante. Se me ha explicado, en caso de faltar o ausentarme sin previo aviso (24 horas antes) a mi hora de cirugía, los 30.000 de la reserva no serán devueltos, debiendo pagar nuevamente el valor de reserva por programación de cirugía. De la misma forma si el doctor decide no llevar a cabo la cirugía por no seguir las instrucciones explicadas en la evaluación de cirugía al NO tomar la pre-medicación entregada antes del procedimiento quirúrgico o por NO traer/mostrar los exámenes complementarios requeridos, habiendo sido de mi absoluta responsabilidad. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_CIRUGIA — CL / es-CL

- Título: Consentimiento informado de cirugía odontológica
- Tipo: INFORMED_CONSENT
- Páginas fuente: [7]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 6
- Párrafos unidos: 43
- Frases de representante: ['tutor', 'paciente o tutor legal']
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de cirugía odontológica

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de cirugía odontológica

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO CIRUGÍA PROCEDIMIENTO ___ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Puedo presentar posterior a una cirugía de forma inmediata o tardía, inflamación, aumento de volumen, dolor, infección, alveolitis húmeda, alveolitis seca, hemorragia, hematomas o equimosis. Menos frecuente puede ocurrir fractura dental o de tejido óseo, alteración sensitiva de los nervios de forma temporal o definitiva, traslado o impulsión de piezas dentales a otros sitios anatómicos (seno maxilar), comunicación buco sinusal por piezas que tengan íntima relación anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos, molestias en músculos o articulación temporo mandibular por mantener abierta la boca mucho tiempo, dificultad para abrir la boca o masticar, fracturas de instrumentos. Durante el procedimiento, existe la posibilidad de nuevos hallazgos clínicos y patológicos que no se pudieron predecir mediante el examen clínico y radiográfico, cambiando el curso del tratamiento inclusive llevando a realizar tratamientos adicionales, como una biopsia, eliminación de una masa tumoral, enucleación de quistes, o aplicación de injertos e insumos biológicos, etc. Por lo que el paciente deberá asumir el costo del nuevo presupuesto o la diferencia de este. Si el paciente viene acompañado mientras está siendo operado, se le explicará a su tutor acompañante. Se me ha explicado, en caso de faltar o ausentarme sin previo aviso (24 horas antes) a mi hora de cirugía, los 30.000 de la reserva no serán devueltos, debiendo pagar nuevamente el valor de reserva por programación de cirugía. De la misma forma si el doctor decide no llevar a cabo la cirugía por no seguir las instrucciones explicadas en la evaluación de cirugía al NO tomar la pre-medicación entregada antes del procedimiento quirúrgico o por NO traer/mostrar los exámenes complementarios requeridos, habiendo sido de mi absoluta responsabilidad. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_DESTARTRAJE_OPERATORIA — CO / es-CO

- Título: Consentimiento de destartraje y operatoria dental
- Tipo: INFORMED_CONSENT
- Páginas fuente: [8, 9]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 51
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['tapadura', 'garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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
Comprendo y me comprometo como paciente o tutor legal a que debo seguir las indic

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento de destartraje y operatoria dental

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DESTARTRAJE Y OPERATORIA DENTAL Declaro haber informado de forma clara y veraz a el / la odontólogo/a tratante respecto a mi estado de salud general, condiciones médicas u odontológicas, tratamientos previos y actuales, alergias, cirugías previas y fármacos que utilizo o cualquier otro antecedente. El/la odontólogo/a tratante me ha informado respecto a mi estado de salud bucal y resuelto mis dudas e inquietudes respecto al mismo. Me ha explicado también los tratamientos propuestos junto a las ventajas y desventajas, al igual que los riesgos, beneficios y posibles complicaciones en caso de realizar o no realizar el tratamiento mencionado. Me ha informado respecto a la posible necesidad de uso de anestésicos, indicación de fármacos, elementos de higiene u otras indicaciones que pudiesen ser necesarias para lograr los objetivos del tratamiento. El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía mediante el uso de un instrumento que emite vibraciones y agua en spray. Usualmente el destartraje no es un procedimiento doloroso, sin embargo, esto es subjetivo por lo que en algunos casos se podrían presentar sensibilidad dental o molestias durante o posterior al mismo. En ocasiones el depósito de tártaro también puede ubicarse bajo la encía, necesitando complementar el destartraje supragingival con uno subgingival. El uso ultrasonido por sí mismo no daña el tejido dental ni tampoco es capaz de desalojar una obturación (tapadura) o corona antigua que se encuentre en buenas condiciones, si esto ocurriera significa que ya existe un daño previo, que no se encuentra en buen estado y probablemente haya perdido su adhesión; en caso de ocurrir, implica la necesidad de realizar el recambio completo de la obturación, que deberá ser presupuestada y costeada por mí como paciente. La duración de la limpieza está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un tratamiento que cuente con algún tipo de garantía posterior. Las restauraciones (tapaduras) o tratamiento de operatoria permiten restituir parte del diente a través de un material artificial y un sistema adhesivo biocompatible, como es el caso de cuando se ha sufrido caries u otras causas. El tratamiento de caries puede generar sensibilidad postoperatoria, que en su mayoría es reversible y que ocurre debido a múltiples factores como la profundidad de la cavidad, daño o tratamientos previos, contracción de polimerización del material restaurador, estado de la pulpa (nervio) del diente u otros. Debido a estos factores dinámicos, incluso utilizando exámenes radiográficos, no siempre es predecible el estado pulpar del diente y es posible que en algunos casos la sensibilidad o molestia posterior a la atención no remita y que para resolverlo el diente necesite un tratamiento endodóntico (tratamiento de conducto), que en ese caso deberá también ser presupuestado y costeado por el / la paciente. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo/a, entendiendo también la posibilidad de ser derivado con otro/a especialista para concluir mi tratamiento exitosamente. Comprendo que tengo garantías (según plazos indicados en presupuestos) por los tratamientos realizados en clínica {{company.name}}, por lo que si se presenta alguna complicación posterior, es a quienes primero debo contactar y acudir para ser reevaluado y hacer uso de la misma, para verificar

posibilidades tratamiento, repitiéndolo o considerando uno distinto si es que el caso lo amerita y que podría implicar una diferencia a costear sobre el mismo. En caso de ser necesario pasaré por una evaluación de contraloría a cargo del director de la clínica y no será posible hacer uso de garantías si es que soy intervenido/a en otro centro dental y perderé todo tipo de cobertura de este tipo o posibilidades de devolución. Comprendo y me comprometo como paciente o tutor legal a que debo seguir las indicaciones de mi odontólogo/a tratante, siendo responsable con estas mismas y/o con el uso de los fármacos p

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_DESTARTRAJE_OPERATORIA — CL / es-CL

- Título: Consentimiento de destartraje y operatoria dental
- Tipo: INFORMED_CONSENT
- Páginas fuente: [8, 9]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 51
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['tapadura', 'garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento de destartraje y operatoria dental

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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
Comprendo y me comprometo como paciente o tutor legal a que debo seguir las indicaci

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento de destartraje y operatoria dental

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DESTARTRAJE Y OPERATORIA DENTAL Declaro haber informado de forma clara y veraz a el / la odontólogo/a tratante respecto a mi estado de salud general, condiciones médicas u odontológicas, tratamientos previos y actuales, alergias, cirugías previas y fármacos que utilizo o cualquier otro antecedente. El/la odontólogo/a tratante me ha informado respecto a mi estado de salud bucal y resuelto mis dudas e inquietudes respecto al mismo. Me ha explicado también los tratamientos propuestos junto a las ventajas y desventajas, al igual que los riesgos, beneficios y posibles complicaciones en caso de realizar o no realizar el tratamiento mencionado. Me ha informado respecto a la posible necesidad de uso de anestésicos, indicación de fármacos, elementos de higiene u otras indicaciones que pudiesen ser necesarias para lograr los objetivos del tratamiento. El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía mediante el uso de un instrumento que emite vibraciones y agua en spray. Usualmente el destartraje no es un procedimiento doloroso, sin embargo, esto es subjetivo por lo que en algunos casos se podrían presentar sensibilidad dental o molestias durante o posterior al mismo. En ocasiones el depósito de tártaro también puede ubicarse bajo la encía, necesitando complementar el destartraje supragingival con uno subgingival. El uso ultrasonido por sí mismo no daña el tejido dental ni tampoco es capaz de desalojar una obturación (tapadura) o corona antigua que se encuentre en buenas condiciones, si esto ocurriera significa que ya existe un daño previo, que no se encuentra en buen estado y probablemente haya perdido su adhesión; en caso de ocurrir, implica la necesidad de realizar el recambio completo de la obturación, que deberá ser presupuestada y costeada por mí como paciente. La duración de la limpieza está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un tratamiento que cuente con algún tipo de garantía posterior. Las restauraciones (tapaduras) o tratamiento de operatoria permiten restituir parte del diente a través de un material artificial y un sistema adhesivo biocompatible, como es el caso de cuando se ha sufrido caries u otras causas. El tratamiento de caries puede generar sensibilidad postoperatoria, que en su mayoría es reversible y que ocurre debido a múltiples factores como la profundidad de la cavidad, daño o tratamientos previos, contracción de polimerización del material restaurador, estado de la pulpa (nervio) del diente u otros. Debido a estos factores dinámicos, incluso utilizando exámenes radiográficos, no siempre es predecible el estado pulpar del diente y es posible que en algunos casos la sensibilidad o molestia posterior a la atención no remita y que para resolverlo el diente necesite un tratamiento endodóntico (tratamiento de conducto), que en ese caso deberá también ser presupuestado y costeado por el / la paciente. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo/a, entendiendo también la posibilidad de ser derivado con otro/a especialista para concluir mi tratamiento exitosamente. Comprendo que tengo garantías (según plazos indicados en presupuestos) por los tratamientos realizados en clínica {{company.name}}, por lo que si se presenta alguna complicación posterior, es a quienes primero debo contactar y acudir para ser reevaluado y hacer uso de la misma, para verificar

posibilidades tratamiento, repitiéndolo o considerando uno distinto si es que el caso lo amerita y que podría implicar una diferencia a costear sobre el mismo. En caso de ser necesario pasaré por una evaluación de contraloría a cargo del director de la clínica y no será posible hacer uso de garantías si es que soy intervenido/a en otro centro dental y perderé todo tipo de cobertura de este tipo o posibilidades de devolución. Comprendo y me comprometo como paciente o tutor legal a que debo seguir las indicaciones de mi odontólogo/a tratante, siendo responsable con estas mismas y/o con el uso de los fármacos pres

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_IMPLANTOLOGIA — CO / es-CO

- Título: Consentimiento informado de implantología
- Tipo: INFORMED_CONSENT
- Páginas fuente: [10, 11]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 6
- Párrafos unidos: 65
- Frases de representante: ['tutor', 'paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
responsable con las indicaciones y prescripción de fármacos, asistiendo a con

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

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
por no seguir las instrucciones explicadas en

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de implantología

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO IMPLANTOLOGÍA PROCEDIMIENTO ___ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. El tratamiento de implantes consiste en la instalación de un tornillo de titanio en el hueso, el que debe osteointegrarse pudiendo tardar desde 3 a 6 meses antes de ser conectado a través de tornillos protésicos para continuar con la corona sobre implantes. El implante reemplaza la raíz del diente, por lo que la instalación del implante por si sola no corresponde al tratamiento final y definitivo. El tratamiento se completa cuando el o los implantes son rehabilitados mediante una o varias coronas dentales, luego son controlados en una o varias sesiones por el especialista y entrega el alta. El implante está fabricado con titanio y es biocompatible con el cuerpo humano. El tornillo de titanio tiene garantía de por vida y la corona sobre el tornillo de titanio tiene garantía 1 año. Los insumos biológicos, como injertos y membranas NO tienen garantía debido a que su éxito recae en la compatibilidad, cicatrización e integración del organismo del paciente (algunos pacientes rechazan el injerto). En caso de repetir el procedimiento, los insumos biológicos deben ser nuevamente pagados por el paciente. La garantía se hace efectiva una vez que el tratamiento se encuentra terminado en su totalidad dentro de los plazos correspondientes. La garantía se mantendrá mientras el paciente asista a sus controles periódicos, manteniendo los implantes en buen estado, gran parte de los fallos de este tratamiento ocurren por peri-implantitis asociado a placa bacteriana, es decir por la higiene y cepillado a diario del paciente o malos hábitos como el cigarro. A nivel mundial los implantes tienen buena tasa de efectividad, llegando inclusive al 97-98% de éxito al largo plazo, por el contrario, un 2-3% de los pacientes rechazan los implantes por situaciones inherentes al procedimiento, ya sea por rechazo de su organismo y sistema inmunológico, deficiente cicatrización, mal cepillado y mala higiene (infección y placa bacteriana) o malos hábitos de consumo de cigarro, tabaco y drogas. Puedo presentar posterior a una cirugía de forma inmediata o tardía, inflamación, aumento de volumen, dolor, infección, alveolitis húmeda, alveolitis seca, hemorragia, hematomas o equimosis. Menos frecuente puede ocurrir fractura dental o de tejido óseo, alteración sensitiva de los nervios de forma temporal o definitiva, traslado o impulsión de piezas dentales a otros sitios anatómicos (seno maxilar), comunicación buco sinusal por piezas que tengan íntima relación anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos, molestias en músculos o articulación temporo mandibular por mantener abierta la boca mucho tiempo, dificultad para abrir la boca o masticar, fracturas de instrumentos. Durante el procedimiento, existe la posibilidad de nuevos hallazgos clínicos y patológicos que no se pueden predecir mediante el examen clínico y radiográfico, cambiando el curso del tratamiento inclusive llevando a realizar tratamientos adicionales, como una biopsia, eliminación de una masa tumoral, enucleación de quistes, o aplicación de injertos e insumos biológicos, etc. Por lo que el

paciente deberá asumir el costo del nuevo presupuesto o la diferencia de este. Si el paciente viene acompañado mientras está siendo operado, se le explicará a su tutor acompañante. Se me ha explicado, en caso de faltar o ausentarme sin previo aviso (24 horas antes) a mi hora de cirugía, los 30.000 de la reserva no serán devueltos, debiendo pagar nuevamente el valor de reserva por programación de cirugía. De la misma forma si el doctor decide no llevar a cabo la cirugía por no seguir las instrucciones explicadas en la evaluación y planificación de cirugía al NO tomar la pre-medicación entregada antes del procedimiento quirúrgico o por NO traer/mostrar los exámenes complementarios requer

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_IMPLANTOLOGIA — CL / es-CL

- Título: Consentimiento informado de implantología
- Tipo: INFORMED_CONSENT
- Páginas fuente: [10, 11]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 6
- Párrafos unidos: 65
- Frases de representante: ['tutor', 'paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
responsable con las indicaciones y prescripción de fármacos, asistiendo a con

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

```markdown
# Consentimiento informado de implantología

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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
por no seguir las instrucciones explicadas en la

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de implantología

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO IMPLANTOLOGÍA PROCEDIMIENTO ___ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. El tratamiento de implantes consiste en la instalación de un tornillo de titanio en el hueso, el que debe osteointegrarse pudiendo tardar desde 3 a 6 meses antes de ser conectado a través de tornillos protésicos para continuar con la corona sobre implantes. El implante reemplaza la raíz del diente, por lo que la instalación del implante por si sola no corresponde al tratamiento final y definitivo. El tratamiento se completa cuando el o los implantes son rehabilitados mediante una o varias coronas dentales, luego son controlados en una o varias sesiones por el especialista y entrega el alta. El implante está fabricado con titanio y es biocompatible con el cuerpo humano. El tornillo de titanio tiene garantía de por vida y la corona sobre el tornillo de titanio tiene garantía 1 año. Los insumos biológicos, como injertos y membranas NO tienen garantía debido a que su éxito recae en la compatibilidad, cicatrización e integración del organismo del paciente (algunos pacientes rechazan el injerto). En caso de repetir el procedimiento, los insumos biológicos deben ser nuevamente pagados por el paciente. La garantía se hace efectiva una vez que el tratamiento se encuentra terminado en su totalidad dentro de los plazos correspondientes. La garantía se mantendrá mientras el paciente asista a sus controles periódicos, manteniendo los implantes en buen estado, gran parte de los fallos de este tratamiento ocurren por peri-implantitis asociado a placa bacteriana, es decir por la higiene y cepillado a diario del paciente o malos hábitos como el cigarro. A nivel mundial los implantes tienen buena tasa de efectividad, llegando inclusive al 97-98% de éxito al largo plazo, por el contrario, un 2-3% de los pacientes rechazan los implantes por situaciones inherentes al procedimiento, ya sea por rechazo de su organismo y sistema inmunológico, deficiente cicatrización, mal cepillado y mala higiene (infección y placa bacteriana) o malos hábitos de consumo de cigarro, tabaco y drogas. Puedo presentar posterior a una cirugía de forma inmediata o tardía, inflamación, aumento de volumen, dolor, infección, alveolitis húmeda, alveolitis seca, hemorragia, hematomas o equimosis. Menos frecuente puede ocurrir fractura dental o de tejido óseo, alteración sensitiva de los nervios de forma temporal o definitiva, traslado o impulsión de piezas dentales a otros sitios anatómicos (seno maxilar), comunicación buco sinusal por piezas que tengan íntima relación anatómica con el seno maxilar, reacciones alérgicas a la anestesia o fármacos, molestias en músculos o articulación temporo mandibular por mantener abierta la boca mucho tiempo, dificultad para abrir la boca o masticar, fracturas de instrumentos. Durante el procedimiento, existe la posibilidad de nuevos hallazgos clínicos y patológicos que no se pueden predecir mediante el examen clínico y radiográfico, cambiando el curso del tratamiento inclusive llevando a realizar tratamientos adicionales, como una biopsia, eliminación de una masa tumoral, enucleación de quistes, o aplicación de injertos e insumos biológicos, etc. Por lo que el

paciente deberá asumir el costo del nuevo presupuesto o la diferencia de este. Si el paciente viene acompañado mientras está siendo operado, se le explicará a su tutor acompañante. Se me ha explicado, en caso de faltar o ausentarme sin previo aviso (24 horas antes) a mi hora de cirugía, los 30.000 de la reserva no serán devueltos, debiendo pagar nuevamente el valor de reserva por programación de cirugía. De la misma forma si el doctor decide no llevar a cabo la cirugía por no seguir las instrucciones explicadas en la evaluación y planificación de cirugía al NO tomar la pre-medicación entregada antes del procedimiento quirúrgico o por NO traer/mostrar los exámenes complementarios requerido

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_ODONTOPEDIATRIA — CO / es-CO

- Título: Consentimiento informado de odontopediatría
- Tipo: INFORMED_CONSENT
- Páginas fuente: [12, 13]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 59
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['tapadura', 'garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
en caso de ser necesario. En caso contrario si consu

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

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
Comprendo que tengo garantías por los tratamientos realiz

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de odontopediatría

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO ODONTOPEDIATRÍA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía (supragingival) mediante el uso de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros y eliminarlos mediante la irrigación a través de agua. El tártaro en ocasiones se aloja en el tejido subgingival (por debajo de la encía) o tejido radicular del diente, debiendo ser derivado a la especialidad de periodoncia para un adecuado tratamiento, presupuestando el destartraje subgingival y pulido radicular según corresponda. El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua (tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba en buen estado perdiendo su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de la limpieza está directamente vinculada al cuidado e higiene personal del paciente. Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries, contracción de polimerización, calor del fresado al eliminar la caries), en otros casos la sensibilidad o molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del diente. Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y se derivará al paciente (especialidad de rehabilitación oral). Los tratamientos pulpares en niños (pulpotomía o pulpectomía) ayudan a conservar el diente en su posición, manteniendo el espacio del diente y dientes vecinos para las futuras erupciones de piezas permanentes. Aun así, existe una probabilidad de fracaso endodóntico en niños (inherente al trabajo del odontopediatra), por lo que se tendrá que recurrir a nuevas acciones, por ejemplo, una exodoncia (extracción), lo que debe ser costeado por el paciente. En términos generales el acelerado metabolismo y recambio dentario que tienen los niños aumentan la posibilidad de riesgos y complicaciones inesperadas, como: dolor, inflamación, infección, pulpitis,

aumentos de volumen, hematomas, equimosis. En caso de presentar fiebre y deshidratación se recomienda llevar al infante inmediatamente a urgencia médica de alta complejidad (hospital). Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento co

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_ODONTOPEDIATRIA — CL / es-CL

- Título: Consentimiento informado de odontopediatría
- Tipo: INFORMED_CONSENT
- Páginas fuente: [12, 13]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 59
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['tapadura', 'garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
en caso de ser necesario. En caso contrario si consu

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

```markdown
# Consentimiento informado de odontopediatría

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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
Comprendo que tengo garantías por los tratamientos realizado

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de odontopediatría

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO ODONTOPEDIATRÍA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía (supragingival) mediante el uso de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros y eliminarlos mediante la irrigación a través de agua. El tártaro en ocasiones se aloja en el tejido subgingival (por debajo de la encía) o tejido radicular del diente, debiendo ser derivado a la especialidad de periodoncia para un adecuado tratamiento, presupuestando el destartraje subgingival y pulido radicular según corresponda. El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua (tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba en buen estado perdiendo su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de la limpieza está directamente vinculada al cuidado e higiene personal del paciente. Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries, contracción de polimerización, calor del fresado al eliminar la caries), en otros casos la sensibilidad o molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del diente. Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y se derivará al paciente (especialidad de rehabilitación oral). Los tratamientos pulpares en niños (pulpotomía o pulpectomía) ayudan a conservar el diente en su posición, manteniendo el espacio del diente y dientes vecinos para las futuras erupciones de piezas permanentes. Aun así, existe una probabilidad de fracaso endodóntico en niños (inherente al trabajo del odontopediatra), por lo que se tendrá que recurrir a nuevas acciones, por ejemplo, una exodoncia (extracción), lo que debe ser costeado por el paciente. En términos generales el acelerado metabolismo y recambio dentario que tienen los niños aumentan la posibilidad de riesgos y complicaciones inesperadas, como: dolor, inflamación, infección, pulpitis,

aumentos de volumen, hematomas, equimosis. En caso de presentar fiebre y deshidratación se recomienda llevar al infante inmediatamente a urgencia médica de alta complejidad (hospital). Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consu

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## RECHAZO_TRATAMIENTO — CO / es-CO

- Título: Rechazo de tratamiento odontológico, quirúrgico o diagnóstico
- Tipo: TREATMENT_REFUSAL
- Páginas fuente: [14]
- Estado: **BLOCKED**
- Compatibilidad firmante: `FUTURE_WORKFLOW`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 9
- Párrafos unidos: 18
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:TREATMENT_REFUSAL']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Rechazo de tratamiento odontológico, quirúrgico o diagnóstico

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE RECHAZO AL TRATAMIENTO ODONTOLÓGICO, QUIRÚRGICO O PRUEBAS DIAGNÓSTICAS Por medio de la presente DECLARO que he sido debidamente informado por el número_________________ - ___ en relación a la necesidad de someterme a los siguientes tratamientos o pruebas diagnósticas: Declaro que he sido debidamente informado y que entiendo los riesgos y beneficios del tratamiento y/o pruebas diagnósticas recomendadas por el dentista tratante. Declaro que se me han respondido y aclarado todas mis dudas acerca del tratamiento y/o pruebas diagnósticas recomendadas por el dentista tratante. Considerando todas las opciones anteriores, aceptando y entendiendo los riesgos y posibles consecuencias de mi decisión, declaro que no es mi deseo continuar con el tratamiento y/o pruebas propuestas por el dentista tratante. NOMBRE PACIENTE: RUT PACIENTE:

```

## RECHAZO_TRATAMIENTO — CL / es-CL

- Título: Rechazo de tratamiento odontológico, quirúrgico o diagnóstico
- Tipo: TREATMENT_REFUSAL
- Páginas fuente: [14]
- Estado: **BLOCKED**
- Compatibilidad firmante: `FUTURE_WORKFLOW`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 9
- Párrafos unidos: 18
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:TREATMENT_REFUSAL']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Rechazo de tratamiento odontológico, quirúrgico o diagnóstico

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Rechazo de tratamiento odontológico, quirúrgico o diagnóstico

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE RECHAZO AL TRATAMIENTO ODONTOLÓGICO, QUIRÚRGICO O PRUEBAS DIAGNÓSTICAS Por medio de la presente DECLARO que he sido debidamente informado por el número_________________ - ___ en relación a la necesidad de someterme a los siguientes tratamientos o pruebas diagnósticas: Declaro que he sido debidamente informado y que entiendo los riesgos y beneficios del tratamiento y/o pruebas diagnósticas recomendadas por el dentista tratante. Declaro que se me han respondido y aclarado todas mis dudas acerca del tratamiento y/o pruebas diagnósticas recomendadas por el dentista tratante. Considerando todas las opciones anteriores, aceptando y entendiendo los riesgos y posibles consecuencias de mi decisión, declaro que no es mi deseo continuar con el tratamiento y/o pruebas propuestas por el dentista tratante. NOMBRE PACIENTE: RUT PACIENTE:

```

## CONS_DESTARTRAJE — CO / es-CO

- Título: Consentimiento informado de destartraje
- Tipo: INFORMED_CONSENT
- Páginas fuente: [15]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 32
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['tapadura', 'garantía']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de destartraje

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE DESTARTRAJE El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía (supragingival) mediante el uso de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros y eliminarlos mediante la irrigación a través de agua. El tártaro en ocasiones se aloja en el tejido subgingival (por debajo de la encía) o tejido radicular del diente, debiendo ser derivado a la especialidad de periodoncia para un adecuado tratamiento, presupuestando el destartraje subgingival y pulido radicular según corresponda. El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua (tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba en buen estado perdiendo su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de la limpieza está directamente vinculada al cuidado e higiene personal del paciente. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. La duración de la limpieza está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un tratamiento que cuente con algún tipo de garantía posterior. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_DESTARTRAJE — CL / es-CL

- Título: Consentimiento informado de destartraje
- Tipo: INFORMED_CONSENT
- Páginas fuente: [15]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 32
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['tapadura', 'garantía']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de destartraje

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de destartraje

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE DESTARTRAJE El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: El destartraje supragingival y pulido coronario o limpieza dental consiste en la remoción del tártaro dental (sarro) adherido a la superficie del diente que se encuentra por sobre la encía (supragingival) mediante el uso de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros y eliminarlos mediante la irrigación a través de agua. El tártaro en ocasiones se aloja en el tejido subgingival (por debajo de la encía) o tejido radicular del diente, debiendo ser derivado a la especialidad de periodoncia para un adecuado tratamiento, presupuestando el destartraje subgingival y pulido radicular según corresponda. El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua (tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba en buen estado perdiendo su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de la limpieza está directamente vinculada al cuidado e higiene personal del paciente. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. La duración de la limpieza está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un tratamiento que cuente con algún tipo de garantía posterior. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_ENDODONCIA — CO / es-CO

- Título: Consentimiento informado de endodoncia
- Tipo: INFORMED_CONSENT
- Páginas fuente: [16, 17]
- Estado: **NEEDS_REVIEW**
- Compatibilidad firmante: `ADULT_SELF`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 52
- Frases de representante: No detectadas
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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
la posibilidad de ser deriva

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de endodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE ENDODONCIA PROCEDIMIENTO _____ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. El tratamiento endodóntico (de conducto) consiste en la eliminación y extracción del tejido pulpar (nervio dental) rellenando con un material biocompatible los canales radiculares, para esto se ingresa a través del diente, eliminando el tejido infectado por caries, fracturas o por indicación de rehabilitación (anclar un perno/poste). El tejido pulpar se elimina utilizando limas endodónticas, antimicrobianos o irrigando con hipoclorito y otros elementos que mejoren la desinfección de los conductos radiculares. El tratamiento puede ser sobre una pulpa vital o necrótica (necrosis pulpar). Los retratamientos tienen un pronóstico de éxito reservado ya que son dientes que ya fueron tratados anteriormente y presentan mayor desgaste de tejido dentario. En ocasiones el tratamiento fracasa y el diente se deberá extraer, llevando el tratamiento a buscar otros caminos como implantes o prótesis. El tratamiento endodóntico corresponde al 50% del tratamiento final, ya que, una vez terminado el tratamiento de conducto, la corona dental se cierra y obtura con un material provisorio dentro de los que usualmente son fermín y vidrio ionómero, este doble sellado corresponde a un tratamiento provisorio y temporal que con el tiempo se infiltra hacia el interior del diente pudiendo volverse a infectar los canales radiculares. El tratamiento endodóntico se garantiza cuando el diente se ha rehabilitado definitivamente dentro de 30 días terminando la endodoncia, ya sea con una obturación simple o restauración indirecta (endocorona, incrustación, corona). Durante el procedimiento pueden ocurrir situaciones inherentes al operador (tratante), tales como, fractura de limas endodónticas por fatiga de material, fractura dentaria o radicular por debilitamiento de sus paredes producto del avance de caries o infección, aparición de quistes radiculares por avance de la infección desde el diente al hueso, para esto se deberá realizar una cirugía apical o exodoncia (según corresponda), debiendo asumir el costo el paciente, perforaciones o falsas vías desde el diente al periodonto, inyección y extravasación de hipoclorito a los tejidos que rodean al diente, pudiendo producir incluso quemaduras lo que se suele proteger con aislación absoluta para evitar que esto suceda, dolores, sensibilidad o molestias posterior al término de la endodoncia reversibles o irreversibles, desalojo del cemento temporal entre sesiones, conductos calcificados o pulpolitos que imposibiliten realizar el tratamiento endodóntico. Me han explicado que a pesar de terminar la endodoncia y estar correctamente realizada, el tratamiento podría no funcionar debido a la persistencia de inflamación/infección por bacterias resistentes. Entiendo que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e

intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de re

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_ENDODONCIA — CL / es-CL

- Título: Consentimiento informado de endodoncia
- Tipo: INFORMED_CONSENT
- Páginas fuente: [16, 17]
- Estado: **NEEDS_REVIEW**
- Compatibilidad firmante: `ADULT_SELF`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 52
- Frases de representante: No detectadas
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de endodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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
la posibilidad de ser derivado

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de endodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE ENDODONCIA PROCEDIMIENTO _____ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. El tratamiento endodóntico (de conducto) consiste en la eliminación y extracción del tejido pulpar (nervio dental) rellenando con un material biocompatible los canales radiculares, para esto se ingresa a través del diente, eliminando el tejido infectado por caries, fracturas o por indicación de rehabilitación (anclar un perno/poste). El tejido pulpar se elimina utilizando limas endodónticas, antimicrobianos o irrigando con hipoclorito y otros elementos que mejoren la desinfección de los conductos radiculares. El tratamiento puede ser sobre una pulpa vital o necrótica (necrosis pulpar). Los retratamientos tienen un pronóstico de éxito reservado ya que son dientes que ya fueron tratados anteriormente y presentan mayor desgaste de tejido dentario. En ocasiones el tratamiento fracasa y el diente se deberá extraer, llevando el tratamiento a buscar otros caminos como implantes o prótesis. El tratamiento endodóntico corresponde al 50% del tratamiento final, ya que, una vez terminado el tratamiento de conducto, la corona dental se cierra y obtura con un material provisorio dentro de los que usualmente son fermín y vidrio ionómero, este doble sellado corresponde a un tratamiento provisorio y temporal que con el tiempo se infiltra hacia el interior del diente pudiendo volverse a infectar los canales radiculares. El tratamiento endodóntico se garantiza cuando el diente se ha rehabilitado definitivamente dentro de 30 días terminando la endodoncia, ya sea con una obturación simple o restauración indirecta (endocorona, incrustación, corona). Durante el procedimiento pueden ocurrir situaciones inherentes al operador (tratante), tales como, fractura de limas endodónticas por fatiga de material, fractura dentaria o radicular por debilitamiento de sus paredes producto del avance de caries o infección, aparición de quistes radiculares por avance de la infección desde el diente al hueso, para esto se deberá realizar una cirugía apical o exodoncia (según corresponda), debiendo asumir el costo el paciente, perforaciones o falsas vías desde el diente al periodonto, inyección y extravasación de hipoclorito a los tejidos que rodean al diente, pudiendo producir incluso quemaduras lo que se suele proteger con aislación absoluta para evitar que esto suceda, dolores, sensibilidad o molestias posterior al término de la endodoncia reversibles o irreversibles, desalojo del cemento temporal entre sesiones, conductos calcificados o pulpolitos que imposibiliten realizar el tratamiento endodóntico. Me han explicado que a pesar de terminar la endodoncia y estar correctamente realizada, el tratamiento podría no funcionar debido a la persistencia de inflamación/infección por bacterias resistentes. Entiendo que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e

intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de reali

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_OBTURACION_DIRECTA — CO / es-CO

- Título: Consentimiento informado de obturación directa
- Tipo: INFORMED_CONSENT
- Páginas fuente: [18]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 36
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de obturación directa

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE OBTURACIÓN DIRECTA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries, contracción de polimerización, calor del fresado al eliminar la caries), en otros casos la sensibilidad o molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del diente. Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y se derivará al paciente (especialidad de rehabilitación oral). Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes de realizarlo.

```

## CONS_OBTURACION_DIRECTA — CL / es-CL

- Título: Consentimiento informado de obturación directa
- Tipo: INFORMED_CONSENT
- Páginas fuente: [18]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 36
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de obturación directa

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de obturación directa

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE OBTURACIÓN DIRECTA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries, contracción de polimerización, calor del fresado al eliminar la caries), en otros casos la sensibilidad o molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del diente. Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y se derivará al paciente (especialidad de rehabilitación oral). Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes de realizarlo.

```

## CONS_OBTURACION_BASE — CO / es-CO

- Título: Consentimiento informado de obturación directa con base cavitaria
- Tipo: INFORMED_CONSENT
- Páginas fuente: [19]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 42
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de obturación directa con base cavitaria

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE OBTURACION DIRECTA CON BASE CAVITARIA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries profunda además de la obturación de resina necesitara un sellado hermético con una base cavitaria, cemento protector pulpo-dentinario que proporciona un excelente aislamiento térmico, químico y eléctrico. Una barrera antibacteriana y antitoxinas. En algunos casos se puede realizar en dos sesiones para evaluar cómo se comporta el diente post eliminación de la caries profunda dejando la cavidad sellada con la base cavitaria y obturada con un material provisorio para posteriormente realizar la obturación de resina compuesta. El tratamiento de caries profunda puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries, contracción de polimerización, calor del fresado al eliminar la caries). Cuando la caries ha sido un daño progresivo el sellado hermético puede reactivar procesos infecciosos, donde la sensibilidad o molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del diente. Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y se derivará al paciente (especialidad de rehabilitación oral). Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes de realizarlo.

```

## CONS_OBTURACION_BASE — CL / es-CL

- Título: Consentimiento informado de obturación directa con base cavitaria
- Tipo: INFORMED_CONSENT
- Páginas fuente: [19]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 42
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de obturación directa con base cavitaria

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de obturación directa con base cavitaria

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE OBTURACION DIRECTA CON BASE CAVITARIA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: Las obturaciones (tapaduras) permiten restaurar el diente a través de un material artificial biocompatible con el diente el cual se pega mediante un sistema adhesivo. El tratamiento de caries profunda además de la obturación de resina necesitara un sellado hermético con una base cavitaria, cemento protector pulpo-dentinario que proporciona un excelente aislamiento térmico, químico y eléctrico. Una barrera antibacteriana y antitoxinas. En algunos casos se puede realizar en dos sesiones para evaluar cómo se comporta el diente post eliminación de la caries profunda dejando la cavidad sellada con la base cavitaria y obturada con un material provisorio para posteriormente realizar la obturación de resina compuesta. El tratamiento de caries profunda puede generar sensibilidad postoperatoria la que en su mayoría es reversible (avance de caries, contracción de polimerización, calor del fresado al eliminar la caries). Cuando la caries ha sido un daño progresivo el sellado hermético puede reactivar procesos infecciosos, donde la sensibilidad o molestia es irreversible y se deberá realizar un tratamiento endodóntico (tratamiento de conducto) lo que siendo un tratamiento adicional deberá ser costeado por el paciente, ya que en ocasiones no se puede predecir con el examen clínico o radiográfico el daño que presenta el tejido pulpar (nervio) del diente. Otro inconveniente es la posibilidad de desalojo de la restauración o su fractura, lo que será analizado por el dentista y se evaluará la garantía. En ocasiones también el desgaste de eliminación de caries es mayor al esperado por lo que el tratamiento planificado de restauración directa simple o compuesta no puede ser llevado a cabo y para solucionar el problema se deberá recurrir a una restauración indirecta, con la utilización de un laboratorio, ya sea una incrustación o corona con sistema de perno metálico o poste de fibra de vidrio, por lo que se entregará un presupuesto nuevo y se derivará al paciente (especialidad de rehabilitación oral). Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes de realizarlo.

```

## CONS_PERIODONCIA — CO / es-CO

- Título: Consentimiento informado de periodoncia
- Tipo: INFORMED_CONSENT
- Páginas fuente: [20]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 42
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['tapadura', 'garantía']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de periodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE PERIODONCIA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: El tratamiento periodontal consiste en la remoción del tártaro dental (sarro) adherido a la superficie del diente o los tejidos de soporte (periodonto). Se busca la eliminación de la infección, inflamación, sangrado y conservar la mayor cantidad de tejido óseo y dental. Esto se consigue mediante un destartraje supragingival, subgingival, pulido/alisado radicular y pulido coronario. Se puede realizar un tratamiento no quirúrgico (convencional) o quirúrgico. Por lo general se utilizan curetas y/o la aplicación de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros y eliminarlos mediante la irrigación a través de agua, adicional a esto se emplean antimicrobianos, antibióticos o medicamentos para ayudar a que el sistema elimine la infección. El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua (tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba en buen estado desde el inicio, y perdió su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de la limpieza está directamente vinculada al cuidado diario e higiene personal del paciente, debiendo siempre volver a sus controles para mantener una buena salud oral. Se me ha explicado que posterior al tratamiento periodontal, la enfermedad se puede reagudizar presentando inflamación, aumento de volumen o nuevas infecciones, además mis dientes pueden quedar con movilidad o mayor grado de movilidad del que tenían ya que siempre estuvieron así, y estaban aparentemente firmes a causa de la infección y tártaro (sarro), debido a esto es posible que necesite exodoncias (extracciones) y elementos protésicos adicionales, los que no contempla el tratamiento periodontal, estos serán presupuestados y derivados al especialista. Comprendo que la evolución y recuperación de mi enfermedad no se puede predecir ya que depende en gran parte de mi sistema inmune y organismo. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que la duración de la limpieza y éxito de mi tratamiento periodontal está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un tratamiento que cuente con algún tipo de garantía posterior. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_PERIODONCIA — CL / es-CL

- Título: Consentimiento informado de periodoncia
- Tipo: INFORMED_CONSENT
- Páginas fuente: [20]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 42
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['tapadura', 'garantía']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de periodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de periodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE PERIODONCIA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: El tratamiento periodontal consiste en la remoción del tártaro dental (sarro) adherido a la superficie del diente o los tejidos de soporte (periodonto). Se busca la eliminación de la infección, inflamación, sangrado y conservar la mayor cantidad de tejido óseo y dental. Esto se consigue mediante un destartraje supragingival, subgingival, pulido/alisado radicular y pulido coronario. Se puede realizar un tratamiento no quirúrgico (convencional) o quirúrgico. Por lo general se utilizan curetas y/o la aplicación de un scaler o ultrasonido que emite vibraciones para fragmentar los depósitos duros y eliminarlos mediante la irrigación a través de agua, adicional a esto se emplean antimicrobianos, antibióticos o medicamentos para ayudar a que el sistema elimine la infección. El ultrasonido NO daña el tejido dental ni tampoco es capaz de desalojar una obturación antigua (tapadura), si esto ocurriera significa que la obturación presentaba un daño previo o no se encontraba en buen estado desde el inicio, y perdió su correcta adhesión. Si se llega a desalojar alguna obturación, incrustación o corona, la responsabilidad NO es del dentista y el paciente deberá cubrir los gastos adicionales del tratamiento para solucionar el problema. Frecuentemente este procedimiento no es doloroso, pero el dolor es subjetivo por lo que a veces se podría sentir sensibilidad dental o molestias ya sea durante o posterior al tratamiento. La duración de la limpieza está directamente vinculada al cuidado diario e higiene personal del paciente, debiendo siempre volver a sus controles para mantener una buena salud oral. Se me ha explicado que posterior al tratamiento periodontal, la enfermedad se puede reagudizar presentando inflamación, aumento de volumen o nuevas infecciones, además mis dientes pueden quedar con movilidad o mayor grado de movilidad del que tenían ya que siempre estuvieron así, y estaban aparentemente firmes a causa de la infección y tártaro (sarro), debido a esto es posible que necesite exodoncias (extracciones) y elementos protésicos adicionales, los que no contempla el tratamiento periodontal, estos serán presupuestados y derivados al especialista. Comprendo que la evolución y recuperación de mi enfermedad no se puede predecir ya que depende en gran parte de mi sistema inmune y organismo. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que la duración de la limpieza y éxito de mi tratamiento periodontal está directamente vinculada al cuidado e higiene bucal personal, por lo tanto no es un tratamiento que cuente con algún tipo de garantía posterior. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_PROTESIS_FIJA — CO / es-CO

- Título: Consentimiento informado de rehabilitación oral prótesis fija
- Tipo: INFORMED_CONSENT
- Páginas fuente: [21]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 38
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de rehabilitación oral prótesis fija

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL PRÓTESIS FIJA PROCEDIMIENTO(S) _______________________________________________________________ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. La rehabilitación oral busca devolver dientes perdidos mediante el uso de elementos artificiales protésicos, dentro de las prótesis fijas se encuentran las endo-coronas, coronas (prótesis fija unitaria) o puentes (prótesis fija plural). Estas pueden ser realizadas con metal, metal-cerámicas o libres de metal, apoyándose de pernos metálicos intra-conducto o postes de fibra de vidrios, entre otros elementos. Durante el procedimiento o posterior a la instalación protésica fija, pueden ocurrir eventos inherentes al tratante los que son propios de la técnica en sí, tales como, fracturas de tejido dental, fracturas de paredes o piso del diente, fractura radicular, fractura coronaria, fractura de postes o pernos intra- conductos, desalojos de provisorios entre sesiones, caries futuras por mala higiene y dieta cariogénica, fractura coronaria de prótesis fija porcelana, cerámica o metal, inflamación de los tejidos blandos circundantes, infecciones, fatiga de material. Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del paciente, este deberá de pagar los costos adicionales que signifiquen corregir y mejorar el tratamiento. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica CLINICA SEIS, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica CLINICA SEIS para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_PROTESIS_FIJA — CL / es-CL

- Título: Consentimiento informado de rehabilitación oral prótesis fija
- Tipo: INFORMED_CONSENT
- Páginas fuente: [21]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 38
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de rehabilitación oral prótesis fija

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de rehabilitación oral prótesis fija

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL PRÓTESIS FIJA PROCEDIMIENTO(S) _______________________________________________________________ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. La rehabilitación oral busca devolver dientes perdidos mediante el uso de elementos artificiales protésicos, dentro de las prótesis fijas se encuentran las endo-coronas, coronas (prótesis fija unitaria) o puentes (prótesis fija plural). Estas pueden ser realizadas con metal, metal-cerámicas o libres de metal, apoyándose de pernos metálicos intra-conducto o postes de fibra de vidrios, entre otros elementos. Durante el procedimiento o posterior a la instalación protésica fija, pueden ocurrir eventos inherentes al tratante los que son propios de la técnica en sí, tales como, fracturas de tejido dental, fracturas de paredes o piso del diente, fractura radicular, fractura coronaria, fractura de postes o pernos intra- conductos, desalojos de provisorios entre sesiones, caries futuras por mala higiene y dieta cariogénica, fractura coronaria de prótesis fija porcelana, cerámica o metal, inflamación de los tejidos blandos circundantes, infecciones, fatiga de material. Dentro del periodo de garantía y en caso de fallas se realizará una evaluación con el especialista y director técnico para determinar la causa de lo ocurrido, en caso de ser responsabilidad del paciente, este deberá de pagar los costos adicionales que signifiquen corregir y mejorar el tratamiento. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica CLINICA SEIS, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica CLINICA SEIS para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_PROTESIS_REMOVIBLE — CO / es-CO

- Título: Consentimiento informado de rehabilitación oral prótesis removible
- Tipo: INFORMED_CONSENT
- Páginas fuente: [22, 23]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 80
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
prótesis 24 horas antes de su hora (todo el día), ideal dormir con ella sólo esa vez, de esta fo

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

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
Luego de una instalación protésica, si el paciente la utiliza por primera

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de rehabilitación oral prótesis removible

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE REHABILITACIÓN ORAL PRÓTESIS REMOVIBLE PROCEDIMIENTO(S) _______________________________________________________________ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. La rehabilitación oral busca devolver dientes perdidos mediante el uso de elementos artificiales protésicos, dentro de las prótesis removibles se encuentra la prótesis total, prótesis parcial de base acrílica, parcial de base metálica, prótesis valplast o termoplástica, prótesis inmediata/temporal o provisoria, entre otras. Una prótesis de base metálica presenta mejor resistencia y estabilidad que una de base acrílica, se afirma de los dientes (pilares) a través de retenedores (ganchos), por lo que se necesita un mínimo de tejido óseo (hueso) y dientes para su confección, los dientes móviles o con enfermedad periodontal no son buenos pilares para sostener elementos protésicos. Las prótesis acrílicas tienen más acrílico y se usan cuando no hay muchos dientes, por lo que su soporte esta dado más que nada en su relación con la cantidad de hueso. El paladar es un soporte primario, por lo que en general se utiliza como soporte y el evitarlo hace que la prótesis pueda no quedar bien diseñada, presentando molestias. Existe una baja cantidad de pacientes que, a pesar del buen diseño y fabricación de una prótesis, siguiendo los pasos al pie de la letra en su fabricación, preservando correctamente los tejidos e instalándola como corresponde, el paciente no la soportará y la rechazará por temas de confort y comodidad, esto es ajeno al trabajo del odontólogo, por lo que no existirá devolución de dinero y la opción más recomendada será implantología. Para la fabricación de una prótesis, al menos se necesitan 4 sesiones o más, cada sesión con diferencia de 7 a 10 días. Por lo que no es un procedimiento rápido. La rapidez del odontólogo está en estrecha relación al trabajo externo y envío de los laboratorios, lo que no es responsabilidad directa del odontólogo o clínica {{company.name}} Si el paciente necesita extracciones previas a su prótesis removible, esto aumentara el tiempo de espera, ya que el hueso se demora en cicatrizar 3 meses, por lo que se podría, según evaluación del clínico, comenzar con las primeras etapas e impresiones para la prótesis después de 4-6 semanas de las extracciones, el tiempo aumenta en pacientes con cicatrización lenta o enfermedades no controladas. Mientras cicatriza el tejido óseo, es posible utilizar prótesis temporal, provisoria e inmediata, las que se instalan al mismo momento de la extracción dental, entendiendo que, son prótesis diseñadas solo como emergencia y con uso limitado, las que deberán ser ajustadas constantemente hasta que cicatrice el tejido óseo (hueso) y se pueda comenzar con la etapa de una prótesis definitiva. Una prótesis inmediata o provisoria y una prótesis definitiva son procedimientos independientes por lo que el paciente debe pagar cada prótesis independientemente. La prótesis inmediata/temporal NO reemplaza una prótesis definitiva. Durante el procedimiento o posterior a la instalación protésica removible, pueden ocurrir eventos inherentes al tratante los que son propios de la técnica en sí o su uso, tales como, fracturas de tejido

dental (piezas pilares), fracturas de paredes o piso del diente, fractura radicular, fractura coronaria, fractura de ganchos metálicos, caries futuras por mala higiene y dieta cariogénica, fractura coronaria de prótesis fija donde se engancha el retenedor (alambre que afirma la prótesis), inflamación de los tejidos blandos circundantes, infecciones, dolor, incomodidad, fatiga de material, fractura de prótesis o dientes artificiales, desalojo de dientes protésicos. Luego de una instalación protésica, si el paciente la utiliza por primera vez, es normal sentir incomodidad o cambios en la forma de comer o hablar, por lo que se recomienda practi

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_PROTESIS_REMOVIBLE — CL / es-CL

- Título: Consentimiento informado de rehabilitación oral prótesis removible
- Tipo: INFORMED_CONSENT
- Páginas fuente: [22, 23]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 80
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
prótesis 24 horas antes de su hora (todo el día), ideal dormir con ella sólo esa vez, de esta fo

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

```markdown
# Consentimiento informado de rehabilitación oral prótesis removible

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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
Luego de una instalación protésica, si el paciente la utiliza por primera ve

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de rehabilitación oral prótesis removible

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE REHABILITACIÓN ORAL PRÓTESIS REMOVIBLE PROCEDIMIENTO(S) _______________________________________________________________ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. La rehabilitación oral busca devolver dientes perdidos mediante el uso de elementos artificiales protésicos, dentro de las prótesis removibles se encuentra la prótesis total, prótesis parcial de base acrílica, parcial de base metálica, prótesis valplast o termoplástica, prótesis inmediata/temporal o provisoria, entre otras. Una prótesis de base metálica presenta mejor resistencia y estabilidad que una de base acrílica, se afirma de los dientes (pilares) a través de retenedores (ganchos), por lo que se necesita un mínimo de tejido óseo (hueso) y dientes para su confección, los dientes móviles o con enfermedad periodontal no son buenos pilares para sostener elementos protésicos. Las prótesis acrílicas tienen más acrílico y se usan cuando no hay muchos dientes, por lo que su soporte esta dado más que nada en su relación con la cantidad de hueso. El paladar es un soporte primario, por lo que en general se utiliza como soporte y el evitarlo hace que la prótesis pueda no quedar bien diseñada, presentando molestias. Existe una baja cantidad de pacientes que, a pesar del buen diseño y fabricación de una prótesis, siguiendo los pasos al pie de la letra en su fabricación, preservando correctamente los tejidos e instalándola como corresponde, el paciente no la soportará y la rechazará por temas de confort y comodidad, esto es ajeno al trabajo del odontólogo, por lo que no existirá devolución de dinero y la opción más recomendada será implantología. Para la fabricación de una prótesis, al menos se necesitan 4 sesiones o más, cada sesión con diferencia de 7 a 10 días. Por lo que no es un procedimiento rápido. La rapidez del odontólogo está en estrecha relación al trabajo externo y envío de los laboratorios, lo que no es responsabilidad directa del odontólogo o clínica {{company.name}} Si el paciente necesita extracciones previas a su prótesis removible, esto aumentara el tiempo de espera, ya que el hueso se demora en cicatrizar 3 meses, por lo que se podría, según evaluación del clínico, comenzar con las primeras etapas e impresiones para la prótesis después de 4-6 semanas de las extracciones, el tiempo aumenta en pacientes con cicatrización lenta o enfermedades no controladas. Mientras cicatriza el tejido óseo, es posible utilizar prótesis temporal, provisoria e inmediata, las que se instalan al mismo momento de la extracción dental, entendiendo que, son prótesis diseñadas solo como emergencia y con uso limitado, las que deberán ser ajustadas constantemente hasta que cicatrice el tejido óseo (hueso) y se pueda comenzar con la etapa de una prótesis definitiva. Una prótesis inmediata o provisoria y una prótesis definitiva son procedimientos independientes por lo que el paciente debe pagar cada prótesis independientemente. La prótesis inmediata/temporal NO reemplaza una prótesis definitiva. Durante el procedimiento o posterior a la instalación protésica removible, pueden ocurrir eventos inherentes al tratante los que son propios de la técnica en sí o su uso, tales como, fracturas de tejido

dental (piezas pilares), fracturas de paredes o piso del diente, fractura radicular, fractura coronaria, fractura de ganchos metálicos, caries futuras por mala higiene y dieta cariogénica, fractura coronaria de prótesis fija donde se engancha el retenedor (alambre que afirma la prótesis), inflamación de los tejidos blandos circundantes, infecciones, dolor, incomodidad, fatiga de material, fractura de prótesis o dientes artificiales, desalojo de dientes protésicos. Luego de una instalación protésica, si el paciente la utiliza por primera vez, es normal sentir incomodidad o cambios en la forma de comer o hablar, por lo que se recomienda practicar

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_REHAB_IMPLANTES — CO / es-CO

- Título: Consentimiento informado de rehabilitación oral sobre implantes
- Tipo: INFORMED_CONSENT
- Páginas fuente: [24, 25]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 72
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
“desmontar, mantener y limpieza”, la que sólo puede realizar el odo

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

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
generar inflamaci

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de rehabilitación oral sobre implantes

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL SOBRE IMPLANTES PROCEDIMIENTO(S) _______________________________________________________________ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. La rehabilitación oral sobre implantes busca devolver dientes perdidos mediante el uso de elementos artificiales protésicos que se anclan a través de tornillos o se cementan en los implantes de titanio integrados al hueso. Dentro de las prótesis sobre implantes, se encuentran; coronas unitarias o plurales sobre implantes (cementadas o atornilladas), sobredentaduras (removibles sobre implantes), prótesis hibridas (fijas) atornilladas sobre implantes. Para la fabricación de una corona o prótesis sobre implantes, al menos se necesitan 4 sesiones o más, cada sesión con diferencia de 7 a 10 días. Por lo que no es un procedimiento rápido. La rapidez del odontólogo está en estrecha relación al stock de insumos (empresa externa de implantes), avances de los laboratorios (externos) y envíos por empresas de transporte nacional (Chilexpress o correos), situaciones que no son responsabilidad directa del odontólogo o clínica {{company.name}}. Posterior a la cirugía el implante puede quedar con una inclinación no favorable e imposible de predecir por lo que se necesitará otro tipo de sistema de pernos lo que me podría llevar a tener que pagar un costo adicional a lo ya presupuestado, de la misma forma algún diente provisional extra o cualquier acción necesaria que favorezca el resultado final del tratamiento. Si el paciente necesita extracciones previas a su tratamiento final, esto aumentará el tiempo de espera, ya que el hueso se demora en cicatrizar 3 meses, será criterio del especialista cuando avanzar con las siguientes etapas, el tiempo aumenta en pacientes con cicatrización lenta o enfermedades no controladas. Mientras cicatriza el tejido óseo, es posible utilizar prótesis temporal, provisoria e inmediata, las que se instalan en el mismo momento de la extracción dental o aplicación de injertos, entendiendo que, son prótesis diseñadas sólo como emergencia y con uso limitado, las que deberán ser ajustadas constantemente hasta que cicatrice el tejido óseo (hueso) y se pueda comenzar con la etapa de una prótesis definitiva. Una prótesis inmediata o provisoria y una prótesis definitiva son procedimientos distintos por lo que el paciente debe pagar cada prótesis independientemente. La prótesis inmediata/ temporal NO reemplaza una prótesis definitiva sobre implantes. Durante el procedimiento o posterior a la instalación de la rehabilitación sobre implantes, pueden ocurrir eventos inherentes al odontólogo los que son propios de la técnica en sí o por su uso, tales como, des-osteointegración de implantes (no se integró correctamente), desalojo de dientes protésicos, fractura coronaria de la cerámica sobre implantes, fractura o desalojo de los tornillos y aditamentos de implantología, fractura parcial o total de prótesis hibridas o sobredentaduras, inflamación, dolor o molestias, incomodidad.

Luego de una instalación protésica removible, si el paciente la utiliza por primera vez, es normal sentir incomodidad o cambios en la forma de comer o hablar, por lo que se recomienda practicar en casa, leyendo en voz alta 10 minutos al día, comer cosas livianas y acostumbrarse a ellas. Si presenta dolor, inflamación, ulceras o erosiones, debe suspender su uso, agendar una visita al especialista y utilizar la prótesis 24 horas antes de su hora (todo el día), ideal dormir con ella sólo esa vez, de esta forma se marcarán las zonas de sobre compresión para realizar desgastes precisos sobre la prótesis, eliminando las molestias. Recuerde que NO debe dormir con la prótesis removible sobre implantes (NUNCA), ya que puede generar inflamaciones, los tejidos no descansan y proliferan hongos. Es frecuente la estomatitis sub- protésica por el mal d

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_REHAB_IMPLANTES — CL / es-CL

- Título: Consentimiento informado de rehabilitación oral sobre implantes
- Tipo: INFORMED_CONSENT
- Páginas fuente: [24, 25]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 72
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantía', 'garantías', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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
“desmontar, mantener y limpieza”, la que sólo puede realizar el odo

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v1

```markdown
# Consentimiento informado de rehabilitación oral sobre implantes

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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
generar inflamacione

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de rehabilitación oral sobre implantes

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE REHABILITACIÓN ORAL SOBRE IMPLANTES PROCEDIMIENTO(S) _______________________________________________________________ El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. La rehabilitación oral sobre implantes busca devolver dientes perdidos mediante el uso de elementos artificiales protésicos que se anclan a través de tornillos o se cementan en los implantes de titanio integrados al hueso. Dentro de las prótesis sobre implantes, se encuentran; coronas unitarias o plurales sobre implantes (cementadas o atornilladas), sobredentaduras (removibles sobre implantes), prótesis hibridas (fijas) atornilladas sobre implantes. Para la fabricación de una corona o prótesis sobre implantes, al menos se necesitan 4 sesiones o más, cada sesión con diferencia de 7 a 10 días. Por lo que no es un procedimiento rápido. La rapidez del odontólogo está en estrecha relación al stock de insumos (empresa externa de implantes), avances de los laboratorios (externos) y envíos por empresas de transporte nacional (Chilexpress o correos), situaciones que no son responsabilidad directa del odontólogo o clínica {{company.name}}. Posterior a la cirugía el implante puede quedar con una inclinación no favorable e imposible de predecir por lo que se necesitará otro tipo de sistema de pernos lo que me podría llevar a tener que pagar un costo adicional a lo ya presupuestado, de la misma forma algún diente provisional extra o cualquier acción necesaria que favorezca el resultado final del tratamiento. Si el paciente necesita extracciones previas a su tratamiento final, esto aumentará el tiempo de espera, ya que el hueso se demora en cicatrizar 3 meses, será criterio del especialista cuando avanzar con las siguientes etapas, el tiempo aumenta en pacientes con cicatrización lenta o enfermedades no controladas. Mientras cicatriza el tejido óseo, es posible utilizar prótesis temporal, provisoria e inmediata, las que se instalan en el mismo momento de la extracción dental o aplicación de injertos, entendiendo que, son prótesis diseñadas sólo como emergencia y con uso limitado, las que deberán ser ajustadas constantemente hasta que cicatrice el tejido óseo (hueso) y se pueda comenzar con la etapa de una prótesis definitiva. Una prótesis inmediata o provisoria y una prótesis definitiva son procedimientos distintos por lo que el paciente debe pagar cada prótesis independientemente. La prótesis inmediata/ temporal NO reemplaza una prótesis definitiva sobre implantes. Durante el procedimiento o posterior a la instalación de la rehabilitación sobre implantes, pueden ocurrir eventos inherentes al odontólogo los que son propios de la técnica en sí o por su uso, tales como, des-osteointegración de implantes (no se integró correctamente), desalojo de dientes protésicos, fractura coronaria de la cerámica sobre implantes, fractura o desalojo de los tornillos y aditamentos de implantología, fractura parcial o total de prótesis hibridas o sobredentaduras, inflamación, dolor o molestias, incomodidad.

Luego de una instalación protésica removible, si el paciente la utiliza por primera vez, es normal sentir incomodidad o cambios en la forma de comer o hablar, por lo que se recomienda practicar en casa, leyendo en voz alta 10 minutos al día, comer cosas livianas y acostumbrarse a ellas. Si presenta dolor, inflamación, ulceras o erosiones, debe suspender su uso, agendar una visita al especialista y utilizar la prótesis 24 horas antes de su hora (todo el día), ideal dormir con ella sólo esa vez, de esta forma se marcarán las zonas de sobre compresión para realizar desgastes precisos sobre la prótesis, eliminando las molestias. Recuerde que NO debe dormir con la prótesis removible sobre implantes (NUNCA), ya que puede generar inflamaciones, los tejidos no descansan y proliferan hongos. Es frecuente la estomatitis sub- protésica por el mal dise

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

## CONS_APROBACION_ESTETICA — CO / es-CO

- Título: Aprobación estética de rehabilitación oral
- Tipo: AESTHETIC_APPROVAL
- Páginas fuente: [26]
- Estado: **BLOCKED**
- Compatibilidad firmante: `FUTURE_WORKFLOW`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 6
- Párrafos unidos: 28
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:AESTHETIC_APPROVAL', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Aprobación estética de rehabilitación oral

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE REHABILITACION ORAL APROBACIÓN ESTÉTICA E N R E L A C I O N A L PROCEDIMIENTO: El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Acepto y apruebo en color, forma, tamaño, posición y diseño mi tratamiento protésico fijo y/o removible por lo que autorizo a terminar definitivamente este proceso. Consiento enviar a terminar el trabajo al laboratorio y me encuentro conforme con el resultado estético final. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_APROBACION_ESTETICA — CL / es-CL

- Título: Aprobación estética de rehabilitación oral
- Tipo: AESTHETIC_APPROVAL
- Páginas fuente: [26]
- Estado: **BLOCKED**
- Compatibilidad firmante: `FUTURE_WORKFLOW`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 6
- Párrafos unidos: 28
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:AESTHETIC_APPROVAL', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Aprobación estética de rehabilitación oral

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Aprobación estética de rehabilitación oral

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE REHABILITACION ORAL APROBACIÓN ESTÉTICA E N R E L A C I O N A L PROCEDIMIENTO: El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Acepto y apruebo en color, forma, tamaño, posición y diseño mi tratamiento protésico fijo y/o removible por lo que autorizo a terminar definitivamente este proceso. Consiento enviar a terminar el trabajo al laboratorio y me encuentro conforme con el resultado estético final. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_URGENCIA — CO / es-CO

- Título: Consentimiento informado de urgencia odontológica
- Tipo: INFORMED_CONSENT
- Páginas fuente: [27]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 33
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de urgencia odontológica

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE URGENCIA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Asisto por urgencia odontológica y luego de una evaluación clínica complementada con imágenes r a d i o g r á fi c a s t e n g o c o m o p o s i b l e diagnóstico_________________________________________________________ Y p a r a s o l u c i o n a r m i u r g e n c i a a c e p t o e l t r a t a m i e n t o d e _______________________________________________. Comprendo que el tratamiento de urgencia no es definitivo solo ayuda a disminuir temporalmente la infección, cuadro clínico o dolor por lo que luego, deberé realizar un diagnóstico integral y ser derivado a la especialidad correspondiente quien me entregará el tratamiento definitivo. Existe la posibilidad que la urgencia dental sobrepase la capacidad de resolución del centro dental debiendo ser derivado a nivel hospitalario o establecimientos de alta complejidad. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes de realizarlo.

```

## CONS_URGENCIA — CL / es-CL

- Título: Consentimiento informado de urgencia odontológica
- Tipo: INFORMED_CONSENT
- Páginas fuente: [27]
- Estado: **BLOCKED**
- Compatibilidad firmante: `ADULT_OR_REPRESENTATIVE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 33
- Frases de representante: ['paciente o tutor legal']
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:ADULT_OR_REPRESENTATIVE', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de urgencia odontológica

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de urgencia odontológica

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO DE URGENCIA El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Asisto por urgencia odontológica y luego de una evaluación clínica complementada con imágenes r a d i o g r á fi c a s t e n g o c o m o p o s i b l e diagnóstico_________________________________________________________ Y p a r a s o l u c i o n a r m i u r g e n c i a a c e p t o e l t r a t a m i e n t o d e _______________________________________________. Comprendo que el tratamiento de urgencia no es definitivo solo ayuda a disminuir temporalmente la infección, cuadro clínico o dolor por lo que luego, deberé realizar un diagnóstico integral y ser derivado a la especialidad correspondiente quien me entregará el tratamiento definitivo. Existe la posibilidad que la urgencia dental sobrepase la capacidad de resolución del centro dental debiendo ser derivado a nivel hospitalario o establecimientos de alta complejidad. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes de realizarlo.

```

## CONS_OXIDO_NITROSO — CO / es-CO

- Título: Consentimiento informado de óxido nitroso
- Tipo: INFORMED_CONSENT
- Páginas fuente: [28, 29]
- Estado: **BLOCKED**
- Compatibilidad firmante: `REPRESENTATIVE_REQUIRED`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 55
- Frases de representante: ['tutor legal', 'LACTANTES', 'paciente o tutor legal']
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:REPRESENTATIVE_REQUIRED', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

Profesional: {{profes

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de óxido nitroso

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE ÓXIDO NITROSO Yo ________________________________, RUT: _____________________ como paciente o en calidad de tutor legal del paciente __________________________________, El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos, óxido nitroso y del procedimiento a realizar, entendiendo que: El nivel de sedación es mínimo a moderado de tipo inhalatoria intranasal con óxido nitroso/oxígeno, respecto al óxido nitroso, entiendo y acepto que: • En ocasiones proporciona relajación y/o risa. • Seré sometido al uso de óxido nitroso por un especialista calificado y certificado. • Estaré despierto y completamente consciente de mi entorno. • Seré capaz de responder a preguntas y seguir instrucciones de mi tratante. • El O. Nitroso tiene contraindicaciones y no debo estar resfriado ni enfermo, tampoco mis vías respiratorias deben estar infectadas con algún patógeno ni recientemente debo haberme realizado una cirugía del oído medio. • El O.N se utiliza en pacientes para el control del dolor, ansiedad, miedo o paciente con necesidades especiales. Las posibles complicaciones por el uso de óxido nitroso son las siguientes • Náuseas y vómitos, siendo la complicación más usual, pero de baja frecuencia. Por esto siendo ADULTO, NO debo comer 8 horas antes del procedimiento alimentos grasos, 6 horas alimentos sólidos ni ingerir líquidos 2 horas antes y para los LACTANTES, seguir un ayuno de 4 horas para sólidos y 2 horas para líquidos. Recordar que la leche se considera dentro del ítem de alimento sólido. • Hormigueo en dedos, mejilla, labios, lengua, cuello, hombros y/o cabeza, siendo pasajero • Calor, rubor o enrojecimiento, siendo un efecto pasajero y temporal • Sensación de estar “fuera del cuerpo”, flotando, ido o volando, siendo un efecto pasajero. • Sentir lentitud al hablar o movilizar alguna estructura del cuerpo, siendo momentáneo. • Al terminar el procedimiento o en su fase final, posibles temblores o movimientos involuntarios, los que son completamente transitorios y una vez recuperado se detienen. Es posible que la sensación que me produzca el uso de óxido nitroso sea desagradable y estimule mi actividad y función motora, lo que puede llevar a suspender la atención y procedimiento por parte de mi profesional tratante o mía. En algunos casos inclusive, se puede complementar con alguna otra

técnica de sedación o control de estímulos para llevar a cabo la intervención, lo que me será explicado previamente a mi o a mi tutor legal. Aunque el uso del óxido nitroso se considera una práctica segura y eficaz, siempre debo informar en caso de estar embarazada al personal de salud para recibir el tratamiento indicado. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes de realizarlo. Firma _____________________ CURICÓ ___ de _______del _____

```

## CONS_OXIDO_NITROSO — CL / es-CL

- Título: Consentimiento informado de óxido nitroso
- Tipo: INFORMED_CONSENT
- Páginas fuente: [28, 29]
- Estado: **BLOCKED**
- Compatibilidad firmante: `REPRESENTATIVE_REQUIRED`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 5
- Párrafos unidos: 55
- Frases de representante: ['tutor legal', 'LACTANTES', 'paciente o tutor legal']
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['incompatible_signer_for_current_adult_self_flow:REPRESENTATIVE_REQUIRED', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de óxido nitroso

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

Profesional: {{professio

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Consentimiento informado de óxido nitroso

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE ÓXIDO NITROSO Yo ________________________________, RUT: _____________________ como paciente o en calidad de tutor legal del paciente __________________________________, El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos, óxido nitroso y del procedimiento a realizar, entendiendo que: El nivel de sedación es mínimo a moderado de tipo inhalatoria intranasal con óxido nitroso/oxígeno, respecto al óxido nitroso, entiendo y acepto que: • En ocasiones proporciona relajación y/o risa. • Seré sometido al uso de óxido nitroso por un especialista calificado y certificado. • Estaré despierto y completamente consciente de mi entorno. • Seré capaz de responder a preguntas y seguir instrucciones de mi tratante. • El O. Nitroso tiene contraindicaciones y no debo estar resfriado ni enfermo, tampoco mis vías respiratorias deben estar infectadas con algún patógeno ni recientemente debo haberme realizado una cirugía del oído medio. • El O.N se utiliza en pacientes para el control del dolor, ansiedad, miedo o paciente con necesidades especiales. Las posibles complicaciones por el uso de óxido nitroso son las siguientes • Náuseas y vómitos, siendo la complicación más usual, pero de baja frecuencia. Por esto siendo ADULTO, NO debo comer 8 horas antes del procedimiento alimentos grasos, 6 horas alimentos sólidos ni ingerir líquidos 2 horas antes y para los LACTANTES, seguir un ayuno de 4 horas para sólidos y 2 horas para líquidos. Recordar que la leche se considera dentro del ítem de alimento sólido. • Hormigueo en dedos, mejilla, labios, lengua, cuello, hombros y/o cabeza, siendo pasajero • Calor, rubor o enrojecimiento, siendo un efecto pasajero y temporal • Sensación de estar “fuera del cuerpo”, flotando, ido o volando, siendo un efecto pasajero. • Sentir lentitud al hablar o movilizar alguna estructura del cuerpo, siendo momentáneo. • Al terminar el procedimiento o en su fase final, posibles temblores o movimientos involuntarios, los que son completamente transitorios y una vez recuperado se detienen. Es posible que la sensación que me produzca el uso de óxido nitroso sea desagradable y estimule mi actividad y función motora, lo que puede llevar a suspender la atención y procedimiento por parte de mi profesional tratante o mía. En algunos casos inclusive, se puede complementar con alguna otra

técnica de sedación o control de estímulos para llevar a cabo la intervención, lo que me será explicado previamente a mi o a mi tutor legal. Aunque el uso del óxido nitroso se considera una práctica segura y eficaz, siempre debo informar en caso de estar embarazada al personal de salud para recibir el tratamiento indicado. Entiendo como paciente o tutor legal que debo seguir las indicaciones de mi tratante, siendo responsable con las indicaciones y prescripción de fármacos, asistiendo a controles y preguntado nuevas dudas que pueda tener. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregara un presupuesto debidamente antes de realizarlo. Firma _____________________ CURICÓ ___ de _______del _____

```

## CONS_PLANO_RELAJACION — CO / es-CO

- Título: Consentimiento informado de plano de relajación y estabilización
- Tipo: INFORMED_CONSENT
- Páginas fuente: [30]
- Estado: **NEEDS_REVIEW**
- Compatibilidad firmante: `ADULT_SELF`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 33
- Frases de representante: No detectadas
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Consentimiento informado de plano de relajación y estabilización

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE PLANO DE RELAJACION Y ESTABILIZACIÓN El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. El plano de relajación o estabilización oclusal consiste en un dispositivo interoclusal de acrílico que cubre los dientes para protegerlos de desgastes excesivos no funcionales. El plano NO resuelve por sí solo el bruxismo ya que se necesita un enfoque multidisciplinario y otros tratamientos. El plano se debe utilizar durante la noche mientras se duerme y en ocasiones durante el día (según corresponda), en caso de molestias se debe asistir con el odontólogo tratante para modificar y ajustar el plano de relajación. Debo seguir las indicaciones de mi tratante en cuanto al tiempo y forma de uso. Es normal y transitorio sentir salivación excesiva o incomodidad los primeros días. Cada día se debe higienizar el plano utilizando agua de la llave y un cepillo duro (EXCLUSIVO PARA EL PLANO), además en el comercio venden pastillas efervescentes para limpiar estos elementos protésicos. Me comprometo a remover el plano de mi boca utilizando ambas manos y guardándolo adecuadamente para evitar su pérdida o fractura y debo asistir a los controles que mi odontólogo indique. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_PLANO_RELAJACION — CL / es-CL

- Título: Consentimiento informado de plano de relajación y estabilización
- Tipo: INFORMED_CONSENT
- Páginas fuente: [30]
- Estado: **NEEDS_REVIEW**
- Compatibilidad firmante: `ADULT_SELF`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 33
- Frases de representante: No detectadas
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Consentimiento informado de plano de relajación y estabilización

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Consentimiento informado de plano de relajación y estabilización

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE PLANO DE RELAJACION Y ESTABILIZACIÓN El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. El plano de relajación o estabilización oclusal consiste en un dispositivo interoclusal de acrílico que cubre los dientes para protegerlos de desgastes excesivos no funcionales. El plano NO resuelve por sí solo el bruxismo ya que se necesita un enfoque multidisciplinario y otros tratamientos. El plano se debe utilizar durante la noche mientras se duerme y en ocasiones durante el día (según corresponda), en caso de molestias se debe asistir con el odontólogo tratante para modificar y ajustar el plano de relajación. Debo seguir las indicaciones de mi tratante en cuanto al tiempo y forma de uso. Es normal y transitorio sentir salivación excesiva o incomodidad los primeros días. Cada día se debe higienizar el plano utilizando agua de la llave y un cepillo duro (EXCLUSIVO PARA EL PLANO), además en el comercio venden pastillas efervescentes para limpiar estos elementos protésicos. Me comprometo a remover el plano de mi boca utilizando ambas manos y guardándolo adecuadamente para evitar su pérdida o fractura y debo asistir a los controles que mi odontólogo indique. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_RETIRO_ORTODONCIA — CO / es-CO

- Título: Retiro anticipado de ortodoncia y paciente externo
- Tipo: TREATMENT_TERMINATION_ACKNOWLEDGEMENT
- Páginas fuente: [31]
- Estado: **BLOCKED**
- Compatibilidad firmante: `FUTURE_WORKFLOW`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 32
- Frases de representante: No detectadas
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:TREATMENT_TERMINATION_ACKNOWLEDGEMENT', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Retiro anticipado de ortodoncia y paciente externo

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE RETIRO ORTODONCIA ANTICIPADO Y PACIENTE EXTERNO El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Por diferentes motivos personales y voluntariamente indico mi deseo de terminar el tratamiento de ortodoncia anticipadamente, comprendo plenamente los riesgos de terminar voluntariamente el proceso antes de tiempo y las consecuencias que pueda traer en el futuro, el odontólogo me ha explicado y resuelto todas mis dudas e inquietudes por lo que libero de toda responsabilidad al profesional y a la clínica dental, entendiendo que, no voy a completar el tratamiento como corresponde. Siendo un paciente de clínica externa, donde instalé y realicé mi tratamiento en otra clínica ajena a CLINICA SEIS. Decido por motivos personales no seguir con el tratamiento y voluntariamente darle término anticipado, liberando de toda responsabilidad al personal, a la doctora que retirara mi ortodoncia y clínica {{company.name}} ya que esta es MI decisión completamente voluntaria. Reitero que acepto las condiciones y consecuencias de la decisión que he tomado. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## CONS_RETIRO_ORTODONCIA — CL / es-CL

- Título: Retiro anticipado de ortodoncia y paciente externo
- Tipo: TREATMENT_TERMINATION_ACKNOWLEDGEMENT
- Páginas fuente: [31]
- Estado: **BLOCKED**
- Compatibilidad firmante: `FUTURE_WORKFLOW`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 5
- Párrafos unidos: 32
- Frases de representante: No detectadas
- Términos locales: ['garantías', 'garantía', 'contraloría']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:TREATMENT_TERMINATION_ACKNOWLEDGEMENT', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Retiro anticipado de ortodoncia y paciente externo

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Retiro anticipado de ortodoncia y paciente externo

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

CONSENTIMIENTO INFORMADO DE RETIRO ORTODONCIA ANTICIPADO Y PACIENTE EXTERNO El odontólogo tratante ha resuelto mis dudas e inquietudes, me ha explicado las ventajas, riesgos y complicaciones del uso de fármacos, anestésicos y del procedimiento a realizar, entendiendo que: He entregado información real, fidedigna y veraz en cuanto a mi historial clínico, enfermedades sistémicas, hábitos y consumo de alcohol o drogas. Por diferentes motivos personales y voluntariamente indico mi deseo de terminar el tratamiento de ortodoncia anticipadamente, comprendo plenamente los riesgos de terminar voluntariamente el proceso antes de tiempo y las consecuencias que pueda traer en el futuro, el odontólogo me ha explicado y resuelto todas mis dudas e inquietudes por lo que libero de toda responsabilidad al profesional y a la clínica dental, entendiendo que, no voy a completar el tratamiento como corresponde. Siendo un paciente de clínica externa, donde instalé y realicé mi tratamiento en otra clínica ajena a CLINICA SEIS. Decido por motivos personales no seguir con el tratamiento y voluntariamente darle término anticipado, liberando de toda responsabilidad al personal, a la doctora que retirara mi ortodoncia y clínica {{company.name}} ya que esta es MI decisión completamente voluntaria. Reitero que acepto las condiciones y consecuencias de la decisión que he tomado. Comprendo que tengo garantías por los tratamientos realizados en clínica {{company.name}}, los que perderé si frente a cualquier urgencia sobre dicho tratamiento consulto primero en otro centro dental e intervienen en mi tratamiento. Deberé consultar primero en clínica {{company.name}} para hacer valer mi garantía como paciente, por lo que pasaré por una contraloría dirigida a cargo del director de la clínica en caso de ser necesario. En caso contrario si consulto primero en otro prestador de salud perderé mis garantías sobre el tratamiento y no existirá devolución de dinero. Doy mi consentimiento para realizar el o los procedimientos indicados por el odontólogo, entendiendo la posibilidad de ser derivado a otro especialista para complementar mi tratamiento correctamente, asumiendo los costos que signifiquen por lo cual se me entregará un presupuesto debidamente antes de realizarlo.

```

## IND_CIRUGIA — CO / es-CO

- Título: Indicaciones de cirugía
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [32]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 26
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de cirugía

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES CIRUGÍA • Morder gasa por 45 minutos, luego remover con delicadeza y desecharla. • En caso de hemorragia o sangrado espontáneo poner nueva gasa en la zona afectada. • No escupir, no enjuagarse con ningún enjuague bucal o líquido. • No comer mientras dure el efecto de la anestesia. • Dieta blanda y fría las primeras 48 horas, luego aumentar de a poco la consistencia y temperatura de alimentos. • Comer o masticar por el lado contrario a la cirugía. • Estornudar o toser con la boca abierta. • No aspirar, no succionar, no utilizar bombillas o popotes. • No fumar por 7 días. • No hacer deportes por 7 días. • Reposo relativo por 3 días. • Dormir semi sentado, la cabeza debe estar por sobre los pies. • Cepillado normal, pero sin tocar el área afectada, para enjuagarse mueva la cabeza y para escupir sólo abra la boca y permita que el líquido caiga por sí solo. NO escupir y NO enjuagarse. • Hielo local no directo. Cubra con un paño el hielo y aplique en la zona afectada. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial.

```

## IND_CIRUGIA — CL / es-CL

- Título: Indicaciones de cirugía
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [32]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 26
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de cirugía

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de cirugía

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES CIRUGÍA • Morder gasa por 45 minutos, luego remover con delicadeza y desecharla. • En caso de hemorragia o sangrado espontáneo poner nueva gasa en la zona afectada. • No escupir, no enjuagarse con ningún enjuague bucal o líquido. • No comer mientras dure el efecto de la anestesia. • Dieta blanda y fría las primeras 48 horas, luego aumentar de a poco la consistencia y temperatura de alimentos. • Comer o masticar por el lado contrario a la cirugía. • Estornudar o toser con la boca abierta. • No aspirar, no succionar, no utilizar bombillas o popotes. • No fumar por 7 días. • No hacer deportes por 7 días. • Reposo relativo por 3 días. • Dormir semi sentado, la cabeza debe estar por sobre los pies. • Cepillado normal, pero sin tocar el área afectada, para enjuagarse mueva la cabeza y para escupir sólo abra la boca y permita que el líquido caiga por sí solo. NO escupir y NO enjuagarse. • Hielo local no directo. Cubra con un paño el hielo y aplique en la zona afectada. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial.

```

## IND_CIRUGIA_IMPLANTES — CO / es-CO

- Título: Indicaciones de cirugía de implantes
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [33]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 26
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de cirugía de implantes

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES CIRUGÍA DE IMPLANTES Reposo absoluto el primer y segundo día. Reposo relativo los días siguientes, mientras haya malestar. No agacharse, no hacer fuerzas, permanecer sentado o semisentado, incluso en las dos primeras noches. Suspender actividades deportivas si las realiza por 1 semana al menos. Alimentación blanda: comidas picadas o molidas. Evitar alimentos que dejen residuos, y los que fermentan, como masas y azúcares. No fumar por al menos una semana. Higiene cuidadosa. Cepillar cuidadosamente las áreas dentadas no involucradas en la cirugía. La herida y los puntos, limpiarla con un algodón empapado en un colutorio con clorhexidina 0.12%, como Perioaid u Oralgene. En el caso de haberse indicado antibióticos, mantener rigurosamente su dosis y frecuencia por los días indicados. No puede suspenderse sin consulta. Los analgésicos y anti-inflamatorios prescritos pueden espaciarse en la medida que las molestias vayan disminuyendo, hasta suprimirse totalmente. Durante el primer y segundo día, aplicar hielo (NUNCA DIRECTO) en una bolsa sobre la parte de la cara operada, en intervalos de 10 minutos por 10 minutos. Asistir al control y retiro de sutura a los 14 días. Avisar al cirujano Dr.(a) de presentar hemorragias severas u otras anomalías que pudieran sugerir complicaciones, asistir a la clínica. Si tiene hematoma es normal y puede demorar unos 10 a 15 días en remitir. Comprendo que debo seguir las siguientes indicaciones entregadas por mi odontólogo tratante:

```

## IND_CIRUGIA_IMPLANTES — CL / es-CL

- Título: Indicaciones de cirugía de implantes
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [33]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 26
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de cirugía de implantes

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de cirugía de implantes

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES CIRUGÍA DE IMPLANTES Reposo absoluto el primer y segundo día. Reposo relativo los días siguientes, mientras haya malestar. No agacharse, no hacer fuerzas, permanecer sentado o semisentado, incluso en las dos primeras noches. Suspender actividades deportivas si las realiza por 1 semana al menos. Alimentación blanda: comidas picadas o molidas. Evitar alimentos que dejen residuos, y los que fermentan, como masas y azúcares. No fumar por al menos una semana. Higiene cuidadosa. Cepillar cuidadosamente las áreas dentadas no involucradas en la cirugía. La herida y los puntos, limpiarla con un algodón empapado en un colutorio con clorhexidina 0.12%, como Perioaid u Oralgene. En el caso de haberse indicado antibióticos, mantener rigurosamente su dosis y frecuencia por los días indicados. No puede suspenderse sin consulta. Los analgésicos y anti-inflamatorios prescritos pueden espaciarse en la medida que las molestias vayan disminuyendo, hasta suprimirse totalmente. Durante el primer y segundo día, aplicar hielo (NUNCA DIRECTO) en una bolsa sobre la parte de la cara operada, en intervalos de 10 minutos por 10 minutos. Asistir al control y retiro de sutura a los 14 días. Avisar al cirujano Dr.(a) de presentar hemorragias severas u otras anomalías que pudieran sugerir complicaciones, asistir a la clínica. Si tiene hematoma es normal y puede demorar unos 10 a 15 días en remitir. Comprendo que debo seguir las siguientes indicaciones entregadas por mi odontólogo tratante:

```

## IND_ENDODONCIA — CO / es-CO

- Título: Indicaciones de endodoncia
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [34]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 31
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de endodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES ENDODONCIA • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. Espere 2 horas antes de comer. • Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado endodóntico. Lo importante es realizar la obturación final antes del primer mes de terminada la endodoncia. • Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede desalojar la obturación provisoria al usar hilo dental o con el cepillado. • Es normal sentir sensibilidad localizada en el diente las primeras 48 horas. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES BLANQUEAMIENTO • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros. • Evite alimentos muy fríos los primeros días. • No fumar. • En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave. APLICACIÓN DE FLUOR BARNIZ • No toque el barniz o sus dientes con los dedos • No comer por 3 horas. • No tomar agua por 1 hora. • No cepillar los dientes por 12 horas. • Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo. • Cambiar cepillo por uno nuevo.

```

## IND_ENDODONCIA — CL / es-CL

- Título: Indicaciones de endodoncia
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [34]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 31
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de endodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de endodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES ENDODONCIA • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. Espere 2 horas antes de comer. • Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado endodóntico. Lo importante es realizar la obturación final antes del primer mes de terminada la endodoncia. • Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede desalojar la obturación provisoria al usar hilo dental o con el cepillado. • Es normal sentir sensibilidad localizada en el diente las primeras 48 horas. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES BLANQUEAMIENTO • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros. • Evite alimentos muy fríos los primeros días. • No fumar. • En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave. APLICACIÓN DE FLUOR BARNIZ • No toque el barniz o sus dientes con los dedos • No comer por 3 horas. • No tomar agua por 1 hora. • No cepillar los dientes por 12 horas. • Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo. • Cambiar cepillo por uno nuevo.

```

## IND_BLANQUEAMIENTO — CO / es-CO

- Título: Indicaciones de blanqueamiento
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [34]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 31
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de blanqueamiento

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES ENDODONCIA • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. Espere 2 horas antes de comer. • Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado endodóntico. Lo importante es realizar la obturación final antes del primer mes de terminada la endodoncia. • Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede desalojar la obturación provisoria al usar hilo dental o con el cepillado. • Es normal sentir sensibilidad localizada en el diente las primeras 48 horas. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES BLANQUEAMIENTO • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros. • Evite alimentos muy fríos los primeros días. • No fumar. • En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave. APLICACIÓN DE FLUOR BARNIZ • No toque el barniz o sus dientes con los dedos • No comer por 3 horas. • No tomar agua por 1 hora. • No cepillar los dientes por 12 horas. • Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo. • Cambiar cepillo por uno nuevo.

```

## IND_BLANQUEAMIENTO — CL / es-CL

- Título: Indicaciones de blanqueamiento
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [34]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 31
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de blanqueamiento

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de blanqueamiento

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES ENDODONCIA • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. Espere 2 horas antes de comer. • Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado endodóntico. Lo importante es realizar la obturación final antes del primer mes de terminada la endodoncia. • Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede desalojar la obturación provisoria al usar hilo dental o con el cepillado. • Es normal sentir sensibilidad localizada en el diente las primeras 48 horas. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES BLANQUEAMIENTO • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros. • Evite alimentos muy fríos los primeros días. • No fumar. • En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave. APLICACIÓN DE FLUOR BARNIZ • No toque el barniz o sus dientes con los dedos • No comer por 3 horas. • No tomar agua por 1 hora. • No cepillar los dientes por 12 horas. • Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo. • Cambiar cepillo por uno nuevo.

```

## IND_FLUOR_BARNIZ — CO / es-CO

- Título: Aplicación de flúor barniz
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [34]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 31
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Aplicación de flúor barniz

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES ENDODONCIA • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. Espere 2 horas antes de comer. • Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado endodóntico. Lo importante es realizar la obturación final antes del primer mes de terminada la endodoncia. • Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede desalojar la obturación provisoria al usar hilo dental o con el cepillado. • Es normal sentir sensibilidad localizada en el diente las primeras 48 horas. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES BLANQUEAMIENTO • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros. • Evite alimentos muy fríos los primeros días. • No fumar. • En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave. APLICACIÓN DE FLUOR BARNIZ • No toque el barniz o sus dientes con los dedos • No comer por 3 horas. • No tomar agua por 1 hora. • No cepillar los dientes por 12 horas. • Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo. • Cambiar cepillo por uno nuevo.

```

## IND_FLUOR_BARNIZ — CL / es-CL

- Título: Aplicación de flúor barniz
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [34]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 31
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Aplicación de flúor barniz

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Aplicación de flúor barniz

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES ENDODONCIA • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. Espere 2 horas antes de comer. • Evite morder alimentos duros mientras mantenga su obturación provisoria o doble sellado endodóntico. Lo importante es realizar la obturación final antes del primer mes de terminada la endodoncia. • Realizar cepillado prolijo y tener cuidado en el diente tratado endodónticamente ya que puede desalojar la obturación provisoria al usar hilo dental o con el cepillado. • Es normal sentir sensibilidad localizada en el diente las primeras 48 horas. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES BLANQUEAMIENTO • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • Evite alimentos con colorantes, bebidas cola, café, té, Cheetos, vino, entre otros. • Evite alimentos muy fríos los primeros días. • No fumar. • En caso de sensibilidad, es normal en este tipo de procedimientos los primeros días, utilizar pasta dental y enjuague para dientes sensibles, cepillarse sin fuerza y con cepillo suave. APLICACIÓN DE FLUOR BARNIZ • No toque el barniz o sus dientes con los dedos • No comer por 3 horas. • No tomar agua por 1 hora. • No cepillar los dientes por 12 horas. • Para cepillarse luego de 12 horas, utilizar un cepillo antiguo y viejo, luego elimínalo. • Cambiar cepillo por uno nuevo.

```

## IND_OBTURACIONES_RESINA — CO / es-CO

- Título: Indicaciones de obturaciones en resina
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [35, 36]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 4
- Párrafos unidos: 59
- Frases de representante: ['apoderado']
- Términos locales: ['calugas', 'tapadura']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de obturaciones en resina

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES DE OBTURACIONES – RESINA • Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES PARA DESTARTRAJE (LIMPIEZA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Utilizar cepillo de corte recto de cerdas suaves. • La limpieza no suelta dientes ni desaloja obturaciones. INDICACIONES GENERALES ODONTOPEDIATRIA • Utiliza cepillos y pasta dental acorde a la edad del paciente • En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental, mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado. • En escolares motiva y supervisa el cepillado individual del paciente. • Cuida la alimentación de tu hijo, mantén una alimentación saludable. • Realiza controles periódicos. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. OBTURACIONES – RESINA

• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES ORTODONCIA • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un periodo de adaptación de tus dientes • Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos. • No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar en trozos pequeños, etc.) • No comer alimentos pegajosos (calugas, chicle, masticables, etc.) • No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar. • No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente • Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES PERIODONCIA DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • No fumar por 72 horas. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Usar cepillo suave • La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados falsamente por el sarro.

```

## IND_OBTURACIONES_RESINA — CL / es-CL

- Título: Indicaciones de obturaciones en resina
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [35, 36]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 4
- Párrafos unidos: 59
- Frases de representante: ['apoderado']
- Términos locales: ['calugas', 'tapadura']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de obturaciones en resina

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de obturaciones en resina

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES DE OBTURACIONES – RESINA • Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES PARA DESTARTRAJE (LIMPIEZA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Utilizar cepillo de corte recto de cerdas suaves. • La limpieza no suelta dientes ni desaloja obturaciones. INDICACIONES GENERALES ODONTOPEDIATRIA • Utiliza cepillos y pasta dental acorde a la edad del paciente • En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental, mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado. • En escolares motiva y supervisa el cepillado individual del paciente. • Cuida la alimentación de tu hijo, mantén una alimentación saludable. • Realiza controles periódicos. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. OBTURACIONES – RESINA

• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES ORTODONCIA • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un periodo de adaptación de tus dientes • Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos. • No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar en trozos pequeños, etc.) • No comer alimentos pegajosos (calugas, chicle, masticables, etc.) • No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar. • No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente • Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES PERIODONCIA DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • No fumar por 72 horas. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Usar cepillo suave • La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados falsamente por el sarro.

```

## IND_DESTARTRAJE — CO / es-CO

- Título: Indicaciones para destartraje
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [35]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 30
- Frases de representante: ['apoderado']
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones para destartraje

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES DE OBTURACIONES – RESINA • Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES PARA DESTARTRAJE (LIMPIEZA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Utilizar cepillo de corte recto de cerdas suaves. • La limpieza no suelta dientes ni desaloja obturaciones. INDICACIONES GENERALES ODONTOPEDIATRIA • Utiliza cepillos y pasta dental acorde a la edad del paciente • En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental, mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado. • En escolares motiva y supervisa el cepillado individual del paciente. • Cuida la alimentación de tu hijo, mantén una alimentación saludable. • Realiza controles periódicos. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. OBTURACIONES – RESINA

```

## IND_DESTARTRAJE — CL / es-CL

- Título: Indicaciones para destartraje
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [35]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 30
- Frases de representante: ['apoderado']
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones para destartraje

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones para destartraje

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES DE OBTURACIONES – RESINA • Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES PARA DESTARTRAJE (LIMPIEZA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Utilizar cepillo de corte recto de cerdas suaves. • La limpieza no suelta dientes ni desaloja obturaciones. INDICACIONES GENERALES ODONTOPEDIATRIA • Utiliza cepillos y pasta dental acorde a la edad del paciente • En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental, mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado. • En escolares motiva y supervisa el cepillado individual del paciente. • Cuida la alimentación de tu hijo, mantén una alimentación saludable. • Realiza controles periódicos. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. OBTURACIONES – RESINA

```

## IND_ODONTOPEDIATRIA_GENERAL — CO / es-CO

- Título: Indicaciones generales de odontopediatría
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [35]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 30
- Frases de representante: ['apoderado']
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones generales de odontopediatría

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES DE OBTURACIONES – RESINA • Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES PARA DESTARTRAJE (LIMPIEZA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Utilizar cepillo de corte recto de cerdas suaves. • La limpieza no suelta dientes ni desaloja obturaciones. INDICACIONES GENERALES ODONTOPEDIATRIA • Utiliza cepillos y pasta dental acorde a la edad del paciente • En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental, mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado. • En escolares motiva y supervisa el cepillado individual del paciente. • Cuida la alimentación de tu hijo, mantén una alimentación saludable. • Realiza controles periódicos. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. OBTURACIONES – RESINA

```

## IND_ODONTOPEDIATRIA_GENERAL — CL / es-CL

- Título: Indicaciones generales de odontopediatría
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [35]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 30
- Frases de representante: ['apoderado']
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones generales de odontopediatría

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones generales de odontopediatría

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

INDICACIONES DE OBTURACIONES – RESINA • Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES PARA DESTARTRAJE (LIMPIEZA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Utilizar cepillo de corte recto de cerdas suaves. • La limpieza no suelta dientes ni desaloja obturaciones. INDICACIONES GENERALES ODONTOPEDIATRIA • Utiliza cepillos y pasta dental acorde a la edad del paciente • En pre-escolares asegúrate diariamente de cepillar y mantener una correcta higiene dental, mínimo 3 veces al día, ideal después de cada comida. El cepillado lo realiza el apoderado. • En escolares motiva y supervisa el cepillado individual del paciente. • Cuida la alimentación de tu hijo, mantén una alimentación saludable. • Realiza controles periódicos. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. OBTURACIONES – RESINA

```

## IND_ORTODONCIA — CO / es-CO

- Título: Indicaciones de ortodoncia
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [36]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 35
- Frases de representante: No detectadas
- Términos locales: ['calugas', 'tapadura']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de ortodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES ORTODONCIA • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un periodo de adaptación de tus dientes • Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos. • No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar en trozos pequeños, etc.) • No comer alimentos pegajosos (calugas, chicle, masticables, etc.) • No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar. • No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente • Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES PERIODONCIA DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • No fumar por 72 horas. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Usar cepillo suave • La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados falsamente por el sarro.

```

## IND_ORTODONCIA — CL / es-CL

- Título: Indicaciones de ortodoncia
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [36]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 35
- Frases de representante: No detectadas
- Términos locales: ['calugas', 'tapadura']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de ortodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de ortodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES ORTODONCIA • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un periodo de adaptación de tus dientes • Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos. • No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar en trozos pequeños, etc.) • No comer alimentos pegajosos (calugas, chicle, masticables, etc.) • No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar. • No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente • Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES PERIODONCIA DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • No fumar por 72 horas. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Usar cepillo suave • La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados falsamente por el sarro.

```

## IND_PERIODONCIA — CO / es-CO

- Título: Indicaciones de periodoncia
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [36, 37]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 4
- Párrafos unidos: 59
- Frases de representante: ['MENOR']
- Términos locales: ['calugas', 'tapadura']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de periodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES ORTODONCIA • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un periodo de adaptación de tus dientes • Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos. • No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar en trozos pequeños, etc.) • No comer alimentos pegajosos (calugas, chicle, masticables, etc.) • No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar. • No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente • Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES PERIODONCIA DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • No fumar por 72 horas. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Usar cepillo suave • La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados falsamente por el sarro.

• Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su tratante si esto sucede. • Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde. • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. INDICACIONES PREOPERATORIAS -CIRUGÍA MENOR MAXILOFACIAL Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local A continuación le entregamos las recomendaciones e instrucciones que deben seguir los pacientes que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad, eficacia y correcto desarrollo del procedimiento quirúrgico ambulatorio. I. Requisitos Generales del Paciente • Ayuno: No es necesario ayuno. Se recomienda evitar comidas pesadas al menos 2 horas antes del procedimiento. Debe consumir un desayuno o colación ligera si la cirugía es en la mañana/tarde, pues pasará un par de horas antes de poder comer luego de la anestesia. • Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación contraria del equipo médico. Si Ud. toma anticoagulantes o antiagregantes, debe haber sido evaluado previamente por el cirujano y/o hematología si corresponde. Llevar una lista de medicamentos actuales. • Higiene oral: Realizar higiene oral habitual antes de asistir al procedimiento. • Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria aguda, herpes oral activo o descompensación de enfermedades crónicas, debe comunicarse con anticipación para reagendar la cirugía. • Acompañante: Es recomendable asistir con un acompañante, especialmente si el paciente es de edad avanzada o con antecedentes médicos relevantes.

```

## IND_PERIODONCIA — CL / es-CL

- Título: Indicaciones de periodoncia
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [36, 37]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 4
- Párrafos unidos: 59
- Frases de representante: ['MENOR']
- Términos locales: ['calugas', 'tapadura']
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS', 'localized_terms_require_human_review']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de periodoncia

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de periodoncia

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

• Evite alimentos con colorantes que puedan teñir su obturación por 24 -48 horas (coloca cola, té). • Evite fumar por 24-48 horas. • En caso de dolor o sensibilidad post operatoria (contracción de polimerización, pulpitis), asistir a control con su tratante. • En caso que la obturación haya quedado alta o áspera, asistir a control con su tratante. INDICACIONES ORTODONCIA • Los primeros días o el primer mes, es común sentir molestias, sensibilidad o dolor. Existe un periodo de adaptación de tus dientes • Mantén una buena higiene, utilizando un cepillo especial para ortodoncia, cepillo monotip y cepillos interproximales. Seguir indicaciones del especialista. Cepillarse mínimo 4 minutos. • No comer alimentos duros (maní, frutos secos, morder frutas como manzana, es mejor cortar en trozos pequeños, etc.) • No comer alimentos pegajosos (calugas, chicle, masticables, etc.) • No manipular los Brackets en el hogar utilizando cualquier elemento que los pueda desalojar. • No faltes a tus controles, el tratamiento no avanza si no te controlas periódicamente • Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES PERIODONCIA DESTARTRAJE SUPRAGINGIVAL, SUBGINGIVAL Y PULIDO RADICULAR (LIMPIEZA PROFUNDA) • Diariamente realice una correcta higiene dental, mínimo 3 veces al día. • No fumar por 72 horas. • En caso de sensibilidad, es normal en este tipo de procedimiento los primeros días, utilizar pasta dental desensibilizante, frotar el cuello del diente o sector afectado y dormir con ella, sin enjuagarse. • Usar cepillo suave • La limpieza no suelta dientes ni desaloja obturaciones, si esto sucede significa que la obturación (tapadura) ya estaba con alguna falla previa y los dientes estaban afirmados falsamente por el sarro.

• Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su tratante si esto sucede. • Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde. • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. INDICACIONES PREOPERATORIAS -CIRUGÍA MENOR MAXILOFACIAL Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local A continuación le entregamos las recomendaciones e instrucciones que deben seguir los pacientes que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad, eficacia y correcto desarrollo del procedimiento quirúrgico ambulatorio. I. Requisitos Generales del Paciente • Ayuno: No es necesario ayuno. Se recomienda evitar comidas pesadas al menos 2 horas antes del procedimiento. Debe consumir un desayuno o colación ligera si la cirugía es en la mañana/tarde, pues pasará un par de horas antes de poder comer luego de la anestesia. • Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación contraria del equipo médico. Si Ud. toma anticoagulantes o antiagregantes, debe haber sido evaluado previamente por el cirujano y/o hematología si corresponde. Llevar una lista de medicamentos actuales. • Higiene oral: Realizar higiene oral habitual antes de asistir al procedimiento. • Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria aguda, herpes oral activo o descompensación de enfermedades crónicas, debe comunicarse con anticipación para reagendar la cirugía. • Acompañante: Es recomendable asistir con un acompañante, especialmente si el paciente es de edad avanzada o con antecedentes médicos relevantes.

```

## IND_PREOP_CIRUGIA_MAXILOFACIAL — CO / es-CO

- Título: Indicaciones preoperatorias de cirugía menor maxilofacial
- Tipo: PRE_CARE_INSTRUCTIONS
- Páginas fuente: [37, 38]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 4
- Párrafos unidos: 62
- Frases de representante: ['menor', 'lactante']
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:PRE_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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
su deformación con el calor. No usar nunca agua hirvie

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Indicaciones preoperatorias de cirugía menor maxilofacial

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

• Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su tratante si esto sucede. • Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde. • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. INDICACIONES PREOPERATORIAS -CIRUGÍA MENOR MAXILOFACIAL Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local A continuación le entregamos las recomendaciones e instrucciones que deben seguir los pacientes que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad, eficacia y correcto desarrollo del procedimiento quirúrgico ambulatorio. I. Requisitos Generales del Paciente • Ayuno: No es necesario ayuno. Se recomienda evitar comidas pesadas al menos 2 horas antes del procedimiento. Debe consumir un desayuno o colación ligera si la cirugía es en la mañana/tarde, pues pasará un par de horas antes de poder comer luego de la anestesia. • Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación contraria del equipo médico. Si Ud. toma anticoagulantes o antiagregantes, debe haber sido evaluado previamente por el cirujano y/o hematología si corresponde. Llevar una lista de medicamentos actuales. • Higiene oral: Realizar higiene oral habitual antes de asistir al procedimiento. • Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria aguda, herpes oral activo o descompensación de enfermedades crónicas, debe comunicarse con anticipación para reagendar la cirugía. • Acompañante: Es recomendable asistir con un acompañante, especialmente si el paciente es de edad avanzada o con antecedentes médicos relevantes.

II. Pacientes Embarazadas y en Lactancia • Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad, preferentemente en el segundo trimestre del embarazo (semanas 14 a 28). Se debe informar al equipo tratante sobre la edad gestacional. Se evitarán fármacos contraindicados durante la gestación. El uso de anestésicos locales con vasoconstrictor está permitido en dosis controladas. Evitar posición supina prolongada durante el procedimiento para prevenir síndrome de hipotensión supina. Se recomienda asistencia con acompañante. • Pacientes en Lactancia: La mayoría de los anestésicos locales (como la lidocaína) y antibióticos de uso habitual (como amoxicilina) son compatibles con la lactancia. Si se prescriben analgésicos o antibióticos, consultar siempre la compatibilidad con lactancia. Si se indican medicamentos poco compatibles, se puede realizar extracción de leche previa para alimentar al lactante en las horas posteriores. III. Documentación Necesaria • Exámenes complementarios (si fueron solicitados previamente como scanner o panorámica si los realizó en otro centro). IV. Consideraciones Específicas para el Procedimiento • Vestimenta y otros: Ropa cómoda y fácil de remover. Evitar maquillaje, uñas pintadas, alhajas o accesorios en cara/cuello. Barba recortada 1 cm máximo, para lograr una adecuada desinfección. • Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales. INDICACIONES REHABILITACION ORAL Prótesis removible parcial o total • Mantenga una buena higiene bucal (dientes, mucosas, lengua), al menos 3 veces al día e ideal después de cada comida. • Mantenga una buena higiene de su prótesis removible, cepille su prótesis con un cepillo independiente, utilice otro para sus dientes. • Lave su prótesis con jabón líquido neutro o de glicerina bajo el chorro de agua. • No cepille su prótesis con pasta dental ya que puede rayar la superficie por las partículas abrasivas que podría tener. • Semanalmente limpie su prótesis con tabletas efervescentes de limpieza profunda. • No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos. • Al retirar su prótesis puede mantenerla en un vaso con agua (temperatura normal) para evitar su deformación con el calor. No usar nunca agua hirviendo ya que puede deformar su

```

## IND_PREOP_CIRUGIA_MAXILOFACIAL — CL / es-CL

- Título: Indicaciones preoperatorias de cirugía menor maxilofacial
- Tipo: PRE_CARE_INSTRUCTIONS
- Páginas fuente: [37, 38]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 4
- Párrafos unidos: 62
- Frases de representante: ['menor', 'lactante']
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:PRE_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones preoperatorias de cirugía menor maxilofacial

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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
su deformación con el calor. No usar nunca agua hirviendo

[Contenido truncado para revisión editorial local. Ver JSON para el texto completo.]
```

### Contenido normalizado v2

```markdown
# Indicaciones preoperatorias de cirugía menor maxilofacial

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

• Puede presentar reacciones de tejido blando, aumento de volumen e infección. Visite a su tratante si esto sucede. • Siga las indicaciones del especialista y tome los medicamentos recetados si corresponde. • Cuidado y precaución con la alimentación ya que podría morderse si está bajo los efectos de la anestesia. INDICACIONES PREOPERATORIAS -CIRUGÍA MENOR MAXILOFACIAL Protocolo de Indicaciones Preoperatorias – Cirugía Menor Maxilofacial con Anestesia Local A continuación le entregamos las recomendaciones e instrucciones que deben seguir los pacientes que serán sometidos a cirugía menor maxilofacial bajo anestesia local, garantizando la seguridad, eficacia y correcto desarrollo del procedimiento quirúrgico ambulatorio. I. Requisitos Generales del Paciente • Ayuno: No es necesario ayuno. Se recomienda evitar comidas pesadas al menos 2 horas antes del procedimiento. Debe consumir un desayuno o colación ligera si la cirugía es en la mañana/tarde, pues pasará un par de horas antes de poder comer luego de la anestesia. • Medicamentos habituales: Debe continuar con su medicación habitual, salvo indicación contraria del equipo médico. Si Ud. toma anticoagulantes o antiagregantes, debe haber sido evaluado previamente por el cirujano y/o hematología si corresponde. Llevar una lista de medicamentos actuales. • Higiene oral: Realizar higiene oral habitual antes de asistir al procedimiento. • Estado de salud general: En caso de presentar síntomas como fiebre, infección respiratoria aguda, herpes oral activo o descompensación de enfermedades crónicas, debe comunicarse con anticipación para reagendar la cirugía. • Acompañante: Es recomendable asistir con un acompañante, especialmente si el paciente es de edad avanzada o con antecedentes médicos relevantes.

II. Pacientes Embarazadas y en Lactancia • Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad, preferentemente en el segundo trimestre del embarazo (semanas 14 a 28). Se debe informar al equipo tratante sobre la edad gestacional. Se evitarán fármacos contraindicados durante la gestación. El uso de anestésicos locales con vasoconstrictor está permitido en dosis controladas. Evitar posición supina prolongada durante el procedimiento para prevenir síndrome de hipotensión supina. Se recomienda asistencia con acompañante. • Pacientes en Lactancia: La mayoría de los anestésicos locales (como la lidocaína) y antibióticos de uso habitual (como amoxicilina) son compatibles con la lactancia. Si se prescriben analgésicos o antibióticos, consultar siempre la compatibilidad con lactancia. Si se indican medicamentos poco compatibles, se puede realizar extracción de leche previa para alimentar al lactante en las horas posteriores. III. Documentación Necesaria • Exámenes complementarios (si fueron solicitados previamente como scanner o panorámica si los realizó en otro centro). IV. Consideraciones Específicas para el Procedimiento • Vestimenta y otros: Ropa cómoda y fácil de remover. Evitar maquillaje, uñas pintadas, alhajas o accesorios en cara/cuello. Barba recortada 1 cm máximo, para lograr una adecuada desinfección. • Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales. INDICACIONES REHABILITACION ORAL Prótesis removible parcial o total • Mantenga una buena higiene bucal (dientes, mucosas, lengua), al menos 3 veces al día e ideal después de cada comida. • Mantenga una buena higiene de su prótesis removible, cepille su prótesis con un cepillo independiente, utilice otro para sus dientes. • Lave su prótesis con jabón líquido neutro o de glicerina bajo el chorro de agua. • No cepille su prótesis con pasta dental ya que puede rayar la superficie por las partículas abrasivas que podría tener. • Semanalmente limpie su prótesis con tabletas efervescentes de limpieza profunda. • No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos. • Al retirar su prótesis puede mantenerla en un vaso con agua (temperatura normal) para evitar su deformación con el calor. No usar nunca agua hirviendo ya que puede deformar su

```

## IND_REHABILITACION_ORAL — CO / es-CO

- Título: Indicaciones de rehabilitación oral
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [38, 39]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 4
- Párrafos unidos: 55
- Frases de representante: ['menor', 'lactante']
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de rehabilitación oral

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

II. Pacientes Embarazadas y en Lactancia • Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad, preferentemente en el segundo trimestre del embarazo (semanas 14 a 28). Se debe informar al equipo tratante sobre la edad gestacional. Se evitarán fármacos contraindicados durante la gestación. El uso de anestésicos locales con vasoconstrictor está permitido en dosis controladas. Evitar posición supina prolongada durante el procedimiento para prevenir síndrome de hipotensión supina. Se recomienda asistencia con acompañante. • Pacientes en Lactancia: La mayoría de los anestésicos locales (como la lidocaína) y antibióticos de uso habitual (como amoxicilina) son compatibles con la lactancia. Si se prescriben analgésicos o antibióticos, consultar siempre la compatibilidad con lactancia. Si se indican medicamentos poco compatibles, se puede realizar extracción de leche previa para alimentar al lactante en las horas posteriores. III. Documentación Necesaria • Exámenes complementarios (si fueron solicitados previamente como scanner o panorámica si los realizó en otro centro). IV. Consideraciones Específicas para el Procedimiento • Vestimenta y otros: Ropa cómoda y fácil de remover. Evitar maquillaje, uñas pintadas, alhajas o accesorios en cara/cuello. Barba recortada 1 cm máximo, para lograr una adecuada desinfección. • Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales. INDICACIONES REHABILITACION ORAL Prótesis removible parcial o total • Mantenga una buena higiene bucal (dientes, mucosas, lengua), al menos 3 veces al día e ideal después de cada comida. • Mantenga una buena higiene de su prótesis removible, cepille su prótesis con un cepillo independiente, utilice otro para sus dientes. • Lave su prótesis con jabón líquido neutro o de glicerina bajo el chorro de agua. • No cepille su prótesis con pasta dental ya que puede rayar la superficie por las partículas abrasivas que podría tener. • Semanalmente limpie su prótesis con tabletas efervescentes de limpieza profunda. • No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos. • Al retirar su prótesis puede mantenerla en un vaso con agua (temperatura normal) para evitar su deformación con el calor. No usar nunca agua hirviendo ya que puede deformar su

prótesis. Los elementos protésicos deben ser controlados cada 6 meses o 1 año para realizar ajustes y rebasados. Prótesis fija (carillas, incrustaciones, coronas, coronas sobre implantes) • No comer alimentos muy duros (masticar hielo, frutos secos). Evitar malos hábitos: comerse las uñas, abrir botellas con los dientes. • Evitar alimentos que puedan teñir la cerámica. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES ODONTOPEDIATRIA TRAUMA DENTOALVEOLAR • REALIZAR CEPILLADO CON CEPILLO SUAVE DESPUÉS DE CADA COMIDA • UTILIZAR CLORHEXIDINA 0,12% CON COTONITO O GASA EN LA ZONA POR 10-15 DIAS • DIETA BLANCA POR 10 DÍAS • EVITAR USO DE CHUPETE, MAMADERA O BOMBILLAS. • UTILIZAR BÁLSAMO LABIAL EN CASO DE HERIDA EN EL LABIO • DEBE VOLVER A CONTROL Y TRATAMIENTO • INDICACIONES:

```

## IND_REHABILITACION_ORAL — CL / es-CL

- Título: Indicaciones de rehabilitación oral
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [38, 39]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 4
- Líneas de firma eliminadas: 4
- Párrafos unidos: 55
- Frases de representante: ['menor', 'lactante']
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de rehabilitación oral

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de rehabilitación oral

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

II. Pacientes Embarazadas y en Lactancia • Embarazadas: La cirugía menor con anestesia local puede realizarse con seguridad, preferentemente en el segundo trimestre del embarazo (semanas 14 a 28). Se debe informar al equipo tratante sobre la edad gestacional. Se evitarán fármacos contraindicados durante la gestación. El uso de anestésicos locales con vasoconstrictor está permitido en dosis controladas. Evitar posición supina prolongada durante el procedimiento para prevenir síndrome de hipotensión supina. Se recomienda asistencia con acompañante. • Pacientes en Lactancia: La mayoría de los anestésicos locales (como la lidocaína) y antibióticos de uso habitual (como amoxicilina) son compatibles con la lactancia. Si se prescriben analgésicos o antibióticos, consultar siempre la compatibilidad con lactancia. Si se indican medicamentos poco compatibles, se puede realizar extracción de leche previa para alimentar al lactante en las horas posteriores. III. Documentación Necesaria • Exámenes complementarios (si fueron solicitados previamente como scanner o panorámica si los realizó en otro centro). IV. Consideraciones Específicas para el Procedimiento • Vestimenta y otros: Ropa cómoda y fácil de remover. Evitar maquillaje, uñas pintadas, alhajas o accesorios en cara/cuello. Barba recortada 1 cm máximo, para lograr una adecuada desinfección. • Alergias: Informar cualquier alergia a medicamentos, alimentos o materiales dentales. INDICACIONES REHABILITACION ORAL Prótesis removible parcial o total • Mantenga una buena higiene bucal (dientes, mucosas, lengua), al menos 3 veces al día e ideal después de cada comida. • Mantenga una buena higiene de su prótesis removible, cepille su prótesis con un cepillo independiente, utilice otro para sus dientes. • Lave su prótesis con jabón líquido neutro o de glicerina bajo el chorro de agua. • No cepille su prótesis con pasta dental ya que puede rayar la superficie por las partículas abrasivas que podría tener. • Semanalmente limpie su prótesis con tabletas efervescentes de limpieza profunda. • No duerma con su prótesis, esto genera infecciones, inflamación de mucosas y hongos. • Al retirar su prótesis puede mantenerla en un vaso con agua (temperatura normal) para evitar su deformación con el calor. No usar nunca agua hirviendo ya que puede deformar su

prótesis. Los elementos protésicos deben ser controlados cada 6 meses o 1 año para realizar ajustes y rebasados. Prótesis fija (carillas, incrustaciones, coronas, coronas sobre implantes) • No comer alimentos muy duros (masticar hielo, frutos secos). Evitar malos hábitos: comerse las uñas, abrir botellas con los dientes. • Evitar alimentos que puedan teñir la cerámica. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES ODONTOPEDIATRIA TRAUMA DENTOALVEOLAR • REALIZAR CEPILLADO CON CEPILLO SUAVE DESPUÉS DE CADA COMIDA • UTILIZAR CLORHEXIDINA 0,12% CON COTONITO O GASA EN LA ZONA POR 10-15 DIAS • DIETA BLANCA POR 10 DÍAS • EVITAR USO DE CHUPETE, MAMADERA O BOMBILLAS. • UTILIZAR BÁLSAMO LABIAL EN CASO DE HERIDA EN EL LABIO • DEBE VOLVER A CONTROL Y TRATAMIENTO • INDICACIONES:

```

## IND_TRAUMA_DENTOALVEOLAR — CO / es-CO

- Título: Indicaciones de odontopediatría trauma dentoalveolar
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [39]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 23
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

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

### Contenido normalizado v2

```markdown
# Indicaciones de odontopediatría trauma dentoalveolar

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Colombia Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

prótesis. Los elementos protésicos deben ser controlados cada 6 meses o 1 año para realizar ajustes y rebasados. Prótesis fija (carillas, incrustaciones, coronas, coronas sobre implantes) • No comer alimentos muy duros (masticar hielo, frutos secos). Evitar malos hábitos: comerse las uñas, abrir botellas con los dientes. • Evitar alimentos que puedan teñir la cerámica. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES ODONTOPEDIATRIA TRAUMA DENTOALVEOLAR • REALIZAR CEPILLADO CON CEPILLO SUAVE DESPUÉS DE CADA COMIDA • UTILIZAR CLORHEXIDINA 0,12% CON COTONITO O GASA EN LA ZONA POR 10-15 DIAS • DIETA BLANCA POR 10 DÍAS • EVITAR USO DE CHUPETE, MAMADERA O BOMBILLAS. • UTILIZAR BÁLSAMO LABIAL EN CASO DE HERIDA EN EL LABIO • DEBE VOLVER A CONTROL Y TRATAMIENTO • INDICACIONES:

```

## IND_TRAUMA_DENTOALVEOLAR — CL / es-CL

- Título: Indicaciones de odontopediatría trauma dentoalveolar
- Tipo: POST_CARE_INSTRUCTIONS
- Páginas fuente: [39]
- Estado: **BLOCKED**
- Compatibilidad firmante: `NO_PATIENT_SIGNATURE`
- Marcadores eliminados: 3
- Líneas de firma eliminadas: 4
- Párrafos unidos: 23
- Frases de representante: No detectadas
- Términos locales: No detectados
- Variables: ['company.name', 'document.clinical_date', 'patient.document_number', 'patient.document_type', 'patient.full_name', 'professional.full_name', 'professional.license_number', 'site.address', 'site.city', 'site.name']
- Alertas: ['special_document_type_requires_dedicated_workflow:POST_CARE_INSTRUCTIONS']

### Texto fuente

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

### Contenido normalizado v1

```markdown
# Indicaciones de odontopediatría trauma dentoalveolar

Paciente: {{patient.full_name}}
Identificación: {{patient.document_type}} {{patient.document_number}}
Fecha clínica: {{document.clinical_date}}
País documental: Chile
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

### Contenido normalizado v2

```markdown
# Indicaciones de odontopediatría trauma dentoalveolar

Paciente: {{patient.full_name}} Identificación: {{patient.document_type}} {{patient.document_number}} Fecha clínica: {{document.clinical_date}} País documental: Chile Clínica: {{company.name}} Sede: {{site.name}} Dirección de sede: {{site.address}}, {{site.city}}

prótesis. Los elementos protésicos deben ser controlados cada 6 meses o 1 año para realizar ajustes y rebasados. Prótesis fija (carillas, incrustaciones, coronas, coronas sobre implantes) • No comer alimentos muy duros (masticar hielo, frutos secos). Evitar malos hábitos: comerse las uñas, abrir botellas con los dientes. • Evitar alimentos que puedan teñir la cerámica. • Seguir receta indicada. Tomar medicamentos según prescripción. • Seguir indicaciones de especialista. • En caso de urgencia asistir a clínica o centro asistencial. INDICACIONES ODONTOPEDIATRIA TRAUMA DENTOALVEOLAR • REALIZAR CEPILLADO CON CEPILLO SUAVE DESPUÉS DE CADA COMIDA • UTILIZAR CLORHEXIDINA 0,12% CON COTONITO O GASA EN LA ZONA POR 10-15 DIAS • DIETA BLANCA POR 10 DÍAS • EVITAR USO DE CHUPETE, MAMADERA O BOMBILLAS. • UTILIZAR BÁLSAMO LABIAL EN CASO DE HERIDA EN EL LABIO • DEBE VOLVER A CONTROL Y TRATAMIENTO • INDICACIONES:

```
