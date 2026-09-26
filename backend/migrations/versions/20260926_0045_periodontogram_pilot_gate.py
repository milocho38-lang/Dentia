"""add controlled periodontogram pilot gate

Revision ID: 20260926_0045
Revises: 20260923_0044
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260926_0045"
down_revision = "20260923_0044"
branch_labels = None
depends_on = None


PERMISSIONS = (
    (
        "periodontogram.pilot.view",
        "Ver piloto de Periodontograma",
        "Consultar la habilitación piloto de Periodontograma y sus odontólogos autorizados.",
    ),
    (
        "periodontogram.pilot.manage",
        "Administrar piloto de Periodontograma",
        "Habilitar el piloto por empresa y autorizar o revocar odontólogos participantes.",
    ),
)


def _seed_permissions() -> None:
    for code, name, description in PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permisos (
                    id, code, nombre, modulo, descripcion, is_active,
                    created_at, updated_at
                )
                VALUES (
                    gen_random_uuid(), :code, :name, 'periodontogram',
                    :description, true, now(), now()
                )
                ON CONFLICT (code) DO UPDATE
                SET nombre = EXCLUDED.nombre,
                    modulo = EXCLUDED.modulo,
                    descripcion = EXCLUDED.descripcion,
                    is_active = true,
                    updated_at = now()
                """
            ).bindparams(code=code, name=name, description=description)
        )

    permission_codes = [item[0] for item in PERMISSIONS]
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos AS role_permission
            USING roles AS role, permisos AS permission
            WHERE role_permission.rol_id = role.id
              AND role_permission.permiso_id = permission.id
              AND permission.code = ANY(:permission_codes)
              AND role.code <> 'PLATFORM_ADMIN'
            """
        ).bindparams(permission_codes=permission_codes)
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
            JOIN permisos AS permission
              ON permission.code = ANY(:permission_codes)
            WHERE role.code = 'PLATFORM_ADMIN'
            ON CONFLICT (rol_id, permiso_id) DO UPDATE
            SET empresa_id = EXCLUDED.empresa_id,
                is_active = true,
                updated_at = now()
            """
        ).bindparams(permission_codes=permission_codes)
    )


def upgrade() -> None:
    op.create_table(
        "periodontogram_pilot_company_gates",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enabled_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "(is_enabled IS TRUE AND enabled_at IS NOT NULL "
            "AND enabled_by_user_id IS NOT NULL AND disabled_at IS NULL "
            "AND disabled_by_user_id IS NULL) OR is_enabled IS FALSE",
            name="periodontogram_pilot_company_gate_state",
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["enabled_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["disabled_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", name="uq_periodontogram_pilot_company_gate"),
    )
    op.create_index(
        "ix_periodontogram_pilot_company_gates_empresa_id",
        "periodontogram_pilot_company_gates",
        ["empresa_id"],
    )
    op.create_table(
        "periodontogram_pilot_dentist_authorizations",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("odontologo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("authorized_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revocation_reason", sa.String(300), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "(is_active IS TRUE AND revoked_at IS NULL "
            "AND revoked_by_user_id IS NULL) OR "
            "(is_active IS FALSE AND revoked_at IS NOT NULL "
            "AND revoked_by_user_id IS NOT NULL)",
            name="periodontogram_pilot_dentist_authorization_state",
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["odontologo_id", "empresa_id"],
            ["odontologos.id", "odontologos.empresa_id"],
            name="fk_periodontogram_pilot_dentist_company",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["authorized_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_periodontogram_pilot_company_active",
        "periodontogram_pilot_dentist_authorizations",
        ["empresa_id", "is_active"],
    )
    op.create_index(
        "uq_periodontogram_pilot_active_dentist",
        "periodontogram_pilot_dentist_authorizations",
        ["empresa_id", "odontologo_id"],
        unique=True,
        postgresql_where=sa.text("is_active IS TRUE"),
    )
    _seed_permissions()


def downgrade() -> None:
    permission_codes = [item[0] for item in PERMISSIONS]
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos
            WHERE permiso_id IN (
                SELECT id FROM permisos WHERE code = ANY(:permission_codes)
            )
            """
        ).bindparams(permission_codes=permission_codes)
    )
    op.execute(
        sa.text(
            "DELETE FROM permisos WHERE code = ANY(:permission_codes)"
        ).bindparams(permission_codes=permission_codes)
    )
    op.drop_index(
        "uq_periodontogram_pilot_active_dentist",
        table_name="periodontogram_pilot_dentist_authorizations",
    )
    op.drop_index(
        "ix_periodontogram_pilot_company_active",
        table_name="periodontogram_pilot_dentist_authorizations",
    )
    op.drop_table("periodontogram_pilot_dentist_authorizations")
    op.drop_index(
        "ix_periodontogram_pilot_company_gates_empresa_id",
        table_name="periodontogram_pilot_company_gates",
    )
    op.drop_table("periodontogram_pilot_company_gates")
