"""add periodontal teeth and six-site clinical model

Revision ID: 20260923_0043
Revises: 20260922_0042
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260923_0043"
down_revision = "20260922_0042"
branch_labels = None
depends_on = None


PERMANENT_FDI = "18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28,48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38"
MOLAR_FDI = "18,17,16,26,27,28,48,47,46,36,37,38"


def upgrade() -> None:
    op.create_table(
        "periodontal_teeth",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fdi_number", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(20), server_default="PRESENT", nullable=False),
        sa.Column("mobility_grade", sa.Integer(), nullable=True),
        sa.Column("furcation_mesial", sa.Boolean(), nullable=True),
        sa.Column("furcation_distal", sa.Boolean(), nullable=True),
        sa.Column("clinical_note", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(f"fdi_number IN ({PERMANENT_FDI})", name="periodontal_tooth_permanent_fdi"),
        sa.CheckConstraint("state IN ('PRESENT', 'ABSENT', 'IMPLANT')", name="periodontal_tooth_state"),
        sa.CheckConstraint("mobility_grade IS NULL OR mobility_grade BETWEEN 0 AND 3", name="periodontal_tooth_mobility_range"),
        sa.CheckConstraint("state = 'PRESENT' OR mobility_grade IS NULL", name="periodontal_tooth_mobility_natural_only"),
        sa.CheckConstraint(
            "state <> 'ABSENT' OR (mobility_grade IS NULL AND furcation_mesial IS NULL AND furcation_distal IS NULL)",
            name="periodontal_tooth_absent_has_no_data",
        ),
        sa.CheckConstraint(
            "state <> 'IMPLANT' OR (furcation_mesial IS NULL AND furcation_distal IS NULL)",
            name="periodontal_tooth_implant_has_no_furcation",
        ),
        sa.CheckConstraint(
            f"(furcation_mesial IS NULL AND furcation_distal IS NULL) OR fdi_number IN ({MOLAR_FDI})",
            name="periodontal_tooth_furcation_molars_only",
        ),
        sa.ForeignKeyConstraint(
            ["version_id", "exam_id", "empresa_id"],
            ["periodontal_exam_versions.id", "periodontal_exam_versions.exam_id", "periodontal_exam_versions.empresa_id"],
            name="fk_periodontal_tooth_version_exam_company",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "version_id", "empresa_id", name="uq_periodontal_teeth_id_version_company"),
        sa.UniqueConstraint("version_id", "fdi_number", name="uq_periodontal_tooth_version_fdi"),
    )
    op.create_index(
        "ix_periodontal_teeth_version_fdi",
        "periodontal_teeth",
        ["empresa_id", "version_id", "fdi_number"],
    )

    op.create_table(
        "periodontal_sites",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tooth_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_code", sa.String(30), nullable=False),
        sa.Column("probing_depth_mm", sa.Integer(), nullable=True),
        sa.Column("gingival_margin_mm", sa.Integer(), nullable=True),
        sa.Column("bleeding_on_probing", sa.Boolean(), nullable=True),
        sa.Column("plaque", sa.Boolean(), nullable=True),
        sa.Column("suppuration", sa.Boolean(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "site_code IN ('BUCCAL_DISTAL', 'BUCCAL_MID', 'BUCCAL_MESIAL', "
            "'LINGUAL_DISTAL', 'LINGUAL_MID', 'LINGUAL_MESIAL')",
            name="periodontal_site_code",
        ),
        sa.CheckConstraint("probing_depth_mm IS NULL OR probing_depth_mm BETWEEN 0 AND 50", name="periodontal_site_pd_range"),
        sa.CheckConstraint("gingival_margin_mm IS NULL OR gingival_margin_mm BETWEEN -50 AND 50", name="periodontal_site_gm_range"),
        sa.ForeignKeyConstraint(
            ["tooth_id", "version_id", "empresa_id"],
            ["periodontal_teeth.id", "periodontal_teeth.version_id", "periodontal_teeth.empresa_id"],
            name="fk_periodontal_site_tooth_version_company",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tooth_id", "site_code", name="uq_periodontal_site_tooth_code"),
    )
    op.create_index(
        "ix_periodontal_sites_version_tooth",
        "periodontal_sites",
        ["empresa_id", "version_id", "tooth_id"],
    )

    op.execute(
        """
        CREATE FUNCTION prevent_finalized_periodontal_clinical_mutation()
        RETURNS trigger AS $$
        DECLARE
            target_version_id uuid;
            target_status varchar;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                target_version_id := OLD.version_id;
            ELSE
                target_version_id := NEW.version_id;
            END IF;
            SELECT status INTO target_status
            FROM periodontal_exam_versions
            WHERE id = target_version_id;
            IF target_status = 'FINALIZED' THEN
                RAISE EXCEPTION 'Finalized periodontal clinical data is immutable';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_periodontal_teeth_immutable
        BEFORE INSERT OR UPDATE OR DELETE ON periodontal_teeth
        FOR EACH ROW EXECUTE FUNCTION prevent_finalized_periodontal_clinical_mutation()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_periodontal_sites_immutable
        BEFORE INSERT OR UPDATE OR DELETE ON periodontal_sites
        FOR EACH ROW EXECUTE FUNCTION prevent_finalized_periodontal_clinical_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER trg_periodontal_sites_immutable ON periodontal_sites")
    op.execute("DROP TRIGGER trg_periodontal_teeth_immutable ON periodontal_teeth")
    op.execute("DROP FUNCTION prevent_finalized_periodontal_clinical_mutation()")
    op.drop_index("ix_periodontal_sites_version_tooth", table_name="periodontal_sites")
    op.drop_table("periodontal_sites")
    op.drop_index("ix_periodontal_teeth_version_fdi", table_name="periodontal_teeth")
    op.drop_table("periodontal_teeth")
