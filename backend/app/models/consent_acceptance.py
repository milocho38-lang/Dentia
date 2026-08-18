from datetime import date, datetime
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ConsentAcceptance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_aceptaciones"
    __table_args__ = (
        UniqueConstraint("consent_instance_id", name="uq_consent_acceptance_instance"),
        UniqueConstraint("access_session_id", "idempotency_key", name="uq_consent_acceptance_idempotency"),
        CheckConstraint("status IN ('INITIATED','SUBMITTED','COMPLETED','FAILED','INVALIDATED')", name="ck_consent_acceptance_status"),
        Index("ix_consent_acceptance_company_instance", "empresa_id", "consent_instance_id"),
    )
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    site_id: Mapped[UUID] = mapped_column("sede_id", PGUUID(as_uuid=True), ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column("paciente_id", PGUUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False)
    consent_instance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_instancias.id", ondelete="RESTRICT"), nullable=False)
    access_session_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_sesiones_acceso.id", ondelete="RESTRICT"), nullable=False)
    public_session_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_sesiones_publicas.id", ondelete="RESTRICT"), nullable=False)
    otp_challenge_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_otp_desafios.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False, default="PATIENT_SELF", server_default="PATIENT_SELF")
    acting_on_own_behalf: Mapped[bool] = mapped_column(Boolean, nullable=False)
    responsible_adult_snapshot_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consentimiento_adultos_responsables.id", ondelete="RESTRICT"), nullable=True)
    typed_full_name: Mapped[str] = mapped_column(String(250), nullable=False)
    signer_full_name_snapshot: Mapped[str | None] = mapped_column(String(250), nullable=True)
    signer_document_type_snapshot: Mapped[str | None] = mapped_column(String(30), nullable=True)
    signer_document_number_snapshot: Mapped[str | None] = mapped_column(String(80), nullable=True)
    signer_relationship_type_snapshot: Mapped[str | None] = mapped_column(String(40), nullable=True)
    signer_relationship_other_snapshot: Mapped[str | None] = mapped_column(String(160), nullable=True)
    signer_email_masked_snapshot: Mapped[str | None] = mapped_column(String(220), nullable=True)
    minor_participation_status_snapshot: Mapped[str | None] = mapped_column(String(80), nullable=True)
    minor_participation_observation_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    patient_name_snapshot: Mapped[str] = mapped_column(String(250), nullable=False)
    patient_birth_date_snapshot: Mapped[date] = mapped_column(Date, nullable=False)
    patient_document_type_snapshot: Mapped[str] = mapped_column(String(30), nullable=False)
    patient_document_number_snapshot: Mapped[str | None] = mapped_column(String(80), nullable=True)
    recipient_masked_snapshot: Mapped[str] = mapped_column(String(220), nullable=False)
    declaration_set_code: Mapped[str] = mapped_column(String(80), nullable=False)
    declarations_country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    declarations_locale: Mapped[str] = mapped_column(String(10), nullable=False)
    declarations_version: Mapped[str] = mapped_column(String(60), nullable=False)
    declarations_legal_status: Mapped[str] = mapped_column(String(30), nullable=False)
    declarations_effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    declarations_set_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    test_document: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone_name: Mapped[str] = mapped_column(String(100), nullable=False)
    local_datetime: Mapped[str] = mapped_column(String(80), nullable=False)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(20), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ConsentAcceptanceDeclaration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_aceptacion_declaraciones"
    __table_args__ = (UniqueConstraint("acceptance_id", "code", name="uq_consent_acceptance_declaration_code"),)
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    acceptance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_aceptaciones.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    declaration_version: Mapped[str] = mapped_column(String(60), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    responded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)


class ConsentSignatureArtifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_firmas_artefactos"
    __table_args__ = (UniqueConstraint("acceptance_id", name="uq_consent_signature_acceptance"),)
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    acceptance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_aceptaciones.id", ondelete="RESTRICT"), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(700), nullable=False)
    signature_type: Mapped[str] = mapped_column(String(30), nullable=False)
    typed_name_snapshot: Mapped[str] = mapped_column(String(250), nullable=False)
    graphic_present: Mapped[bool] = mapped_column(Boolean, nullable=False)
    sanitization_version: Mapped[str] = mapped_column(String(50), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)


