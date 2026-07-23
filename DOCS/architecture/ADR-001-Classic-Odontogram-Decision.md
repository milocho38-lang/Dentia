# ADR-001 — Decisión de representación clínica del odontograma

## Estado

Aceptado

## Contexto

Dentia requiere un odontograma que permita precisión clínica, lectura rápida y ubicación inequívoca de hallazgos, diagnósticos y tratamientos.

Durante la validación clínica del Odontograma Dentia 2.0 con odontólogo especialista se identificó que la representación anatómica 3D del diente, aunque visualmente atractiva y útil para comprensión anatómica, puede generar ambigüedad cuando se utiliza como mapa diagnóstico principal.

Una lesión pintada sobre un diente 3D puede generar dudas sobre si corresponde a:

- superficie oclusal;
- vestibular;
- palatina;
- lingual;
- cervical;
- furca.

El odontólogo indicó que la representación clásica del odontograma evita esta ambigüedad porque utiliza simbología clínica conocida y una ubicación espacial definida.

Dentia necesita separar claramente:

- lectura clínica rápida;
- detalle anatómico avanzado;
- historial clínico de la pieza;
- interpretación de superficies.

## Decisión

Dentia utilizará una arquitectura híbrida:

- odontograma clásico como mapa clínico principal;
- Tooth Component dentro de Dental Inspector como representación anatómica avanzada.

El odontograma clásico será responsable de la lectura clínica rápida, ubicación de superficies, símbolos odontológicos convencionales y diagnóstico visual inmediato.

El Tooth Component / Dental Inspector será responsable del detalle anatómico, evolución clínica, historial, tratamientos e información complementaria.

## Consecuencias positivas

- Menor ambigüedad clínica.
- Mayor familiaridad para odontólogos.
- Mejor interpretación de superficies.
- Separación clara entre mapa clínico e historia clínica detallada.
- El odontograma principal prioriza precisión y velocidad de lectura.
- El Tooth Component conserva valor como representación anatómica avanzada sin asumir el rol de mapa superficial principal.

## Consecuencias negativas

- Necesidad de mantener dos representaciones.
- Mayor complejidad de diseño.
- Necesidad de sincronización entre odontograma clásico y Dental Inspector.
- Requiere definir reglas claras para evitar divergencias visuales entre ambas capas.

## Alternativas descartadas

### Utilizar únicamente Tooth Component 3D como odontograma

Descartado porque puede generar interpretación clínica incorrecta al ubicar diagnósticos y hallazgos sobre superficies.

### Pintar diagnósticos directamente sobre anatomía 3D

Descartado porque una marca sobre anatomía 3D puede confundirse entre superficies o estructuras clínicas diferentes.

## Motivo

La claridad clínica tiene prioridad sobre la estética visual.

Dentia debe evitar cualquier representación que pueda inducir una interpretación odontológica equivocada.
