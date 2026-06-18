from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "permisos"

    code: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    name: Mapped[str] = mapped_column("nombre", String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(
        "descripcion",
        Text,
        nullable=True,
    )
    module: Mapped[str] = mapped_column("modulo", String(100), nullable=False)
