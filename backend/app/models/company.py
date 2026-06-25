from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "empresas"

    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    company_type: Mapped[str | None] = mapped_column(
        "tipo_empresa", String(50), nullable=True
    )
    tax_id: Mapped[str | None] = mapped_column("nit", String(50), nullable=True)
    normalized_tax_id: Mapped[str | None] = mapped_column(
        "nit_normalizado", String(50), nullable=True, index=True
    )
    phone: Mapped[str | None] = mapped_column(
        "telefono", String(50), nullable=True
    )
    email: Mapped[str | None] = mapped_column(
        "correo", String(200), nullable=True
    )
    address: Mapped[str | None] = mapped_column(
        "direccion", String(300), nullable=True
    )
    city: Mapped[str | None] = mapped_column(
        "ciudad", String(100), nullable=True
    )
    country: Mapped[str | None] = mapped_column(
        "pais", String(100), nullable=True
    )
    timezone: Mapped[str] = mapped_column(
        "zona_horaria",
        String(100),
        nullable=False,
        default="America/Bogota",
        server_default="America/Bogota",
    )
    status: Mapped[str] = mapped_column(
        "estado",
        String(20),
        nullable=False,
        default="Activa",
        server_default="Activa",
    )
    installation_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "usuarios.id",
            name="fk_empresas_created_by_usuarios",
            use_alter=True,
        ),
        nullable=True,
    )
