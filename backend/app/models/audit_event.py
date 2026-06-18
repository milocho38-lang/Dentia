from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class AuditEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auditoria_eventos"
    __table_args__ = (
        Index(
            "ix_auditoria_eventos_empresa_fecha",
            "empresa_id",
            "fecha",
        ),
        Index(
            "ix_auditoria_eventos_usuario_fecha",
            "usuario_id",
            "fecha",
        ),
        Index(
            "ix_auditoria_eventos_session_id",
            "session_id",
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
    session_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("auth_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    entity: Mapped[str] = mapped_column(
        "entidad",
        String(100),
        nullable=False,
    )
    entity_id: Mapped[UUID | None] = mapped_column(
        "entidad_id",
        PGUUID(as_uuid=True),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        "accion",
        String(100),
        nullable=False,
    )
    result: Mapped[str] = mapped_column(
        "resultado",
        String(30),
        nullable=False,
    )
    detail: Mapped[dict | None] = mapped_column(
        "detalle",
        JSONB,
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        "ip_origen",
        INET,
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        "fecha",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
