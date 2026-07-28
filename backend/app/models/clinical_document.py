from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ClinicalDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documentos_clinicos"
    __table_args__ = (
        CheckConstraint(
            "tipo_documento IN ('REFERRAL', 'CLINICAL_REPORT', 'CERTIFICATE', 'GENERAL_LETTER')",
            name="ck_documentos_clinicos_tipo",
        ),
        CheckConstraint(
            "estado IN ('DRAFT', 'FINALIZED', 'VOIDED')",
            name="ck_documentos_clinicos_estado",
        ),
        CheckConstraint("version >= 1", name="ck_documentos_clinicos_version_positive"),
        UniqueConstraint("empresa_id", "numero_documento", name="uq_documentos_clinicos_empresa_numero"),
        Index("ix_documentos_clinicos_empresa_paciente", "empresa_id", "paciente_id"),
        Index("ix_documentos_clinicos_empresa_estado", "empresa_id", "estado"),
        Index("ix_documentos_clinicos_empresa_tipo", "empresa_id", "tipo_documento"),
        Index("ix_documentos_clinicos_empresa_fecha", "empresa_id", "fecha_clinica"),
        Index("ix_documentos_clinicos_profesional", "empresa_id", "dentist_profile_id"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )
    site_id: Mapped[UUID] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id",
        PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    professional_user_id: Mapped[UUID | None] = mapped_column(
        "professional_user_id",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    dentist_profile_id: Mapped[UUID | None] = mapped_column(
        "dentist_profile_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_treatment_id: Mapped[UUID | None] = mapped_column(
        "tratamiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamientos.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_evolution_id: Mapped[UUID | None] = mapped_column(
        "evolucion_id",
        PGUUID(as_uuid=True),
        ForeignKey("evoluciones_clinicas.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_appointment_id: Mapped[UUID | None] = mapped_column(
        "cita_id",
        PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_document_id: Mapped[UUID | None] = mapped_column(
        "previous_document_id",
        PGUUID(as_uuid=True),
        ForeignKey("documentos_clinicos.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_type: Mapped[str] = mapped_column("tipo_documento", String(40), nullable=False)
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False, default="DRAFT", server_default="DRAFT")
    document_number: Mapped[str | None] = mapped_column("numero_documento", String(40), nullable=True)
    sequence: Mapped[int | None] = mapped_column("consecutivo", Integer, nullable=True)
    title: Mapped[str | None] = mapped_column("titulo", String(200), nullable=True)
    recipient_name: Mapped[str | None] = mapped_column("destinatario_nombre", String(200), nullable=True)
    recipient_entity: Mapped[str | None] = mapped_column("destinatario_entidad", String(200), nullable=True)
    recipient_specialty: Mapped[str | None] = mapped_column("destinatario_especialidad", String(160), nullable=True)
    subject: Mapped[str | None] = mapped_column("asunto", String(250), nullable=True)
    body: Mapped[str] = mapped_column("contenido", Text, nullable=False)
    clinical_date: Mapped[date] = mapped_column("fecha_clinica", Date, nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column("finalized_at", DateTime(timezone=True), nullable=True)
    finalized_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column("voided_at", DateTime(timezone=True), nullable=True)
    voided_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    void_reason: Mapped[str | None] = mapped_column("void_reason", Text, nullable=True)
    institution_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    patient_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    professional_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    document_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pdf_storage_path: Mapped[str | None] = mapped_column(String(600), nullable=True)
    pdf_sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
    integrity_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
