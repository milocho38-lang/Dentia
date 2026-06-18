from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class AuthAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auth_attempts"
    __table_args__ = (
        Index(
            "ix_auth_attempts_fingerprint_fecha",
            "email_fingerprint",
            "fecha",
        ),
        Index(
            "ix_auth_attempts_ip_fecha",
            "ip_address",
            "fecha",
        ),
        Index(
            "ix_auth_attempts_usuario_fecha",
            "usuario_id",
            "fecha",
        ),
    )

    company_id: Mapped[UUID | None] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        "usuario_id",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    email_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        index=True,
    )
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str] = mapped_column(
        "resultado",
        String(30),
        nullable=False,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        "motivo_fallo",
        String(50),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        "fecha",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
