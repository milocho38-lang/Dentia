# D003A - Modelo de Datos

# Estructura Organizacional y Seguridad

Versión: 1.0

## Objetivo

Definir las entidades base que soportan:

* Multiempresa.
* Múltiples sedes.
* Usuarios.
* Roles.
* Permisos.
* Odontólogos.
* Especialidades.

Estas tablas constituyen la base de toda la plataforma.

---

# Tabla: empresas

Representa el consultorio, clínica o profesional independiente.

## Campos

| Campo        | Tipo         | Descripción                          |
| ------------ | ------------ | ------------------------------------ |
| id           | UUID         | Identificador único                  |
| nombre       | VARCHAR(200) | Nombre comercial                     |
| nit          | VARCHAR(50)  | Documento tributario                 |
| telefono     | VARCHAR(50)  | Teléfono principal                   |
| correo       | VARCHAR(200) | Correo principal                     |
| direccion    | VARCHAR(300) | Dirección                            |
| ciudad       | VARCHAR(100) | Ciudad                               |
| tipo_empresa | VARCHAR(50)  | Independiente, consultorio o clínica |
| estado       | VARCHAR(20)  | Activa/Inactiva                      |
| created_at   | DATETIME     | Fecha creación                       |
| updated_at   | DATETIME     | Fecha actualización                  |
| created_by   | UUID         | Usuario creador                      |
| is_active    | BOOLEAN      | Registro activo                      |

---

## Relación

```text
empresa
 ├── sedes
 ├── usuarios
 ├── odontologos
 ├── pacientes
 ├── tratamientos
 ├── pagos
 └── documentos
```

---

# Tabla: sedes

Representa una ubicación física.

## Campos

| Campo      | Tipo         |
| ---------- | ------------ |
| id         | UUID         |
| empresa_id | UUID         |
| nombre     | VARCHAR(150) |
| direccion  | VARCHAR(300) |
| ciudad     | VARCHAR(100) |
| telefono   | VARCHAR(50)  |
| estado     | VARCHAR(20)  |
| created_at | DATETIME     |
| updated_at | DATETIME     |
| created_by | UUID         |
| is_active  | BOOLEAN      |

---

## Relación

```text
empresa 1 ─── N sedes
```

---

# Tabla: usuarios

Usuarios que ingresan al sistema.

## Campos

| Campo         | Tipo         |
| ------------- | ------------ |
| id            | UUID         |
| empresa_id    | UUID         |
| nombre        | VARCHAR(200) |
| correo        | VARCHAR(200) |
| celular       | VARCHAR(50)  |
| password_hash | TEXT         |
| ultimo_login  | DATETIME     |
| estado        | VARCHAR(20)  |
| created_at    | DATETIME     |
| updated_at    | DATETIME     |
| created_by    | UUID         |
| is_active     | BOOLEAN      |

---

## Observaciones

Un usuario puede tener múltiples roles.

Ejemplo:

```text
Juan Pérez

✓ Odontólogo
✓ Administrador
```

---

# Tabla: roles

Roles disponibles.

## Campos

| Campo       | Tipo         |
| ----------- | ------------ |
| id          | UUID         |
| nombre      | VARCHAR(100) |
| descripcion | TEXT         |
| created_at  | DATETIME     |
| updated_at  | DATETIME     |

---

## Roles Iniciales

```text
Administrador
Secretaria
Odontólogo
Odontólogo Administrador
```

---

# Tabla: usuario_roles

Relación entre usuarios y roles.

## Campos

| Campo      | Tipo     |
| ---------- | -------- |
| id         | UUID     |
| usuario_id | UUID     |
| rol_id     | UUID     |
| created_at | DATETIME |

---

## Relación

```text
usuarios N ─── N roles
```

---

# Tabla: permisos

Permisos individuales.

## Campos

| Campo       | Tipo         |
| ----------- | ------------ |
| id          | UUID         |
| nombre      | VARCHAR(100) |
| descripcion | TEXT         |

---

## Ejemplos

```text
crear_paciente
editar_paciente
crear_cita
cancelar_cita
registrar_pago
reversar_pago
ver_reportes
```

---

# Tabla: rol_permisos

Asocia permisos a roles.

## Campos

| Campo      | Tipo |
| ---------- | ---- |
| id         | UUID |
| rol_id     | UUID |
| permiso_id | UUID |

---

## Relación

```text
roles N ─── N permisos
```

---

# Tabla: odontologos

Información profesional del odontólogo.

## Campos

| Campo                | Tipo         |
| -------------------- | ------------ |
| id                   | UUID         |
| empresa_id           | UUID         |
| usuario_id           | UUID         |
| nombres              | VARCHAR(200) |
| documento            | VARCHAR(50)  |
| registro_profesional | VARCHAR(100) |
| celular              | VARCHAR(50)  |
| correo               | VARCHAR(200) |
| estado               | VARCHAR(20)  |
| created_at           | DATETIME     |
| updated_at           | DATETIME     |
| created_by           | UUID         |
| is_active            | BOOLEAN      |

---

## Relación

```text
usuario 1 ─── 0/1 odontólogo
empresa 1 ─── N odontólogos
```

---

# Tabla: especialidades

Catálogo configurable.

## Campos

| Campo       | Tipo         |
| ----------- | ------------ |
| id          | UUID         |
| empresa_id  | UUID         |
| nombre      | VARCHAR(150) |
| descripcion | TEXT         |
| estado      | VARCHAR(20)  |
| created_at  | DATETIME     |
| updated_at  | DATETIME     |
| created_by  | UUID         |
| is_active   | BOOLEAN      |

---

## Especialidades Iniciales

```text
Odontología General
Ortodoncia
Endodoncia
Periodoncia
Cirugía Oral
Implantología
Rehabilitación Oral
Odontopediatría
Estética Dental
Higiene Oral
```

---

# Tabla: odontologo_especialidades

Relación entre odontólogos y especialidades.

## Campos

| Campo           | Tipo |
| --------------- | ---- |
| id              | UUID |
| odontologo_id   | UUID |
| especialidad_id | UUID |

---

## Relación

```text
odontólogo N ─── N especialidades
```

---

# Tabla: odontologo_sedes

Define en qué sedes atiende un odontólogo.

## Campos

| Campo         | Tipo |
| ------------- | ---- |
| id            | UUID |
| odontologo_id | UUID |
| sede_id       | UUID |

---

## Relación

```text
odontólogo N ─── N sedes
```

---

# Reglas Técnicas

## RT-001

Todo registro operativo deberá pertenecer a una empresa.

---

## RT-002

Los usuarios únicamente podrán acceder a información de su empresa.

---

## RT-003

Toda tabla principal deberá incluir:

```text
id
created_at
updated_at
created_by
is_active
```

---

## RT-004

Las eliminaciones físicas estarán prohibidas en tablas críticas.

Los registros deberán marcarse como:

```text
is_active = false
```

---

## RT-005

El sistema deberá estar preparado desde el inicio para operación SaaS multiempresa.

---

# Resumen de Relaciones

```text
empresa
 ├── sedes
 ├── usuarios
 │     └── roles
 │           └── permisos
 │
 └── odontologos
       ├── especialidades
       └── sedes
```
