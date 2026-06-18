# D003E - Modelo de Datos

# Alertas, Comunicaciones, IA, Auditoría y Configuración

Versión: 1.0

## Objetivo

Definir las entidades relacionadas con:

* Alertas operativas.
* Comunicaciones con pacientes.
* WhatsApp.
* Inteligencia Artificial.
* Auditoría.
* Configuración global.

Este bloque soporta la operación diaria, seguimiento y crecimiento futuro del sistema.

---

# 1. Alertas

## Tabla: alertas

Almacena todas las alertas generadas por el sistema.

### Campos

| Campo                  | Tipo          |
| ---------------------- | ------------- |
| id                     | UUID          |
| empresa_id             | UUID          |
| paciente_id            | UUID NULL     |
| cita_id                | UUID NULL     |
| tratamiento_id         | UUID NULL     |
| presupuesto_id         | UUID NULL     |
| orden_laboratorio_id   | UUID NULL     |
| tipo_alerta            | VARCHAR(100)  |
| prioridad              | VARCHAR(20)   |
| fecha_generacion       | DATETIME      |
| fecha_vencimiento      | DATETIME NULL |
| observaciones          | TEXT          |
| estado                 | VARCHAR(20)   |
| usuario_responsable_id | UUID NULL     |
| created_at             | DATETIME      |
| updated_at             | DATETIME      |

---

## Tipos Iniciales

```text id="61i4lj"
Control Próximo
Control Vencido
Presupuesto Sin Respuesta
Tratamiento Sin Próxima Cita
Laboratorio Próximo a Vencer
Laboratorio Vencido
Laboratorio Recibido
Saldo Pendiente
Stock Bajo
```

---

## Prioridad

```text id="iws40m"
Baja
Media
Alta
```

---

## Estado

```text id="ey5xgw"
Pendiente
Gestionada
Descartada
```

---

# Tabla: alerta_gestiones

Historial de acciones realizadas sobre alertas.

### Campos

| Campo            | Tipo     |
| ---------------- | -------- |
| id               | UUID     |
| alerta_id        | UUID     |
| fecha            | DATETIME |
| accion_realizada | TEXT     |
| resultado        | TEXT     |
| observacion      | TEXT     |
| usuario_id       | UUID     |

---

## Objetivo

Mantener trazabilidad de seguimiento.

---

# 2. Comunicaciones

## Tabla: plantillas_mensaje

Plantillas reutilizables.

### Campos

| Campo      | Tipo         |
| ---------- | ------------ |
| id         | UUID         |
| empresa_id | UUID         |
| nombre     | VARCHAR(200) |
| tipo       | VARCHAR(100) |
| contenido  | TEXT         |
| estado     | VARCHAR(20)  |
| created_at | DATETIME     |
| updated_at | DATETIME     |

---

## Tipos Iniciales

```text id="2h66c3"
Confirmación Cita
Recordatorio Cita
Presupuesto Pendiente
Control Pendiente
Saldo Pendiente
Laboratorio Listo
```

---

# Tabla: comunicaciones

Registro histórico de comunicaciones.

### Campos

| Campo          | Tipo        |
| -------------- | ----------- |
| id             | UUID        |
| empresa_id     | UUID        |
| paciente_id    | UUID        |
| cita_id        | UUID NULL   |
| tratamiento_id | UUID NULL   |
| plantilla_id   | UUID NULL   |
| tipo           | VARCHAR(30) |
| contenido      | TEXT        |
| resultado      | VARCHAR(50) |
| usuario_id     | UUID        |
| fecha          | DATETIME    |

---

## Tipo

```text id="l7o0c4"
WhatsApp
Llamada
Correo
Presencial
```

---

## Resultado

```text id="5f9z9s"
Enviado
Entregado
Contactado
No Responde
Pendiente
```

---

# 3. Inteligencia Artificial

## Tabla: ia_solicitudes

Registro de uso de IA.

### Campos

| Campo            | Tipo          |
| ---------------- | ------------- |
| id               | UUID          |
| empresa_id       | UUID          |
| usuario_id       | UUID          |
| paciente_id      | UUID NULL     |
| tratamiento_id   | UUID NULL     |
| tipo_solicitud   | VARCHAR(100)  |
| entrada_resumida | TEXT          |
| salida_generada  | TEXT          |
| tokens_estimados | INTEGER       |
| costo_estimado   | DECIMAL(12,4) |
| fecha            | DATETIME      |

---

## Tipos Iniciales

```text id="8s39lt"
Redactar Evolución
Generar WhatsApp
Resumir Paciente
Sugerir Alerta
```

---

## Objetivo

Permitir medir uso y costos futuros de IA.

---

# 4. Auditoría

## Tabla: auditoria_eventos

Registro de acciones críticas.

### Campos

