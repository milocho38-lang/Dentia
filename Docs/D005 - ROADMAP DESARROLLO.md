# D005 - Roadmap de Desarrollo

Versión: 1.0

## Objetivo

Definir el orden oficial de construcción de la Plataforma de Gestión Odontológica.

Este roadmap tiene como propósito:

- Guiar el trabajo de Codex.
- Evitar desarrollos fuera de orden.
- Reducir retrabajos.
- Garantizar estabilidad.
- Construir un MVP funcional lo antes posible.

---

# 1. Estrategia General

La plataforma se desarrollará por fases.

Cada fase deberá:

- Funcionar completamente.
- Ser probada.
- Mantener compatibilidad con fases anteriores.
- Tener documentación actualizada.

---

## Regla Principal

No iniciar una fase nueva hasta que la fase actual esté:

```text
Implementada
Probada
Aprobada
```

---

# 2. MVP Objetivo

El MVP deberá permitir operar un consultorio odontológico real.

---

## Debe incluir

- Usuarios.
- Pacientes.
- Agenda.
- Historia clínica.
- Odontograma.
- Presupuestos.
- Tratamientos.
- Pagos.
- Caja.
- Consentimiento informado.
- Protección de datos.

---

## No requiere inicialmente

- Inventario.
- Laboratorios.
- IA.
- SaaS.
- WhatsApp Business.
- Nube.

---

# FASE 0
# Preparación del Proyecto

---

## C001 - Crear estructura del proyecto

Objetivo:

Crear estructura base:

```text
frontend/
backend/
database/
storage/
docs/
scripts/
```

---

## C002 - Configurar Backend

Objetivo:

Crear proyecto FastAPI.

Incluye:

- Configuración inicial.
- Variables de entorno.
- Estructura de carpetas.

Resultado:

```text
localhost:8000
```

funcionando.

---

## C003 - Configurar Frontend

Objetivo:

Crear proyecto Next.js.

Incluye:

- TypeScript.
- Tailwind.
- Layout inicial.

Resultado:

```text
localhost:3000
```

funcionando.

---

## C004 - Configurar PostgreSQL

Objetivo:

Conexión base de datos.

Incluye:

- SQLAlchemy.
- Alembic.
- UUID.

Resultado:

Base conectada.

---

# FASE 1
# Seguridad y Configuración

---

## C005 - Login

Incluye:

- Usuario.
- Contraseña.
- JWT.

---

## C006 - Roles

Incluye:

- Administrador.
- Secretaria.
- Odontólogo.
- Odontólogo Administrador.

---

## C007 - Permisos

Incluye:

- Crear.
- Editar.
- Consultar.
- Eliminar lógico.

---

## C008 - Empresas

Incluye:

- Datos empresa.
- Configuración básica.

---

## C009 - Sedes

Incluye:

- Crear.
- Editar.
- Activar.
- Inactivar.

---

## C010 - Odontólogos

Incluye:

- Especialidades.
- Sedes.
- Estado.

---

# FASE 2
# Pacientes

---

## C011 - Pacientes

Incluye:

- Crear.
- Editar.
- Consultar.
- Buscar.

---

## C012 - Responsables

Incluye:

- Menores de edad.
- Responsables legales.

---

## C013 - Expediente del Paciente

Incluye:

- Datos generales.
- Historial.
- Accesos rápidos.

---

# FASE 3
# Agenda

---

## C014 - Tipos de Cita

Incluye:

- Configuración.
- Duración.
- Sobrecupo permitido.

---

## C015 - Agenda

Incluye:

- Vista diaria.
- Vista semanal.
- Vista mensual.

---

## C016 - Programación

Incluye:

- Crear cita.
- Editar cita.
- Reprogramar.

---

## C017 - Sobrecupos

Incluye:

- Advertencia.
- Confirmación.
- Marcación visual.

---

## C018 - Confirmaciones

Incluye:

- WhatsApp.
- Llamada.
- Presencial.

---

# FASE 4
# Historia Clínica

---

## C019 - Historia Clínica

Incluye:

- Antecedentes.
- Alergias.
- Medicamentos.

---

## C020 - Evoluciones

Incluye:

- Crear.
- Corregir.
- Historial.

---

## C021 - Auditoría Clínica

Incluye:

- Trazabilidad.
- Correcciones.

---

# FASE 5
# Odontograma

---

## C022 - Motor Odontograma

Incluye:

- Piezas.
- Estados.
- Eventos.

---

## C023 - Interfaz Visual

Incluye:

- Selección interactiva.
- Visualización clínica.

---

## C024 - Historial

Incluye:

- Evolución por pieza.

---

# FASE 6
# Presupuestos

---

## C025 - Procedimientos

Incluye:

- Catálogo.
- Especialidades.

---

## C026 - Presupuestos

Incluye:

- Crear.
- PDF.
- Seguimiento.

---

## C027 - Seguimiento Comercial

