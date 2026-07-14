"""add reports permissions

Revision ID: 20260714_0013
Revises: 20260709_0012
Create Date: 2026-07-14 00:13:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260714_0013"
down_revision: str | Sequence[str] | None = "20260709_0012"
branch_labels = None
depends_on = None


PERMISSIONS = (
    (
        "reports.operational",
        "Ver reportes operativos",
        "reports",
        "Consultar métricas operativas de agenda, pacientes y seguimientos.",
    ),
    (
        "reports.financial",
        "Ver reportes financieros",
        "reports",
        "Consultar ingresos, producción clínica, ventas aprobadas y cartera.",
    ),
    (
        "reports.clinical_aggregate",
        "Ver agregados clínicos",
        "reports",
        "Consultar métricas clínicas agregadas sin contenido sensible individual.",
    ),
    (
        "reports.cross_site",
        "Ver reportes multisede",
        "reports",
        "Consultar reportes de todas las sedes autorizadas.",
    ),
    (
        "reports.own_scope",
        "Ver reportes propios",
        "reports",
        "Consultar reportes limitados al alcance propio del usuario.",
    ),
)


ROLE_PERMISSIONS = {
    "ADMINISTRATOR": [
        "reports.view",
        "reports.operational",
        "reports.financial",
        "reports.clinical_aggregate",
        "reports.cross_site",
    ],
    "DENTIST_ADMIN": [
        "reports.view",
        "reports.operational",
        "reports.financial",
        "reports.clinical_aggregate",
        "reports.cross_site",
    ],
    "DENTIST": [
        "reports.view",
        "reports.operational",
        "reports.clinical_aggregate",
        "reports.own_scope",
    ],
    "SECRETARY": [
        "reports.view",
        "reports.operational",
    ],
}


def _upsert_permissions() -> None:
    for code, name, module, description in PERMISSIONS:
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


def _assign_permissions() -> None:
    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        op.execute(
            sa.text(
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
                JOIN permisos p ON p.code = ANY(:permission_codes)
                WHERE r.code = :role_code
                  AND NOT EXISTS (
                    SELECT 1
                    FROM rol_permisos rp
                    WHERE rp.rol_id = r.id
                      AND rp.permiso_id = p.id
                  )
                """
            ).bindparams(
                sa.bindparam("role_code", value=role_code),
                sa.bindparam(
                    "permission_codes",
                    value=permission_codes,
                    type_=postgresql.ARRAY(sa.String()),
                ),
            )
        )


def upgrade() -> None:
    _upsert_permissions()
    _assign_permissions()


def downgrade() -> None:
    codes = [code for code, *_ in PERMISSIONS]
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos rp
            USING permisos p
            WHERE rp.permiso_id = p.id
              AND p.code = ANY(:codes)
            """
        ).bindparams(sa.bindparam("codes", value=codes, type_=postgresql.ARRAY(sa.String())))
    )
    op.execute(
        sa.text("DELETE FROM permisos WHERE code = ANY(:codes)").bindparams(
            sa.bindparam("codes", value=codes, type_=postgresql.ARRAY(sa.String()))
        )
    )
