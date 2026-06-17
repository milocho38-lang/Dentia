# D003C - Modelo de Datos

# Presupuestos, Tratamientos y Pagos

Versión: 1.0

## Objetivo

Definir las entidades relacionadas con:

* Presupuestos.
* Seguimiento comercial.
* Tratamientos.
* Etapas.
* Procedimientos.
* Pagos.
* Caja.
* Cartera.

Este bloque constituye el núcleo administrativo y financiero de la plataforma.

---

# Tabla: presupuestos

Presupuesto entregado al paciente.

## Campos

| Campo             | Tipo          |
| ----------------- | ------------- |
| id                | UUID          |
| empresa_id        | UUID          |
| paciente_id       | UUID          |
| odontologo_id     | UUID          |
| fecha             | DATETIME      |
| valor_total       | DECIMAL(14,2) |
| estado            | VARCHAR(30)   |
| fecha_vencimiento | DATE          |
| observaciones     | TEXT          |
| created_at        | DATETIME      |
| updated_at        | DATETIME      |
| created_by        | UUID          |
| is_active         | BOOLEAN       |

---

## Estados

```text id="v92ujk"
Borrador
Entregado
En Seguimiento
Aceptado
Rechazado
Vencido
```

---

# Tabla: presupuesto_items

Detalle de procedimientos incluidos.

## Campos

| Campo            | Tipo             |
| ---------------- | ---------------- |
| id               | UUID             |
| presupuesto_id   | UUID             |
| procedimiento_id | UUID             |
| descripcion      | TEXT             |
| pieza_dental     | VARCHAR(20) NULL |
| cantidad         | DECIMAL(10,2)    |
| valor_unitario   | DECIMAL(14,2)    |
| valor_total      | DECIMAL(14,2)    |

---

## Relación

```text id="3pk85z"
presupuesto 1 ─── N items
```

---

# Tabla: presupuesto_seguimientos

Gestión comercial posterior a la valoración.

## Campos

| Campo          | Tipo        |
| -------------- | ----------- |
| id             | UUID        |
| presupuesto_id | UUID        |
| fecha          | DATETIME    |
| medio_contacto | VARCHAR(30) |
| resultado      | VARCHAR(50) |
| observacion    | TEXT        |
| usuario_id     | UUID        |

---

## Medio Contacto

```text id="7ryglt"
Llamada
WhatsApp
Correo
Presencial
```

---

## Resultado

```text id="62yxmt"
Contactado
No Responde
Interesado
Pendiente
Aceptado
Rechazado
```

---

# Tabla: tratamientos

Representa un tratamiento activo o histórico.

## Campos

| Campo                     | Tipo          |
| ------------------------- | ------------- |
| id                        | UUID          |
| empresa_id                | UUID          |
| paciente_id               | UUID          |
| presupuesto_id            | UUID          |
| odontologo_responsable_id | UUID          |
| especialidad_id           | UUID          |
| nombre                    | VARCHAR(200)  |
| descripcion               | TEXT          |
| fecha_inicio              | DATE          |
| fecha_fin_estimada        | DATE          |
| fecha_fin_real            | DATE NULL     |
| valor_total               | DECIMAL(14,2) |
| valor_abonado             | DECIMAL(14,2) |
| saldo_pendiente           | DECIMAL(14,2) |
| porcentaje_avance         | DECIMAL(5,2)  |
| estado                    | VARCHAR(30)   |
| observaciones             | TEXT          |
| created_at                | DATETIME      |
| updated_at                | DATETIME      |
| created_by                | UUID          |
| is_active                 | BOOLEAN       |

---

## Estados

```text id="v54f7z"
Planeado
Activo
Suspendido
Finalizado
Cancelado
```

---

## Regla

Un presupuesto aceptado podrá generar un tratamiento.

---

# Tabla: tratamiento_etapas

Permite dividir tratamientos complejos.

## Campos

| Campo          | Tipo         |
| -------------- | ------------ |
| id             | UUID         |
| tratamiento_id | UUID         |
| nombre         | VARCHAR(200) |
| descripcion    | TEXT         |
| orden          | INTEGER      |
| estado         | VARCHAR(30)  |
| fecha_inicio   | DATE         |
| fecha_fin      | DATE NULL    |

---

## Estados

```text id="4p6vfx"
Pendiente
En Proceso
Finalizada
Cancelada
```

---

## Ejemplos

```text id="v3x9c4"
Valoración
Preparación
Laboratorio
Instalación
Control
```

---

# Tabla: tratamiento_procedimientos

Procedimientos incluidos dentro del tratamiento.

## Campos

| Campo            | Tipo             |
| ---------------- | ---------------- |
| id               | UUID             |
| tratamiento_id   | UUID             |
| procedimiento_id | UUID             |
| pieza_dental     | VARCHAR(20) NULL |
| cantidad         | DECIMAL(10,2)    |
| valor            | DECIMAL(14,2)    |
| estado           | VARCHAR(30)      |

---

## Estados

```text id="1s9zv7"
Pendiente
Realizado
Cancelado
```

---

# Tabla: pagos

Pagos realizados por pacientes.

## Campos

