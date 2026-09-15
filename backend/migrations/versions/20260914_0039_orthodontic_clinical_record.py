"""add versioned orthodontic clinical record

Revision ID: 20260914_0039
Revises: 20260914_0038
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260914_0039"
down_revision = "20260914_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orthodontic_clinical_records",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("orthodontic_case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["orthodontic_case_id", "empresa_id"],
            ["orthodontic_cases.id", "orthodontic_cases.empresa_id"],
            name="fk_orthodontic_record_case_company",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "orthodontic_case_id", name="uq_orthodontic_record_case"
        ),
        sa.UniqueConstraint(
            "id", "empresa_id", name="uq_orthodontic_records_id_company"
        ),
    )
    op.create_index(
        "ix_orthodontic_records_patient",
        "orthodontic_clinical_records",
        ["empresa_id", "paciente_id"],
    )

    op.create_table(
        "orthodontic_clinical_record_versions",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT", nullable=False),
        sa.Column("schema_version", sa.String(60), nullable=False),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "content",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "schema_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "content_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("based_on_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("clinical_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone_name", sa.String(80), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finalized_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'FINALIZED')",
            name="orthodontic_record_version_status",
        ),
        sa.CheckConstraint(
            "version_number >= 1 AND row_version >= 1",
            name="orthodontic_record_version_positive_versions",
        ),
        sa.CheckConstraint(
            "(status = 'DRAFT' AND finalized_at IS NULL "
            "AND finalized_by_user_id IS NULL AND content_hash IS NULL "
            "AND content_snapshot IS NULL) OR "
            "(status = 'FINALIZED' AND finalized_at IS NOT NULL "
            "AND finalized_by_user_id IS NOT NULL AND content_hash IS NOT NULL "
            "AND content_snapshot IS NOT NULL)",
            name="orthodontic_record_version_finalization_state",
        ),
        sa.ForeignKeyConstraint(
            ["record_id", "empresa_id"],
            [
                "orthodontic_clinical_records.id",
                "orthodontic_clinical_records.empresa_id",
            ],
            name="fk_orthodontic_record_version_record_company",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["based_on_version_id"],
            ["orthodontic_clinical_record_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["finalized_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "record_id",
            "version_number",
            name="uq_orthodontic_record_version_number",
        ),
    )
    op.create_index(
        "uq_orthodontic_record_single_draft",
        "orthodontic_clinical_record_versions",
        ["record_id"],
        unique=True,
        postgresql_where=sa.text("status = 'DRAFT'"),
    )
    op.create_index(
        "ix_orthodontic_record_versions_history",
        "orthodontic_clinical_record_versions",
        ["empresa_id", "record_id", "version_number"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_orthodontic_record_versions_history",
        table_name="orthodontic_clinical_record_versions",
    )
    op.drop_index(
        "uq_orthodontic_record_single_draft",
        table_name="orthodontic_clinical_record_versions",
    )
    op.drop_table("orthodontic_clinical_record_versions")
    op.drop_index(
        "ix_orthodontic_records_patient",
        table_name="orthodontic_clinical_records",
    )
    op.drop_table("orthodontic_clinical_records")
