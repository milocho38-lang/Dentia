from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Boolean,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Treatment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tratamientos"
    __table_args__ = (
        Index("ix_tratamientos_empresa_paciente", "empresa_id", "paciente_id"),
        Index("ix_tratamientos_empresa_estado", "empresa_id", "estado"),
        Index(
            "ix_tratamientos_empresa_odontologo",
            "empresa_id",
            "odontologo_responsable_id",
        ),
        Index("ix_tratamientos_empresa_sede", "empresa_id", "sede_principal_id"),
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
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(
        "descripcion", Text, nullable=True
    )
    specialty: Mapped[str | None] = mapped_column(
        "especialidad", String(120), nullable=True
    )
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False)
    responsible_dentist_id: Mapped[UUID | None] = mapped_column(
        "odontologo_responsable_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    main_site_id: Mapped[UUID | None] = mapped_column(
        "sede_principal_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    start_date: Mapped[date | None] = mapped_column(
        "fecha_inicio", Date, nullable=True
    )
    end_date: Mapped[date | None] = mapped_column(
        "fecha_fin", Date, nullable=True
    )
    observations: Mapped[str | None] = mapped_column(
        "observaciones", Text, nullable=True
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


class TreatmentProcedure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tratamiento_procedimientos"
    __table_args__ = (
        CheckConstraint("valor_unitario >= 0", name="ck_proc_valor_unitario_no_negativo"),
        CheckConstraint("cantidad > 0", name="ck_proc_cantidad_positiva"),
        CheckConstraint("valor_total >= 0", name="ck_proc_valor_total_no_negativo"),
        Index("ix_proc_empresa_tratamiento", "empresa_id", "tratamiento_id"),
        Index("ix_proc_empresa_estado", "empresa_id", "estado"),
        Index("ix_proc_empresa_odontologo", "empresa_id", "odontologo_id"),
        Index("ix_proc_empresa_sede", "empresa_id", "sede_id"),
        Index("ix_proc_catalogo", "catalogo_procedimiento_id"),
        Index("ix_proc_cita", "cita_id"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    treatment_id: Mapped[UUID] = mapped_column(
        "tratamiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamientos.id", ondelete="CASCADE"),
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
    catalog_procedure_id: Mapped[UUID | None] = mapped_column(
        "catalogo_procedimiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("catalogo_procedimientos.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(
        "categoria", String(120), nullable=True
    )
    dentist_id: Mapped[UUID | None] = mapped_column(
        "odontologo_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    site_id: Mapped[UUID | None] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    appointment_id: Mapped[UUID | None] = mapped_column(
        "cita_id",
        PGUUID(as_uuid=True),
        ForeignKey("citas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    unit_value: Mapped[Decimal] = mapped_column(
        "valor_unitario", Numeric(14, 2), nullable=False, default=0
    )
    quantity: Mapped[Decimal] = mapped_column(
        "cantidad", Numeric(10, 2), nullable=False, default=1
    )
    total_value: Mapped[Decimal] = mapped_column(
        "valor_total", Numeric(14, 2), nullable=False, default=0
    )
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False)
    estimated_date: Mapped[date | None] = mapped_column(
        "fecha_estimada", Date, nullable=True
    )
    performed_at: Mapped[datetime | None] = mapped_column(
        "fecha_realizacion", DateTime(timezone=True), nullable=True
    )
    observations: Mapped[str | None] = mapped_column(
        "observaciones", Text, nullable=True
    )
    requires_tooth: Mapped[bool] = mapped_column(
        "requiere_pieza_dental", Boolean, nullable=False, default=False
    )
    scope_type: Mapped[str] = mapped_column(
        "tipo_alcance", String(30), nullable=False, default="GENERAL", server_default="GENERAL"
    )
    zone: Mapped[str | None] = mapped_column(
        "zona", String(40), nullable=True
    )
    tooth: Mapped[str | None] = mapped_column(
        "pieza_dental", String(30), nullable=True
    )
    surfaces: Mapped[list[str] | None] = mapped_column(
        "caras", JSONB, nullable=True
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


class ProcedureCatalogItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "catalogo_procedimientos"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "nombre_normalizado",
            name="uq_catalogo_proc_empresa_nombre_normalizado",
        ),
        CheckConstraint("valor_sugerido IS NULL OR valor_sugerido >= 0", name="ck_catalogo_proc_valor_no_negativo"),
        Index("ix_catalogo_proc_empresa_activo", "empresa_id", "activo"),
        Index("ix_catalogo_proc_empresa_categoria", "empresa_id", "categoria"),
        Index("ix_catalogo_proc_empresa_id", "empresa_id"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        "nombre_normalizado", String(220), nullable=False
    )
    category: Mapped[str | None] = mapped_column(
        "categoria", String(120), nullable=True
    )
    description: Mapped[str | None] = mapped_column(
        "descripcion", Text, nullable=True
    )
    suggested_value: Mapped[Decimal | None] = mapped_column(
        "valor_sugerido", Numeric(14, 2), nullable=True
    )
    suggested_scope_type: Mapped[str | None] = mapped_column(
        "tipo_alcance_sugerido", String(30), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        "activo", Boolean, nullable=False, default=True, server_default="true"
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


class Budget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "presupuestos"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "tratamiento_id",
            "version",
            name="uq_presupuestos_empresa_tratamiento_version",
        ),
        CheckConstraint("valor_final >= 0", name="ck_presupuestos_valor_final_no_negativo"),
        CheckConstraint("descuento_valor >= 0", name="ck_presupuestos_descuento_no_negativo"),
        CheckConstraint(
            "valor_descuento_calculado >= 0",
            name="ck_presupuestos_descuento_calc_no_negativo",
        ),
        Index("ix_presupuestos_empresa_estado", "empresa_id", "estado"),
        Index("ix_presupuestos_empresa_paciente", "empresa_id", "paciente_id"),
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
    treatment_id: Mapped[UUID] = mapped_column(
        "tratamiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamientos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    number: Mapped[str | None] = mapped_column("numero", String(50), nullable=True)
    version: Mapped[int] = mapped_column("version", Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False)
    gross_value: Mapped[Decimal] = mapped_column(
        "valor_bruto", Numeric(14, 2), nullable=False, default=0
    )
    discount_type: Mapped[str | None] = mapped_column(
        "descuento_tipo", String(20), nullable=True
    )
    discount_value: Mapped[Decimal] = mapped_column(
        "descuento_valor", Numeric(14, 2), nullable=False, default=0
    )
    discount_calculated_value: Mapped[Decimal] = mapped_column(
        "valor_descuento_calculado", Numeric(14, 2), nullable=False, default=0
    )
    final_value: Mapped[Decimal] = mapped_column(
        "valor_final", Numeric(14, 2), nullable=False, default=0
    )
    observations: Mapped[str | None] = mapped_column(
        "observaciones", Text, nullable=True
    )
    issued_at: Mapped[datetime] = mapped_column(
        "fecha_emision", DateTime(timezone=True), nullable=False
    )
    expires_on: Mapped[date | None] = mapped_column(
        "fecha_vencimiento", Date, nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        "aprobado_at", DateTime(timezone=True), nullable=True
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        "aprobado_by",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        "rechazado_at", DateTime(timezone=True), nullable=True
    )
    rejected_by: Mapped[UUID | None] = mapped_column(
        "rechazado_by",
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


class BudgetDetail(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "presupuesto_detalle"
    __table_args__ = (
        Index("ix_presupuesto_detalle_presupuesto", "presupuesto_id"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    budget_id: Mapped[UUID] = mapped_column(
        "presupuesto_id",
        PGUUID(as_uuid=True),
        ForeignKey("presupuestos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    procedure_id: Mapped[UUID | None] = mapped_column(
        "procedimiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamiento_procedimientos.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(
        "categoria", String(120), nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column("cantidad", Numeric(10, 2), nullable=False)
    unit_value: Mapped[Decimal] = mapped_column(
        "valor_unitario", Numeric(14, 2), nullable=False
    )
    total_value: Mapped[Decimal] = mapped_column(
        "valor_total", Numeric(14, 2), nullable=False
    )
    order: Mapped[int] = mapped_column("orden", Integer, nullable=False)
    observations: Mapped[str | None] = mapped_column(
        "observaciones", Text, nullable=True
    )
    scope_type: Mapped[str] = mapped_column(
        "tipo_alcance", String(30), nullable=False, default="GENERAL", server_default="GENERAL"
    )
    zone: Mapped[str | None] = mapped_column(
        "zona", String(40), nullable=True
    )
    tooth: Mapped[str | None] = mapped_column(
        "pieza_dental", String(30), nullable=True
    )
    surfaces: Mapped[list[str] | None] = mapped_column(
        "caras", JSONB, nullable=True
    )


class TreatmentPayment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pagos_tratamiento"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_pagos_tratamiento_valor_positivo"),
        Index("ix_pagos_empresa_fecha", "empresa_id", "fecha_pago"),
        Index("ix_pagos_empresa_tratamiento", "empresa_id", "tratamiento_id"),
        Index("ix_pagos_empresa_paciente", "empresa_id", "paciente_id"),
        Index("ix_pagos_empresa_sede", "empresa_id", "sede_id"),
        Index("ix_pagos_empresa_odontologo", "empresa_id", "odontologo_id"),
        Index("ix_pagos_empresa_estado", "empresa_id", "estado"),
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
    treatment_id: Mapped[UUID] = mapped_column(
        "tratamiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamientos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    budget_id: Mapped[UUID | None] = mapped_column(
        "presupuesto_id",
        PGUUID(as_uuid=True),
        ForeignKey("presupuestos.id", ondelete="SET NULL"),
        nullable=True,
    )
    site_id: Mapped[UUID] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    dentist_id: Mapped[UUID | None] = mapped_column(
        "odontologo_id",
        PGUUID(as_uuid=True),
        ForeignKey("odontologos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    paid_at: Mapped[datetime] = mapped_column(
        "fecha_pago", DateTime(timezone=True), nullable=False
    )
    value: Mapped[Decimal] = mapped_column("valor", Numeric(14, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(
        "medio_pago", String(30), nullable=False
    )
    reference: Mapped[str | None] = mapped_column(
        "referencia", String(120), nullable=True
    )
    observation: Mapped[str | None] = mapped_column(
        "observacion", Text, nullable=True
    )
    status: Mapped[str] = mapped_column("estado", String(20), nullable=False)
    registered_by: Mapped[UUID | None] = mapped_column(
        "registrado_by",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    reversed_at: Mapped[datetime | None] = mapped_column(
        "reversado_at", DateTime(timezone=True), nullable=True
    )
    reversed_by: Mapped[UUID | None] = mapped_column(
        "reversado_by",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    reversal_reason: Mapped[str | None] = mapped_column(
        "motivo_reversion", Text, nullable=True
    )


class TreatmentEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tratamiento_eventos"
    __table_args__ = (
        Index("ix_tratamiento_eventos_tratamiento_fecha", "tratamiento_id", "created_at"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    treatment_id: Mapped[UUID] = mapped_column(
        "tratamiento_id",
        PGUUID(as_uuid=True),
        ForeignKey("tratamientos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        "tipo_evento", String(100), nullable=False
    )
    description: Mapped[str] = mapped_column("descripcion", Text, nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        "usuario_id",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
