# D003D - Modelo de Datos

# Laboratorios, Inventario, Documentos y Archivos

Versión: 1.0

## Objetivo

Definir las entidades relacionadas con:

* Laboratorios externos.
* Órdenes de laboratorio.
* Inventario básico.
* Documentos legales.
* Repositorio de archivos clínicos.

---

# 1. Laboratorios

## Tabla: laboratorios

Información de laboratorios externos.

### Campos

| Campo         | Tipo         |
| ------------- | ------------ |
| id            | UUID         |
| empresa_id    | UUID         |
| nombre        | VARCHAR(200) |
| contacto      | VARCHAR(200) |
| celular       | VARCHAR(50)  |
| correo        | VARCHAR(200) |
| direccion     | VARCHAR(300) |
| observaciones | TEXT         |
| estado        | VARCHAR(20)  |
| created_at    | DATETIME     |
| updated_at    | DATETIME     |
| created_by    | UUID         |
| is_active     | BOOLEAN      |

---

## Estados

```text
Activo
Inactivo
```

---

# Tabla: ordenes_laboratorio

Representa trabajos enviados a laboratorios externos.

### Campos

| Campo                  | Tipo          |
| ---------------------- | ------------- |
| id                     | UUID          |
| empresa_id             | UUID          |
| paciente_id            | UUID          |
| tratamiento_id         | UUID          |
| cita_id                | UUID NULL     |
| laboratorio_id         | UUID          |
| tipo_trabajo           | VARCHAR(200)  |
| descripcion            | TEXT          |
| fecha_envio            | DATE          |
| fecha_estimada_entrega | DATE          |
| fecha_recibido         | DATE NULL     |
| costo                  | DECIMAL(14,2) |
| factura_pendiente      | BOOLEAN       |
| observaciones          | TEXT          |
| estado                 | VARCHAR(30)   |
| created_at             | DATETIME      |
| updated_at             | DATETIME      |
| created_by             | UUID          |
| is_active              | BOOLEAN       |

---

## Estados

```text
Pendiente Envío
Enviada
En Proceso
Recibida
Entregada al Paciente
Cancelada
Repetida
```

---

## Ejemplos de Trabajos

```text
Corona
Prótesis
Carilla
Retenedor
Placa
Alineador
Incrustación
```

---

# Tabla: laboratorio_seguimientos

Historial de cambios de estado.

### Campos

| Campo                | Tipo        |
| -------------------- | ----------- |
| id                   | UUID        |
| orden_laboratorio_id | UUID        |
| fecha                | DATETIME    |
| estado_anterior      | VARCHAR(30) |
| estado_nuevo         | VARCHAR(30) |
| observacion          | TEXT        |
| usuario_id           | UUID        |

---

## Objetivo

Mantener trazabilidad completa de cada trabajo.

---

# 2. Inventario Básico

## Tabla: inventario_items

Catálogo de insumos odontológicos.

### Campos

| Campo         | Tipo          |
| ------------- | ------------- |
| id            | UUID          |
| empresa_id    | UUID          |
| nombre        | VARCHAR(200)  |
| categoria     | VARCHAR(100)  |
| unidad_medida | VARCHAR(50)   |
| stock_actual  | DECIMAL(14,2) |
| stock_minimo  | DECIMAL(14,2) |
| observaciones | TEXT          |
| estado        | VARCHAR(20)   |
| created_at    | DATETIME      |
| updated_at    | DATETIME      |
| created_by    | UUID          |
| is_active     | BOOLEAN       |

---

## Ejemplos

```text
Anestesia
Resina
Guantes
Cubetas
Ácido Grabador
Composite
Alginato
```

---

# Tabla: inventario_movimientos

Movimientos de inventario.

### Campos

| Campo           | Tipo          |
| --------------- | ------------- |
| id              | UUID          |
| item_id         | UUID          |
| fecha           | DATETIME      |
| tipo_movimiento | VARCHAR(20)   |
| cantidad        | DECIMAL(14,2) |
| concepto        | TEXT          |
| usuario_id      | UUID          |

---

## Tipo Movimiento

```text
Entrada
Salida
Ajuste
```

---

## Regla

El stock actual deberá actualizarse automáticamente.

---

# 3. Documentos Legales

## Tabla: documentos

Documentos legales asociados al paciente.

### Campos

| Campo                   | Tipo          |
| ----------------------- | ------------- |
| id                      | UUID          |
| empresa_id              | UUID          |
| paciente_id             | UUID          |
| tratamiento_id          | UUID NULL     |
| tipo_documento          | VARCHAR(100)  |
| nombre                  | VARCHAR(250)  |
| fecha_generacion        | DATETIME      |
| fecha_firma             | DATETIME NULL |
| archivo_id              | UUID NULL     |
| estado                  | VARCHAR(30)   |
| generado_por_usuario_id | UUID          |
| created_at              | DATETIME      |
| updated_at              | DATETIME      |

