# ESTRUCTURA_PROYECTO

Este documento describe la estructura fisica inicial del proyecto Dentia creada para la tarea C001 del roadmap.

La estructura corresponde a la base oficial indicada en D004. No incluye funcionalidades, modulos clinicos, tablas, endpoints ni pantallas.

## Estructura base

```text
Dentia/
├── frontend/
├── backend/
├── database/
├── storage/
├── DOCS/
├── scripts/
├── README.md
├── RESUMEN_PROYECTO.md
└── ESTRUCTURA_PROYECTO.md
```

## Carpetas

### frontend/

Carpeta reservada para la aplicacion frontend de Dentia.

Segun D004, aqui se ubicara posteriormente el proyecto Next.js con React, TypeScript y Tailwind CSS. En C001 solo se crea la carpeta fisica, sin pantallas, componentes, rutas ni servicios.

### backend/

Carpeta reservada para la aplicacion backend de Dentia.

Segun D004, aqui se ubicara posteriormente el proyecto FastAPI con SQLAlchemy, Alembic y Pydantic. En C001 solo se crea la carpeta fisica, sin routers, services, repositories, models, schemas, endpoints ni logica de negocio.

### database/

Carpeta reservada para recursos relacionados con base de datos.

Segun D004, aqui podran ubicarse posteriormente configuraciones, migraciones o recursos auxiliares de PostgreSQL y Alembic. En C001 no se crean tablas, migraciones ni modelos de datos.

### storage/

Carpeta reservada para el almacenamiento local inicial de archivos.

Segun D004, el MVP podra usar almacenamiento local para archivos clinicos, documentos y otros recursos, siempre gestionados por el backend. En C001 solo se crea la carpeta base, sin estructura interna de pacientes, empresas ni archivos reales.

### scripts/

Carpeta reservada para scripts auxiliares del proyecto.

Podra contener en fases posteriores utilidades de instalacion, mantenimiento, respaldo o automatizacion. En C001 no se crean scripts ejecutables.

### DOCS/

Carpeta existente de documentacion funcional, tecnica, roadmap e identidad visual del proyecto.

No fue creada ni modificada durante C001.

## Archivos .gitkeep

Se agregan archivos `.gitkeep` en las carpetas vacias principales para conservar la estructura en control de versiones:

- `frontend/.gitkeep`
- `backend/.gitkeep`
- `database/.gitkeep`
- `storage/.gitkeep`
- `scripts/.gitkeep`

Estos archivos no representan funcionalidad del sistema.

## Validacion de alcance

C001 queda limitado a estructura fisica del proyecto.

No se implemento:

- Funcionalidad clinica.
- Funcionalidad administrativa.
- Funcionalidad financiera.
- Modulos frontend.
- Pantallas.
- Endpoints.
- Tablas.
- Migraciones.
- Modelos de datos.
- Servicios de negocio.

