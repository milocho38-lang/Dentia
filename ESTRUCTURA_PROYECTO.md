# ESTRUCTURA_PROYECTO

Este documento describe el estado físico del proyecto Dentia al finalizar las
tareas C001, C002, C003, C003B y C004 del roadmap.

La estructura contiene la base del repositorio, un backend FastAPI inicial y un
frontend Next.js inicial. La persistencia PostgreSQL y el sistema de migraciones
ya están configurados, pero todavía no existen tablas ni módulos clínicos,
administrativos o financieros.

## Estado del roadmap

### C001 - Estructura del proyecto

Completada:

- Carpetas principales del repositorio.
- Documentación funcional y técnica.
- Directorios reservados para base de datos, almacenamiento y scripts.

### C002 - Backend inicial

Implementado:

- Aplicación FastAPI.
- Configuración mediante variables de entorno.
- Logging básico.
- Endpoint de salud.
- Estructura por capas preparada para crecimiento.

No incluye:

- SQLAlchemy.
- Alembic.
- Conexión activa a PostgreSQL.
- Modelos, repositorios o servicios de negocio.

### C003 - Frontend inicial

Implementado:

- Next.js.
- React.
- TypeScript.
- Tailwind CSS.
- Layout y página inicial.
- Tokens básicos de la identidad visual Dentia.

No incluye:

- Integración con el backend.
- Autenticación.
- Pantallas operativas.
- Módulos clínicos o administrativos.

### C003B - Higiene técnica

Completada:

- Reglas profesionales de exclusión mediante `.gitignore`.
- Normalización de archivos mediante `.gitattributes`.
- Retiro de configuraciones locales y bytecode del seguimiento de Git.
- Protección de storage, logs, dumps y artefactos temporales.
- Unificación de la documentación bajo `DOCS/`.
- Corrección de referencias documentales.

### C004 - Persistencia PostgreSQL

Completada:

- PostgreSQL local.
- SQLAlchemy.
- psycopg.
- Alembic.
- Engine y `SessionLocal`.
- Base declarativa.
- Directorio de migraciones.
- Migración inicial vacía.
- Validación de conexión, upgrade y downgrade.

No incluye:

- Modelos funcionales.
- Tablas de negocio.
- Datos iniciales.

## Estructura actual

```text
Dentia/
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── database/
│   │   ├── jobs/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── migrations/
│   │   ├── versions/
│   │   │   └── 20260617_0001_initial_empty.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
├── database/
├── storage/
├── DOCS/
├── scripts/
├── .gitattributes
├── .gitignore
├── README.md
├── RESUMEN_PROYECTO.md
└── ESTRUCTURA_PROYECTO.md
```

## Convenciones de higiene

- `backend/.env` es configuración local y no se versiona.
- `backend/.env.example` documenta las variables requeridas.
- Cachés de Python, dependencias, compilaciones y archivos temporales no se
  versionan.
- El contenido operativo de `storage/` no se versiona; únicamente se conserva
  `storage/.gitkeep`.
- Dumps de PostgreSQL, logs y bases de datos locales quedan excluidos.
- Git normaliza los archivos de texto para reducir diferencias entre Windows,
  macOS y Linux.
- `DOCS/` es el nombre oficial de la carpeta documental.

## Carpetas principales

### frontend/

Aplicación web de Dentia. Actualmente contiene la base de Next.js y la pantalla
inicial. Las páginas, componentes, servicios y hooks de los módulos se
incorporarán siguiendo el roadmap.

### backend/

API de Dentia. Actualmente contiene la aplicación FastAPI, configuración,
logging, endpoint de salud, engine SQLAlchemy, sesiones, base declarativa y
Alembic. Las capas de models, schemas, repositories, services y middleware
están preparadas para las siguientes fases.

### database/

Reservada para recursos auxiliares relacionados con la base de datos. Las
migraciones Alembic oficiales viven dentro de `backend/migrations/`.

### storage/

Almacenamiento local futuro para archivos clínicos y documentos. Su contenido
está protegido por `.gitignore` para impedir que información operativa o
sensible sea incorporada al repositorio.

### scripts/

Reservada para automatizaciones de instalación, mantenimiento, respaldo y
operación local.

### DOCS/

Contiene la documentación funcional, reglas de negocio, modelo de datos,
arquitectura técnica, roadmap, identidad visual e historial de decisiones.

## Persistencia

La configuración local utiliza:

```text
PostgreSQL: localhost:5432
Base: dentia
Driver: psycopg
ORM: SQLAlchemy
Migraciones: Alembic
```

La URL completa se obtiene exclusivamente desde `backend/.env`. El archivo
versionado `backend/.env.example` sirve como plantilla local.

La revisión inicial de Alembic no crea tablas de negocio.

## Validación de alcance

Hasta C003 no se han implementado:

- Funcionalidad clínica.
- Funcionalidad administrativa.
- Funcionalidad financiera.
- Autenticación.
- Tablas de negocio.
- Servicios de negocio.
- Integraciones externas.