Incluye:

- Contactos.
- Historial.
- Alertas.

---

## C028 - Conversión a Tratamiento

Incluye:

- Aceptación.
- Creación automática.

---

# FASE 7
# Tratamientos

---

## C029 - Tratamientos

Incluye:

- Estados.
- Avance.
- Costos.

---

## C030 - Etapas

Incluye:

- Planeación.
- Ejecución.

---

## C031 - Procedimientos

Incluye:

- Seguimiento.
- Ejecución.

---

## C032 - Cierre

Incluye:

- Resumen.
- Estado final.

---

## C033 - Conformidad

Incluye:

- Firma.
- Observaciones.
- Evidencia.

---

## C033A - Consentimiento Informado MVP

Incluye:

- Generación básica.
- Registro de aceptación.
- Evidencia adjunta o firma simple.

No incluye firma electrónica certificada.

---

## C033B - Protección de Datos MVP

Incluye:

- Generación básica.
- Registro de aceptación.
- Evidencia adjunta o firma simple.

No incluye firma electrónica certificada.

---

# FASE 8
# Pagos y Caja

---

## C034 - Pagos

Incluye:

- Valoración.
- Anticipos.
- Abonos.

---

## C035 - Cartera

Incluye:

- Saldos.
- Pendientes.

---

## C036 - Caja

Incluye:

- Ingresos.
- Movimientos.

---

## C037 - Cierre Diario

Incluye:

- Consolidado.
- Observaciones.

---

## C038 - Reversiones

Incluye:

- Auditoría.
- Motivos.

---

# MVP COMPLETADO

Al finalizar C038 la aplicación ya podrá operar un consultorio real.

---

# FASE 9
# Laboratorios

---

## C039 - Laboratorios

---

## C040 - Órdenes

---

## C041 - Seguimientos

---

## C042 - Alertas

---

## C043 - Cita de Entrega

---

# FASE 10
# Archivos y Documentos Legales Avanzados

---

## C044 - Repositorio de Archivos

---

## C045 - Radiografías

---

## C046 - Fotografías

---

## C047 - Documentos Legales Avanzados

---

## C047A - Consentimientos Avanzados

Incluye:

- Versionamiento documental.
- Flujos avanzados de firma.
- Gestión avanzada de plantillas.

No reemplaza el consentimiento informado básico incluido en el MVP.

---

## C048 - Protección de Datos Avanzada

Incluye:

- Versionamiento documental.
- Flujos avanzados de firma.
- Gestión avanzada de plantillas.

No reemplaza la protección de datos básica incluida en el MVP.

---

## C049 - Cierre de Tratamiento

---

# FASE 11
# Inventario

---

## C050 - Insumos

---

## C051 - Movimientos

---

## C052 - Stock Mínimo

---

## C053 - Alertas

---

# FASE 12
# Alertas Operativas

---

## C054 - Motor de Alertas

---

## C055 - Controles Periódicos

---

## C056 - Presupuestos Sin Respuesta

---

## C057 - Tratamientos Sin Próxima Cita

---

## C058 - Dashboard de Alertas

---

# FASE 13
# Comunicaciones

---

## C059 - Plantillas

---

## C060 - WhatsApp Manual

---

## C061 - Historial Comunicaciones

---

# FASE 14
# Reportes

---

## C062 - Dashboard Ejecutivo

---

## C063 - Reportes Financieros

---

## C064 - Reportes Clínicos

---

## C065 - Reportes Operativos

---

# FASE 15
# Inteligencia Artificial

---

## C066 - Infraestructura IA

---

## C067 - Generador de Evoluciones

---

## C068 - Resumen Paciente

---

## C069 - WhatsApp Inteligente

---

## C070 - Alertas Inteligentes

---

# FASE 16
# SaaS

---

## C071 - Docker

---

## C072 - Storage Cloud

---

## C073 - PostgreSQL Cloud

---

## C074 - Multiempresa SaaS

---

## C075 - Despliegue Producción

---

# Prioridad Real del Proyecto

La prioridad práctica será:

```text
Fase 0
Fase 1
Fase 2
Fase 3
Fase 4
Fase 5
Fase 6
Fase 7
Fase 8
```

Es decir:

```text
C001 a C038
```

Ese conjunto constituye el MVP oficial.

---

# Regla para Codex

Codex deberá:

1. Implementar un módulo a la vez.
2. No avanzar sin aprobación.
3. No modificar módulos ya aprobados sin justificación.
4. Entregar:
   - Archivos modificados.
   - Tablas creadas.
   - Pruebas realizadas.
   - Pasos de validación.

---

# Resultado Esperado

Al finalizar el roadmap completo se obtendrá una plataforma:

- Multiempresa.
- Multiusuario.
- Escalable.
- Preparada para SaaS.
- Preparada para IA.
- Orientada a odontólogos y secretarias.
- Comercializable como producto de software.
