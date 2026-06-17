# AGENTS.md

# Proyecto

Plataforma de Gestión Odontológica

---

# Objetivo General

Desarrollar una plataforma integral para odontólogos independientes, consultorios odontológicos y clínicas odontológicas.

El sistema deberá gestionar:

* Pacientes
* Agenda
* Historia clínica
* Odontograma
* Presupuestos
* Tratamientos
* Pagos
* Caja
* Laboratorios
* Inventario básico
* Documentos legales
* Alertas
* WhatsApp
* Reportes
* IA futura

---

# Documentación de Referencia

Antes de realizar cualquier modificación, leer:

1. docs/D001_ARQUITECTURA_FUNCIONAL.md
2. docs/D002_REGLAS_NEGOCIO.md
3. docs/D002A_CASOS_USO.md
4. docs/D003_MODELO_DATOS.md
5. docs/D004_ARQUITECTURA_TECNICA.md
6. docs/D005_ROADMAP.md

Las decisiones de desarrollo deben respetar dichos documentos.

---

# Arquitectura Tecnológica

Frontend:

* Next.js
* React
* TypeScript
* Tailwind CSS

Backend:

* FastAPI
* SQLAlchemy
* Alembic
* Pydantic

Base de Datos:

* PostgreSQL

---

# Convenciones de Desarrollo

## Idioma

Código:

* Inglés

Interfaz de Usuario:

* Español

Ejemplo:

Clase:

Patient

Pantalla:

Paciente

---

## Base de Datos

Toda tabla principal deberá incluir:

* id
* created_at
* updated_at
* created_by
* is_active

Cuando aplique:

* empresa_id
* sede_id

---

## Convención de Archivos

Modelos:

patient.py

Schemas:

patient_schema.py

Servicios:

patient_service.py

Endpoints:

patient_router.py

---

## Frontend

Páginas:

app/pacientes

Componentes:

components/pacientes

Servicios API:

services/patientService.ts

---

# Principios de Desarrollo

1. No duplicar lógica de negocio en frontend.
2. Las validaciones críticas deben ejecutarse en backend.
3. Toda operación financiera debe quedar auditada.
4. Ninguna información clínica debe eliminarse físicamente.
5. Toda modificación crítica debe generar auditoría.
6. Todo desarrollo debe ser compatible con multiempresa.
7. El sistema debe funcionar inicialmente en entorno local.
8. La arquitectura debe permitir futura migración SaaS.

---

# Flujo de Trabajo

Antes de programar:

1. Analizar documentos.
2. Identificar impacto.
3. Proponer plan.

Durante el desarrollo:

1. Implementar módulo solicitado.
2. Mantener compatibilidad con módulos existentes.
3. No modificar módulos no relacionados sin justificación.

Después del desarrollo:

1. Explicar cambios realizados.
2. Indicar archivos modificados.
3. Indicar tablas nuevas si aplica.
4. Indicar pasos de prueba.

---

# Roadmap

Seguir estrictamente el orden definido en:

docs/D005_ROADMAP.md

No avanzar a módulos posteriores sin aprobación.

---

# Restricciones

No implementar:

* Facturación electrónica.
* Portal del paciente.
* Comisiones por odontólogo.
* Gestión de sillones.

A menos que exista una instrucción explícita posterior.

---

# Preparación para IA

La arquitectura debe permitir futuras funciones:

* Redacción de evoluciones.
* Generación de WhatsApp.
* Resumen de pacientes.
* Alertas inteligentes.

Sin depender de IA para la operación normal del sistema.

---

# Regla Principal

Priorizar siempre:

1. Estabilidad.
2. Simplicidad.
3. Facilidad de uso para odontólogos y secretarias.
4. Escalabilidad futura.
