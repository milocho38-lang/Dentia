"""add orthodontic patient cases

Revision ID: 20260914_0037
Revises: 20260914_0036
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260914_0037"
down_revision = "20260914_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orthodontic_cases",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("historia_clinica_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sede_principal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("responsible_dentist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("closure_reason_code", sa.String(40), nullable=True),
        sa.Column("closure_notes", sa.Text(), nullable=True),
        sa.Column("treatment_plan", sa.Text(), nullable=True),
        sa.Column("current_appliance_summary", sa.Text(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'SUSPENDED', 'COMPLETED')", name="orthodontic_case_status"),
        sa.CheckConstraint("row_version >= 1", name="orthodontic_case_row_version_positive"),
        sa.CheckConstraint("(status = 'COMPLETED' AND completed_at IS NOT NULL) OR (status <> 'COMPLETED' AND completed_at IS NULL)", name="orthodontic_case_completion_state"),
        sa.CheckConstraint("(status = 'DRAFT' AND started_at IS NULL) OR (status <> 'DRAFT' AND started_at IS NOT NULL)", name="orthodontic_case_started_state"),
        sa.CheckConstraint("(status = 'COMPLETED' AND closed_by_user_id IS NOT NULL AND closure_reason_code IN ('COMPLETED', 'DISCONTINUED')) OR (status <> 'COMPLETED' AND closed_by_user_id IS NULL AND closure_reason_code IS NULL AND closure_notes IS NULL)", name="orthodontic_case_closure_state"),
        sa.CheckConstraint("closure_reason_code <> 'DISCONTINUED' OR closure_notes IS NOT NULL", name="orthodontic_case_discontinuation_reason"),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["historia_clinica_id"], ["historias_clinicas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsible_dentist_id", "empresa_id"], ["odontologos.id", "odontologos.empresa_id"], name="fk_orthodontic_case_responsible_company", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sede_principal_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_orthodontic_case_open_patient",
        "orthodontic_cases",
        ["empresa_id", "paciente_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('DRAFT', 'ACTIVE', 'SUSPENDED')"),
    )
    op.create_index(
        "ix_orthodontic_cases_patient_created",
        "orthodontic_cases",
        ["empresa_id", "paciente_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_orthodontic_cases_patient_created", table_name="orthodontic_cases")
    op.drop_index("uq_orthodontic_case_open_patient", table_name="orthodontic_cases")
    op.drop_table("orthodontic_cases")