| Campo      | Tipo         |
| ---------- | ------------ |
| id         | UUID         |
| empresa_id | UUID         |
| usuario_id | UUID         |
| entidad    | VARCHAR(100) |
| entidad_id | UUID         |
| accion     | VARCHAR(100) |
| detalle    | TEXT         |
| ip_origen  | VARCHAR(100) |
| fecha      | DATETIME     |

---

## Ejemplos de Acción

```text id="mym61l"
Crear Paciente
Modificar Paciente
Crear Cita
Cancelar Cita
Registrar Pago
Reversar Pago
Modificar Evolución
Finalizar Tratamiento
Anular Documento
```

---

## Objetivo

Cumplimiento legal y trazabilidad.

---

# 5. Configuración Global

## Tabla: configuraciones_empresa

Configuraciones generales.

### Campos

| Campo       | Tipo         |
| ----------- | ------------ |
| id          | UUID         |
| empresa_id  | UUID         |
| clave       | VARCHAR(200) |
| valor       | TEXT         |
| descripcion | TEXT         |
| updated_at  | DATETIME     |

---

## Ejemplos

```text id="q3ncf5"
dias_seguimiento_presupuesto = 7
dias_recordatorio_control = 15
stock_minimo_default = 5
```

---

# Tabla: parametros_laboratorio

Configuración de tiempos estándar.

### Campos

| Campo          | Tipo         |
| -------------- | ------------ |
| id             | UUID         |
| empresa_id     | UUID         |
| tipo_trabajo   | VARCHAR(200) |
| dias_estimados | INTEGER      |
| created_at     | DATETIME     |
| updated_at     | DATETIME     |

---

## Ejemplos

```text id="86n91u"
Corona = 7 días
Retenedor = 5 días
Prótesis = 10 días
Carilla = 7 días
```

---

# Tabla: parametros_control

Controles periódicos sugeridos.

### Campos

| Campo             | Tipo     |
| ----------------- | -------- |
| id                | UUID     |
| empresa_id        | UUID     |
| procedimiento_id  | UUID     |
| periodicidad_dias | INTEGER  |
| created_at        | DATETIME |
| updated_at        | DATETIME |

---

## Ejemplos

```text id="p8e8xs"
Profilaxis = 180 días
Ortodoncia = 30 días
Retenedor = 180 días
```

---

# 6. Dashboard

## Vista Lógica: dashboard_operativo

No requiere tabla física.

Obtiene información desde:

```text id="b49h9g"
citas
alertas
tratamientos
pagos
laboratorios
```

---

## Indicadores Iniciales

```text id="3rlqlg"
Citas Hoy
Pacientes Hoy
Pagos del Día
Alertas Pendientes
Tratamientos Activos
Laboratorios Pendientes
```

---

# Relaciones Principales

```text id="2yjgm8"
alerta
 └── alerta_gestiones

plantilla_mensaje
 └── comunicaciones

paciente
 ├── comunicaciones
 ├── alertas
 └── ia_solicitudes

usuario
 ├── auditoria
 ├── comunicaciones
 ├── alertas
 └── ia_solicitudes

empresa
 ├── configuraciones
 ├── parametros_laboratorio
 └── parametros_control
```

---

# Reglas Técnicas

## RT-029

Las alertas nunca deberán eliminarse.

Solo podrán:

```text id="td7j7r"
Pendiente
Gestionada
Descartada
```

---

## RT-030

Toda gestión de alerta deberá registrarse en alerta_gestiones.

---

## RT-031

Las comunicaciones deberán quedar asociadas al paciente cuando corresponda.

---

## RT-032

Las plantillas deberán ser configurables por empresa.

---

## RT-033

El módulo IA deberá ser opcional.

La aplicación deberá funcionar completamente sin IA.

---

## RT-034

Todo uso de IA deberá registrarse para controlar costos.

---

## RT-035

Toda acción crítica deberá registrarse en auditoría.

---

## RT-036

La auditoría no podrá modificarse desde la interfaz normal del sistema.

---

## RT-037

Las configuraciones deberán ser parametrizables sin necesidad de cambios de código.

---

## RT-038

Los tiempos de seguimiento de presupuestos, controles y laboratorios deberán configurarse por empresa.

---

# Resumen Final del Modelo de Datos

El modelo completo queda dividido en:

```text id="wz6zot"
D003A
Estructura Organizacional y Seguridad

D003B
Pacientes, Agenda e Historia Clínica

D003C
Presupuestos, Tratamientos y Pagos

D003D
Laboratorios, Inventario, Documentos y Archivos

D003E
Alertas, Comunicaciones, IA, Auditoría y Configuración
```

Total aproximado:

```text id="g29tdv"
45+ tablas principales
Arquitectura multiempresa
Preparada para SaaS
Preparada para IA
Preparada para crecimiento futuro
```

Este modelo constituye la base de datos oficial v1.0 del proyecto.
