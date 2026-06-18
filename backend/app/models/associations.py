from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint, false
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "usuario_roles"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "rol_id",
            name="uq_usuario_roles_usuario_rol",
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
    role_id: Mapped[UUID] = mapped_column(
        "rol_id",
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class RolePermission(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "rol_permisos"
    __table_args__ = (
        UniqueConstraint(
            "rol_id",
            "permiso_id",
            name="uq_rol_permisos_rol_permiso",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        "empresa_id",
        PGUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        "rol_id",
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        "permiso_id",
        PGUUID(as_uuid=True),
        ForeignKey("permisos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )


class UserSite(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "usuario_sedes"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "sede_id",
            name="uq_usuario_sedes_usuario_sede",
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
    site_id: Mapped[UUID] = mapped_column(
        "sede_id",
        PGUUID(as_uuid=True),
        ForeignKey("sedes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_default: Mapped[bool] = mapped_column(
        "es_principal",
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
