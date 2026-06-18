# D001 - Arquitectura Funcional

Versión: 1.0

## Objetivo del Producto

Desarrollar una plataforma integral para odontólogos independientes, consultorios odontológicos y clínicas odontológicas que permita gestionar la operación clínica, administrativa y financiera desde una única herramienta.

La plataforma deberá facilitar el trabajo diario de odontólogos y secretarias mediante una interfaz simple, intuitiva y orientada a la productividad.

El sistema deberá ser escalable para operar inicialmente de forma local y posteriormente evolucionar a un modelo SaaS multiempresa.

---

# Tipos de Clientes

## Odontólogo Independiente

Profesional que atiende sin secretaria o con apoyo administrativo limitado.

Características:

* Puede atender en una o varias sedes.
* Puede desempeñar simultáneamente funciones clínicas y administrativas.
* Requiere agenda, historia clínica, tratamientos y control financiero.

---

## Consultorio Odontológico

Consultorio con uno o varios odontólogos y personal administrativo.

Características:

* Agenda compartida.
* Gestión de pacientes.
* Control financiero.
* Seguimiento de tratamientos.
* Comunicación con pacientes.

---

## Clínica Odontológica

Organización con múltiples especialidades y varios profesionales.

Características:

* Gestión multiusuario.
* Gestión multisede.
* Seguimiento integral de pacientes.
* Indicadores financieros y operativos.

---

# Especialidades Soportadas

La plataforma deberá soportar inicialmente:

* Odontología General
* Ortodoncia
* Endodoncia
* Periodoncia
* Cirugía Oral
* Implantología
* Rehabilitación Oral
* Odontopediatría
* Estética Dental
* Higiene Oral

El sistema deberá permitir agregar nuevas especialidades sin modificar el código.

---

# Roles del Sistema

## Administrador

Responsable de la configuración general.

Funciones:

* Configuración de empresa.
* Gestión de usuarios.
* Gestión de sedes.
* Reportes.
* Configuración general.

---

## Secretaria

Responsable de la operación administrativa.

Funciones:

* Agenda.
* Pacientes.
* Presupuestos.
* Pagos.
* Seguimiento.
* WhatsApp.

---

## Odontólogo

Responsable de la operación clínica.

Funciones:

* Historia clínica.
* Evoluciones.
* Odontograma.
* Tratamientos.
* Documentos clínicos.

---

## Odontólogo Administrador

Perfil orientado a odontólogos que trabajan sin secretaria.

Funciones:

* Agenda.
* Pacientes.
* Historia clínica.
* Presupuestos.
* Tratamientos.
* Pagos.
* Reportes.
* Configuración básica.

---

# Flujo General del Paciente

## Etapa 1 - Captación

1. Paciente solicita cita.
2. Secretaria u odontólogo registra paciente.
3. Se agenda valoración inicial.

---

## Etapa 2 - Valoración

1. Paciente asiste.
2. Se diligencia historia clínica.
3. Se registra odontograma.
4. Se establece diagnóstico.

---

## Etapa 3 - Presupuesto

1. Se genera presupuesto.
2. Se presenta al paciente.
3. El paciente acepta o rechaza.
4. Si no responde, se generan alertas de seguimiento.

---

## Etapa 4 - Tratamiento

1. Se crea tratamiento.
2. Se registran anticipos.
3. Se programan citas.
4. Se registran evoluciones.
5. Se registran pagos.
6. Se realizan controles.

---

## Etapa 5 - Laboratorio

Cuando aplique:

1. Se genera orden de laboratorio.
2. Se registra fecha estimada.
3. Se realizan seguimientos.
4. Se recibe trabajo.
5. Se cita nuevamente al paciente.

---

## Etapa 6 - Finalización

1. Se completa el tratamiento.
2. Se registran evidencias.
3. Se genera documento de cierre.
4. El paciente registra conformidad.
5. Se programa control futuro.

---

# Módulos Principales

## Dashboard

Visualización de:

* Citas del día.
* Pacientes pendientes.
* Alertas.
* Tratamientos activos.
* Ingresos diarios.

---

## Agenda

Funciones:

* Vista diaria.
* Vista semanal.
* Vista mensual.
* Filtros por odontólogo.
* Filtros por sede.
* Confirmación de citas.
* Reprogramaciones.
* Sobrecupos controlados.

---

## Pacientes

Funciones:

* Registro.
* Actualización.
* Historial.
* Información de contacto.
* Responsables para menores.

---

## Historia Clínica

Funciones:

* Antecedentes.
* Alergias.
* Medicamentos.
* Diagnósticos.
* Evoluciones.

---

## Odontograma

Funciones:

* Registro por pieza dental.
* Estado actual.
* Historial de procedimientos.
* Seguimiento clínico.

---

## Presupuestos

Funciones:

* Generación.
* Conversión a tratamiento.
* Seguimiento comercial.
* Alertas de seguimiento.

---

## Tratamientos

Funciones:

* Planes de tratamiento.
* Etapas.
* Evoluciones.
* Control financiero.
* Estado de avance.

---

## Pagos y Caja

Funciones:

* Valoración inicial.
* Anticipos.
* Abonos.
* Pago total.
* Caja diaria.
* Cartera.

---

## Laboratorios

Funciones:

* Órdenes de laboratorio.
* Seguimientos.
* Costos.
* Facturas pendientes.
* Alertas.

---

## Inventario Básico

Funciones:

* Insumos odontológicos.
* Entradas.
* Salidas.
* Stock mínimo.
* Alertas.

---

## Archivos Clínicos

Funciones:

* Fotografías.
* Radiografías.
* PDFs.
* Documentos clínicos.

Repositorio ilimitado por paciente.

---

## Documentos Legales

Funciones:

* Consentimientos informados.
* Protección de datos.
* Autorizaciones de menores.
* Presupuestos aceptados.
* Cierre de tratamiento.
* Conformidad del paciente.

---

## Alertas y Seguimiento

Alertas para:

* Controles periódicos.
* Profilaxis semestral.
* Tratamientos sin próxima cita.
* Presupuestos sin respuesta.
* Laboratorios pendientes.
* Stock bajo.
* Saldos pendientes.

---

## WhatsApp

Funciones:

* Confirmación de citas.
* Recordatorios.
* Seguimiento de presupuestos.
* Seguimiento de tratamientos.
* Cobro de saldos.
* Programación de controles.

---

## Reportes

Funciones:

* Ingresos.
* Cartera.
* Pacientes nuevos.
* Tratamientos activos.
* Laboratorios.
* Inventario.

---

## Inteligencia Artificial (Fase Futura)

La plataforma deberá quedar preparada para:

* Redacción de evoluciones clínicas.
* Generación de mensajes de WhatsApp.
* Resumen de pacientes.
* Alertas inteligentes.

La operación normal del sistema no dependerá de IA.

---

# Arquitectura Tecnológica

Frontend:

* Next.js
* React
* TypeScript

Backend:

* FastAPI
* SQLAlchemy

Base de Datos:

* PostgreSQL

Despliegue Inicial:

* Local

Despliegue Futuro:

* SaaS Multiempresa

---

# Alcance Inicial

Incluye:

* Agenda
* Pacientes
* Historia clínica
* Odontograma
* Presupuestos
* Tratamientos
* Pagos
* Caja
* Laboratorios
* Inventario básico
* Archivos clínicos
* Documentos legales
* Alertas
* WhatsApp
* Reportes

No incluye inicialmente:

* Facturación electrónica.
* Portal del paciente.
* Comisiones por odontólogo.
* Gestión por sillones.
