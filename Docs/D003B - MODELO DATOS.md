# D003B - Modelo de Datos

# Pacientes, Agenda e Historia Clínica

Versión: 1.0

## Objetivo

Definir las entidades relacionadas con:

* Pacientes.
* Responsables legales.
* Agenda.
* Tipos de cita.
* Historia clínica.
* Evoluciones.
* Odontograma.

Este bloque constituye el núcleo clínico de la plataforma.

---

# Tabla: pacientes

Información principal del paciente.

## Campos

| Campo                       | Tipo         |
| --------------------------- | ------------ |
| id                          | UUID         |
| empresa_id                  | UUID         |
| tipo_documento              | VARCHAR(20)  |
| documento                   | VARCHAR(50)  |
| nombres                     | VARCHAR(200) |
| apellidos                   | VARCHAR(200) |
| fecha_nacimiento            | DATE         |
| sexo                        | VARCHAR(20)  |
| celular                     | VARCHAR(50)  |
| correo                      | VARCHAR(200) |
| direccion                   | VARCHAR(300) |
| ciudad                      | VARCHAR(100) |
| contacto_emergencia_nombre  | VARCHAR(200) |
| contacto_emergencia_celular | VARCHAR(50)  |
| observaciones               | TEXT         |
| estado                      | VARCHAR(20)  |
| created_at                  | DATETIME     |
| updated_at                  | DATETIME     |
| created_by                  | UUID         |
| is_active                   | BOOLEAN      |

---

## Restricciones

No podrá existir otro paciente con el mismo documento dentro de la misma empresa.

---

# Tabla: responsables_paciente

Responsables legales para menores de edad o dependientes.

## Campos

| Campo                    | Tipo         |
| ------------------------ | ------------ |
| id                       | UUID         |
| paciente_id              | UUID         |
| nombre                   | VARCHAR(200) |
| documento                | VARCHAR(50)  |
| parentesco               | VARCHAR(100) |
| celular                  | VARCHAR(50)  |
| correo                   | VARCHAR(200) |
| es_responsable_principal | BOOLEAN      |
| created_at               | DATETIME     |

---

## Relación

```text
paciente 1 ─── N responsables
```

---

# Tabla: tipos_cita

Catálogo configurable de citas.

## Campos

| Campo                     | Tipo         |
| ------------------------- | ------------ |
| id                        | UUID         |
| empresa_id                | UUID         |
| nombre                    | VARCHAR(150) |
| duracion_sugerida_minutos | INTEGER      |
| permite_sobrecupo         | BOOLEAN      |
| requiere_tratamiento      | BOOLEAN      |
| estado                    | VARCHAR(20)  |
| created_at                | DATETIME     |
| updated_at                | DATETIME     |
| is_active                 | BOOLEAN      |

---

## Ejemplos

```text
Valoración Inicial
Control Ortodoncia
Profilaxis
Retiro de Puntos
Impresión
Cirugía
Control Postoperatorio
```

---

# Tabla: citas

Agenda principal.

## Campos

| Campo              | Tipo        |
| ------------------ | ----------- |
| id                 | UUID        |
| empresa_id         | UUID        |
| paciente_id        | UUID        |
| odontologo_id      | UUID        |
| sede_id            | UUID        |
| tratamiento_id     | UUID NULL   |
| tipo_cita_id       | UUID        |
| fecha_inicio       | DATETIME    |
| fecha_fin          | DATETIME    |
| motivo             | TEXT        |
| estado             | VARCHAR(30) |
| es_sobrecupo       | BOOLEAN     |
| medio_confirmacion | VARCHAR(30) |
| observaciones      | TEXT        |
| created_at         | DATETIME    |
| updated_at         | DATETIME    |
| created_by         | UUID        |
| is_active          | BOOLEAN     |

---

## Estados

```text
Programada
Confirmada
Atendida
Cancelada
Reprogramada
No Asistió
```

---

## Medio Confirmación

```text
WhatsApp
Llamada
Presencial
Sin Confirmar
```

---

# Tabla: cita_historial

Historial de cambios de agenda.

## Campos

| Campo           | Tipo        |
| --------------- | ----------- |
| id              | UUID        |
| cita_id         | UUID        |
| estado_anterior | VARCHAR(30) |
| estado_nuevo    | VARCHAR(30) |
| fecha_anterior  | DATETIME    |
| fecha_nueva     | DATETIME    |
| motivo          | TEXT        |
| usuario_id      | UUID        |
| fecha_registro  | DATETIME    |

---

## Objetivo

Mantener trazabilidad completa de cancelaciones y reprogramaciones.

---

# Tabla: historias_clinicas

Información clínica general del paciente.

## Campos

