# D004D - Arquitectura Técnica
# Base de Datos y Almacenamiento de Archivos

Versión: 1.0

## Objetivo

Definir la arquitectura técnica de la base de datos y del almacenamiento de archivos de la Plataforma de Gestión Odontológica.

Este documento cubre:

- PostgreSQL.
- Migraciones.
- Convenciones de tablas.
- Estrategia multiempresa.
- Manejo de archivos clínicos.
- Fotografías.
- Radiografías.
- PDFs.
- Documentos legales.
- Backups.
- Preparación para nube/SaaS.

---

# 1. Base de Datos

## Motor Seleccionado

```text
PostgreSQL
```

---

## Justificación

PostgreSQL se selecciona por:

- Estabilidad.
- Escalabilidad.
- Soporte para relaciones complejas.
- Buen rendimiento.
- Compatibilidad con SaaS.
- Soporte para UUID.
- Facilidad de migración a servidores administrados.

---

# 2. ORM y Migraciones

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

## Regla

Todo cambio estructural en la base de datos deberá realizarse mediante migraciones Alembic.

No se deberán modificar tablas manualmente en producción.

---

# 3. Convenciones Generales de Tablas

Toda tabla principal deberá incluir:

```text
id
created_at
updated_at
created_by
is_active
```

---

## id

Tipo:

```text
UUID
```

Uso:

- Llave primaria.
- Identificador único global.
- Preparación para SaaS.

---

## created_at

Fecha y hora de creación del registro.

---

## updated_at

Fecha y hora de última actualización.

---

## created_by

Usuario que creó el registro.

---

## is_active

Campo para eliminación lógica.

```text
true  = registro activo
false = registro inactivo
```

---

# 4. Política de Eliminación

No se permitirán eliminaciones físicas en tablas críticas.

Se utilizará eliminación lógica:

```text
is_active = false
```

---

## Tablas Críticas

Ejemplos:

- pacientes
- citas
- historias_clinicas
- evoluciones_clinicas
- tratamientos
- pagos
- documentos
- archivos
- auditoria_eventos

---

# 5. Multiempresa

Todas las entidades operativas deberán incluir:

```text
empresa_id
```

---

## Ejemplos

```text
pacientes
citas
presupuestos
tratamientos
pagos
laboratorios
inventario_items
documentos
archivos
alertas
comunicaciones
```

---

## Regla

Toda consulta operativa deberá filtrar por:

```text
empresa_id
```

para garantizar aislamiento de datos.

---

# 6. Índices Recomendados

Se deberán crear índices para campos usados frecuentemente en búsquedas y filtros.

---

## Índices Iniciales

```text
pacientes.empresa_id
pacientes.documento
pacientes.nombres
pacientes.apellidos

citas.empresa_id
citas.paciente_id
citas.odontologo_id
citas.sede_id
citas.fecha_inicio

tratamientos.empresa_id
tratamientos.paciente_id
tratamientos.estado

pagos.empresa_id
pagos.paciente_id
pagos.tratamiento_id
pagos.fecha

alertas.empresa_id
alertas.estado
alertas.tipo_alerta
alertas.fecha_vencimiento

archivos.empresa_id
archivos.paciente_id
```

---

# 7. Restricciones Únicas

## Pacientes

No podrá existir más de un paciente con el mismo documento dentro de la misma empresa.

```text
empresa_id + documento
```

---

## Usuarios

No podrá existir más de un usuario con el mismo correo dentro de la misma empresa.

```text
empresa_id + correo
```

---

# 8. Relaciones

La base de datos deberá respetar relaciones mediante llaves foráneas.

Ejemplos:

```text
paciente_id
odontologo_id
sede_id
tratamiento_id
presupuesto_id
documento_id
archivo_id
```

---

# 9. Fechas y Zonas Horarias

La base de datos almacenará fechas en formato estándar.

Recomendación:

```text
UTC
```

La interfaz mostrará fechas en hora local de la empresa o sede.

---

# 10. Tipos Monetarios

Los valores monetarios deberán almacenarse como:

```text
DECIMAL(14,2)
```

No usar FLOAT para valores financieros.

---

# 11. Estados

Los estados deberán manejarse como texto controlado inicialmente.

Ejemplos:

```text
Activo
Inactivo
Programada
Confirmada
Finalizado
Reversado
```

---

## Recomendación futura

Cuando el sistema crezca, evaluar catálogos de estados o enumeraciones controladas.

---

# 12. Almacenamiento de Archivos

## Estrategia Inicial

Los archivos se almacenarán en el sistema de archivos local.

La base de datos no almacenará archivos binarios.

Solo almacenará:

```text
ruta_archivo
nombre_archivo
mime_type
tamaño_bytes
metadatos
relaciones
```

