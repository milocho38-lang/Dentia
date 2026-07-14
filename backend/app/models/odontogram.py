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
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Odontogram(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "odontogramas"
    __table_args__ = (
        UniqueConstraint("empresa_id", "paciente_id", name="uq_odontogramas_empresa_paciente"),
        CheckConstraint("version >= 1", name="ck_odontogramas_version_positive"),
        CheckConstraint("estado IN ('ACTIVE', 'INACTIVE')", name="ck_odontogramas_estado"),
        CheckConstraint(
            "denticion_preferida IN ('PERMANENT', 'PRIMARY', 'MIXED')",
            name="ck_odontogramas_denticion_preferida",
        ),
        Index("ix_odontogramas_empresa_paciente", "empresa_id", "paciente_id"),
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
    status: Mapped[str] = mapped_column(
        "estado",
        String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )
    preferred_dentition: Mapped[str] = mapped_column(
        "denticion_preferida",
        String(20),
        nullable=False,
        default="PERMANENT",
        server_default="PERMANENT",
    )
    created_on: Mapped[datetime] = mapped_column(
        "fecha_creacion",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )


class OdontogramCatalogItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "odontograma_catalogo"
    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="uq_odontograma_catalogo_empresa_codigo"),
        CheckConstraint(
            "tipo IN ('STRUCTURAL_STATE', 'FINDING', 'DIAGNOSIS', 'PLANNED_PROCEDURE', 'PERFORMED_PROCEDURE', 'OBSERVATION')",
            name="ck_odontograma_catalogo_tipo",
        ),
        Index("ix_odontograma_catalogo_empresa_tipo", "empresa_id", "tipo"),
        Index("ix_odontograma_catalogo_codigo", "codigo"),
        Index(
            "uq_odontograma_catalogo_global_codigo",
            "codigo",
            unique=True,
            postgresql_where=text("empresa_id IS NULL"),
        ),
    )

    company_id: Mapped[UUID | None] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column("codigo", String(80), nullable=False)
    name: Mapped[str] = mapped_column("nombre", String(160), nullable=False)
    type: Mapped[str] = mapped_column("tipo", String(40), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column("categoria", String(120), nullable=True)
    description: Mapped[str | None] = mapped_column("descripcion", Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(60), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    allowed_scopes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    allowed_surfaces: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )


class OdontogramEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "odontograma_eventos"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_odontograma_eventos_version_positive"),
        CheckConstraint(
            "tipo_evento IN ('STRUCTURAL_STATE_CHANGED', 'FINDING_ADDED', 'DIAGNOSIS_ADDED', 'PLANNED_PROCEDURE_ADDED', 'PROCEDURE_PERFORMED', 'OBSERVATION_ADDED', 'CORRECTION', 'COMPENSATING_EVENT')",
            name="ck_odontograma_eventos_tipo",
        ),
        CheckConstraint(
            "estado IN ('DRAFT', 'CONFIRMED', 'VOIDED_BY_COMPENSATING_EVENT')",
            name="ck_odontograma_eventos_estado",
        ),
        Index("ix_odontograma_eventos_empresa_paciente_fecha", "empresa_id", "paciente_id", "fecha_clinica"),
        Index("ix_odontograma_eventos_empresa_paciente_estado", "empresa_id", "paciente_id", "estado"),
        Index("ix_odontograma_eventos_evolucion", "evolucion_id"),
        Index("ix_odontograma_eventos_tratamiento", "tratamiento_id"),
        Index("ix_odontograma_eventos_procedimiento", "procedimiento_id"),
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
    odontogram_id: Mapped[UUID] = mapped_column(
        "odontograma_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontogramas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evolution_id: Mapped[UUID | None] = mapped_column(
        "evolucion_id",
        PGUUID(as_uuid=True),
        ForeignKey("evoluciones_clinicas.id", ondelete="SET NULL"),
        nullable=True,
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
    )
    procedure_id: Mapped[UUID | None] = mapped_column(
        "procedimiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamiento_procedimientos.id", ondelete="SET NULL"),
        nullable=True,
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
    event_type: Mapped[str] = mapped_column("tipo_evento", String(60), nullable=False)
    status: Mapped[str] = mapped_column(
        "estado",
        String(40),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )
    clinical_date: Mapped[datetime] = mapped_column(
        "fecha_clinica",
        DateTime(timezone=True),
        nullable=False,
    )
    timezone_name: Mapped[str] = mapped_column("zona_horaria", String(100), nullable=False)
    observation: Mapped[str | None] = mapped_column("observacion", Text, nullable=True)
    correction_reason: Mapped[str | None] = mapped_column("motivo_correccion", Text, nullable=True)
    parent_event_id: Mapped[UUID | None] = mapped_column(
        "parent_event_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontograma_eventos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    content_hash: Mapped[str | None] = mapped_column("hash_contenido", String(128), nullable=True)
    confirmed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class OdontogramEventDetail(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "odontograma_evento_detalles"
    __table_args__ = (
        CheckConstraint(
            "scope_type IN ('GENERAL', 'ZONE', 'TOOTH', 'TOOTH_SURFACE')",
            name="ck_odontograma_detalles_scope",
        ),
        CheckConstraint(
            "dentition IS NULL OR dentition IN ('PERMANENT', 'PRIMARY', 'SUPERNUMERARY')",
            name="ck_odontograma_detalles_dentition",
        ),
        CheckConstraint(
            "layer IN ('STRUCTURAL', 'FINDING', 'DIAGNOSIS', 'PLANNED', 'PERFORMED', 'OBSERVATION')",
            name="ck_odontograma_detalles_layer",
        ),
        Index("ix_odontograma_detalles_evento", "evento_id"),
        Index("ix_odontograma_detalles_diente", "empresa_id", "tooth_code"),
        Index("ix_odontograma_detalles_catalogo", "catalog_item_id"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[UUID] = mapped_column(
        "evento_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontograma_eventos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    catalog_item_id: Mapped[UUID] = mapped_column(
        "catalog_item_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontograma_catalogo.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False)
    zone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tooth_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dentition: Mapped[str | None] = mapped_column(String(30), nullable=True)
    surfaces: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    layer: Mapped[str] = mapped_column(String(30), nullable=False)
    status_after: Mapped[str | None] = mapped_column(String(80), nullable=True)
    detail_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
