from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Site(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "sedes"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "nombre_normalizado",
            name="uq_sedes_empresa_nombre_normalizado",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(150), nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        "nombre_normalizado", String(150), nullable=False
    )
    address: Mapped[str] = mapped_column(
        "direccion", String(300), nullable=False
    )
    city: Mapped[str] = mapped_column("ciudad", String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(
        "telefono", String(50), nullable=True
    )
    timezone: Mapped[str | None] = mapped_column(
        "zona_horaria", String(100), nullable=True
    )
    status: Mapped[str] = mapped_column(
        "estado",
        String(20),
        nullable=False,
        default="Activa",
        server_default="Activa",
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "usuarios.id",
            name="fk_sedes_created_by_usuarios",
            use_alter=True,
        ),
        nullable=True,
    )
