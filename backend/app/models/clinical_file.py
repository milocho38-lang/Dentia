from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ClinicalFile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "archivos_clinicos"
    __table_args__ = (
        Index("ix_archivos_clinicos_empresa_paciente", "empresa_id", "paciente_id"),
        Index("ix_archivos_clinicos_empresa_tipo", "empresa_id", "tipo_archivo"),
    )

    company_id: Mapped[UUID] = mapped_column("empresa_id", PGUUID(as_uuid=True), ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column("paciente_id", PGUUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False)
    treatment_id: Mapped[UUID | None] = mapped_column("tratamiento_id", PGUUID(as_uuid=True), ForeignKey("tratamientos.id", ondelete="SET NULL"), nullable=True)
    appointment_id: Mapped[UUID | None] = mapped_column("cita_id", PGUUID(as_uuid=True), ForeignKey("citas.id", ondelete="SET NULL"), nullable=True)
    file_type: Mapped[str] = mapped_column("tipo_archivo", String(30), nullable=False)
    category: Mapped[str] = mapped_column("categoria", String(30), nullable=False)
    original_name: Mapped[str] = mapped_column("nombre_archivo", String(300), nullable=False)
    storage_key: Mapped[str] = mapped_column("ruta_archivo", String(600), nullable=False, unique=True)
    idempotency_key: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column("tamano_bytes", BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column("descripcion", Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column("fecha_carga", DateTime(timezone=True), nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column("cargado_por_usuario_id", PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
