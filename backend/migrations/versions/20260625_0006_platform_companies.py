"""add platform company administration

Revision ID: 20260625_0006
Revises: 20260621_0005
Create Date: 2026-06-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260625_0006"
down_revision: str | Sequence[str] | None = "20260621_0005"
branch_labels = None
depends_on = None


PLATFORM_PERMISSIONS = (
    (
        "platform.companies.view",
        "Ver empresas de plataforma",
        "platform",
        "Consultar empresas administradas por la plataforma.",
    ),
    (
        "platform.companies.manage",
        "Administrar empresas de plataforma",
        "platform",
        "Crear, activar e inactivar empresas desde plataforma.",
    ),
)


def upgrade() -> None:
    op.add_column("empresas", sa.Column("pais", sa.String(100), nullable=True))

    for code, name, module, description in PLATFORM_PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active)
                VALUES (gen_random_uuid(), :code, :name, :module, :description, true)
                ON CONFLICT (code) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    modulo = EXCLUDED.modulo,
                    descripcion = EXCLUDED.descripcion,
                    is_active = true
                """
            ).bindparams(
                code=code,
                name=name,
                module=module,
                description=description,
            )
        )

    op.execute(
        """
        INSERT INTO roles (
            id, empresa_id, code, nombre, descripcion, is_system, is_active, created_by
        )
        SELECT
            gen_random_uuid(),
            e.id,
            'PLATFORM_ADMIN',
            'Administrador de plataforma',
            'Administración de empresas y clínicas de la plataforma.',
            true,
            true,
            e.created_by
        FROM empresas e
        WHERE NOT EXISTS (
            SELECT 1
            FROM roles r
            WHERE r.empresa_id = e.id
              AND r.code = 'PLATFORM_ADMIN'
        )
        """
    )
    op.execute(
        """
        INSERT INTO rol_permisos (
            id, empresa_id, rol_id, permiso_id, is_active, created_by
        )
        SELECT
            gen_random_uuid(),
            r.empresa_id,
            r.id,
            p.id,
            true,
            r.created_by
        FROM roles r
        JOIN permisos p ON p.code IN (
            'platform.companies.view',
            'platform.companies.manage'
        )
        WHERE r.code = 'PLATFORM_ADMIN'
          AND NOT EXISTS (
            SELECT 1
            FROM rol_permisos rp
            WHERE rp.rol_id = r.id
              AND rp.permiso_id = p.id
          )
        """
    )
    op.execute(
        """
        INSERT INTO usuario_roles (
            id, empresa_id, usuario_id, rol_id, is_active, created_by
        )
        SELECT
            gen_random_uuid(),
            e.id,
            e.created_by,
            r.id,
            true,
            e.created_by
        FROM empresas e
        JOIN usuarios u ON u.id = e.created_by
        JOIN roles r
          ON r.empresa_id = e.id
         AND r.code = 'PLATFORM_ADMIN'
        WHERE e.created_by IS NOT NULL
          AND u.empresa_id = e.id
          AND NOT EXISTS (
            SELECT 1
            FROM usuario_roles ur
            WHERE ur.usuario_id = e.created_by
              AND ur.rol_id = r.id
          )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM usuario_roles ur
        USING roles r
        WHERE ur.rol_id = r.id
          AND r.code = 'PLATFORM_ADMIN'
        """
    )
    op.execute(
        """
        DELETE FROM rol_permisos rp
        USING roles r
        WHERE rp.rol_id = r.id
          AND r.code = 'PLATFORM_ADMIN'
        """
    )
    op.execute("DELETE FROM roles WHERE code = 'PLATFORM_ADMIN'")
    op.execute(
        """
        DELETE FROM permisos
        WHERE code IN (
            'platform.companies.view',
            'platform.companies.manage'
        )
        """
    )
    op.drop_column("empresas", "pais")
