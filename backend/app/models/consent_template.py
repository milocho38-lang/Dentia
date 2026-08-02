from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ConsentTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_plantillas"
    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="uq_consent_template_empresa_codigo"),
        Index("ix_consent_template_empresa_activa", "empresa_id", "is_active"),
        Index("ix_consent_template_empresa_pais_tipo", "empresa_id", "country_code", "document_kind"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column("codigo", String(80), nullable=False)
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    description: Mapped[str | None] = mapped_column("descripcion", Text, nullable=True)
    document_kind: Mapped[str] = mapped_column(String(60), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)


class ConsentTemplateVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_plantilla_versiones"
    __table_args__ = (
        UniqueConstraint("template_id", "version_number", name="uq_consent_template_version_number"),
        CheckConstraint("version_number >= 1", name="ck_consent_template_version_number_positive"),
        CheckConstraint("row_version >= 1", name="ck_consent_template_row_version_positive"),
        CheckConstraint("priority BETWEEN 0 AND 1000", name="ck_consent_template_priority_range"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED','SUPERSEDED','RETIRED','VOIDED')", name="ck_consent_template_version_status"),
        CheckConstraint("scope_type IN ('GENERAL','SPECIFIC')", name="ck_consent_template_scope_type"),
        Index("ix_consent_template_version_empresa_estado", "empresa_id", "status"),
        Index("ix_consent_template_version_template_estado", "template_id", "status"),
        Index("uq_consent_template_one_published", "template_id", unique=True, postgresql_where=text("status = 'PUBLISHED'")),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantillas.id", ondelete="RESTRICT"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", server_default="DRAFT")
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_format: Mapped[str] = mapped_column(String(40), nullable=False, default="RESTRICTED_MARKDOWN_V1", server_default="RESTRICTED_MARKDOWN_V1")
    variable_schema_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    based_on_version_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantilla_versiones.id", ondelete="SET NULL"), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False, default="GENERAL", server_default="GENERAL")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    retire_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)


class ConsentTemplateVersionSite(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_plantilla_version_sedes"
    __table_args__ = (UniqueConstraint("version_id", "site_id", name="uq_consent_version_site"), Index("ix_consent_version_site_empresa", "empresa_id", "site_id"))
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantilla_versiones.id", ondelete="RESTRICT"), nullable=False)
    site_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False)


class ConsentTemplateVersionProcedure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_plantilla_version_procedimientos"
    __table_args__ = (UniqueConstraint("version_id", "procedure_catalog_id", name="uq_consent_version_procedure"), Index("ix_consent_version_procedure_empresa", "empresa_id", "procedure_catalog_id"))
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantilla_versiones.id", ondelete="RESTRICT"), nullable=False)
    procedure_catalog_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("catalogo_procedimientos.id", ondelete="RESTRICT"), nullable=False)


class ConsentTemplateVersionSpecialty(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_plantilla_version_especialidades"
    __table_args__ = (UniqueConstraint("version_id", "specialty_code", name="uq_consent_version_specialty"), Index("ix_consent_version_specialty_empresa", "empresa_id", "specialty_code"))
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantilla_versiones.id", ondelete="RESTRICT"), nullable=False)
    specialty_code: Mapped[str] = mapped_column(String(80), nullable=False)
    specialty_name: Mapped[str] = mapped_column(String(160), nullable=False)


class ConsentInstanceSequence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_instancia_consecutivos"
    __table_args__ = (UniqueConstraint("empresa_id", name="uq_consent_instance_sequence_company"),)

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    next_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class ConsentInstance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_instancias"
    __table_args__ = (
        UniqueConstraint("empresa_id", "sequence_number", name="uq_consent_instance_company_sequence"),
        UniqueConstraint("empresa_id", "visible_number", name="uq_consent_instance_company_visible"),
        CheckConstraint("sequence_number >= 1", name="ck_consent_instance_sequence_positive"),
        CheckConstraint("row_version >= 1", name="ck_consent_instance_row_version_positive"),
        CheckConstraint("status IN ('DRAFT','READY_FOR_REVIEW','PENDING_SIGNATURE','VOIDED')", name="ck_consent_instance_status"),
        Index("ix_consent_instance_company_patient_date", "empresa_id", "paciente_id", "clinical_date"),
        Index("ix_consent_instance_company_status", "empresa_id", "status"),
        Index("ix_consent_instance_company_site", "empresa_id", "sede_id"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    site_id: Mapped[UUID] = mapped_column("sede_id", PGUUID(as_uuid=True), ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column("paciente_id", PGUUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False)
    template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantillas.id", ondelete="RESTRICT"), nullable=False)
    template_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantilla_versiones.id", ondelete="RESTRICT"), nullable=False)
    appointment_id: Mapped[UUID | None] = mapped_column("cita_id", PGUUID(as_uuid=True), ForeignKey("citas.id", ondelete="SET NULL"), nullable=True)
    treatment_id: Mapped[UUID | None] = mapped_column("tratamiento_id", PGUUID(as_uuid=True), ForeignKey("tratamientos.id", ondelete="SET NULL"), nullable=True)
    professional_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    dentist_profile_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("odontologos.id", ondelete="SET NULL"), nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    visible_number: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT", server_default="DRAFT")
    document_kind: Mapped[str] = mapped_column(String(60), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    clinical_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone_name: Mapped[str] = mapped_column("zona_horaria", String(100), nullable=False)
    display_title: Mapped[str] = mapped_column(String(250), nullable=False)
    rendered_content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_content_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    variable_values_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    missing_variables: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    context_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    template_version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    template_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    instance_content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    context_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    integrity_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    professional_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    professional_confirmed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class ConsentInstanceProcedure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_instancia_procedimientos"
    __table_args__ = (
        UniqueConstraint("instance_id", "order_number", name="uq_consent_instance_procedure_order"),
        Index("ix_consent_instance_procedure_company", "empresa_id", "instance_id"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    instance_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_instancias.id", ondelete="RESTRICT"), nullable=False)
    procedure_catalog_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("catalogo_procedimientos.id", ondelete="SET NULL"), nullable=True)
    treatment_procedure_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tratamiento_procedimientos.id", ondelete="SET NULL"), nullable=True)
    code_snapshot: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    description_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)


class ConsentAccessSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_sesiones_acceso"
    __table_args__ = (
        CheckConstraint("status IN ('ISSUED','OTP_PENDING','VERIFIED','VIEWED','CLARIFICATION_REQUESTED','REVOKED','EXPIRED')", name="ck_consent_access_status"),
        CheckConstraint("row_version >= 1", name="ck_consent_access_row_version"),
        CheckConstraint("open_count >= 0", name="ck_consent_access_open_count"),
        Index("ix_consent_access_company_instance", "empresa_id", "consent_instance_id"),
        Index("ix_consent_access_token_hash", "public_token_hash", unique=True),
    )
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    site_id: Mapped[UUID] = mapped_column("sede_id", PGUUID(as_uuid=True), ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False)
    consent_instance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_instancias.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ISSUED", server_default="ISSUED")
    public_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    public_token_prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clarification_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open_window_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    open_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="EMAIL", server_default="EMAIL")
    recipient_masked: Mapped[str] = mapped_column(String(220), nullable=False)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class ConsentOtpChallenge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_otp_desafios"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','VERIFIED','INVALIDATED','BLOCKED','DELIVERY_FAILED','EXPIRED')", name="ck_consent_otp_status"),
        CheckConstraint("failed_attempts >= 0 AND resend_count >= 0", name="ck_consent_otp_counts"),
        Index("ix_consent_otp_access_status", "access_session_id", "status"),
        Index("ix_consent_otp_rate_ip", "request_ip_hash", "issued_at"),
        Index("ix_consent_otp_rate_recipient", "recipient_hash", "issued_at"),
    )
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    access_session_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_sesiones_acceso.id", ondelete="RESTRICT"), nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING", server_default="PENDING")
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="EMAIL", server_default="EMAIL")
    recipient_masked: Mapped[str] = mapped_column(String(220), nullable=False)
    recipient_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    resend_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsentPublicSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_sesiones_publicas"
    __table_args__ = (CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')", name="ck_consent_public_session_status"), Index("ix_consent_public_session_hash", "session_token_hash", unique=True))
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    access_session_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_sesiones_acceso.id", ondelete="RESTRICT"), nullable=False)
    session_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsentClarificationRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_solicitudes_aclaracion"
    __table_args__ = (CheckConstraint("status IN ('OPEN','RESOLVED')", name="ck_consent_clarification_status"), Index("ix_consent_clarification_company_instance", "empresa_id", "consent_instance_id"))
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    consent_instance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_instancias.id", ondelete="RESTRICT"), nullable=False)
    access_session_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_sesiones_acceso.id", ondelete="RESTRICT"), nullable=False)
    professional_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", server_default="OPEN")
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