| Campo                    | Tipo     |
| ------------------------ | -------- |
| id                       | UUID     |
| paciente_id              | UUID     |
| fecha_apertura           | DATETIME |
| antecedentes_medicos     | TEXT     |
| alergias                 | TEXT     |
| medicamentos_actuales    | TEXT     |
| enfermedades_relevantes  | TEXT     |
| antecedentes_quirurgicos | TEXT     |
| observaciones_generales  | TEXT     |
| created_at               | DATETIME |
| updated_at               | DATETIME |

---

## Relación

```text
paciente 1 ─── 1 historia_clinica
```

---

# Tabla: evoluciones_clinicas

Registro clínico por atención.

## Campos

| Campo                   | Tipo        |
| ----------------------- | ----------- |
| id                      | UUID        |
| paciente_id             | UUID        |
| cita_id                 | UUID        |
| tratamiento_id          | UUID NULL   |
| odontologo_id           | UUID        |
| fecha                   | DATETIME    |
| diagnostico             | TEXT        |
| procedimiento_realizado | TEXT        |
| evolucion               | TEXT        |
| recomendaciones         | TEXT        |
| estado                  | VARCHAR(20) |
| created_at              | DATETIME    |
| updated_at              | DATETIME    |
| created_by              | UUID        |

---

## Estados

```text
Vigente
Corregida
Anulada
```

---

## Restricción

No podrá eliminarse físicamente.

---

# Tabla: evolucion_correcciones

Historial de modificaciones.

## Campos

| Campo          | Tipo     |
| -------------- | -------- |
| id             | UUID     |
| evolucion_id   | UUID     |
| texto_anterior | TEXT     |
| texto_nuevo    | TEXT     |
| motivo         | TEXT     |
| usuario_id     | UUID     |
| fecha          | DATETIME |

---

## Objetivo

Mantener trazabilidad clínica.

---

# Tabla: odontograma_piezas

Estado actual de cada pieza dental.

## Campos

| Campo               | Tipo         |
| ------------------- | ------------ |
| id                  | UUID         |
| paciente_id         | UUID         |
| numero_pieza        | VARCHAR(10)  |
| estado_actual       | VARCHAR(100) |
| observaciones       | TEXT         |
| fecha_actualizacion | DATETIME     |

---

## Ejemplos de estado

```text
Sano
Caries
Restaurado
Corona
Implante
Ausente
Endodoncia
Extracción Indicada
```

---

# Tabla: odontograma_eventos

Historial de eventos del odontograma.

## Campos

| Campo          | Tipo         |
| -------------- | ------------ |
| id             | UUID         |
| paciente_id    | UUID         |
| numero_pieza   | VARCHAR(10)  |
| tratamiento_id | UUID NULL    |
| cita_id        | UUID NULL    |
| tipo_evento    | VARCHAR(100) |
| procedimiento  | VARCHAR(200) |
| superficie     | VARCHAR(50)  |
| observaciones  | TEXT         |
| odontologo_id  | UUID         |
| fecha          | DATETIME     |

---

## Ejemplos de eventos

```text
Caries detectada
Resina realizada
Corona instalada
Implante colocado
Extracción realizada
```

---

# Tabla: procedimientos

Catálogo general de procedimientos odontológicos.

## Campos

| Campo                     | Tipo         |
| ------------------------- | ------------ |
| id                        | UUID         |
| empresa_id                | UUID         |
| nombre                    | VARCHAR(200) |
| especialidad_id           | UUID         |
| duracion_sugerida_minutos | INTEGER      |
| valor_sugerido            | DECIMAL      |
| requiere_consentimiento   | BOOLEAN      |
| requiere_laboratorio      | BOOLEAN      |
| requiere_control          | BOOLEAN      |
| periodicidad_control_dias | INTEGER NULL |
| estado                    | VARCHAR(20)  |
| created_at                | DATETIME     |
| updated_at                | DATETIME     |
| is_active                 | BOOLEAN      |

---

## Ejemplos

```text
Valoración Inicial
Profilaxis
Ortodoncia Mensual
Endodoncia
Corona
Extracción
Blanqueamiento
Implante
```

---

# Relaciones Principales

```text
paciente
 ├── responsables
 ├── historia_clinica
 ├── citas
 ├── evoluciones
 ├── odontograma_piezas
 └── odontograma_eventos

odontologo
 ├── citas
 ├── evoluciones
 └── odontograma_eventos

tipo_cita
 └── citas

procedimiento
 └── odontograma_eventos
```

---

# Reglas Técnicas

## RT-006

Toda cita deberá pertenecer a:

* Paciente
* Odontólogo
* Sede

---

## RT-007

Las citas podrán existir con o sin tratamiento asociado.

Ejemplo:

```text
Valoración Inicial
```

No requiere tratamiento previo.

---

## RT-008

Toda atención clínica deberá generar una evolución.

---

## RT-009

Todo cambio clínico relevante deberá reflejarse en el odontograma cuando aplique.

---

## RT-010

Las evoluciones clínicas nunca deberán eliminarse físicamente.

---

## RT-011

El odontograma deberá conservar historial completo de cambios.
