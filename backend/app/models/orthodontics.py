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


class OrthodonticsEntitlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontics_entitlements"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            name="uq_orthodontics_entitlements_company",
        ),
        UniqueConstraint(
            "id",
            "empresa_id",
            name="uq_orthodontics_entitlements_id_company",
        ),
        CheckConstraint(
            "seat_limit >= 0",
            name="orthodontics_entitlement_seat_limit_nonnegative",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED', 'DISABLED')",
            name="orthodontics_entitlement_status",
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_from IS NULL "
            "OR effective_until >= effective_from",
            name="orthodontics_entitlement_effective_range",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="DISABLED",
        server_default="DISABLED",
    )
    seat_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    effective_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class OrthodonticsDentistAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontics_dentist_assignments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["entitlement_id", "empresa_id"],
            [
                "orthodontics_entitlements.id",
                "orthodontics_entitlements.empresa_id",
            ],
            name="fk_orthodontics_assignment_entitlement_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["odontologo_id", "empresa_id"],
            ["odontologos.id", "odontologos.empresa_id"],
            name="fk_orthodontics_assignment_dentist_company",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "(is_active IS TRUE AND revoked_at IS NULL) "
            "OR (is_active IS FALSE AND revoked_at IS NOT NULL)",
            name="orthodontics_assignment_revocation_state",
        ),
        Index(
            "uq_orthodontics_assignment_active_dentist",
            "empresa_id",
            "odontologo_id",
            unique=True,
            postgresql_where=text("is_active IS TRUE"),
        ),
        Index(
            "ix_orthodontics_assignment_company_active",
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
    entitlement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
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
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    assigned_by_user_id: Mapped[UUID] = mapped_column(
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


class OrthodonticCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontic_cases"
    __table_args__ = (
        ForeignKeyConstraint(
            ["responsible_dentist_id", "empresa_id"],
            ["odontologos.id", "odontologos.empresa_id"],
            name="fk_orthodontic_case_responsible_company",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'SUSPENDED', 'COMPLETED')",
            name="orthodontic_case_status",
        ),
        UniqueConstraint(
            "id",
            "empresa_id",
            name="uq_orthodontic_cases_id_company",
        ),
        CheckConstraint(
            "row_version >= 1",
            name="orthodontic_case_row_version_positive",
        ),
        CheckConstraint(
            "(status = 'COMPLETED' AND completed_at IS NOT NULL) OR "
            "(status <> 'COMPLETED' AND completed_at IS NULL)",
            name="orthodontic_case_completion_state",
        ),
        CheckConstraint(
            "(status = 'DRAFT' AND started_at IS NULL) OR "
            "(status <> 'DRAFT' AND started_at IS NOT NULL)",
            name="orthodontic_case_started_state",
        ),
        CheckConstraint(
            "(status = 'COMPLETED' AND closed_by_user_id IS NOT NULL "
            "AND closure_reason_code IN ('COMPLETED', 'DISCONTINUED')) OR "
            "(status <> 'COMPLETED' AND closed_by_user_id IS NULL "
            "AND closure_reason_code IS NULL AND closure_notes IS NULL)",
            name="orthodontic_case_closure_state",
        ),
        CheckConstraint(
            "closure_reason_code <> 'DISCONTINUED' OR closure_notes IS NOT NULL",
            name="orthodontic_case_discontinuation_reason",
        ),
        Index(
            "uq_orthodontic_case_open_patient",
            "empresa_id",
            "paciente_id",
            unique=True,
            postgresql_where=text("status IN ('DRAFT', 'ACTIVE', 'SUSPENDED')"),
        ),
        Index(
            "ix_orthodontic_cases_patient_created",
            "empresa_id",
            "paciente_id",
            "created_at",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id",
        PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    clinical_record_id: Mapped[UUID] = mapped_column(
        "historia_clinica_id",
        PGUUID(as_uuid=True),
        ForeignKey("historias_clinicas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    primary_site_id: Mapped[UUID] = mapped_column(
        "sede_principal_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    responsible_dentist_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    closure_reason_code: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )
    closure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_appliance_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class OrthodonticClinicalRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontic_clinical_records"
    __table_args__ = (
        ForeignKeyConstraint(
            ["orthodontic_case_id", "empresa_id"],
            ["orthodontic_cases.id", "orthodontic_cases.empresa_id"],
            name="fk_orthodontic_record_case_company",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "orthodontic_case_id",
            name="uq_orthodontic_record_case",
        ),
        UniqueConstraint(
            "id",
            "empresa_id",
            name="uq_orthodontic_records_id_company",
        ),
        Index(
            "ix_orthodontic_records_patient",
            "empresa_id",
            "paciente_id",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id", PGUUID(as_uuid=True), nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id",
        PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    orthodontic_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )


class OrthodonticClinicalRecordVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontic_clinical_record_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["record_id", "empresa_id"],
            ["orthodontic_clinical_records.id", "orthodontic_clinical_records.empresa_id"],
            name="fk_orthodontic_record_version_record_company",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "record_id",
            "version_number",
            name="uq_orthodontic_record_version_number",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'FINALIZED')",
            name="orthodontic_record_version_status",
        ),
        CheckConstraint(
            "version_number >= 1 AND row_version >= 1",
            name="orthodontic_record_version_positive_versions",
        ),
        CheckConstraint(
            "(status = 'DRAFT' AND finalized_at IS NULL "
            "AND finalized_by_user_id IS NULL AND content_hash IS NULL "
            "AND content_snapshot IS NULL) OR "
            "(status = 'FINALIZED' AND finalized_at IS NOT NULL "
            "AND finalized_by_user_id IS NOT NULL AND content_hash IS NOT NULL "
            "AND content_snapshot IS NOT NULL)",
            name="orthodontic_record_version_finalization_state",
        ),
        Index(
            "uq_orthodontic_record_single_draft",
            "record_id",
            unique=True,
            postgresql_where=text("status = 'DRAFT'"),
        ),
        Index(
            "ix_orthodontic_record_versions_history",
            "empresa_id",
            "record_id",
            "version_number",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id", PGUUID(as_uuid=True), nullable=False
    )
    record_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    schema_version: Mapped[str] = mapped_column(String(60), nullable=False)
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    content: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    schema_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    content_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    based_on_version_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orthodontic_clinical_record_versions.id", ondelete="RESTRICT"),
        nullable=True,
    )
    clinical_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timezone_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    finalized_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class OrthodonticCatalogOption(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontic_catalog_options"
    __table_args__ = (
        CheckConstraint(
            "catalog_type IN ('ARCH_MATERIAL', 'ARCH_SIZE', 'CONTROL_INTERVAL')",
            name="orthodontic_catalog_option_type",
        ),
        CheckConstraint(
            "scope IN ('DENTIA_BASE', 'TENANT')",
            name="orthodontic_catalog_option_scope",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'RETIRED')",
            name="orthodontic_catalog_option_status",
        ),
        CheckConstraint(
            "(scope = 'DENTIA_BASE' AND empresa_id IS NULL) OR "
            "(scope = 'TENANT' AND empresa_id IS NOT NULL)",
            name="orthodontic_catalog_option_scope_company",
        ),
        CheckConstraint(
            "(catalog_type = 'CONTROL_INTERVAL' AND interval_value IS NOT NULL "
            "AND interval_unit IN ('WEEK', 'MONTH')) OR "
            "(catalog_type <> 'CONTROL_INTERVAL' AND interval_value IS NULL "
            "AND interval_unit IS NULL)",
            name="orthodontic_catalog_option_interval",
        ),
        Index(
            "uq_orthodontic_catalog_base_code",
            "catalog_type",
            "code",
            unique=True,
            postgresql_where=text("scope = 'DENTIA_BASE'"),
        ),
        Index(
            "uq_orthodontic_catalog_tenant_code",
            "empresa_id",
            "catalog_type",
            "code",
            unique=True,
            postgresql_where=text("scope = 'TENANT'"),
        ),
        Index(
            "ix_orthodontic_catalog_visible",
            "empresa_id",
            "catalog_type",
            "status",
        ),
    )

    company_id: Mapped[UUID | None] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=True,
    )
    catalog_type: Mapped[str] = mapped_column(String(40), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    interval_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interval_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )


class OrthodonticEvolution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontic_evolutions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["orthodontic_case_id", "empresa_id"],
            ["orthodontic_cases.id", "orthodontic_cases.empresa_id"],
            name="fk_orthodontic_evolution_case_company",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "clinical_evolution_id",
            name="uq_orthodontic_evolution_clinical_evolution",
        ),
        CheckConstraint("row_version >= 1", name="orthodontic_evolution_row_version_positive"),
        CheckConstraint(
            "next_control_unit IS NULL OR next_control_unit IN ('WEEK', 'MONTH')",
            name="orthodontic_evolution_control_unit",
        ),
        Index(
            "ix_orthodontic_evolutions_case_created",
            "empresa_id",
            "orthodontic_case_id",
            "created_at",
        ),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), nullable=False)
    orthodontic_case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    clinical_evolution_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("evoluciones_clinicas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    schema_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ORT3_V1", server_default="ORT3_V1"
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    upper_material_option_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orthodontic_catalog_options.id", ondelete="RESTRICT")
    )
    upper_material_code: Mapped[str | None] = mapped_column(String(80))
    upper_material_label: Mapped[str | None] = mapped_column(String(160))
    upper_size_option_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orthodontic_catalog_options.id", ondelete="RESTRICT")
    )
    upper_size_code: Mapped[str | None] = mapped_column(String(80))
    upper_size_label: Mapped[str | None] = mapped_column(String(160))
    lower_material_option_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orthodontic_catalog_options.id", ondelete="RESTRICT")
    )
    lower_material_code: Mapped[str | None] = mapped_column(String(80))
    lower_material_label: Mapped[str | None] = mapped_column(String(160))
    lower_size_option_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orthodontic_catalog_options.id", ondelete="RESTRICT")
    )
    lower_size_code: Mapped[str | None] = mapped_column(String(80))
    lower_size_label: Mapped[str | None] = mapped_column(String(160))
    upper_aligner_note: Mapped[str | None] = mapped_column(String(500))
    lower_aligner_note: Mapped[str | None] = mapped_column(String(500))
    elastic_type: Mapped[str | None] = mapped_column(String(500))
    elastic_configuration: Mapped[str | None] = mapped_column(String(1000))
    next_session_instructions: Mapped[str | None] = mapped_column(Text)
    next_control_option_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orthodontic_catalog_options.id", ondelete="RESTRICT")
    )
    next_control_code: Mapped[str | None] = mapped_column(String(80))
    next_control_label: Mapped[str | None] = mapped_column(String(160))
    next_control_value: Mapped[int | None] = mapped_column(Integer)
    next_control_unit: Mapped[str | None] = mapped_column(String(20))
    suggested_next_control_date: Mapped[date | None] = mapped_column(Date)
    alert_text: Mapped[str | None] = mapped_column(String(2000))
    alert_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    orthodontic_payload_hash: Mapped[str | None] = mapped_column(String(128))


class OrthodonticEvolutionMiniScrew(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontic_evolution_mini_screws"
    __table_args__ = (
        CheckConstraint(
            "screw_type IN ('SELF_TAPPING', 'SELF_DRILLING')",
            name="orthodontic_mini_screw_type",
        ),
        CheckConstraint(
            "location IN ('INTERRADICULAR', 'PALATAL', 'RETROMOLAR', 'INFRAZYGOMATIC_OR_ANTERIOR_ALVEOLAR')",
            name="orthodontic_mini_screw_location",
        ),
        CheckConstraint(
            "material IN ('TITANIUM', 'STEEL')",
            name="orthodontic_mini_screw_material",
        ),
        Index("ix_orthodontic_mini_screws_evolution", "orthodontic_evolution_id", "sort_order"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False
    )
    orthodontic_evolution_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orthodontic_evolutions.id", ondelete="RESTRICT"), nullable=False
    )
    screw_type: Mapped[str] = mapped_column(String(30), nullable=False)
    location: Mapped[str] = mapped_column(String(60), nullable=False)
    material: Mapped[str] = mapped_column(String(30), nullable=False)
    measurement: Mapped[str] = mapped_column(String(160), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
