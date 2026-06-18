from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint(
            "correo_normalizado",
            name="uq_usuarios_correo_normalizado",
        ),
        CheckConstraint(
            "failed_login_attempts >= 0",
            name="failed_login_attempts_nonnegative",
        ),
        CheckConstraint("auth_version >= 1", name="auth_version_positive"),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    default_site_id: Mapped[UUID | None] = mapped_column(
        "default_sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    email: Mapped[str] = mapped_column("correo", String(320), nullable=False)
    normalized_email: Mapped[str] = mapped_column(
        "correo_normalizado",
        String(320),
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        "celular",
        String(50),
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        "ultimo_login",
        DateTime(timezone=True),
        nullable=True,
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    auth_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    status: Mapped[str] = mapped_column(
        "estado",
        String(20),
        nullable=False,
        default="Pendiente",
        server_default="Pendiente",
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "usuarios.id",
            name="fk_usuarios_created_by_usuarios",
            use_alter=True,
        ),
        nullable=True,
    )
