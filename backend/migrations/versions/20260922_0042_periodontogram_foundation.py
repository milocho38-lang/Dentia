"""add periodontogram clinical foundation

Revision ID: 20260922_0042
Revises: 20260921_0041
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260922_0042"
down_revision = "20260921_0041"
branch_labels = None
depends_on = None


PERMISSIONS = (
    ("periodontogram.view", "Ver periodontogramas", "Consultar periodontogramas e historial autorizado del paciente."),
    ("periodontogram.create", "Crear periodontogramas", "Crear un control periodontal independiente en borrador."),
    ("periodontogram.update_draft", "Actualizar borradores de periodontograma", "Modificar datos periodontales mientras la versión esté en borrador."),
    ("periodontogram.finalize", "Finalizar periodontogramas", "Finalizar y congelar una versión de periodontograma."),
    ("periodontogram.correct", "Corregir periodontogramas", "Crear una nueva versión correctiva sin alterar el histórico finalizado."),
)
AUTHORIZED_ROLES = ("DENTIST", "DENTIST_ADMIN")


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

    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos AS role_permission
            USING roles AS role, permisos AS permission
            WHERE role_permission.rol_id = role.id
              AND role_permission.permiso_id = permission.id
              AND permission.code = ANY(:permission_codes)
              AND role.code <> ALL(:authorized_roles)
            """
        ).bindparams(
            permission_codes=[item[0] for item in PERMISSIONS],
            authorized_roles=list(AUTHORIZED_ROLES),
        )
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
            WHERE role.code = ANY(:authorized_roles)
            ON CONFLICT (rol_id, permiso_id) DO UPDATE
            SET empresa_id = EXCLUDED.empresa_id,
                is_active = true,
                updated_at = now()
            """
        ).bindparams(
            permission_codes=[item[0] for item in PERMISSIONS],
            authorized_roles=list(AUTHORIZED_ROLES),
        )
    )


def upgrade() -> None:
    op.create_table(
        "periodontal_exams",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("responsible_dentist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT", nullable=False),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("clinical_date", sa.Date(), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('DRAFT', 'FINALIZED')", name="periodontal_exam_status"),
        sa.CheckConstraint("row_version >= 1", name="periodontal_exam_row_version_positive"),
        sa.CheckConstraint(
            "(status = 'DRAFT' AND finalized_at IS NULL) OR "
            "(status = 'FINALIZED' AND finalized_at IS NOT NULL)",
            name="periodontal_exam_finalization_state",
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["responsible_dentist_id", "empresa_id"],
            ["odontologos.id", "odontologos.empresa_id"],
            name="fk_periodontal_exam_dentist_company",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "empresa_id", name="uq_periodontal_exams_id_company"),
    )
    op.create_index(
        "ix_periodontal_exams_patient_date",
        "periodontal_exams",
        ["empresa_id", "paciente_id", "clinical_date"],
    )

    op.create_table(
        "periodontal_exam_versions",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT", nullable=False),
        sa.Column("schema_version", sa.String(60), nullable=False),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("snapshot_hash", sa.String(64), nullable=True),
        sa.Column("supersedes_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finalized_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('DRAFT', 'FINALIZED')", name="periodontal_exam_version_status"),
        sa.CheckConstraint("version_number >= 1 AND row_version >= 1", name="periodontal_exam_version_positive_versions"),
        sa.CheckConstraint(
            "(status = 'DRAFT' AND finalized_at IS NULL AND finalized_by_user_id IS NULL "
            "AND snapshot IS NULL AND snapshot_hash IS NULL) OR "
            "(status = 'FINALIZED' AND finalized_at IS NOT NULL AND finalized_by_user_id IS NOT NULL "
            "AND snapshot IS NOT NULL AND snapshot_hash IS NOT NULL)",
            name="periodontal_exam_version_finalization_state",
        ),
        sa.CheckConstraint(
            "supersedes_version_id IS NULL OR correction_reason IS NOT NULL",
            name="periodontal_exam_version_correction_reason",
        ),
        sa.ForeignKeyConstraint(
            ["exam_id", "empresa_id"],
            ["periodontal_exams.id", "periodontal_exams.empresa_id"],
            name="fk_periodontal_exam_version_exam_company",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["supersedes_version_id"], ["periodontal_exam_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["finalized_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "empresa_id", name="uq_periodontal_exam_versions_id_company"),
        sa.UniqueConstraint(
            "id",
            "exam_id",
            "empresa_id",
            name="uq_periodontal_exam_versions_id_exam_company",
        ),
        sa.UniqueConstraint("exam_id", "version_number", name="uq_periodontal_exam_version_number"),
    )
    op.create_index(
        "uq_periodontal_exam_single_draft",
        "periodontal_exam_versions",
        ["exam_id"],
        unique=True,
        postgresql_where=sa.text("status = 'DRAFT'"),
    )
    op.create_index(
        "ix_periodontal_exam_versions_history",
        "periodontal_exam_versions",
        ["empresa_id", "exam_id", "version_number"],
    )
    op.create_foreign_key(
        "fk_periodontal_exam_current_version_company",
        "periodontal_exams",
        "periodontal_exam_versions",
        ["current_version_id", "id", "empresa_id"],
        ["id", "exam_id", "empresa_id"],
        ondelete="RESTRICT",
    )
    op.execute(
        """
        CREATE FUNCTION prevent_finalized_periodontal_version_mutation()
        RETURNS trigger AS $$
        BEGIN
            IF OLD.status = 'FINALIZED' THEN
                RAISE EXCEPTION 'Finalized periodontal exam versions are immutable';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_periodontal_version_immutable
        BEFORE UPDATE OR DELETE ON periodontal_exam_versions
        FOR EACH ROW EXECUTE FUNCTION prevent_finalized_periodontal_version_mutation()
        """
    )
    _seed_permissions()


def downgrade() -> None:
    permission_codes = [item[0] for item in PERMISSIONS]
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos
            WHERE permiso_id IN (SELECT id FROM permisos WHERE code = ANY(:codes))
            """
        ).bindparams(codes=permission_codes)
    )
    op.execute(sa.text("DELETE FROM permisos WHERE code = ANY(:codes)").bindparams(codes=permission_codes))
    op.execute("DROP TRIGGER trg_periodontal_version_immutable ON periodontal_exam_versions")
    op.execute("DROP FUNCTION prevent_finalized_periodontal_version_mutation()")
    op.drop_constraint(
        "fk_periodontal_exam_current_version_company",
        "periodontal_exams",
        type_="foreignkey",
    )
    op.drop_index("ix_periodontal_exam_versions_history", table_name="periodontal_exam_versions")
    op.drop_index("uq_periodontal_exam_single_draft", table_name="periodontal_exam_versions")
    op.drop_table("periodontal_exam_versions")
    op.drop_index("ix_periodontal_exams_patient_date", table_name="periodontal_exams")
    op.drop_table("periodontal_exams")
