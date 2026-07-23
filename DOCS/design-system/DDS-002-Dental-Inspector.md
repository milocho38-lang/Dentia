# DDS-002 — Dental Inspector

## Dentia Design System

Versión 1.0

---

# Filosofía

El odontograma comunica.

El Dental Inspector explica.

El odontograma muestra el estado general del paciente.

El Dental Inspector muestra toda la historia clínica de un único diente.

El odontólogo nunca edita directamente sobre el odontograma.

Siempre trabaja desde el Dental Inspector.

El odontograma es el mapa.

El Dental Inspector es el expediente del diente.

---

# Objetivo

Cuando el odontólogo haga clic sobre cualquier diente del odontograma deberá abrirse un panel inteligente que concentre absolutamente toda la información clínica relacionada con ese diente.

El objetivo es evitar navegar entre diferentes módulos.

Toda la información relevante deberá estar disponible sin abandonar el contexto del paciente.

---

# Ubicación

Desktop

Siempre ocupará el costado derecho del odontograma.

No será una ventana emergente.

No será un modal.

No abrirá una página nueva.

Debe sentirse como parte natural del odontograma.

---

# Ancho

Aproximadamente entre 380 y 450 px.

Nunca cubrir el odontograma completo.

El odontograma continúa visible mientras se trabaja.

---

# Encabezado

Debe mostrar inmediatamente:

------------------------------------------------

Diente 37

Primer Molar Inferior Izquierdo

Estado actual

Corona definitiva

------------------------------------------------

Botones superiores:

Cerrar

Modo paciente (futuro)

Comparar (futuro)

---

# Tarjeta Estado Actual

Siempre será la primera.

Debe responder inmediatamente:

¿Qué tiene actualmente este diente?

Ejemplo

Estado

✔ Corona definitiva

✔ Endodoncia

✔ Funcional

Fecha última intervención

Hace 2 años

Odontólogo

Dr. Camilo Medina

---

# Línea de tiempo

Debajo del estado.

Orden cronológico descendente.

Ejemplo

2026

Control

Sin novedades

-------------------

2025

Corona definitiva

-------------------

2025

Endodoncia

-------------------

2024

Diagnóstico de caries profunda

Cada evento podrá expandirse.

Nunca abandonar el panel.

---

# Diagnósticos

Lista de diagnósticos asociados exclusivamente a este diente.

Ejemplo

Diagnósticos

Caries oclusal

Fractura cúspide vestibular

Lesión cervical

Cada uno con:

Fecha

Estado

Profesional

Observaciones

---

# Tratamientos

Mostrar únicamente tratamientos relacionados con este diente.

Ejemplo

Tratamientos

✔ Endodoncia

✔ Corona

○ Cambio de corona planificado

Desde aquí podrá abrirse el tratamiento completo.

Sin buscar nuevamente al paciente.

---

# Fotografías

Preparar la estructura.

No implementar todavía.

Cuando exista:

Miniaturas.

Click para ampliar.

Comparación temporal.

---

# Radiografías

Preparar estructura.

No implementar todavía.

Se visualizarán aquí.

---

# Procedimientos

Listado cronológico.

Ejemplo

Resina

Profilaxis localizada

Corona

Sellante

Extracción

Con fecha y profesional.

---

# Observaciones

Mostrar las observaciones clínicas relacionadas únicamente con ese diente.

No mostrar observaciones generales del paciente.

---

# Superficies

Representación gráfica.

O

M

D

V

L

Cada superficie deberá reflejar exactamente el estado actual.

No únicamente el diagnóstico.

También tratamientos realizados.

---

# Acciones

Al final del panel.

Botones

Agregar diagnóstico

Agregar tratamiento

Agregar observación

Agregar fotografía (futuro)

Agregar radiografía (futuro)

Nunca colocar estos botones arriba.

---

# Panel colapsable

El odontólogo podrá cerrar el panel.

Al seleccionar otro diente:

El panel cambia automáticamente.

Nunca abrir múltiples paneles.

---

# Integración con tratamientos

Cuando un tratamiento finalice.

El panel deberá actualizar automáticamente:

Estado.

Cronología.

Procedimientos.

Sin doble registro.

---

# Integración con Historia Clínica

Cuando exista una evolución relacionada con ese diente.

Debe aparecer automáticamente en la cronología.

No duplicar información.

---

# Integración con Timeline

En versiones futuras.

Mover la línea de tiempo del paciente.

↓

El Dental Inspector mostrará el estado del diente en esa fecha.

---

# Integración con Comparador

En versiones futuras.

Mostrar dos estados simultáneamente.

Ejemplo

Ingreso

↓

Actual

Resaltando únicamente los cambios.

---

# Modo Paciente

Futuro.

Ocultar:

Diagnósticos técnicos.

Mostrar únicamente:

Explicaciones sencillas.

Fotografías.

Evolución.

Ideal para explicar tratamientos.

---

# UX

El panel nunca debe sentirse como un formulario.

Debe sentirse como un expediente clínico.

Toda la información importante debe poder entenderse sin editar nada.

La edición será secundaria.

La consulta será prioritaria.

---

# Rendimiento

El panel deberá cargar únicamente la información del diente seleccionado.

Nunca consultar nuevamente todo el paciente.

La apertura debe sentirse inmediata.

---

# Reutilización

Este componente deberá poder utilizarse posteriormente en:

Implantología

Ortodoncia

Periodoncia

Endodoncia

Odontopediatría

Sin rediseños importantes.

---

# Criterios de aceptación

✅ El odontólogo comprende completamente la situación clínica de un diente sin abandonar el odontograma.

✅ El panel concentra historia, diagnósticos, tratamientos y cronología.

✅ No existen formularios complejos visibles por defecto.

✅ El odontograma continúa visible durante toda la consulta.

✅ El componente transmite la sensación de estar consultando la historia clínica de un diente y no simplemente editando un registro.

---

# Observación

El Dental Inspector constituye el segundo componente fundamental del Dentia Design System.

DDS-001 define cómo se representa visualmente un diente.

DDS-002 define cómo se consulta y administra toda la información clínica asociada a ese diente.

Ambos componentes serán la base para la construcción del nuevo Odontograma Dentia 2.0.