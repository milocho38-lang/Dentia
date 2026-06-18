# D004C - Arquitectura Técnica
# Backend

Versión: 1.0

## Objetivo

Definir la arquitectura del Backend de la Plataforma de Gestión Odontológica.

El Backend será responsable de:

- Lógica de negocio.
- Seguridad.
- Autenticación.
- Autorización.
- Persistencia de datos.
- Generación de alertas.
- Auditoría.
- Integraciones futuras.
- Servicios de IA.

Será el núcleo operativo de toda la plataforma.

---

# 1. Tecnologías

## Framework Principal

```text
FastAPI
```

---

## Lenguaje

```text
Python 3.12+
```

---

## ORM

```text
SQLAlchemy
```

---

## Migraciones

```text
Alembic
```

---

## Validaciones

```text
Pydantic
```

---

## Autenticación

```text
JWT
```

---

## Hash de Contraseñas

```text
Argon2id
```

---

# 2. Arquitectura por Capas

La aplicación seguirá una arquitectura de capas.

```text
Router
    ↓
Service
    ↓
Repository
    ↓
Database
```

---

## Router

Responsable de:

- Recibir solicitudes HTTP.
- Validar entrada.
- Invocar servicios.
- Retornar respuestas.

No contendrá lógica de negocio.

---

## Service

Responsable de:

- Reglas de negocio.
- Validaciones operativas.
- Procesos clínicos.
- Procesos financieros.

Es la capa principal del sistema.

---

## Repository

Responsable de:

- Acceso a base de datos.
- Consultas.
- Inserciones.
- Actualizaciones.

---

## Database

Responsable de:

- Persistencia.

---

# 3. Estructura General

```text
backend/

├── app/
│
├── routers/
├── services/
├── repositories/
├── models/
├── schemas/
├── core/
├── database/
├── middleware/
├── utils/
├── jobs/
└── tests/
```

---

# 4. Carpeta Models

Contendrá entidades SQLAlchemy.

Ejemplos:

```text
patient.py
appointment.py
treatment.py
payment.py
```

---

## Ejemplo

```python
class Patient(Base):
    pass
```

---

# 5. Carpeta Schemas

Contendrá modelos Pydantic.

Ejemplos:

```text
patient_schema.py
appointment_schema.py
```

---

## Objetivo

Validar:

- Entradas.
- Salidas.
- Contratos API.

---

# 6. Carpeta Repositories

Responsable de acceso a datos.

Ejemplo:

```text
patient_repository.py
```

Funciones:

```python
create()
update()
delete()
get_by_id()
search()
```

---

# 7. Carpeta Services

Contiene la lógica de negocio.

Ejemplo:

```text
patient_service.py
appointment_service.py
payment_service.py
```

---

## Regla

Toda regla de negocio deberá estar aquí.

---

# 8. Carpeta Routers

Define los endpoints REST.

Ejemplo:

```text
patient_router.py
```

---

## Ejemplos de Endpoint

```http
GET    /patients
GET    /patients/{id}
POST   /patients
PUT    /patients/{id}
DELETE /patients/{id}
```

---

# 9. Carpeta Core

Configuración global.

Ejemplos:

```text
config.py
security.py
jwt.py
settings.py
```

---

# 10. Carpeta Middleware

Responsable de:

- Auditoría.
- Logging.
- Seguridad.
- Manejo de errores.

---

# 11. Carpeta Utils

Funciones auxiliares.

Ejemplos:

```text
date_utils.py
currency_utils.py
pdf_utils.py
```

---

# 12. Carpeta Jobs

Procesos automáticos.

Ejemplos:

```text
alert_job.py
followup_job.py
control_job.py
```

---

## Funciones

Generar:

- Alertas.
- Seguimientos.
- Procesos programados.

---

# 13. API REST

Todas las funcionalidades se expondrán mediante API REST.

---

## Formato

Entrada:

```json
{
  "name": "Juan Pérez"
}
```

Salida:

```json
{
  "success": true,
  "data": {}
}
```

---

# 14. Convención de Respuestas

Respuesta Exitosa

```json
{
  "success": true,
  "message": "Paciente creado",
  "data": {}
}
```

---

Respuesta Error

```json
{
  "success": false,
  "message": "Paciente ya existe"
}
```

---

# 15. Autenticación

Ingreso mediante:

```text
Correo
+
Contraseña
```

---

## Flujo

```text
Login
 ↓
Access Token JWT
 +
Refresh Token
 ↓
Frontend
 ↓
API
```

El Access Token tendrá una duración de 15 minutos.

El Refresh Token tendrá una duración máxima de 8 horas y expirará tras 60
minutos de inactividad.

---

# 16. Autorización

Basada en:

```text
Roles
Permisos
```

---

## Ejemplo

```text
Secretaria
  Puede:
    Crear Citas

  No Puede:
    Reversar Pagos
```

---

# 17. Auditoría

Toda acción crítica generará registro.

Ejemplos:

```text
Crear Paciente
Modificar Paciente
Registrar Pago
Reversar Pago
Cancelar Cita
```

---

## Información Registrada

```text
Usuario
Fecha
Hora
Acción
Entidad
ID Entidad
```

---

# 18. Validaciones Clínicas

Ejemplos:

---

## VC-001

No permitir evolución sin paciente.

---

## VC-002

No permitir evolución sin odontólogo.

---

## VC-003

No permitir cierre de tratamiento sin estado final.

---

## VC-004

No permitir finalizar tratamiento sin conformidad registrada.

---

# 19. Validaciones Financieras

## VF-001

No permitir pagos negativos.

---

## VF-002

No permitir reversión sin motivo.

---

## VF-003

Todo pago debe generar movimiento de caja.

---

## VF-004

No permitir eliminar pagos.

---

# 20. Alertas Automáticas

El backend será responsable de generar:

```text
Controles próximos
Controles vencidos
Presupuestos pendientes
Laboratorios pendientes
Stock bajo
```

---

## Frecuencia

Inicialmente:

```text
Diaria
```

---

# 21. Generación de PDF

El backend será responsable de generar:

```text
Consentimientos
Presupuestos
Cierres
Documentos Legales
```

---

## Librería Sugerida

```text
ReportLab
```

---

# 22. Gestión de Archivos

El backend administrará:

```text
Carga
Descarga
Visualización
Permisos
```

---

# 23. Integración WhatsApp

Versión MVP:

```text
Generación de mensajes
```

---

Versión futura:

```text
API WhatsApp Business
```

---

# 24. Preparación para IA

Se creará una capa independiente.

```text
ai_service.py
```

---

Funciones futuras:

```text
Generar Evolución
Generar WhatsApp
Resumir Paciente
```

---

## Regla

La aplicación debe funcionar sin IA.

---

# 25. Manejo de Errores

Toda excepción deberá registrarse.

---

## Logs

Información mínima:

```text
Fecha
Usuario
Error
Módulo
Detalle
```

---

# 26. Pruebas

Cada módulo deberá incluir pruebas.

---

## Mínimo

```text
Services
Endpoints
Validaciones
```

---

# 27. Preparación SaaS

Desde el MVP todo acceso deberá filtrarse por:

```text
empresa_id
```

---

## Objetivo

Garantizar aislamiento de datos entre empresas.

---

# 28. Resultado Esperado

Backend:

- Escalable.
- Seguro.
- Multiempresa.
- Preparado para SaaS.
- Preparado para IA.
- Fácil de mantener.
- Compatible con desarrollo asistido por Codex.
