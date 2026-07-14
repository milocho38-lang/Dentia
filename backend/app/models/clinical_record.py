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
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ClinicalRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "historias_clinicas"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "paciente_id",
            name="uq_historias_clinicas_empresa_paciente",
        ),
        CheckConstraint("version >= 1", name="historias_clinicas_version_positive"),
        Index("ix_historias_clinicas_empresa_estado", "empresa_id", "estado"),
        Index("ix_historias_clinicas_paciente", "paciente_id"),
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
    status: Mapped[str] = mapped_column(
        "estado",
        String(20),
        nullable=False,
        default="ACTIVA",
        server_default="ACTIVA",
    )
    opened_at: Mapped[datetime] = mapped_column(
        "fecha_apertura",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    opening_site_id: Mapped[UUID | None] = mapped_column(
        "sede_apertura_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    opening_dentist_id: Mapped[UUID | None] = mapped_column(
        "odontologo_apertura_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chief_complaint: Mapped[str | None] = mapped_column(
        "motivo_consulta", Text, nullable=True
    )
    current_situation: Mapped[str | None] = mapped_column(
        "situacion_actual", Text, nullable=True
    )
    situation_start: Mapped[str | None] = mapped_column(
        "inicio_situacion", String(200), nullable=True
    )
    situation_evolution: Mapped[str | None] = mapped_column(
        "evolucion_situacion", Text, nullable=True
    )
    symptoms: Mapped[str | None] = mapped_column("sintomas", Text, nullable=True)
    previous_treatments: Mapped[str | None] = mapped_column(
        "tratamientos_previos", Text, nullable=True
    )
    informant_type: Mapped[str | None] = mapped_column(
        "informante_tipo", String(50), nullable=True
    )
    informant_name: Mapped[str | None] = mapped_column(
        "informante_nombre", String(200), nullable=True
    )
    informant_relationship: Mapped[str | None] = mapped_column(
        "informante_parentesco", String(100), nullable=True
    )
    informant_document: Mapped[str | None] = mapped_column(
        "informante_documento", String(80), nullable=True
    )
    observations: Mapped[str | None] = mapped_column("observaciones", Text, nullable=True)
    habits: Mapped[dict] = mapped_column(
        "habitos",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    dental_history: Mapped[dict] = mapped_column(
        "antecedentes_odontologicos",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    allergies_state: Mapped[str] = mapped_column(
        "estado_alergias",
        String(40),
        nullable=False,
        default="NO_CONFIRMADA",
        server_default="NO_CONFIRMADA",
    )
    medical_history_state: Mapped[str] = mapped_column(
        "estado_antecedentes",
        String(40),
        nullable=False,
        default="NO_CONFIRMADO",
        server_default="NO_CONFIRMADO",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class ClinicalMedicalHistoryItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "historias_clinicas_antecedentes"
    __table_args__ = (
        CheckConstraint("version >= 1", name="hist_clin_ant_version_positive"),
        Index("ix_hist_clin_ant_historia", "historia_clinica_id"),
        Index("ix_hist_clin_ant_paciente_tipo", "paciente_id", "tipo"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinical_record_id: Mapped[UUID] = mapped_column(
        "historia_clinica_id",
        PGUUID(as_uuid=True),
        ForeignKey("historias_clinicas.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id",
        PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column("tipo", String(120), nullable=False)
    present: Mapped[str] = mapped_column(
        "presente",
        String(20),
        nullable=False,
        default="DESCONOCIDO",
        server_default="DESCONOCIDO",
    )
    detail: Mapped[str | None] = mapped_column("detalle", Text, nullable=True)
    severity: Mapped[str | None] = mapped_column("severidad", String(40), nullable=True)
    status: Mapped[str] = mapped_column(
        "estado",
        String(40),
        nullable=False,
        default="activo",
        server_default="activo",
    )
    source: Mapped[str | None] = mapped_column("fuente", String(120), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class ClinicalAllergy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "historias_clinicas_alergias"
    __table_args__ = (
        CheckConstraint("version >= 1", name="hist_clin_alergias_version_positive"),
        Index("ix_hist_clin_alergias_historia", "historia_clinica_id"),
        Index("ix_hist_clin_alergias_paciente_critica", "paciente_id", "alerta_critica"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinical_record_id: Mapped[UUID] = mapped_column(
        "historia_clinica_id",
        PGUUID(as_uuid=True),
        ForeignKey("historias_clinicas.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id",
        PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column("tipo", String(40), nullable=False)
    substance: Mapped[str] = mapped_column("sustancia", String(200), nullable=False)
    reaction: Mapped[str | None] = mapped_column("reaccion", String(300), nullable=True)
    severity: Mapped[str] = mapped_column(
        "severidad",
        String(40),
        nullable=False,
        default="desconocida",
        server_default="desconocida",
    )
    status: Mapped[str] = mapped_column(
        "estado",
        String(40),
        nullable=False,
        default="no confirmada",
        server_default="no confirmada",
    )
    critical_alert: Mapped[bool] = mapped_column(
        "alerta_critica",
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    observations: Mapped[str | None] = mapped_column("observaciones", Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class ClinicalMedication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "historias_clinicas_medicamentos"
    __table_args__ = (
        CheckConstraint("version >= 1", name="hist_clin_medicamentos_version_positive"),
        Index("ix_hist_clin_meds_historia", "historia_clinica_id"),
        Index("ix_hist_clin_meds_paciente_estado", "paciente_id", "estado"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinical_record_id: Mapped[UUID] = mapped_column(
        "historia_clinica_id",
        PGUUID(as_uuid=True),
        ForeignKey("historias_clinicas.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        "paciente_id",
        PGUUID(as_uuid=True),
        ForeignKey("pacientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    dose: Mapped[str | None] = mapped_column("dosis", String(120), nullable=True)
    frequency: Mapped[str | None] = mapped_column("frecuencia", String(120), nullable=True)
    route: Mapped[str | None] = mapped_column("via", String(80), nullable=True)
    since: Mapped[str | None] = mapped_column("desde", String(120), nullable=True)
    reason: Mapped[str | None] = mapped_column("motivo", String(300), nullable=True)
    prescriber: Mapped[str | None] = mapped_column("prescriptor", String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        "estado",
        String(40),
        nullable=False,
        default="activo",
        server_default="activo",
    )
    observations: Mapped[str | None] = mapped_column("observaciones", Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class ClinicalEvolution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evoluciones_clinicas"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_evoluciones_clinicas_version_positive"),
        CheckConstraint(
            "estado IN ('DRAFT', 'SIGNED', 'VOIDED_BY_COMPENSATING_RECORD')",
            name="ck_evoluciones_clinicas_estado",
        ),
        UniqueConstraint(
            "empresa_id",
            "cita_id",
            name="uq_evoluciones_clinicas_empresa_cita_principal",
        ),
        Index("ix_evoluciones_empresa_paciente_fecha", "empresa_id", "paciente_id", "fecha_atencion"),
        Index("ix_evoluciones_empresa_historia", "empresa_id", "historia_clinica_id"),
        Index("ix_evoluciones_empresa_cita", "empresa_id", "cita_id"),
        Index("ix_evoluciones_empresa_odontologo", "empresa_id", "odontologo_id"),
        Index("ix_evoluciones_empresa_sede", "empresa_id", "sede_id"),
        Index("ix_evoluciones_empresa_estado", "empresa_id", "estado"),
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
    clinical_record_id: Mapped[UUID] = mapped_column(
        "historia_clinica_id",
        PGUUID(as_uuid=True),
        ForeignKey("historias_clinicas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appointment_id: Mapped[UUID | None] = mapped_column(
        "cita_id",
        PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    treatment_id: Mapped[UUID | None] = mapped_column(
        "tratamiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamientos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    site_id: Mapped[UUID] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="RESTRICT"),
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
    attended_at: Mapped[datetime] = mapped_column(
        "fecha_atencion", DateTime(timezone=True), nullable=False
    )
    timezone_name: Mapped[str] = mapped_column(
        "zona_horaria", String(100), nullable=False, default="America/Bogota"
    )
    reason: Mapped[str | None] = mapped_column("motivo", Text, nullable=True)
    subjective: Mapped[str | None] = mapped_column("subjetivo", Text, nullable=True)
    objective: Mapped[str | None] = mapped_column("objetivo", Text, nullable=True)
    assessment: Mapped[str | None] = mapped_column("evaluacion", Text, nullable=True)
    performed_procedure: Mapped[str | None] = mapped_column(
        "procedimiento_realizado", Text, nullable=True
    )
    anesthesia: Mapped[str | None] = mapped_column("anestesia", Text, nullable=True)
    materials: Mapped[str | None] = mapped_column("materiales", Text, nullable=True)
    administered_medications: Mapped[str | None] = mapped_column(
        "medicamentos_administrados", Text, nullable=True
    )
    findings: Mapped[str | None] = mapped_column("hallazgos", Text, nullable=True)
    complications: Mapped[str | None] = mapped_column("complicaciones", Text, nullable=True)
    indications: Mapped[str | None] = mapped_column("indicaciones", Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column("recomendaciones", Text, nullable=True)
    next_control_at: Mapped[datetime | None] = mapped_column(
        "proximo_control_fecha", DateTime(timezone=True), nullable=True
    )
    next_control_reason: Mapped[str | None] = mapped_column(
        "proximo_control_motivo", Text, nullable=True
    )
    followup_id: Mapped[UUID | None] = mapped_column(
        "seguimiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("seguimientos_paciente.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observations: Mapped[str | None] = mapped_column("observaciones", Text, nullable=True)
    status: Mapped[str] = mapped_column(
        "estado", String(40), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    content_hash: Mapped[str | None] = mapped_column("hash_contenido", String(128), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class ClinicalEvolutionProcedure(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evoluciones_procedimientos"
    __table_args__ = (
        CheckConstraint(
            "accion IN ('PLANNED', 'PERFORMED', 'REVIEWED', 'SUSPENDED')",
            name="ck_evoluciones_proc_accion",
        ),
        Index("ix_evoluciones_proc_evolucion", "evolucion_id"),
        Index("ix_evoluciones_proc_procedimiento", "procedimiento_id"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evolution_id: Mapped[UUID] = mapped_column(
        "evolucion_id",
        PGUUID(as_uuid=True),
        ForeignKey("evoluciones_clinicas.id", ondelete="CASCADE"),
        nullable=False,
    )
    treatment_id: Mapped[UUID | None] = mapped_column(
        "tratamiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamientos.id", ondelete="SET NULL"),
        nullable=True,
    )
    procedure_id: Mapped[UUID] = mapped_column(
        "procedimiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamiento_procedimientos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column("accion", String(30), nullable=False)
    observations: Mapped[str | None] = mapped_column("observaciones", Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ClinicalEvolutionAddendum(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evoluciones_adendas"
    __table_args__ = (
        Index("ix_evoluciones_adendas_evolucion", "evolucion_id"),
        Index("ix_evoluciones_adendas_paciente", "empresa_id", "paciente_id"),
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
    evolution_id: Mapped[UUID] = mapped_column(
        "evolucion_id",
        PGUUID(as_uuid=True),
        ForeignKey("evoluciones_clinicas.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column("motivo", Text, nullable=False)
    content: Mapped[str] = mapped_column("contenido", Text, nullable=False)
    dentist_id: Mapped[UUID] = mapped_column(
        "odontologo_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    site_id: Mapped[UUID] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    content_hash: Mapped[str | None] = mapped_column("hash_contenido", String(128), nullable=True)
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ClinicalTimelineEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "historia_clinica_eventos"
    __table_args__ = (
        Index("ix_historia_eventos_paciente_fecha", "empresa_id", "paciente_id", "fecha_clinica"),
        Index("ix_historia_eventos_historia", "historia_clinica_id"),
        Index("ix_historia_eventos_tipo", "empresa_id", "tipo_evento"),
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
    clinical_record_id: Mapped[UUID] = mapped_column(
        "historia_clinica_id",
        PGUUID(as_uuid=True),
        ForeignKey("historias_clinicas.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column("tipo_evento", String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column("entidad_tipo", String(80), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(
        "entidad_id", PGUUID(as_uuid=True), nullable=True
    )
    title: Mapped[str] = mapped_column("titulo", String(250), nullable=False)
    summary: Mapped[str | None] = mapped_column("descripcion_resumen", Text, nullable=True)
    clinical_date: Mapped[datetime] = mapped_column(
        "fecha_clinica", DateTime(timezone=True), nullable=False
    )
    site_id: Mapped[UUID | None] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="SET NULL"),
        nullable=True,
    )
    dentist_id: Mapped[UUID | None] = mapped_column(
        "odontologo_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    event_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
