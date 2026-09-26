from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class PeriodontogramPilotCompanyGate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "periodontogram_pilot_company_gates"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            name="uq_periodontogram_pilot_company_gate",
        ),
        CheckConstraint(
            "(is_enabled IS TRUE AND enabled_at IS NOT NULL "
            "AND enabled_by_user_id IS NOT NULL AND disabled_at IS NULL "
            "AND disabled_by_user_id IS NULL) OR is_enabled IS FALSE",
            name="periodontogram_pilot_company_gate_state",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    enabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    enabled_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
    )
    disabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    disabled_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
    )


class PeriodontogramPilotDentistAuthorization(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "periodontogram_pilot_dentist_authorizations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["odontologo_id", "empresa_id"],
            ["odontologos.id", "odontologos.empresa_id"],
            name="fk_periodontogram_pilot_dentist_company",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "(is_active IS TRUE AND revoked_at IS NULL "
            "AND revoked_by_user_id IS NULL) OR "
            "(is_active IS FALSE AND revoked_at IS NOT NULL "
            "AND revoked_by_user_id IS NOT NULL)",
            name="periodontogram_pilot_dentist_authorization_state",
        ),
        Index(
            "uq_periodontogram_pilot_active_dentist",
            "empresa_id",
            "odontologo_id",
            unique=True,
            postgresql_where=text("is_active IS TRUE"),
        ),
        Index(
            "ix_periodontogram_pilot_company_active",
            "empresa_id",
            "is_active",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dentist_id: Mapped[UUID] = mapped_column(
        "odontologo_id",
        PGUUID(as_uuid=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    authorized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    authorized_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
    )
    revocation_reason: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )


class PeriodontalExam(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "periodontal_exams"
    __table_args__ = (
        ForeignKeyConstraint(
            ["responsible_dentist_id", "empresa_id"],
            ["odontologos.id", "odontologos.empresa_id"],
            name="fk_periodontal_exam_dentist_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["current_version_id", "id", "empresa_id"],
            [
                "periodontal_exam_versions.id",
                "periodontal_exam_versions.exam_id",
                "periodontal_exam_versions.empresa_id",
            ],
            name="fk_periodontal_exam_current_version_company",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        UniqueConstraint("id", "empresa_id", name="uq_periodontal_exams_id_company"),
        CheckConstraint(
            "status IN ('DRAFT', 'FINALIZED')",
            name="periodontal_exam_status",
        ),
        CheckConstraint("row_version >= 1", name="periodontal_exam_row_version_positive"),
        CheckConstraint(
            "(status = 'DRAFT' AND finalized_at IS NULL) OR "
            "(status = 'FINALIZED' AND finalized_at IS NOT NULL)",
            name="periodontal_exam_finalization_state",
        ),
        Index(
            "ix_periodontal_exams_patient_date",
            "empresa_id",
            "paciente_id",
            "clinical_date",
        ),
        Index(
            "ix_periodontal_exams_evolution_link",
            "empresa_id",
            "paciente_id",
            "evolucion_id",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id", PGUUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False
    )
    site_id: Mapped[UUID] = mapped_column(
        "sede_id", PGUUID(as_uuid=True), ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False
    )
    responsible_dentist_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evolution_id: Mapped[UUID | None] = mapped_column(
        "evolucion_id",
        PGUUID(as_uuid=True),
        ForeignKey("evoluciones_clinicas.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", server_default="DRAFT")
    current_version_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    clinical_date: Mapped[date] = mapped_column(Date, nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    updated_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )


class PeriodontalTooth(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "periodontal_teeth"
    __table_args__ = (
        ForeignKeyConstraint(
            ["version_id", "exam_id", "empresa_id"],
            [
                "periodontal_exam_versions.id",
                "periodontal_exam_versions.exam_id",
                "periodontal_exam_versions.empresa_id",
            ],
            name="fk_periodontal_tooth_version_exam_company",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "version_id", "empresa_id", name="uq_periodontal_teeth_id_version_company"),
        UniqueConstraint("version_id", "fdi_number", name="uq_periodontal_tooth_version_fdi"),
        CheckConstraint(
            "fdi_number IN (18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28,"
            "48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38)",
            name="periodontal_tooth_permanent_fdi",
        ),
        CheckConstraint("state IN ('PRESENT', 'ABSENT', 'IMPLANT')", name="periodontal_tooth_state"),
        CheckConstraint("mobility_grade IS NULL OR mobility_grade BETWEEN 0 AND 3", name="periodontal_tooth_mobility_range"),
        CheckConstraint("state = 'PRESENT' OR mobility_grade IS NULL", name="periodontal_tooth_mobility_natural_only"),
        CheckConstraint(
            "state <> 'ABSENT' OR (mobility_grade IS NULL AND furcation_mesial IS NULL AND furcation_distal IS NULL)",
            name="periodontal_tooth_absent_has_no_data",
        ),
        CheckConstraint(
            "state <> 'IMPLANT' OR (furcation_mesial IS NULL AND furcation_distal IS NULL)",
            name="periodontal_tooth_implant_has_no_furcation",
        ),
        CheckConstraint(
            "(furcation_mesial IS NULL AND furcation_distal IS NULL) OR "
            "fdi_number IN (18,17,16,26,27,28,48,47,46,36,37,38)",
            name="periodontal_tooth_furcation_molars_only",
        ),
        Index("ix_periodontal_teeth_version_fdi", "empresa_id", "version_id", "fdi_number"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), nullable=False)
    exam_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    fdi_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="PRESENT", server_default="PRESENT")
    mobility_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    furcation_mesial: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    furcation_distal: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    clinical_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    updated_by_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)


class PeriodontalSite(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "periodontal_sites"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tooth_id", "version_id", "empresa_id"],
            ["periodontal_teeth.id", "periodontal_teeth.version_id", "periodontal_teeth.empresa_id"],
            name="fk_periodontal_site_tooth_version_company",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tooth_id", "site_code", name="uq_periodontal_site_tooth_code"),
        CheckConstraint(
            "site_code IN ('BUCCAL_DISTAL', 'BUCCAL_MID', 'BUCCAL_MESIAL', "
            "'LINGUAL_DISTAL', 'LINGUAL_MID', 'LINGUAL_MESIAL')",
            name="periodontal_site_code",
        ),
        CheckConstraint("probing_depth_mm IS NULL OR probing_depth_mm BETWEEN 0 AND 50", name="periodontal_site_pd_range"),
        CheckConstraint("gingival_margin_mm IS NULL OR gingival_margin_mm BETWEEN -50 AND 50", name="periodontal_site_gm_range"),
        Index("ix_periodontal_sites_version_tooth", "empresa_id", "version_id", "tooth_id"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), nullable=False)
    exam_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    tooth_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    site_code: Mapped[str] = mapped_column(String(30), nullable=False)
    probing_depth_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gingival_margin_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bleeding_on_probing: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    plaque: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    suppuration: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    updated_by_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)


class PeriodontalExamVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "periodontal_exam_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["exam_id", "empresa_id"],
            ["periodontal_exams.id", "periodontal_exams.empresa_id"],
            name="fk_periodontal_exam_version_exam_company",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "empresa_id", name="uq_periodontal_exam_versions_id_company"),
        UniqueConstraint(
            "id",
            "exam_id",
            "empresa_id",
            name="uq_periodontal_exam_versions_id_exam_company",
        ),
        UniqueConstraint("exam_id", "version_number", name="uq_periodontal_exam_version_number"),
        CheckConstraint(
            "status IN ('DRAFT', 'FINALIZED')",
            name="periodontal_exam_version_status",
        ),
        CheckConstraint(
            "version_number >= 1 AND row_version >= 1",
            name="periodontal_exam_version_positive_versions",
        ),
        CheckConstraint(
            "(status = 'DRAFT' AND finalized_at IS NULL AND finalized_by_user_id IS NULL "
            "AND snapshot IS NULL AND snapshot_hash IS NULL) OR "
            "(status = 'FINALIZED' AND finalized_at IS NOT NULL AND finalized_by_user_id IS NOT NULL "
            "AND snapshot IS NOT NULL AND snapshot_hash IS NOT NULL)",
            name="periodontal_exam_version_finalization_state",
        ),
        CheckConstraint(
            "supersedes_version_id IS NULL OR correction_reason IS NOT NULL",
            name="periodontal_exam_version_correction_reason",
        ),
        Index(
            "uq_periodontal_exam_single_draft",
            "exam_id",
            unique=True,
            postgresql_where=text("status = 'DRAFT'"),
        ),
        Index(
            "ix_periodontal_exam_versions_history",
            "empresa_id",
            "exam_id",
            "version_number",
        ),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), nullable=False)
    exam_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", server_default="DRAFT")
    schema_version: Mapped[str] = mapped_column(String(60), nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    supersedes_version_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("periodontal_exam_versions.id", ondelete="RESTRICT"), nullable=True
    )
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    updated_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    finalized_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True
    )
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
