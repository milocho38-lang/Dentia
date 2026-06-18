# D004E - Arquitectura Técnica
# Seguridad, Despliegue y SaaS

Versión: 1.0

## Objetivo

Definir la estrategia de:

- Seguridad.
- Autenticación.
- Autorización.
- Despliegue local.
- Despliegue futuro en nube.
- Arquitectura SaaS.
- Escalabilidad.
- Monitoreo.
- Continuidad operativa.

---

# 1. Principios de Seguridad

## AS-001

Toda operación requerirá usuario autenticado.

---

## AS-002

Ninguna pantalla operativa será pública.

---

## AS-003

Todo acceso a información deberá validar:

```text
Usuario
Rol
Permisos
Empresa
```

---

## AS-004

Los datos de una empresa nunca podrán ser visibles para otra empresa.

---

# 2. Autenticación

## Método Oficial

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
JWT
 ↓
Frontend
 ↓
API
```

---

## Proceso

1. Usuario inicia sesión.
2. Backend valida credenciales.
3. Backend crea una sesión.
4. Backend genera Access Token JWT.
5. Backend entrega Refresh Token mediante cookie HttpOnly.
6. Frontend mantiene el Access Token en memoria.
7. Cada solicitud protegida incluye el Access Token.

---

# 3. JWT

Información mínima:

```json
{
  "sub": "",
  "sid": "",
  "empresa_id": "",
  "sede_id": "",
  "roles": []
}
```

---

## Duración Inicial

```text
15 minutos
```

---

## Renovación

El Refresh Token se implementará desde C005.

Duración máxima:

```text
8 horas
```

Expiración por inactividad:

```text
60 minutos
```

---

# 4. Contraseñas

Nunca se almacenarán en texto plano.

---

## Hash

```text
Argon2id
```

---

## Restricciones Iniciales

Reglas:

* Mínimo 12 caracteres.
* Permitir espacios y Unicode.
* No exigir combinaciones artificiales.
* No forzar cambios periódicos.

---

# 5. Autorización

Basada en:

```text
Roles
+
Permisos
```

---

## Ejemplo

Secretaria:

```text
Puede:
- Crear pacientes
- Crear citas
- Registrar pagos

No puede:
- Reversar pagos
- Administrar usuarios
```

---

# 6. Seguridad API

Toda API deberá validar:

```text
JWT válido
Usuario activo
Empresa válida
Permisos válidos
```

---

## Regla

Ningún endpoint deberá confiar en información enviada por el frontend.

---

# 7. Seguridad de Archivos

El acceso a archivos deberá realizarse únicamente mediante Backend.

---

## Prohibido

```text
URL pública directa
```

---

## Obligatorio

Validar:

```text
Usuario
Empresa
Permisos
Paciente
```

---

# 8. Auditoría

Toda acción crítica deberá registrarse.

---

## Acciones Mínimas

```text
Login
Logout
Crear Paciente
Modificar Paciente
Crear Cita
Cancelar Cita
Registrar Pago
Reversar Pago
Finalizar Tratamiento
Generar Documento
```

---

# 9. Manejo de Sesiones

Cuando un usuario sea deshabilitado:

```text
No podrá ingresar nuevamente
```

---

## Sesiones activas

Se implementarán desde C005.

El sistema permitirá múltiples sesiones simultáneas y revocación individual o
global.

La sede activa podrá cambiarse sin nueva autenticación y generará un nuevo
Access Token.

---

# 10. Manejo de Errores

El usuario no deberá visualizar errores técnicos.

---

## Correcto

```text
No fue posible guardar el paciente.
```

---

## Incorrecto

```text
SQLAlchemyException...
```

---

# 11. Variables de Entorno

Toda configuración sensible deberá almacenarse fuera del código.

---

## Ejemplos

```text
DATABASE_URL
JWT_SECRET
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_HOURS
SESSION_IDLE_TIMEOUT_MINUTES
STORAGE_PATH
OPENAI_API_KEY
```

---

# 12. Configuración Local

Versión MVP.

---

## Componentes

```text
Frontend
Backend
PostgreSQL
Storage
```

Todo en el mismo equipo.

---

## Diagrama

```text
PC Usuario

