"""add orthodontics entitlement and dentist seats

Revision ID: 20260914_0036
Revises: 20260801_0035
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260914_0036"
down_revision = "20260801_0035"
branch_labels = None
depends_on = None


PERMISSIONS = (
    ("orthodontics.entitlement.view", "Ver habilitación de Ortodoncia", "Consultar la habilitación y los cupos de Ortodoncia de una empresa."),
    ("orthodontics.entitlement.manage", "Administrar habilitación de Ortodoncia", "Habilitar, deshabilitar y ajustar los cupos comerciales de Ortodoncia."),
    ("orthodontics.assignment.view", "Ver asignaciones de Ortodoncia", "Consultar odontólogos y cupos asignados al módulo de Ortodoncia."),
    ("orthodontics.assignment.manage", "Administrar asignaciones de Ortodoncia", "Asignar y retirar cupos de Ortodoncia a odontólogos de la empresa."),
)

ROLE_PERMISSIONS = {
    "PLATFORM_ADMIN": (
        "orthodontics.entitlement.view",
        "orthodontics.entitlement.manage",
    ),
    "ADMINISTRATOR": (
        "orthodontics.entitlement.view",
        "orthodontics.assignment.view",
        "orthodontics.assignment.manage",
    ),
    "DENTIST_ADMIN": (
        "orthodontics.entitlement.view",
        "orthodontics.assignment.view",
        "orthodontics.assignment.manage",
    ),
}


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_odontologos_id_empresa",
        "odontologos",
        ["id", "empresa_id"],
    )
    op.create_table(
        "orthodontics_entitlements",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="DISABLED", nullable=False),
        sa.Column("seat_limit", sa.Integer(), server_default="0", nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("seat_limit >= 0", name="orthodontics_entitlement_seat_limit_nonnegative"),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUSPENDED', 'DISABLED')", name="orthodontics_entitlement_status"),
        sa.CheckConstraint("effective_until IS NULL OR effective_from IS NULL OR effective_until >= effective_from", name="orthodontics_entitlement_effective_range"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", name="uq_orthodontics_entitlements_company"),
        sa.UniqueConstraint("id", "empresa_id", name="uq_orthodontics_entitlements_id_company"),
    )
    op.create_index("ix_orthodontics_entitlements_empresa_id", "orthodontics_entitlements", ["empresa_id"])
    op.create_table(
        "orthodontics_dentist_assignments",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entitlement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("odontologo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revocation_reason", sa.String(300), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("(is_active IS TRUE AND revoked_at IS NULL) OR (is_active IS FALSE AND revoked_at IS NOT NULL)", name="orthodontics_assignment_revocation_state"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["entitlement_id", "empresa_id"], ["orthodontics_entitlements.id", "orthodontics_entitlements.empresa_id"], name="fk_orthodontics_assignment_entitlement_company", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["odontologo_id", "empresa_id"], ["odontologos.id", "odontologos.empresa_id"], name="fk_orthodontics_assignment_dentist_company", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orthodontics_assignment_company_active", "orthodontics_dentist_assignments", ["empresa_id", "is_active"])
    op.create_index(
        "uq_orthodontics_assignment_active_dentist",
        "orthodontics_dentist_assignments",
        ["empresa_id", "odontologo_id"],
        unique=True,
        postgresql_where=sa.text("is_active IS TRUE"),
    )

    for code, name, description in PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
                VALUES (gen_random_uuid(), :code, :name, 'orthodontics', :description, true, now(), now())
                ON CONFLICT (code) DO UPDATE
                SET nombre = EXCLUDED.nombre,
                    modulo = EXCLUDED.modulo,
                    descripcion = EXCLUDED.descripcion,
                    is_active = true,
                    updated_at = now()
                """
            ).bindparams(code=code, name=name, description=description)
        )
    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        for permission_code in permission_codes:
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
                    WHERE role.code = :role_code
                      AND NOT EXISTS (
                          SELECT 1 FROM rol_permisos AS existing
                          WHERE existing.rol_id = role.id
                            AND existing.permiso_id = permission.id
                      )
                    """
                ).bindparams(role_code=role_code, permission_code=permission_code)
            )


def downgrade() -> None:
    codes = tuple(code for code, _, _ in PERMISSIONS)
    op.execute(
        sa.text(
            "DELETE FROM rol_permisos WHERE permiso_id IN (SELECT id FROM permisos WHERE code IN :codes)"
        ).bindparams(sa.bindparam("codes", expanding=True, value=codes))
    )
    op.execute(
        sa.text("DELETE FROM permisos WHERE code IN :codes").bindparams(
            sa.bindparam("codes", expanding=True, value=codes)
        )
    )
    op.drop_index("uq_orthodontics_assignment_active_dentist", table_name="orthodontics_dentist_assignments")
    op.drop_index("ix_orthodontics_assignment_company_active", table_name="orthodontics_dentist_assignments")
    op.drop_table("orthodontics_dentist_assignments")
    op.drop_index("ix_orthodontics_entitlements_empresa_id", table_name="orthodontics_entitlements")
    op.drop_table("orthodontics_entitlements")
    op.drop_constraint("uq_odontologos_id_empresa", "odontologos", type_="unique")
