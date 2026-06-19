from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Patient(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "pacientes"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "documento",
            name="uq_pacientes_empresa_documento",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    first_names: Mapped[str] = mapped_column(
        "nombres", String(150), nullable=False
    )
    last_names: Mapped[str] = mapped_column(
        "apellidos", String(150), nullable=False
    )
    document: Mapped[str] = mapped_column(
        "documento", String(50), nullable=False
    )
    mobile: Mapped[str] = mapped_column("celular", String(50), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class Dentist(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "odontologos"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "usuario_id",
            name="uq_odontologos_empresa_usuario",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        "usuario_id",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        "estado",
        String(20),
        nullable=False,
        default="Activo",
        server_default="Activo",
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class DentistSite(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "odontologo_sedes"
    __table_args__ = (
        UniqueConstraint(
            "odontologo_id",
            "sede_id",
            name="uq_odontologo_sedes_odontologo_sede",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dentist_id: Mapped[UUID] = mapped_column(
        "odontologo_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    site_id: Mapped[UUID] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class AppointmentType(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "tipos_cita"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "nombre",
            name="uq_tipos_cita_empresa_nombre",
        ),
        CheckConstraint(
            "duracion_sugerida_minutos > 0",
            name="duracion_sugerida_positiva",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(100), nullable=False)
    suggested_duration_minutes: Mapped[int] = mapped_column(
        "duracion_sugerida_minutos",
        Integer,
        nullable=False,
    )
    allows_overbook: Mapped[bool] = mapped_column(
        "permite_sobrecupo",
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class Appointment(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "citas"
    __table_args__ = (
        CheckConstraint("fin > inicio", name="fin_posterior_inicio"),
        Index("ix_citas_odontologo_inicio_fin", "odontologo_id", "inicio", "fin"),
        Index("ix_citas_paciente_inicio_fin", "paciente_id", "inicio", "fin"),
        Index("ix_citas_empresa_inicio", "empresa_id", "inicio"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id",
        PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    dentist_id: Mapped[UUID] = mapped_column(
        "odontologo_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    site_id: Mapped[UUID] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    appointment_type_id: Mapped[UUID] = mapped_column(
        "tipo_cita_id",
        PGUUID(as_uuid=True),
        ForeignKey("tipos_cita.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    origin_appointment_id: Mapped[UUID | None] = mapped_column(
        "cita_origen_id",
        PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(
        "inicio", DateTime(timezone=True), nullable=False
    )
    ends_at: Mapped[datetime] = mapped_column(
        "fin", DateTime(timezone=True), nullable=False
    )
    reason: Mapped[str] = mapped_column("motivo", String(300), nullable=False)
    notes: Mapped[str | None] = mapped_column(
        "observaciones", Text, nullable=True
    )
    status: Mapped[str] = mapped_column(
        "estado",
        String(30),
        nullable=False,
        default="Programada",
        server_default="Programada",
        index=True,
    )
    is_overbook: Mapped[bool] = mapped_column(
        "es_sobrecupo",
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    overbook_reason: Mapped[str | None] = mapped_column(
        "justificacion_sobrecupo", String(300), nullable=True
    )
    confirmation_method: Mapped[str | None] = mapped_column(
        "medio_confirmacion", String(20), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        "confirmada_en", DateTime(timezone=True), nullable=True
    )
    confirmed_by: Mapped[UUID | None] = mapped_column(
        "confirmada_por",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
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


class AppointmentHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cita_historial"
    __table_args__ = (
        Index("ix_cita_historial_cita_fecha", "cita_id", "created_at"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appointment_id: Mapped[UUID] = mapped_column(
        "cita_id",
        PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    related_appointment_id: Mapped[UUID | None] = mapped_column(
        "cita_relacionada_id",
        PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_status: Mapped[str | None] = mapped_column(
        "estado_anterior", String(30), nullable=True
    )
    new_status: Mapped[str] = mapped_column(
        "estado_nuevo", String(30), nullable=False
    )
    previous_starts_at: Mapped[datetime | None] = mapped_column(
        "inicio_anterior", DateTime(timezone=True), nullable=True
    )
    new_starts_at: Mapped[datetime | None] = mapped_column(
        "inicio_nuevo", DateTime(timezone=True), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(
        "motivo", String(300), nullable=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        "usuario_id",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
