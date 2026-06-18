# Dentia

Plataforma de gestión odontológica.

## Tecnologías

Frontend:
- Next.js
- React
- TypeScript
- Tailwind CSS

Backend:
- FastAPI
- SQLAlchemy
- Alembic
- psycopg
- PostgreSQL

## Documentación

Toda la documentación funcional y técnica se encuentra en la carpeta DOCS.

## Backend local

Requisitos:

- Python 3.12 o superior.
- PostgreSQL disponible en `localhost:5432`.
- Base de datos local `dentia`.
- Rol local `dentia`.

Creación inicial de PostgreSQL:

```bash
createuser --login --pwprompt dentia
createdb --owner=dentia dentia
```

Para coincidir con `.env.example`, use `dentia` como contraseña únicamente en
el entorno local de desarrollo. En otros entornos se debe definir una
credencial diferente mediante `DATABASE_URL`.

Preparación:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

En Windows PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Migraciones

Todos los comandos Alembic deben ejecutarse desde `backend/`.

Aplicar migraciones:

```bash
alembic -c alembic.ini upgrade head
```

Consultar la revisión actual:

```bash
alembic -c alembic.ini current
```

Revertir una revisión:

```bash
alembic -c alembic.ini downgrade -1
```

Volver a la base vacía:

```bash
alembic -c alembic.ini downgrade base
```

Crear una migración futura:

```bash
alembic -c alembic.ini revision --autogenerate -m "descripcion"
```

La migración inicial de C004 no crea tablas de negocio. Únicamente establece la
línea base de Alembic.

## Instalación inicial de seguridad

Después de aplicar todas las migraciones, ejecute desde `backend/`:

```bash
python -m app.cli.bootstrap
```

También puede proporcionar los datos no sensibles como argumentos:

```bash
python -m app.cli.bootstrap \
  --company-name "Mi Consultorio" \
  --company-slug "mi-consultorio" \
  --site-name "Sede Principal" \
  --admin-name "Administrador" \
  --admin-email "admin@consultorio.local"
```

La contraseña siempre se solicita de forma oculta por consola. El comando solo
funciona cuando no existen empresas ni usuarios y realiza toda la instalación
en una única transacción.
