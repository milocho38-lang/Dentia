from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class OrthodonticsEntitlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontics_entitlements"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            name="uq_orthodontics_entitlements_company",
        ),
        UniqueConstraint(
            "id",
            "empresa_id",
            name="uq_orthodontics_entitlements_id_company",
        ),
        CheckConstraint(
            "seat_limit >= 0",
            name="orthodontics_entitlement_seat_limit_nonnegative",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED', 'DISABLED')",
            name="orthodontics_entitlement_status",
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_from IS NULL "
            "OR effective_until >= effective_from",
            name="orthodontics_entitlement_effective_range",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="DISABLED",
        server_default="DISABLED",
    )
    seat_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    effective_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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


class OrthodonticsDentistAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orthodontics_dentist_assignments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["entitlement_id", "empresa_id"],
            [
                "orthodontics_entitlements.id",
                "orthodontics_entitlements.empresa_id",
            ],
            name="fk_orthodontics_assignment_entitlement_company",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["odontologo_id", "empresa_id"],
            ["odontologos.id", "odontologos.empresa_id"],
            name="fk_orthodontics_assignment_dentist_company",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "(is_active IS TRUE AND revoked_at IS NULL) "
            "OR (is_active IS FALSE AND revoked_at IS NOT NULL)",
            name="orthodontics_assignment_revocation_state",
        ),
        Index(
            "uq_orthodontics_assignment_active_dentist",
            "empresa_id",
            "odontologo_id",
            unique=True,
            postgresql_where=text("is_active IS TRUE"),
        ),
        Index(
            "ix_orthodontics_assignment_company_active",
            "empresa_id",
            "is_active",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entitlement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    dentist_id: Mapped[UUID] = mapped_column(
        "odontologo_id",
        PGUUID(as_uuid=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    assigned_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
    )
    revocation_reason: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )
