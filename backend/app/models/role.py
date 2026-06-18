from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint, false
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Role(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("empresa_id", "code", name="uq_roles_empresa_code"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column("nombre", String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(
        "descripcion",
        Text,
        nullable=True,
    )
    is_system: Mapped[bool] = mapped_column(
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
