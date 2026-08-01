from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text, true
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
