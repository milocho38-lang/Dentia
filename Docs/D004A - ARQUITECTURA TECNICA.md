# D004A - Arquitectura Técnica
# Arquitectura General

Versión: 1.0

## Objetivo

Definir la arquitectura técnica oficial de la Plataforma de Gestión Odontológica, estableciendo los principios, tecnologías, estructura general y lineamientos que deberán respetarse durante todo el desarrollo.

La arquitectura deberá permitir:

- Operación local inicial.
- Escalabilidad futura.
- Multiempresa.
- Multiusuario.
- Integración futura con IA.
- Migración futura a modelo SaaS.

---

# 1. Principios Arquitectónicos

## AT-001 - Separación de Responsabilidades

La solución estará dividida en:

- Frontend
- Backend
- Base de Datos
- Almacenamiento de Archivos

Cada componente tendrá responsabilidades claramente definidas.

---

## AT-002 - Frontend Desacoplado

El Frontend no accederá directamente a la base de datos.

Toda interacción deberá realizarse mediante API REST del Backend.

---

## AT-003 - Backend Centralizado

Toda lógica de negocio deberá ejecutarse en Backend.

Ejemplos:

- Validaciones clínicas.
- Validaciones financieras.
- Cálculo de cartera.
- Generación de alertas.
- Gestión de permisos.
- Auditoría.

---

## AT-004 - Escalabilidad

La arquitectura deberá soportar crecimiento sin rediseños estructurales.

Ejemplos:

- Más usuarios.
- Más pacientes.
- Más sedes.
- Más empresas.

---

## AT-005 - Multiempresa

Desde la primera versión el sistema deberá estar preparado para operar múltiples empresas.

Cada empresa tendrá acceso únicamente a su propia información.

---

## AT-006 - Preparación SaaS

Aunque inicialmente funcionará de forma local, la arquitectura deberá permitir migración futura a SaaS sin reconstrucción completa.

---

# 2. Arquitectura General

## Diagrama Conceptual

```text
┌─────────────────────┐
│      Frontend       │
│      Next.js        │
└──────────┬──────────┘
           │
           │ API REST
           ▼
┌─────────────────────┐
│      Backend        │
│      FastAPI        │
└──────────┬──────────┘
           │
 ┌─────────┴─────────┐
 ▼                   ▼

PostgreSQL       Storage
(Base Datos)     (Archivos)
```

---

# 3. Stack Tecnológico Oficial

## Frontend

Tecnologías seleccionadas:

- Next.js
- React
- TypeScript
- Tailwind CSS

Motivos:

- Excelente experiencia de usuario.
- Escalabilidad.
- Amplia comunidad.
- Compatibilidad con SaaS.

---

## Backend

Tecnologías seleccionadas:

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

Motivos:

- Alto rendimiento.
- Facilidad de mantenimiento.
- Excelente integración con IA futura.
- Productividad de desarrollo.

---

## Base de Datos

Motor seleccionado:

- PostgreSQL

Motivos:

- Estabilidad.
- Escalabilidad.
- Compatibilidad SaaS.
- Excelente soporte para relaciones complejas.

---

## Almacenamiento de Archivos

Versión Inicial:

- Sistema de archivos local.

Versiones Futuras:

- Amazon S3.
- MinIO.
- Google Cloud Storage.

---

# 4. Estructura General del Proyecto

```text
odontologia-app/

├── frontend/
├── backend/
├── database/
├── storage/
├── docs/
├── scripts/
└── README.md
```

---

# 5. Flujo General de Datos

## Caso: Crear Paciente

```text
Usuario
    │
    ▼
Frontend
    │
    ▼
API REST
    │
    ▼
Backend
    │
    ▼
Base de Datos
    │
    ▼
Respuesta
    │
    ▼
Frontend
```

---

# 6. Estrategia Multiempresa

Todas las entidades operativas deberán incluir:

```text
empresa_id
```

Ejemplos:

- Pacientes
- Citas
- Presupuestos
- Tratamientos
- Pagos
- Alertas
- Documentos

---

## Restricción

Un usuario únicamente podrá acceder a registros pertenecientes a su empresa.

---

# 7. Estrategia Multiusuario

El sistema deberá soportar:

- Un odontólogo independiente.
- Consultorios pequeños.
- Clínicas con múltiples usuarios.

Sin cambios en la arquitectura.

---

# 8. Convenciones Generales

## Idioma del Código

Todo el código deberá escribirse en inglés.

Ejemplos:

```python
Patient
Appointment
Treatment
Payment
```

---

## Idioma de la Interfaz

Toda la interfaz deberá mostrarse en español.

Ejemplos:

```text
Paciente
Cita
Tratamiento
Pago
```

---

# 9. Identificadores

Todas las tablas utilizarán:

```text
UUID
```

como llave primaria.

Ejemplo:

```text
550e8400-e29b-41d4-a716-446655440000
```

---

# 10. Auditoría Estándar

Toda tabla principal deberá incluir:

```text
id
created_at
updated_at
created_by
is_active
```

---

# 11. Política de Eliminación

No se permitirán eliminaciones físicas.

Los registros deberán desactivarse mediante:

```text
is_active = false
```

---

# 12. Entorno de Desarrollo Inicial

Configuración estándar:

```text
Frontend   : localhost:3000
Backend    : localhost:8000
PostgreSQL : localhost:5432
```

---

# 13. Objetivo del MVP

La primera versión deberá operar completamente en un computador local.

No se requiere infraestructura cloud para el MVP.

---

# 14. Preparación para Inteligencia Artificial

La arquitectura deberá permitir incorporar posteriormente:

- Redacción de evoluciones.
- Resumen de pacientes.
- Generación de WhatsApp.
- Alertas inteligentes.

La aplicación deberá funcionar completamente incluso si el módulo IA no está disponible.

---

# 15. Resultado Esperado

La arquitectura deberá proporcionar:

- Estabilidad.
- Escalabilidad.
- Facilidad de mantenimiento.
- Compatibilidad SaaS.
- Compatibilidad con IA.
- Desarrollo eficiente con Codex.