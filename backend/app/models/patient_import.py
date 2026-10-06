from uuid import UUID

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class PatientImportSource(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "patient_import_sources"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "code",
            name="uq_patient_import_source_code",
        ),
        UniqueConstraint("id", "company_id", name="uq_patient_import_source_id_company"),
    )

    company_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_system: Mapped[str] = mapped_column(String(40), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class PatientExternalReference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "patient_external_references"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_id",
            "source_patient_id",
            name="uq_patient_external_reference_source",
        ),
        ForeignKeyConstraint(
            ["source_id", "company_id"],
            ["patient_import_sources.id", "patient_import_sources.company_id"],
            name="fk_patient_external_reference_tenant_source",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["patient_id", "company_id"],
            ["pacientes.id", "pacientes.empresa_id"],
            name="fk_patient_external_reference_tenant_patient",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_patient_external_reference_company_patient",
            "company_id",
            "patient_id",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    source_patient_id: Mapped[str] = mapped_column(String(120), nullable=False)
    source_file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    imported_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
