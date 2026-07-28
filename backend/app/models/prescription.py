from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Prescription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recetas"
    __table_args__ = (
        CheckConstraint("estado IN ('DRAFT', 'FINALIZED', 'VOIDED')", name="ck_recetas_estado"),
        CheckConstraint("version >= 1", name="ck_recetas_version_positive"),
        UniqueConstraint("empresa_id", "numero_receta", name="uq_recetas_empresa_numero"),
        Index("ix_recetas_empresa_paciente", "empresa_id", "paciente_id"),
        Index("ix_recetas_empresa_estado", "empresa_id", "estado"),
        Index("ix_recetas_empresa_fecha", "empresa_id", "fecha_clinica"),
        Index("ix_recetas_profesional", "empresa_id", "dentist_profile_id"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    site_id: Mapped[UUID] = mapped_column("sede_id", PGUUID(as_uuid=True), ForeignKey("sedes.id", ondelete="RESTRICT"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column("paciente_id", PGUUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False)
    professional_user_id: Mapped[UUID | None] = mapped_column("professional_user_id", PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    dentist_profile_id: Mapped[UUID | None] = mapped_column("dentist_profile_id", PGUUID(as_uuid=True), ForeignKey("odontologos.id", ondelete="SET NULL"), nullable=True)
    related_treatment_id: Mapped[UUID | None] = mapped_column("tratamiento_id", PGUUID(as_uuid=True), ForeignKey("tratamientos.id", ondelete="SET NULL"), nullable=True)
    related_evolution_id: Mapped[UUID | None] = mapped_column("evolucion_id", PGUUID(as_uuid=True), ForeignKey("evoluciones_clinicas.id", ondelete="SET NULL"), nullable=True)
    related_appointment_id: Mapped[UUID | None] = mapped_column("cita_id", PGUUID(as_uuid=True), ForeignKey("citas.id", ondelete="SET NULL"), nullable=True)
    previous_prescription_id: Mapped[UUID | None] = mapped_column("previous_prescription_id", PGUUID(as_uuid=True), ForeignKey("recetas.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False, default="DRAFT", server_default="DRAFT")
    prescription_number: Mapped[str | None] = mapped_column("numero_receta", String(40), nullable=True)
    sequence: Mapped[int | None] = mapped_column("consecutivo", Integer, nullable=True)
    clinical_date: Mapped[date] = mapped_column("fecha_clinica", Date, nullable=False)
    general_instructions: Mapped[str | None] = mapped_column("indicaciones_generales", Text, nullable=True)
    notes: Mapped[str | None] = mapped_column("notas", Text, nullable=True)
    allergies_reviewed: Mapped[bool] = mapped_column("alergias_revisadas", Boolean, nullable=False, default=False, server_default="false")
    finalized_at: Mapped[datetime | None] = mapped_column("finalized_at", DateTime(timezone=True), nullable=True)
    finalized_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column("voided_at", DateTime(timezone=True), nullable=True)
    voided_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    void_reason: Mapped[str | None] = mapped_column("void_reason", Text, nullable=True)
    institution_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    patient_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    professional_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    prescription_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    clinical_alerts_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pdf_storage_path: Mapped[str | None] = mapped_column(String(600), nullable=True)
    pdf_sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
    integrity_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)


class PrescriptionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "receta_items"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_receta_items_position_positive"),
        Index("ix_receta_items_receta", "receta_id"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    prescription_id: Mapped[UUID] = mapped_column("receta_id", PGUUID(as_uuid=True), ForeignKey("recetas.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    generic_name: Mapped[str] = mapped_column("nombre_generico", String(240), nullable=False)
    brand_name: Mapped[str | None] = mapped_column("marca", String(200), nullable=True)
    pharmaceutical_form: Mapped[str] = mapped_column("forma_farmaceutica", String(160), nullable=False)
    concentration: Mapped[str] = mapped_column("concentracion", String(160), nullable=False)
    dose: Mapped[str] = mapped_column("dosis", String(180), nullable=False)
    route: Mapped[str] = mapped_column("via", String(120), nullable=False)
    frequency: Mapped[str] = mapped_column("frecuencia", String(180), nullable=False)
    duration: Mapped[str] = mapped_column("duracion", String(160), nullable=False)
    total_quantity: Mapped[str] = mapped_column("cantidad_total", String(120), nullable=False)
    quantity_unit: Mapped[str | None] = mapped_column("unidad_cantidad", String(120), nullable=True)
    instructions: Mapped[str | None] = mapped_column("indicaciones", Text, nullable=True)
