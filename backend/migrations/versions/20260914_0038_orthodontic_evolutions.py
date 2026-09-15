"""add structured orthodontic evolutions and catalogs

Revision ID: 20260914_0038
Revises: 20260914_0037
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260914_0038"
down_revision = "20260914_0037"
branch_labels = None
depends_on = None


PERMISSIONS = (
    ("orthodontics.catalog.view", "Ver catálogos de Ortodoncia", "Consultar opciones clínicas base y propias de la empresa."),
    ("orthodontics.catalog.manage", "Administrar catálogos de Ortodoncia", "Crear y retirar opciones clínicas propias de la empresa."),
)

ROLE_PERMISSIONS = {
    "ADMINISTRATOR": ("orthodontics.catalog.view", "orthodontics.catalog.manage"),
    "DENTIST_ADMIN": ("orthodontics.catalog.view", "orthodontics.catalog.manage"),
    "DENTIST": ("orthodontics.catalog.view",),
}

ARCH_MATERIALS = (
    ("STEEL", "Acero"), ("AESTHETIC_ARCH", "Arco estético"),
    ("BIOFORCE", "Bioforce"), ("BIO_MEMALLOY", "Bio memalloy"),
    ("BLUE_ELGILLOY", "Blue elgilloy"), ("BRAIDED", "Braided"),
    ("REVERSE_CURVE", "Curva reversa"), ("DKL", "DKL"),
    ("MEMALLOY", "Memalloy"), ("NITI_NATURAL", "Niti natural"),
    ("NITI_THERMAL", "Niti térmico"), ("NITI_CU", "Niti cu"),
    ("NEOSENTALLOY", "Neosentalloy"), ("SENTALLOY", "Sentalloy"),
    ("TRI_MEMALLOY", "Tri memalloy"), ("TMA_RESOLVE", "TMA / Resolve"),
    ("SKL", "SKL"), ("WITH_POST", "Con poste"),
    ("NO_ARCH", "Sin arco"), ("NO_CHANGE", "Sin cambios"),
)

ARCH_SIZES = (
    ("SIZE_012", ".012"), ("SIZE_014", ".014"), ("SIZE_016", ".016"),
    ("SIZE_018", ".018"), ("SIZE_020", ".020"),
    ("SIZE_016X016", ".016 x .016"), ("SIZE_016X022", ".016 x .022"),
    ("SIZE_017X025", ".017 x .025"), ("SIZE_018X025", ".018 x .025"),
    ("SIZE_019X019", ".019 x .019"), ("SIZE_019X025", ".019 x .025"),
    ("SIZE_020X020", ".020 x .020"), ("SIZE_021X025", ".021 x .025"),
    ("SIZE_022X028", ".022 x .028"), ("NO_ARCH", "Sin arco"),
    ("NO_CHANGE", "Sin cambios"),
)

CONTROL_INTERVALS = tuple(
    [(f"WEEK_{value}", f"{value} semana" if value == 1 else f"{value} semanas", value, "WEEK") for value in range(1, 7)]
    + [(f"MONTH_{value}", f"{value} meses", value, "MONTH") for value in range(2, 13)]
)


def _seed_permissions() -> None:
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


def _seed_catalogs() -> None:
    statement = sa.text(
        """
        INSERT INTO orthodontic_catalog_options (
            id, empresa_id, catalog_type, scope, code, label, status,
            sort_order, interval_value, interval_unit, created_at, updated_at
        )
        VALUES (
            gen_random_uuid(), NULL, :catalog_type, 'DENTIA_BASE', :code, :label,
            'ACTIVE', :sort_order, :interval_value, :interval_unit, now(), now()
        )
        ON CONFLICT DO NOTHING
        """
    )
    for position, (code, label) in enumerate(ARCH_MATERIALS):
        op.execute(statement.bindparams(catalog_type="ARCH_MATERIAL", code=code, label=label, sort_order=position, interval_value=None, interval_unit=None))
    for position, (code, label) in enumerate(ARCH_SIZES):
        op.execute(statement.bindparams(catalog_type="ARCH_SIZE", code=code, label=label, sort_order=position, interval_value=None, interval_unit=None))
    for position, (code, label, value, unit) in enumerate(CONTROL_INTERVALS):
        op.execute(statement.bindparams(catalog_type="CONTROL_INTERVAL", code=code, label=label, sort_order=position, interval_value=value, interval_unit=unit))


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_orthodontic_cases_id_company", "orthodontic_cases", ["id", "empresa_id"]
    )
    op.create_table(
        "orthodontic_catalog_options",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("catalog_type", sa.String(40), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("label", sa.String(160), nullable=False),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("interval_value", sa.Integer(), nullable=True),
        sa.Column("interval_unit", sa.String(20), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("catalog_type IN ('ARCH_MATERIAL', 'ARCH_SIZE', 'CONTROL_INTERVAL')", name="orthodontic_catalog_option_type"),
        sa.CheckConstraint("scope IN ('DENTIA_BASE', 'TENANT')", name="orthodontic_catalog_option_scope"),
        sa.CheckConstraint("status IN ('ACTIVE', 'RETIRED')", name="orthodontic_catalog_option_status"),
        sa.CheckConstraint("(scope = 'DENTIA_BASE' AND empresa_id IS NULL) OR (scope = 'TENANT' AND empresa_id IS NOT NULL)", name="orthodontic_catalog_option_scope_company"),
        sa.CheckConstraint("(catalog_type = 'CONTROL_INTERVAL' AND interval_value IS NOT NULL AND interval_unit IN ('WEEK', 'MONTH')) OR (catalog_type <> 'CONTROL_INTERVAL' AND interval_value IS NULL AND interval_unit IS NULL)", name="orthodontic_catalog_option_interval"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["retired_by_user_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_orthodontic_catalog_base_code", "orthodontic_catalog_options", ["catalog_type", "code"], unique=True, postgresql_where=sa.text("scope = 'DENTIA_BASE'"))
    op.create_index("uq_orthodontic_catalog_tenant_code", "orthodontic_catalog_options", ["empresa_id", "catalog_type", "code"], unique=True, postgresql_where=sa.text("scope = 'TENANT'"))
    op.create_index("ix_orthodontic_catalog_visible", "orthodontic_catalog_options", ["empresa_id", "catalog_type", "status"])

    op.create_table(
        "orthodontic_evolutions",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("orthodontic_case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinical_evolution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schema_version", sa.String(20), server_default="ORT3_V1", nullable=False),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("upper_material_option_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("upper_material_code", sa.String(80), nullable=True),
        sa.Column("upper_material_label", sa.String(160), nullable=True),
        sa.Column("upper_size_option_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("upper_size_code", sa.String(80), nullable=True),
        sa.Column("upper_size_label", sa.String(160), nullable=True),
        sa.Column("lower_material_option_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lower_material_code", sa.String(80), nullable=True),
        sa.Column("lower_material_label", sa.String(160), nullable=True),
        sa.Column("lower_size_option_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lower_size_code", sa.String(80), nullable=True),
        sa.Column("lower_size_label", sa.String(160), nullable=True),
        sa.Column("upper_aligner_note", sa.String(500), nullable=True),
        sa.Column("lower_aligner_note", sa.String(500), nullable=True),
        sa.Column("elastic_type", sa.String(500), nullable=True),
        sa.Column("elastic_configuration", sa.String(1000), nullable=True),
        sa.Column("next_session_instructions", sa.Text(), nullable=True),
        sa.Column("next_control_option_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("next_control_code", sa.String(80), nullable=True),
        sa.Column("next_control_label", sa.String(160), nullable=True),
        sa.Column("next_control_value", sa.Integer(), nullable=True),
        sa.Column("next_control_unit", sa.String(20), nullable=True),
        sa.Column("suggested_next_control_date", sa.Date(), nullable=True),
        sa.Column("alert_text", sa.String(2000), nullable=True),
        sa.Column("alert_active", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("orthodontic_payload_hash", sa.String(128), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("row_version >= 1", name="orthodontic_evolution_row_version_positive"),
        sa.CheckConstraint("next_control_unit IS NULL OR next_control_unit IN ('WEEK', 'MONTH')", name="orthodontic_evolution_control_unit"),
        sa.ForeignKeyConstraint(["orthodontic_case_id", "empresa_id"], ["orthodontic_cases.id", "orthodontic_cases.empresa_id"], name="fk_orthodontic_evolution_case_company", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinical_evolution_id"], ["evoluciones_clinicas.id"], ondelete="RESTRICT"),
        *[sa.ForeignKeyConstraint([column], ["orthodontic_catalog_options.id"], ondelete="RESTRICT") for column in ("upper_material_option_id", "upper_size_option_id", "lower_material_option_id", "lower_size_option_id", "next_control_option_id")],
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinical_evolution_id", name="uq_orthodontic_evolution_clinical_evolution"),
    )
    op.create_index("ix_orthodontic_evolutions_case_created", "orthodontic_evolutions", ["empresa_id", "orthodontic_case_id", "created_at"])

    op.create_table(
        "orthodontic_evolution_mini_screws",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("orthodontic_evolution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("screw_type", sa.String(30), nullable=False),
        sa.Column("location", sa.String(60), nullable=False),
        sa.Column("material", sa.String(30), nullable=False),
        sa.Column("measurement", sa.String(160), nullable=False),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("screw_type IN ('SELF_TAPPING', 'SELF_DRILLING')", name="orthodontic_mini_screw_type"),
        sa.CheckConstraint("location IN ('INTERRADICULAR', 'PALATAL', 'RETROMOLAR', 'INFRAZYGOMATIC_OR_ANTERIOR_ALVEOLAR')", name="orthodontic_mini_screw_location"),
        sa.CheckConstraint("material IN ('TITANIUM', 'STEEL')", name="orthodontic_mini_screw_material"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["orthodontic_evolution_id"], ["orthodontic_evolutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orthodontic_mini_screws_evolution", "orthodontic_evolution_mini_screws", ["orthodontic_evolution_id", "sort_order"])
    _seed_catalogs()
    _seed_permissions()


def downgrade() -> None:
    codes = tuple(code for code, _, _ in PERMISSIONS)
    op.execute(sa.text("DELETE FROM rol_permisos WHERE permiso_id IN (SELECT id FROM permisos WHERE code IN :codes)").bindparams(sa.bindparam("codes", expanding=True, value=codes)))
    op.execute(sa.text("DELETE FROM permisos WHERE code IN :codes").bindparams(sa.bindparam("codes", expanding=True, value=codes)))
    op.drop_index("ix_orthodontic_mini_screws_evolution", table_name="orthodontic_evolution_mini_screws")
    op.drop_table("orthodontic_evolution_mini_screws")
    op.drop_index("ix_orthodontic_evolutions_case_created", table_name="orthodontic_evolutions")
    op.drop_table("orthodontic_evolutions")
    op.drop_index("ix_orthodontic_catalog_visible", table_name="orthodontic_catalog_options")
    op.drop_index("uq_orthodontic_catalog_tenant_code", table_name="orthodontic_catalog_options")
    op.drop_index("uq_orthodontic_catalog_base_code", table_name="orthodontic_catalog_options")
    op.drop_table("orthodontic_catalog_options")
    op.drop_constraint("uq_orthodontic_cases_id_company", "orthodontic_cases", type_="unique")
