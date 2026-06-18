from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AuthSession(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        UniqueConstraint(
            "refresh_token_hash",
            name="uq_auth_sessions_refresh_token_hash",
        ),
        Index(
            "ix_auth_sessions_usuario_last_seen",
            "usuario_id",
            "last_seen_at",
        ),
        Index(
            "ix_auth_sessions_expires_at",
            "expires_at",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        "usuario_id",
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active_site_id: Mapped[UUID | None] = mapped_column(
        "sede_activa_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    token_family_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    rotation_counter: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        index=True,
    )
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    revoke_reason: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
