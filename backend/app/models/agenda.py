from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
        Index(
            "uq_pacientes_empresa_tipo_documento_normalizado",
            "empresa_id",
            "tipo_documento",
            "documento_normalizado",
            unique=True,
            postgresql_where=(
                "tipo_documento <> 'Sin documento' "
                "AND documento_normalizado IS NOT NULL"
            ),
        ),
        Index("ix_pacientes_empresa_busqueda", "empresa_id", "texto_busqueda"),
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
    document_type: Mapped[str] = mapped_column(
        "tipo_documento",
        String(20),
        nullable=False,
        default="Sin documento",
        server_default="Sin documento",
    )
    document: Mapped[str | None] = mapped_column(
        "documento", String(50), nullable=True
    )
    normalized_document: Mapped[str | None] = mapped_column(
        "documento_normalizado", String(50), nullable=True
    )
    mobile: Mapped[str] = mapped_column("celular", String(50), nullable=False)
    normalized_mobile: Mapped[str] = mapped_column(
        "celular_normalizado", String(50), nullable=False, default=""
    )
    birth_date: Mapped[date | None] = mapped_column(
        "fecha_nacimiento", Date, nullable=True
    )
    sex: Mapped[str | None] = mapped_column(
        "sexo", String(20), nullable=True
    )
    email: Mapped[str | None] = mapped_column(
        "correo", String(200), nullable=True
    )
    normalized_email: Mapped[str | None] = mapped_column(
        "correo_normalizado", String(200), nullable=True
    )
    alternate_phone: Mapped[str | None] = mapped_column(
        "telefono_alternativo", String(50), nullable=True
    )
    address: Mapped[str | None] = mapped_column(
        "direccion", String(300), nullable=True
    )
    city: Mapped[str | None] = mapped_column(
        "ciudad", String(100), nullable=True
    )
    department: Mapped[str | None] = mapped_column(
        "departamento", String(100), nullable=True
    )
    emergency_contact_name: Mapped[str | None] = mapped_column(
        "contacto_emergencia_nombre", String(200), nullable=True
    )
    emergency_contact_mobile: Mapped[str | None] = mapped_column(
        "contacto_emergencia_celular", String(50), nullable=True
    )
    administrative_notes: Mapped[str | None] = mapped_column(
        "observaciones_administrativas", Text, nullable=True
    )
    status: Mapped[str] = mapped_column(
        "estado",
        String(20),
        nullable=False,
        default="Activo",
        server_default="Activo",
        index=True,
    )
    profile_complete: Mapped[bool] = mapped_column(
        "perfil_completo",
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    search_text: Mapped[str] = mapped_column(
        "texto_busqueda", Text, nullable=False, default=""
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


class PatientResponsible(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ActiveMixin,
    Base,
):
    __tablename__ = "responsables_paciente"
    __table_args__ = (
        Index(
            "uq_responsables_paciente_principal_activo",
            "paciente_id",
            unique=True,
            postgresql_where="es_responsable_principal = true AND is_active = true",
        ),
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
        ForeignKey("pacientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    document_type: Mapped[str] = mapped_column(
        "tipo_documento", String(20), nullable=False
    )
    document: Mapped[str | None] = mapped_column(
        "documento", String(50), nullable=True
    )
    normalized_document: Mapped[str | None] = mapped_column(
        "documento_normalizado", String(50), nullable=True
    )
    relationship: Mapped[str] = mapped_column(
        "parentesco", String(100), nullable=False
    )
    mobile: Mapped[str] = mapped_column("celular", String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(
        "correo", String(200), nullable=True
    )
    is_primary: Mapped[bool] = mapped_column(
        "es_responsable_principal",
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
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