├── Frontend
├── Backend
├── PostgreSQL
└── Storage
```

---

# 13. Instalación Local

Objetivo:

Permitir instalación sencilla.

---

## Componentes

```text
Python
Node.js
PostgreSQL
```

---

## Futuro

Instalador automático.

---

# 14. Preparación para Docker

La arquitectura deberá permitir contenerización.

---

## Contenedores futuros

```text
Frontend
Backend
PostgreSQL
```

---

# 15. Arquitectura SaaS Futura

Versión futura.

---

## Diagrama

```text
Internet
     │
     ▼

Frontend Cloud
     │
     ▼

Backend Cloud
     │
     ▼

PostgreSQL Cloud
     │
     ▼

Storage Cloud
```

---

# 16. Multiempresa SaaS

Toda empresa tendrá:

```text
empresa_id
```

como mecanismo principal de aislamiento.

---

## Objetivo

Evitar mezcla de información entre clientes.

---

# 17. Escalabilidad

La arquitectura deberá soportar:

```text
1 Empresa
10 Empresas
100 Empresas
1000 Empresas
```

sin rediseño.

---

# 18. Backups

Se deberán respaldar:

```text
Base de Datos
Archivos
Configuración
```

---

## Frecuencia Recomendada

```text
Diaria
```

---

# 19. Recuperación

La restauración deberá permitir:

1. Restaurar base de datos.
2. Restaurar storage.
3. Recuperar operación completa.

---

# 20. Monitoreo Futuro

Preparar integración con:

```text
Logs
Alertas
Métricas
```

---

## Opciones futuras

```text
Grafana
Prometheus
Sentry
```

---

# 21. Integración IA

La IA será opcional.

---

## Arquitectura

```text
Frontend
    │
Backend
    │
AI Service
    │
Proveedor IA
```

---

## Proveedores posibles

```text
OpenAI
Anthropic
Google
```

---

## Regla

Si la IA falla:

```text
La aplicación continúa operando.
```

---

# 22. WhatsApp Futuro

Arquitectura prevista:

```text
Backend
    │
WhatsApp Business API
```

---

## MVP

Solo generación de mensajes.

---

# 23. Escalabilidad de Archivos

Versión Inicial:

```text
Disco Local
```

---

Versión futura:

```text
S3
MinIO
Google Cloud Storage
```

---

# 24. Alta Disponibilidad (Futuro)

Para SaaS se considerará:

```text
Balanceadores
Replicación
Backups automáticos
```

---

# 25. Estrategia de Desarrollo

Desarrollo incremental.

---

## Regla

No avanzar al siguiente módulo hasta:

```text
Compila
Prueba funcional
No rompe módulos existentes
Documentación actualizada
```

---

# 26. Estrategia de Versionamiento

Control de código:

```text
Git
GitHub
```

---

## Convención Inicial

```text
main
develop
feature/*
```

---

# 27. Seguridad Legal

La plataforma deberá facilitar cumplimiento de:

- Protección de datos.
- Consentimientos.
- Trazabilidad clínica.
- Auditoría operativa.

La responsabilidad legal final continuará siendo del consultorio o profesional.

---

# 28. Objetivo SaaS Final

Permitir que múltiples consultorios utilicen la misma plataforma desde internet con:

```text
Aislamiento
Seguridad
Escalabilidad
Backups
Auditoría
```

---

# 29. Resultado Esperado

La arquitectura deberá ser:

- Segura.
- Escalable.
- Multiempresa.
- Preparada para nube.
- Preparada para SaaS.
- Preparada para IA.
- Fácil de mantener.
- Fácil de desplegar.

---

# Resumen D004

El documento D004 queda conformado por:

```text
D004A
Arquitectura General

D004B
Frontend

D004C
Backend

D004D
Base de Datos y Archivos

D004E
Seguridad, Despliegue y SaaS
```

Estos documentos constituyen la arquitectura técnica oficial v1.0 de la Plataforma de Gestión Odontológica.
