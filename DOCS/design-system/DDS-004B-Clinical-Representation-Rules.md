# DDS-004B — Clinical Representation Rules
## Reglas de representación clínica del Odontograma Dentia

Versión 1.0

---

# Propósito

Este documento define las reglas oficiales para representar condiciones clínicas dentro del Odontograma Dentia.

Su objetivo es garantizar que la representación visual:

- sea clínicamente correcta;
- sea rápida de interpretar;
- no genere ambigüedades;
- respete las convenciones odontológicas;
- mantenga consistencia entre profesionales.

---

# Principio fundamental

El odontograma no es una ilustración.

El odontograma es una herramienta clínica.

Por lo tanto:

La claridad clínica tiene prioridad sobre la estética visual.

Una representación visualmente atractiva pero clínicamente ambigua debe considerarse incorrecta.

---

# Relación con otros DDS

## DDS-001 — Tooth Component

Define:

- arquitectura del componente Tooth;
- capas;
- interacción;
- estructura técnica.

---

## DDS-004 — Tooth Visual States

Define:

- estados visuales disponibles;
- colores;
- capas;
- tratamientos.

---

## DDS-004A — Tooth Illustration Guide

Define:

- anatomía;
- volumen;
- estilo gráfico;
- calidad visual.

---

## DDS-004B — Clinical Representation Rules

Define:

- qué debe representarse sobre el diente;
- qué debe representarse mediante simbología clínica;
- qué información no debe dibujarse;
- qué estados requieren interpretación mediante Dental Inspector.

---

# Regla general de capas

El odontograma debe separar claramente:

## Capa anatómica

Representa:

- forma dental;
- estructura;
- restauraciones completas;
- ausencia;
- implantes;
- prótesis.

---

## Capa clínica

Representa:

- diagnósticos;
- lesiones;
- hallazgos;
- superficies afectadas.

Debe utilizar convenciones clínicas claras.

---

## Capa informativa

Representa:

- eventos;
- historial;
- observaciones;
- información complementaria.

No debe alterar la anatomía del diente.

---

# Clasificación de estados

Cada estado clínico debe pertenecer a una de estas categorías.

---

# Grupo A — Representación anatómica directa

Estados que pueden modificar visualmente la pieza dental.

Representación permitida sobre Tooth.

Ejemplos:

## Corona

Puede representarse cubriendo la corona anatómica.

Debe conservar:

- forma;
- volumen;
- diferenciación con diente natural.

---

## Implante

Puede representarse como estructura implantológica.

Debe ser inmediatamente reconocible.

---

## Ausencia dental

Puede representarse como ausencia de estructura.

No utilizar símbolos ambiguos.

---

## Prótesis

Puede representarse como restauración protésica.

---

## Endodoncia realizada

Puede representarse mediante elementos internos discretos.

No debe dominar la anatomía.

---

# Grupo B — Representación clínica sobre superficie

Estados que requieren ubicación anatómica.

La superficie es parte esencial del diagnóstico.

La representación debe seguir reglas odontográficas.

Ejemplos:

## Caries

La representación debe diferenciar:

- oclusal;
- mesial;
- distal;
- vestibular;
- palatina;
- lingual;
- cervical.

No utilizar una marca genérica que pueda confundirse entre superficies.

---

## Restauraciones

Deben indicar claramente:

- superficie restaurada;
- extensión;
- ubicación.

---

## Sellantes

Deben ubicarse únicamente sobre superficies compatibles.

---

# Grupo C — Representación simbólica clínica

Estados donde una pintura sobre el diente puede generar error.

Estos estados NO deben representarse como una lesión genérica sobre la corona.

Ejemplos:

---

## Lesión de furca

No debe dibujarse como una marca sobre la corona.

Debe utilizar simbología periodontal específica.

---

## Lesión periapical

No debe pintarse sobre la corona.

La ubicación real está relacionada con el ápice radicular.

Debe representarse mediante:

- símbolo específico;
- indicador radicular;
- Dental Inspector.

---

## Necrosis pulpar

No tiene una manifestación externa visible.

No debe alterarse la anatomía del diente.

---

## Pulpitis

No debe representarse mediante una lesión superficial.

Debe mantenerse como información clínica.

---

# Grupo D — Solo información clínica

Estados que deben permanecer en:

- contador;
- tooltip;
- historial;
- Dental Inspector.

No modificar visualmente el Tooth.

Ejemplos:

- dolor;
- sensibilidad;
- antecedentes;
- observaciones;
- síntomas;
- diagnósticos internos.

---

# Regla para diagnósticos sin superficie

Si un diagnóstico requiere superficie pero no existe información suficiente:

NO inventar ubicación.

No asumir:

- oclusal;
- vestibular;
- palatino;
- lingual.

Opciones permitidas:

1. Representación genérica claramente identificada.

2. Símbolo clínico neutro.

3. Información únicamente en Dental Inspector.

La decisión debe depender del tipo clínico.

---

# Prohibiciones

Nunca:

- dibujar una enfermedad interna como lesión externa;
- representar furca sobre corona;
- representar lesión periapical como mancha superficial;
- usar colores sin significado clínico;
- priorizar estética sobre interpretación.

---

# Principio de lectura rápida

Un odontólogo debe poder responder:

"¿Qué tiene este diente?"

sin preguntarse:

"¿Qué significa este símbolo?"

Si requiere interpretación adicional:

Debe existir:

- tooltip;
- Dental Inspector;
- historial.

---

# Dental Inspector

Cuando una condición no sea adecuadamente representable en el odontograma:

La información debe trasladarse al Dental Inspector.

El odontograma muestra:

"que existe algo"

El Dental Inspector explica:

"qué es y cuál es su historia".

---

# Objetivo final

El odontograma Dentia debe lograr equilibrio entre:

- belleza visual;
- anatomía;
- velocidad de lectura;
- precisión clínica.

Nunca debe convertirse en una ilustración decorativa.

Debe ser una herramienta clínica confiable.

---

# Criterios de aceptación

Una representación clínica es válida únicamente si:

✅ Es reconocible por un odontólogo.

✅ No genera interpretaciones contradictorias.

✅ Respeta la ubicación anatómica.

✅ Mantiene consistencia con convenciones clínicas.

✅ Mejora la toma de decisiones.

---

# Regla final

Ante cualquier conflicto entre:

"se ve más bonito"

y

"es clínicamente más claro"

siempre gana:

LA CLARIDAD CLÍNICA.