class ConsentEvidenceManifest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_evidencia_manifiestos"
    __table_args__ = (UniqueConstraint("acceptance_id", name="uq_consent_evidence_acceptance"),)
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    acceptance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_aceptaciones.id", ondelete="RESTRICT"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(30), nullable=False)
    manifest: Mapped[dict] = mapped_column(JSONB, nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(700), nullable=False)


class ConsentFinalDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_documentos_finales"
    __table_args__ = (
        UniqueConstraint("consent_instance_id", name="uq_consent_final_document_instance"),
        Index("ix_consent_final_document_download_hash", "public_download_token_hash", unique=True),
    )
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    consent_instance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_instancias.id", ondelete="RESTRICT"), nullable=False)
    acceptance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_aceptaciones.id", ondelete="RESTRICT"), nullable=False)
    evidence_manifest_id: Mapped[UUID | None] = mapped_column(ForeignKey("consentimiento_evidencia_manifiestos.id", ondelete="RESTRICT"), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(700), nullable=False)
    filename: Mapped[str] = mapped_column(String(250), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False, default="application/pdf", server_default="application/pdf")
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    renderer_version: Mapped[str] = mapped_column(String(60), nullable=False)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    public_download_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    public_download_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsentCopyDelivery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_entregas_copia"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','SENT','FAILED')", name="ck_consent_copy_delivery_status"),
        Index("ix_consent_copy_delivery_instance", "empresa_id", "consent_instance_id"),
    )
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    consent_instance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_instancias.id", ondelete="RESTRICT"), nullable=False)
    acceptance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_aceptaciones.id", ondelete="RESTRICT"), nullable=False)
    final_document_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_documentos_finales.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="EMAIL", server_default="EMAIL")
    recipient_masked: Mapped[str] = mapped_column(String(220), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requested_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)


class ConsentPaperPacket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_paquetes_papel"
    __table_args__ = (
        UniqueConstraint("consent_instance_id", name="uq_consent_paper_packet_instance"),
        CheckConstraint("status IN ('PRINTED','SIGNED_PENDING_DIGITIZATION','DIGITIZING','FINALIZED')", name="ck_consent_paper_packet_status"),
        CheckConstraint("expected_page_count >= 1", name="ck_consent_paper_expected_pages"),
        CheckConstraint("uploaded_page_count >= 0", name="ck_consent_paper_uploaded_pages"),
        Index("ix_consent_paper_company_instance", "empresa_id", "consent_instance_id"),
        Index("ix_consent_paper_company_status", "empresa_id", "status"),
    )
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    site_id: Mapped[UUID] = mapped_column("sede_id", PGUUID(as_uuid=True), ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column("paciente_id", PGUUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False)
    consent_instance_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_instancias.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PRINTED", server_default="PRINTED")
    print_storage_key: Mapped[str] = mapped_column(String(700), nullable=False)
    print_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    print_byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expected_page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    printed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    printed_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    paper_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paper_signed_recorded_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True)
    digitalization_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    digitization_finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalized_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True)
    original_physical_retention_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_statements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    verification_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    final_pdf_storage_key: Mapped[str | None] = mapped_column(String(700), nullable=True)
    final_pdf_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    final_pdf_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    final_page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class ConsentPaperPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consentimiento_paginas_papel"
    __table_args__ = (
        UniqueConstraint("paper_packet_id", "position", name="uq_consent_paper_page_position"),
        Index("ix_consent_paper_page_company_packet", "empresa_id", "paper_packet_id"),
    )
    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    paper_packet_id: Mapped[UUID] = mapped_column(ForeignKey("consentimiento_paquetes_papel.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(700), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_mime_type: Mapped[str] = mapped_column(String(80), nullable=False)
    upload_group_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    original_page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
