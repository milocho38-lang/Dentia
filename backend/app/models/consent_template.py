from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, false, text, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ConsentLibraryDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_biblioteca_documentos"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_consent_library_document_code"),
        CheckConstraint("source_page_start >= 1 AND source_page_end >= source_page_start", name="ck_consent_library_pages"),
        CheckConstraint("tipo_documento IN ('INFORMED_CONSENT','TREATMENT_REFUSAL','CERTIFICATE','POST_CARE_INSTRUCTIONS','PRE_CARE_INSTRUCTIONS','NO_WARRANTY_ACKNOWLEDGEMENT','AESTHETIC_APPROVAL','TREATMENT_TERMINATION_ACKNOWLEDGEMENT')", name="ck_consent_library_document_type"),
        CheckConstraint("signer_scope IN ('ADULT_SELF','ADULT_OR_REPRESENTATIVE','REPRESENTATIVE_REQUIRED','NO_SIGNATURE_REQUIRED','ADMINISTRATIVE_RECORD','PATIENT_SELF','PATIENT_OR_RESPONSIBLE_ADULT','RESPONSIBLE_ADULT_REQUIRED','NO_PATIENT_SIGNATURE','SPECIAL_WORKFLOW')", name="ck_consent_library_signer_scope"),
        Index("ix_consent_library_document_type", "tipo_documento"),
        Index("ix_consent_library_document_specialty", "especialidad_codigo"),
    )

    code: Mapped[str] = mapped_column("codigo", String(80), nullable=False)
    title: Mapped[str] = mapped_column("titulo", String(250), nullable=False)
    summary: Mapped[str | None] = mapped_column("resumen", Text, nullable=True)
    document_type: Mapped[str] = mapped_column("tipo_documento", String(60), nullable=False)
    category: Mapped[str] = mapped_column("categoria", String(100), nullable=False)
    specialty_code: Mapped[str | None] = mapped_column("especialidad_codigo", String(80), nullable=True)
    specialty_name: Mapped[str | None] = mapped_column("especialidad_nombre", String(160), nullable=True)
    signer_scope: Mapped[str] = mapped_column(String(40), nullable=False)
    requires_patient_signature: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    supports_electronic_signature: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    source_package_version: Mapped[str] = mapped_column(String(80), nullable=False)
    source_document_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    source_page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    source_title_exact: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_origin_note: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[str] = mapped_column(String(250), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())


class ConsentLibraryVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_biblioteca_versiones"
    __table_args__ = (
        UniqueConstraint("library_document_id", "country_code", "language_code", "version_number", name="uq_consent_library_version_locale_number"),
        CheckConstraint("version_number >= 1", name="ck_consent_library_version_number"),
        CheckConstraint("country_code IN ('CO','CL')", name="ck_consent_library_country"),
        CheckConstraint("language_code IN ('es-CO','es-CL')", name="ck_consent_library_language"),
        CheckConstraint("publication_status IN ('READY_FOR_REVIEW','PUBLISHED','RETIRED')", name="ck_consent_library_publication_status"),
        Index("ix_consent_library_version_status", "publication_status"),
        Index("ix_consent_library_version_country", "country_code", "language_code"),
    )

    library_document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_biblioteca_documentos.id", ondelete="RESTRICT"), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    publication_status: Mapped[str] = mapped_column(String(30), nullable=False, default="READY_FOR_REVIEW", server_default="READY_FOR_REVIEW")
    legal_review_status: Mapped[str] = mapped_column(String(80), nullable=False)
    clinical_review_status: Mapped[str] = mapped_column(String(80), nullable=False)
    reviewed_countries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_reference: Mapped[str | None] = mapped_column(String(250), nullable=True)
    content_format: Mapped[str] = mapped_column(String(40), nullable=False, default="RESTRICTED_MARKDOWN_V1", server_default="RESTRICTED_MARKDOWN_V1")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    variable_schema_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    source_pages: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    transformation_notes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    equivalence_reviewer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    equivalence_review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    equivalence_checklist_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=False)


class ConsentLibraryInstallation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_biblioteca_instalaciones"
    __table_args__ = (
        CheckConstraint("installation_mode IN ('EXACT','CLONE')", name="ck_consent_library_install_mode"),
        CheckConstraint("content_responsibility IN ('DENTIA','CLINIC')", name="ck_consent_library_install_responsibility"),
        Index("ix_consent_library_install_company", "empresa_id"),
        Index("uq_consent_library_install_exact_company_version", "empresa_id", "library_version_id", unique=True, postgresql_where=text("installation_mode = 'EXACT'")),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    library_document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_biblioteca_documentos.id", ondelete="RESTRICT"), nullable=False)
    library_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_biblioteca_versiones.id", ondelete="RESTRICT"), nullable=False)
    installed_template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantillas.id", ondelete="RESTRICT"), nullable=False)
    installed_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_plantilla_versiones.id", ondelete="RESTRICT"), nullable=False)
    installation_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    content_responsibility: Mapped[str] = mapped_column(String(20), nullable=False)
    installed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=False)


class ConsentTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_plantillas"
    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="uq_consent_template_empresa_codigo"),
        Index("ix_consent_template_empresa_activa", "empresa_id", "is_active"),
        Index("ix_consent_template_empresa_pais_tipo", "empresa_id", "country_code", "document_kind"),
        Index("ix_consent_template_origin", "empresa_id", "template_origin"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column("codigo", String(80), nullable=False)
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    description: Mapped[str | None] = mapped_column("descripcion", Text, nullable=True)
    document_kind: Mapped[str] = mapped_column(String(60), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    template_origin: Mapped[str] = mapped_column(String(40), nullable=False, default="CLINIC_CUSTOM", server_default="CLINIC_CUSTOM")
    source_library_document_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_biblioteca_documentos.id", ondelete="SET NULL"), nullable=True)
    content_responsibility: Mapped[str] = mapped_column(String(20), nullable=False, default="CLINIC", server_default="CLINIC")
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
        Index("ix_consent_template_version_source_library", "source_library_version_id"),
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
    source_library_version_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_biblioteca_versiones.id", ondelete="SET NULL"), nullable=True)
    source_document_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    legal_review_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    clinical_review_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reviewed_countries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    installed_from_library_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
        CheckConstraint("status IN ('DRAFT','READY_FOR_REVIEW','PENDING_SIGNATURE','SIGNED','VOIDED')", name="ck_consent_instance_status"),
        CheckConstraint("completion_channel IS NULL OR completion_channel IN ('ELECTRONIC','PAPER')", name="ck_consent_instance_completion_channel"),
        CheckConstraint("signer_policy IN ('PATIENT_SELF','PATIENT_OR_RESPONSIBLE_ADULT','RESPONSIBLE_ADULT_REQUIRED','NO_PATIENT_SIGNATURE','SPECIAL_WORKFLOW')", name="ck_consent_instance_signer_policy"),
        CheckConstraint("signer_actor_type IN ('PATIENT_SELF','RESPONSIBLE_ADULT')", name="ck_consent_instance_signer_actor"),
        CheckConstraint("minor_participation_status IS NULL OR minor_participation_status IN ('INFORMED_AND_AGREED','INFORMED_NO_OBJECTION','COULD_NOT_EXPRESS_DUE_TO_AGE_OR_CONDITION','NOT_APPLICABLE','OTHER')", name="ck_consent_instance_minor_participation"),
        Index("ix_consent_instance_company_patient_date", "empresa_id", "paciente_id", "clinical_date"),
        Index("ix_consent_instance_company_status", "empresa_id", "status"),
        Index("ix_consent_instance_company_site", "empresa_id", "sede_id"),
        Index("ix_consent_instance_signer_actor", "empresa_id", "signer_actor_type"),
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
    completion_channel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_kind: Mapped[str] = mapped_column(String(60), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    clinical_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone_name: Mapped[str] = mapped_column("zona_horaria", String(100), nullable=False)
    display_title: Mapped[str] = mapped_column(String(250), nullable=False)
    signer_policy: Mapped[str] = mapped_column(String(40), nullable=False, default="PATIENT_SELF", server_default="PATIENT_SELF")
    signer_actor_type: Mapped[str] = mapped_column(String(40), nullable=False, default="PATIENT_SELF", server_default="PATIENT_SELF")
    signer_full_name_snapshot: Mapped[str | None] = mapped_column(String(250), nullable=True)
    signer_document_type_snapshot: Mapped[str | None] = mapped_column(String(30), nullable=True)
    signer_document_number_snapshot: Mapped[str | None] = mapped_column(String(80), nullable=True)
    signer_email_snapshot: Mapped[str | None] = mapped_column(String(220), nullable=True)
    signer_phone_snapshot: Mapped[str | None] = mapped_column(String(80), nullable=True)
    signer_relationship_type_snapshot: Mapped[str | None] = mapped_column(String(40), nullable=True)
    signer_relationship_other_snapshot: Mapped[str | None] = mapped_column(String(160), nullable=True)
    minor_participation_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    minor_participation_observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    signer_selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signer_selected_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
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
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class ConsentResponsibleAdult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_adultos_responsables"
    __table_args__ = (
        UniqueConstraint("consent_instance_id", name="uq_consent_responsible_adult_instance"),
        CheckConstraint("relationship_type IN ('MOTHER','FATHER','SIBLING','GRANDPARENT','AUNT_UNCLE','COUSIN','CAREGIVER','NEIGHBOR','LEGAL_REPRESENTATIVE','OTHER')", name="ck_consent_responsible_relationship"),
        CheckConstraint("row_version >= 1", name="ck_consent_responsible_row_version_positive"),
        Index("ix_consent_responsible_company_patient", "empresa_id", "paciente_id"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column("paciente_id", PGUUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False)
    consent_instance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_instancias.id", ondelete="CASCADE"), nullable=False)
    patient_responsible_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("responsables_paciente.id", ondelete="SET NULL"), nullable=True)
    full_name: Mapped[str] = mapped_column(String(250), nullable=False)
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    document_number: Mapped[str] = mapped_column(String(80), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(40), nullable=False)
    relationship_other: Mapped[str | None] = mapped_column(String(160), nullable=True)
    email: Mapped[str] = mapped_column(String(220), nullable=False)
    phone: Mapped[str] = mapped_column(String(80), nullable=False)
    identity_verified_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    identity_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verification_statement: Mapped[str] = mapped_column(Text, nullable=False)
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