| Campo                     | Tipo          |
| ------------------------- | ------------- |
| id                        | UUID          |
| empresa_id                | UUID          |
| paciente_id               | UUID          |
| tratamiento_id            | UUID NULL     |
| cita_id                   | UUID NULL     |
| fecha                     | DATETIME      |
| valor                     | DECIMAL(14,2) |
| medio_pago                | VARCHAR(50)   |
| tipo_pago                 | VARCHAR(50)   |
| observaciones             | TEXT          |
| registrado_por_usuario_id | UUID          |
| estado                    | VARCHAR(20)   |
| created_at                | DATETIME      |
| updated_at                | DATETIME      |

---

## Tipo Pago

```text id="e2sr8r"
Valoración
Anticipo
Abono
Pago Total
```

---

## Medio Pago

```text id="89cq42"
Efectivo
Tarjeta Débito
Tarjeta Crédito
Transferencia
Nequi
Daviplata
Otro
```

---

## Estado

```text id="l6svy8"
Vigente
Reversado
```

---

# Tabla: pago_reversiones

Correcciones financieras.

## Campos

| Campo           | Tipo          |
| --------------- | ------------- |
| id              | UUID          |
| pago_id         | UUID          |
| fecha           | DATETIME      |
| motivo          | TEXT          |
| valor_reversado | DECIMAL(14,2) |
| usuario_id      | UUID          |

---

## Restricción

Ningún pago podrá eliminarse físicamente.

---

# Tabla: caja_movimientos

Movimientos financieros de caja.

## Campos

| Campo           | Tipo          |
| --------------- | ------------- |
| id              | UUID          |
| empresa_id      | UUID          |
| sede_id         | UUID          |
| pago_id         | UUID NULL     |
| fecha           | DATETIME      |
| tipo_movimiento | VARCHAR(20)   |
| valor           | DECIMAL(14,2) |
| concepto        | TEXT          |
| medio_pago      | VARCHAR(50)   |
| usuario_id      | UUID          |

---

## Tipo Movimiento

```text id="fr3zv7"
Ingreso
Egreso
Ajuste
```

---

# Tabla: caja_cierres

Cierre diario de caja.

## Campos

| Campo                  | Tipo          |
| ---------------------- | ------------- |
| id                     | UUID          |
| empresa_id             | UUID          |
| sede_id                | UUID          |
| fecha                  | DATE          |
| total_efectivo         | DECIMAL(14,2) |
| total_transferencia    | DECIMAL(14,2) |
| total_tarjetas         | DECIMAL(14,2) |
| total_otros            | DECIMAL(14,2) |
| total_general          | DECIMAL(14,2) |
| observaciones          | TEXT          |
| cerrado_por_usuario_id | UUID          |
| created_at             | DATETIME      |

---

# Tabla: cierres_tratamiento

Documento lógico de finalización del tratamiento.

## Campos

| Campo                  | Tipo        |
| ---------------------- | ----------- |
| id                     | UUID        |
| tratamiento_id         | UUID        |
| fecha_cierre           | DATETIME    |
| odontologo_id          | UUID        |
| resumen                | TEXT        |
| estado_final           | VARCHAR(50) |
| conformidad_paciente   | VARCHAR(50) |
| observaciones_paciente | TEXT        |
| documento_cierre_id    | UUID NULL   |
| usuario_id             | UUID        |

---

## Conformidad

```text id="tr7tka"
Conforme
Conforme con Observaciones
No Conforme
```

---

# Vista Lógica: Cartera

No requiere tabla física inicial.

La cartera podrá calcularse desde:

```text id="vv46tx"
tratamientos.saldo_pendiente
```

---

## Indicadores de Cartera

Por paciente:

```text id="g5f5l8"
Valor Total
Valor Abonado
Saldo Pendiente
```

---

# Relaciones Principales

```text id="0wlddz"
paciente
 ├── presupuestos
 ├── tratamientos
 └── pagos

presupuesto
 ├── items
 ├── seguimientos
 └── tratamiento

tratamiento
 ├── etapas
 ├── procedimientos
 ├── citas
 ├── pagos
 └── cierre

pagos
 ├── reversos
 └── caja

caja
 ├── movimientos
 └── cierres
```

---

# Reglas Técnicas

## RT-012

Un presupuesto podrá existir sin tratamiento asociado.

---

## RT-013

Un tratamiento deberá originarse desde un presupuesto aceptado.

---

## RT-014

Los valores financieros del tratamiento deberán mantenerse sincronizados:

```text id="dxygvx"
valor_total
valor_abonado
saldo_pendiente
```

---

## RT-015

Todo pago deberá quedar asociado al menos a:

* Paciente

Y opcionalmente a:

* Tratamiento
* Cita

---

## RT-016

Los pagos nunca se eliminarán.

Solo podrán reversarse.

---

## RT-017

Todo ingreso deberá generar movimiento de caja.

---

## RT-018

Los cierres de tratamiento deberán conservarse indefinidamente.

---

## RT-019

El sistema deberá permitir múltiples tratamientos activos para un mismo paciente.

Ejemplo:

```text id="z4k5cg"
Ortodoncia
+
Rehabilitación Oral
```

simultáneamente.

---

## RT-020

Todo cambio financiero crítico deberá registrarse posteriormente en auditoría.
