"""add tenant-safe Dentalink patient import sources and references.

Downgrade is intentionally fail-closed after any patient has been imported.
This migration never deletes or silently detaches imported provenance.

Revision ID: 20261006_0047
Revises: 20261006_0046
Create Date: 2026-10-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261006_0047"
down_revision: str | Sequence[str] | None = "20261006_0046"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_pacientes_id_empresa", "pacientes", ["id", "empresa_id"]
    )
    op.create_table(
        "patient_import_sources",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_system", sa.String(length=40), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "source_system", "code", name="uq_patient_import_source_code"),
        sa.UniqueConstraint("id", "company_id", name="uq_patient_import_source_id_company"),
    )
    op.create_index("ix_patient_import_sources_company_id", "patient_import_sources", ["company_id"])
    op.create_table(
        "patient_external_references",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_patient_id", sa.String(length=120), nullable=False),
        sa.Column("source_file_sha256", sa.String(length=64), nullable=False),
        sa.Column("imported_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["imported_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["source_id", "company_id"],
            ["patient_import_sources.id", "patient_import_sources.company_id"],
            name="fk_patient_external_reference_tenant_source",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id", "company_id"],
            ["pacientes.id", "pacientes.empresa_id"],
            name="fk_patient_external_reference_tenant_patient",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "source_id", "source_patient_id", name="uq_patient_external_reference_source"),
    )
    op.create_index(
        "ix_patient_external_reference_company_patient",
        "patient_external_references",
        ["company_id", "patient_id"],
    )
    op.execute(sa.text("""
        INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
        VALUES (gen_random_uuid(), 'patients.import', 'Importar pacientes', 'patients',
          'Previsualizar y confirmar importaciones de pacientes desde sistemas autorizados.', true, now(), now())
        ON CONFLICT (code) DO NOTHING
    """))
    op.execute(sa.text("""
        INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at)
        SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by, now(), now()
        FROM roles r JOIN permisos p ON p.code = 'patients.import'
        WHERE r.code IN ('ADMINISTRATOR', 'DENTIST_ADMIN') AND NOT EXISTS (
          SELECT 1 FROM rol_permisos rp WHERE rp.rol_id = r.id AND rp.permiso_id = p.id)
    """))


def downgrade() -> None:
    connection = op.get_bind()
    reference_count = connection.execute(
        sa.text("SELECT count(*) FROM patient_external_references")
    ).scalar_one()
    if reference_count:
        raise RuntimeError(
            "Downgrade bloqueado: existen referencias de pacientes importados. "
            "No se eliminarán referencias, pacientes, orígenes ni permisos; aplique un forward fix."
        )

    op.execute(sa.text("""
        DELETE FROM rol_permisos
        WHERE permiso_id = (SELECT id FROM permisos WHERE code = 'patients.import')
    """))
    op.execute(sa.text("DELETE FROM permisos WHERE code = 'patients.import'"))
    op.drop_index("ix_patient_external_reference_company_patient", table_name="patient_external_references")
    op.drop_table("patient_external_references")
    op.drop_index("ix_patient_import_sources_company_id", table_name="patient_import_sources")
    op.drop_table("patient_import_sources")
    op.drop_constraint("uq_pacientes_id_empresa", "pacientes", type_="unique")
