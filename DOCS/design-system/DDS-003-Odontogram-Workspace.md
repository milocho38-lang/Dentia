# DDS-003 — Odontogram Workspace

## Dentia Design System

Versión 1.0

---

# Filosofía

El odontograma no es un dibujo.

Es el centro de trabajo del odontólogo.

Toda la pantalla debe estar diseñada para responder una única pregunta:

**¿Qué debo hacer con este paciente?**

No para registrar información.

Para comprenderla.

---

# Objetivo

Construir un espacio de trabajo donde el odontólogo pueda:

- comprender el estado oral del paciente;
- navegar por la historia clínica dental;
- consultar tratamientos;
- registrar nuevos eventos;
- explicar el diagnóstico al paciente;

sin abandonar nunca el odontograma.

---

# Distribución General

La pantalla se divide en cuatro zonas claramente diferenciadas.

------------------------------------------------------------

Encabezado del Paciente

------------------------------------------------------------

Toolbar clínica

------------------------------------------------------------

Odontograma (70%)

Dental Inspector (30%)

------------------------------------------------------------

Timeline / Leyenda

------------------------------------------------------------

Nunca utilizar ventanas flotantes para funciones principales.

---

# Encabezado

Debe reutilizar el Expediente Clínico.

Mostrar únicamente:

- Nombre
- Documento
- Edad
- Sexo
- Estado
- Botón volver al expediente

Nunca duplicar información clínica.

---

# Toolbar Clínica

Debe ocupar una sola fila.

Contendrá únicamente acciones globales.

Ejemplo:

Guardar

Deshacer

Rehacer

Modo Paciente

Comparar

Timeline

Configuración

No incluir herramientas específicas de un diente.

Esas pertenecen al Dental Inspector.

---

# Área principal

Debe ocupar aproximadamente el 70% del ancho.

Aquí vive exclusivamente el odontograma.

No mostrar formularios.

No mostrar tablas.

No mostrar listas.

El odontograma debe ser el protagonista absoluto.

---

# Distribución de dientes

Mantener la nomenclatura FDI.

Mostrar claramente:

Dentición superior

Dentición inferior

Cuando existan dientes temporales:

Mostrar automáticamente la dentición correspondiente según la edad del paciente.

Permitir cambiar manualmente.

---

# Espaciado

Los dientes deberán respirar.

Nunca quedar pegados.

El odontólogo debe poder identificar rápidamente cada pieza.

---

# Dental Inspector

Siempre visible en escritorio.

Ocupa aproximadamente el 30% del ancho.

Nunca cubre el odontograma.

Nunca aparece como modal.

El panel cambia dinámicamente cuando cambia el diente seleccionado.

---

# Timeline

Ubicada en la parte inferior.

Horizontal.

Muy limpia.

Ejemplo:

Ingreso

──────●────────Hoy

Mover el control debe reconstruir automáticamente el estado del odontograma.

No abrir nuevas pantallas.

---

# Leyenda

Siempre visible.

Muy pequeña.

No competir con el odontograma.

Utilizar únicamente los colores oficiales DDS.

Ejemplo:

Rojo

Diagnóstico

Azul

Tratamiento realizado

Naranja

Tratamiento planificado

Gris

Observación

Verde

Elemento seleccionado

---

# Navegación

Click

Selecciona un diente.

Doble click

Centra la historia del diente.

Hover

Muestra información resumida.

Nunca abrir formularios automáticamente.

---

# Zoom

Permitir aumentar ligeramente el tamaño del odontograma.

No modificar la posición del Dental Inspector.

---

# Responsive

Desktop

Odontograma + Dental Inspector simultáneamente.

Tablet

Panel colapsable.

Mobile

Modo lectura.

No edición completa.

---

# Modo Paciente

Oculta:

- diagnósticos técnicos;
- códigos;
- nomenclaturas profesionales.

Muestra:

- fotografías;
- tratamientos;
- explicaciones simples.

Pensado para girar el monitor y explicar el tratamiento.

---

# Comparador

En versiones futuras.

Permite dividir la pantalla.

Izquierda:

Estado inicial.

Derecha:

Estado actual.

Las diferencias se resaltan automáticamente.

---

# Animaciones

Todas las transiciones:

150–200 ms.

Nunca más.

La sensación debe ser de rapidez.

---

# Accesibilidad

No depender únicamente del color.

Todos los estados importantes deberán poder distinguirse mediante:

- iconografía;
- patrones;
- forma;
- color.

---

# Rendimiento

El odontograma nunca debe redibujarse completamente cuando cambia un solo diente.

Solo se actualiza el componente afectado.

---

# Integraciones futuras

Este Workspace deberá permitir integrar sin rediseño:

- Fotografías clínicas.
- Radiografías.
- CBCT.
- Ortodoncia.
- Implantología.
- IA.
- Comparador histórico.
- Timeline.
- Firma sobre imágenes.

---

# Criterios de aceptación

✅ El odontograma es el protagonista absoluto de la pantalla.

✅ El Dental Inspector permanece siempre visible.

✅ Toda la navegación ocurre sin abandonar el Workspace.

✅ La información clínica se comprende rápidamente.

✅ El espacio transmite profesionalismo y tranquilidad.

✅ El odontólogo puede trabajar durante toda la consulta sin cambiar de módulo.

---

# Observación

DDS-003 define la organización completa del espacio de trabajo del odontograma.

DDS-001 define el componente Tooth.

DDS-002 define el Dental Inspector.

DDS-003 une ambos componentes y establece cómo conviven dentro del nuevo Odontograma Dentia 2.0.

A partir de este documento, cualquier nueva funcionalidad relacionada con odontología deberá respetar esta distribución.