---

# 13. Estructura de Storage Local

```text
storage/

├── empresa_{empresa_id}/
│   ├── pacientes/
│   │   └── paciente_{paciente_id}/
│   │       ├── imagenes/
│   │       ├── radiografias/
│   │       ├── documentos/
│   │       ├── tratamientos/
│   │       └── general/
│   │
│   ├── documentos_legales/
│   ├── laboratorios/
│   └── temporales/
```

---

# 14. Tipos de Archivos Soportados

## Imágenes

```text
.jpg
.jpeg
.png
.webp
```

---

## Radiografías

```text
.jpg
.jpeg
.png
.dicom
.pdf
```

---

## Documentos

```text
.pdf
.docx
.png
.jpg
```

---

# 15. Restricciones de Archivos

El sistema deberá validar:

- Tipo de archivo.
- Tamaño máximo.
- Asociación a empresa.
- Asociación a paciente.
- Permisos del usuario.

---

# 16. Tamaño Máximo Inicial

Tamaño máximo sugerido por archivo:

```text
25 MB
```

Este valor deberá ser configurable.

---

# 17. Archivos Clínicos Ilimitados

El sistema permitirá almacenar múltiples archivos por paciente.

No se definirá un límite funcional por paciente.

---

## Nota

Aunque funcionalmente sea ilimitado, el almacenamiento real dependerá del espacio disponible en disco o nube.

---

# 18. Seguridad de Archivos

Los archivos no deberán exponerse directamente por ruta pública.

El acceso deberá realizarse a través del backend, validando:

- Usuario autenticado.
- Empresa.
- Permisos.
- Relación con paciente o tratamiento.

---

# 19. Documentos Legales

Los documentos legales generados deberán almacenarse como archivos PDF.

Ejemplos:

- Consentimiento informado.
- Protección de datos.
- Plan de tratamiento aceptado.
- Cierre de tratamiento.
- Conformidad del paciente.

---

# 20. Versionamiento Documental

Los documentos firmados no deberán sobrescribirse.

Cuando exista una nueva versión:

```text
documento_v1.pdf
documento_v2.pdf
documento_v3.pdf
```

Se deberá registrar en base de datos mediante:

```text
documento_versiones
```

---

# 21. Archivos Temporales

Los archivos temporales deberán almacenarse en:

```text
storage/empresa_{empresa_id}/temporales/
```

---

## Regla

Los archivos temporales deberán eliminarse periódicamente.

---

# 22. Backups

El sistema deberá contemplar backup de:

- Base de datos.
- Archivos.
- Configuración.

---

# 23. Backup de Base de Datos

Inicialmente se podrá realizar mediante:

```text
pg_dump
```

---

## Ejemplo

```bash
pg_dump odontologia_db > backup_odontologia.sql
```

---

# 24. Backup de Archivos

El directorio:

```text
storage/
```

deberá respaldarse completo.

---

# 25. Restauración

La estrategia de restauración deberá contemplar:

1. Restaurar base de datos.
2. Restaurar carpeta storage.
3. Verificar rutas de archivos.
4. Validar acceso desde la aplicación.

---

# 26. Preparación para Nube

En una versión futura, el almacenamiento podrá migrarse a:

```text
Amazon S3
Google Cloud Storage
Azure Blob Storage
MinIO
```

---

# 27. Abstracción de Storage

El backend deberá tener una capa de servicio:

```text
storage_service.py
```

---

## Objetivo

Permitir cambiar de almacenamiento local a nube sin modificar todos los módulos.

---

# 28. Variables de Entorno

Variables relacionadas:

```text
DATABASE_URL
STORAGE_PATH
MAX_FILE_SIZE_MB
ALLOWED_FILE_TYPES
```

---

# 29. Migración a SaaS

Para SaaS se deberá garantizar:

- Aislamiento por empresa.
- Storage separado por empresa.
- Backups periódicos.
- HTTPS.
- Control de acceso.

---

# 30. Buenas Prácticas

## BP-001

No guardar archivos binarios en PostgreSQL.

---

## BP-002

No exponer rutas reales de archivos al usuario.

---

## BP-003

No eliminar documentos legales firmados.

---

## BP-004

No usar FLOAT para dinero.

---

## BP-005

Toda tabla crítica deberá tener auditoría.

---

## BP-006

Toda consulta operativa deberá filtrar por empresa_id.

---

# 31. Resultado Esperado

La arquitectura de datos y archivos deberá permitir:

- Escalabilidad.
- Seguridad.
- Trazabilidad.
- Almacenamiento ilimitado por paciente.
- Manejo de documentos legales.
- Backups.
- Migración futura a nube/SaaS.