---

## Tipos Iniciales

```text
Consentimiento Informado
Presupuesto Aceptado
Plan de Tratamiento Aceptado
Autorización de Menor
Protección de Datos
Cierre de Tratamiento
Otro
```

---

## Estados

```text
Borrador
Firmado
Vigente
Reemplazado
Anulado
```

---

## Restricción

Los documentos firmados no podrán modificarse.

---

# Tabla: documento_versiones

Historial de versiones documentales.

### Campos

| Campo          | Tipo     |
| -------------- | -------- |
| id             | UUID     |
| documento_id   | UUID     |
| numero_version | INTEGER  |
| motivo         | TEXT     |
| usuario_id     | UUID     |
| fecha          | DATETIME |

---

## Objetivo

Mantener trazabilidad legal.

---

# 4. Archivos Clínicos

## Tabla: archivos

Repositorio general de archivos.

### Campos

| Campo                  | Tipo         |
| ---------------------- | ------------ |
| id                     | UUID         |
| empresa_id             | UUID         |
| paciente_id            | UUID         |
| tratamiento_id         | UUID NULL    |
| cita_id                | UUID NULL    |
| tipo_archivo           | VARCHAR(50)  |
| categoria              | VARCHAR(50)  |
| nombre_archivo         | VARCHAR(300) |
| ruta_archivo           | TEXT         |
| mime_type              | VARCHAR(100) |
| tamaño_bytes           | BIGINT       |
| descripcion            | TEXT         |
| fecha_carga            | DATETIME     |
| cargado_por_usuario_id | UUID         |
| is_active              | BOOLEAN      |

---

## Tipo Archivo

```text
Fotografía
Radiografía
PDF
Documento
Imagen
Otro
```

---

## Categoría

```text
Inicial
Evolución
Final
Legal
Laboratorio
General
```

---

## Ejemplos

```text
Radiografía panorámica inicial
Fotografía antes del tratamiento
Fotografía final
Consentimiento firmado
Orden de laboratorio escaneada
```

---

## Regla

El almacenamiento será ilimitado por paciente.

---

# Tabla: archivo_etiquetas

Etiquetas opcionales para organización.

### Campos

| Campo      | Tipo         |
| ---------- | ------------ |
| id         | UUID         |
| archivo_id | UUID         |
| etiqueta   | VARCHAR(100) |

---

## Ejemplos

```text
Ortodoncia
Implante
Antes
Después
Control
Urgente
```

---

# 5. Configuración de Plantillas

## Tabla: plantillas_documentos

Plantillas configurables por empresa.

### Campos

| Campo          | Tipo         |
| -------------- | ------------ |
| id             | UUID         |
| empresa_id     | UUID         |
| nombre         | VARCHAR(200) |
| tipo_documento | VARCHAR(100) |
| contenido      | TEXT         |
| estado         | VARCHAR(20)  |
| created_at     | DATETIME     |
| updated_at     | DATETIME     |

---

## Objetivo

Permitir personalizar:

* Consentimientos.
* Protección de datos.
* Cierres de tratamiento.
* Autorizaciones.

---

# Relaciones Principales

```text
laboratorio
 └── ordenes_laboratorio
       └── seguimientos

inventario_item
 └── movimientos

paciente
 ├── documentos
 └── archivos

tratamiento
 ├── documentos
 ├── archivos
 └── ordenes_laboratorio

documento
 ├── versiones
 └── archivo

archivo
 └── etiquetas
```

---

# Reglas Técnicas

## RT-021

Todo trabajo enviado a laboratorio deberá estar asociado a:

* Paciente
* Tratamiento
* Laboratorio

---

## RT-022

Los cambios de estado de laboratorio deberán quedar registrados.

---

## RT-023

Los movimientos de inventario nunca deberán eliminarse.

---

## RT-024

Los documentos legales firmados no podrán editarse.

---

## RT-025

Las nuevas versiones deberán generar registro en documento_versiones.

---

## RT-026

Los archivos físicos se almacenarán fuera de la base de datos.

La base de datos almacenará únicamente:

```text
Ruta
Metadatos
Relaciones
```

---

## RT-027

Los archivos deberán poder asociarse simultáneamente a:

* Paciente
* Cita
* Tratamiento

según corresponda.

---

## RT-028

El sistema deberá permitir almacenar:

* Fotografías.
* Radiografías.
* PDFs.
* Consentimientos.
* Documentos escaneados.
* Archivos de laboratorio.

sin límite funcional definido por paciente.
