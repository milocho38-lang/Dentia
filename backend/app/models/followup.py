from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text, false
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AppointmentCare(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "atenciones_cita"
    __table_args__ = (
        Index("uq_atenciones_cita_cita_id", "cita_id", unique=True),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id", PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    appointment_id: Mapped[UUID] = mapped_column(
        "cita_id", PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id", PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    dentist_id: Mapped[UUID] = mapped_column(
        "odontologo_id", PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    attention_description: Mapped[str] = mapped_column(
        "descripcion_atencion", Text, nullable=False
    )
    prescribed_medications: Mapped[str | None] = mapped_column(
        "medicamentos_formulados", Text, nullable=True
    )
    requires_followup: Mapped[bool] = mapped_column(
        "requiere_control", Boolean, nullable=False, default=False, server_default=false()
    )
    recommended_followup_date: Mapped[date | None] = mapped_column(
        "fecha_control_recomendada", Date, nullable=True
    )
    followup_reason: Mapped[str | None] = mapped_column(
        "motivo_control", String(500), nullable=True
    )
    registered_by: Mapped[UUID | None] = mapped_column(
        "registrado_por", PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        "registrado_en", DateTime(timezone=True), nullable=False
    )


class PatientFollowup(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "seguimientos_paciente"
    __table_args__ = (
        Index("uq_seguimientos_atencion", "atencion_id", unique=True),
        Index("ix_seguimientos_empresa_fecha", "empresa_id", "fecha_control"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id", PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id", PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    origin_appointment_id: Mapped[UUID] = mapped_column(
        "cita_origen_id", PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    care_id: Mapped[UUID] = mapped_column(
        "atencion_id", PGUUID(as_uuid=True),
        ForeignKey("atenciones_cita.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dentist_id: Mapped[UUID] = mapped_column(
        "odontologo_id", PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    site_id: Mapped[UUID] = mapped_column(
        "sede_id", PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    followup_date: Mapped[date] = mapped_column(
        "fecha_control", Date, nullable=False, index=True
    )
    contact_from: Mapped[date] = mapped_column(
        "fecha_contacto_desde", Date, nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column("motivo", String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        "estado", String(30), nullable=False, default="Pendiente",
        server_default="Pendiente", index=True
    )
    scheduled_appointment_id: Mapped[UUID | None] = mapped_column(
        "cita_programada_id", PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    last_contact_at: Mapped[datetime | None] = mapped_column(
        "ultimo_contacto_en", DateTime(timezone=True), nullable=True
    )
    next_contact_at: Mapped[datetime | None] = mapped_column(
        "proximo_contacto_en", DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        "cerrado_en", DateTime(timezone=True), nullable=True
    )
    closed_by: Mapped[UUID | None] = mapped_column(
        "cerrado_por", PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    close_reason: Mapped[str | None] = mapped_column(
        "motivo_cierre", String(500), nullable=True
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )


class FollowupManagement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seguimiento_gestiones"

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id", PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    followup_id: Mapped[UUID] = mapped_column(
        "seguimiento_id", PGUUID(as_uuid=True),
        ForeignKey("seguimientos_paciente.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id", PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    management_type: Mapped[str] = mapped_column(
        "tipo", String(30), nullable=False
    )
    result: Mapped[str] = mapped_column(
        "resultado", String(50), nullable=False
    )
    observation: Mapped[str | None] = mapped_column(
        "observacion", Text, nullable=True
    )
    next_contact_at: Mapped[datetime | None] = mapped_column(
        "proximo_contacto_en", DateTime(timezone=True), nullable=True
    )
    message_content: Mapped[str | None] = mapped_column(
        "contenido_mensaje", Text, nullable=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        "usuario_id", PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        "fecha", DateTime(timezone=True), nullable=False
    )
