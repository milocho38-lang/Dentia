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

1. DOCS/D001 - ARQUITECTURA FUNCIONAL.md
2. DOCS/D002 - REGLAS DE NEGOCIO.md
3. DOCS/D002A - CASOS DE USO OPERATIVOS.md
4. DOCS/D003A - MODELO DATOS.md
5. DOCS/D003B - MODELO DATOS.md
6. DOCS/D003C - MODELO DATOS.md
7. DOCS/D003D - MODELO DATOS.md
8. DOCS/D003E - MODELO DATOS.md
9. DOCS/D004A - ARQUITECTURA TECNICA.md
10. DOCS/D004B - ARQUITECTURA TECNICA.md
11. DOCS/D004C - ARQUITECTURA TECNICA.md
12. DOCS/D004D - ARQUITECTURA TECNICA.md
13. DOCS/D004E - ARQUITECTURA TECNICA.md
14. DOCS/D005 - ROADMAP DESARROLLO.md
15. DOCS/D006 - IDENTIDAD VISUAL.md
16. DOCS/D007 - SEGURIDAD Y AUTENTICACION.md
17. DOCS/HISTORIAL_DECISIONES.md

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

DOCS/D005 - ROADMAP DESARROLLO.md

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
