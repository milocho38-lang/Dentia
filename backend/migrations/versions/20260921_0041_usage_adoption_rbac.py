"""add platform usage adoption permission

Revision ID: 20260921_0041
Revises: 20260921_0040
"""

from alembic import op
import sqlalchemy as sa


revision = "20260921_0041"
down_revision = "20260921_0040"
branch_labels = None
depends_on = None


PERMISSION_CODE = "platform.usage.view"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO permisos (
                id, code, nombre, modulo, descripcion, is_active,
                created_at, updated_at
            )
            VALUES (
                gen_random_uuid(), :code, :name, 'platform', :description,
                true, now(), now()
            )
            ON CONFLICT (code) DO UPDATE
            SET nombre = EXCLUDED.nombre,
                modulo = EXCLUDED.modulo,
                descripcion = EXCLUDED.descripcion,
                is_active = true,
                updated_at = now()
            """
        ).bindparams(
            code=PERMISSION_CODE,
            name="Ver métricas de adopción",
            description=(
                "Consultar métricas agregadas de uso y adopción sin contenido "
                "clínico ni identificadores de pacientes."
            ),
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos AS role_permission
            USING roles AS role, permisos AS permission
            WHERE role_permission.rol_id = role.id
              AND role_permission.permiso_id = permission.id
              AND permission.code = :permission_code
              AND role.code <> 'PLATFORM_ADMIN'
            """
        ).bindparams(permission_code=PERMISSION_CODE)
    )
    op.execute(
        sa.text(
            """
            INSERT INTO rol_permisos (
                id, empresa_id, rol_id, permiso_id, is_active,
                created_by, created_at, updated_at
            )
            SELECT gen_random_uuid(), role.empresa_id, role.id,
                   permission.id, true, role.created_by, now(), now()
            FROM roles AS role
            JOIN permisos AS permission ON permission.code = :permission_code
            WHERE role.code = 'PLATFORM_ADMIN'
            ON CONFLICT (rol_id, permiso_id) DO UPDATE
            SET empresa_id = EXCLUDED.empresa_id,
                is_active = true,
                updated_at = now()
            """
        ).bindparams(permission_code=PERMISSION_CODE)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos
            WHERE permiso_id = (
                SELECT id FROM permisos WHERE code = :permission_code
            )
            """
        ).bindparams(permission_code=PERMISSION_CODE)
    )
    op.execute(
        sa.text("DELETE FROM permisos WHERE code = :permission_code").bindparams(
            permission_code=PERMISSION_CODE
        )
    )
