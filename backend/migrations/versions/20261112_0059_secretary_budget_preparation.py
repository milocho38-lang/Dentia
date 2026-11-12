"""grant secretary limited budget preparation permissions

Revision ID: 20261112_0059
Revises: 20261111_0058
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261112_0059"
down_revision = "20261111_0058"
branch_labels = None
depends_on = None


TRACKING_TABLE = "permiso_secretaria_presupuesto_0059"
GRANTS = (
    "treatments.prepare_budget",
    "budgets.create",
    "consent.paper.read",
    "consent.paper.prepare",
)


def upgrade() -> None:
    op.create_table(
        TRACKING_TABLE,
        sa.Column("role_permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("role_permission_id"),
    )
    op.execute(sa.text("""
        INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
        VALUES (
            gen_random_uuid(), 'treatments.prepare_budget',
            'Preparar tratamientos para presupuesto', 'treatments',
            'Crear tratamientos y administrar procedimientos pendientes sin integración clínica.',
            true, now(), now()
        )
        ON CONFLICT (code) DO UPDATE SET
            nombre=EXCLUDED.nombre, modulo=EXCLUDED.modulo,
            descripcion=EXCLUDED.descripcion, is_active=true, updated_at=now()
    """))
    for code in GRANTS:
        op.execute(sa.text(f"""
            WITH inserted AS (
                INSERT INTO rol_permisos (
                    id, empresa_id, rol_id, permiso_id, is_active,
                    created_by, created_at, updated_at
                )
                SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true,
                       r.created_by, now(), now()
                FROM roles r
                JOIN permisos p ON p.code = :code
                WHERE r.code = 'SECRETARY'
                  AND NOT EXISTS (
                      SELECT 1 FROM rol_permisos rp
                      WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
                  )
                RETURNING id
            )
            INSERT INTO {TRACKING_TABLE} (role_permission_id)
            SELECT id FROM inserted
        """).bindparams(code=code))


def downgrade() -> None:
    op.execute(sa.text(f"""
        DELETE FROM rol_permisos
        WHERE id IN (SELECT role_permission_id FROM {TRACKING_TABLE})
    """))
    op.drop_table(TRACKING_TABLE)
    op.execute(sa.text("""
        DELETE FROM rol_permisos
        WHERE permiso_id = (
            SELECT id FROM permisos WHERE code = 'treatments.prepare_budget'
        )
    """))
    op.execute(sa.text("DELETE FROM permisos WHERE code = 'treatments.prepare_budget'"))
