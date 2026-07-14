from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import ActiveMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "empresas"

    name: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(
        "razon_social", String(200), nullable=True
    )
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
    department: Mapped[str | None] = mapped_column(
        "departamento", String(100), nullable=True
    )
    country: Mapped[str | None] = mapped_column(
        "pais", String(100), nullable=True
    )
    mobile: Mapped[str | None] = mapped_column(
        "celular", String(50), nullable=True
    )
    website: Mapped[str | None] = mapped_column(
        "sitio_web", String(300), nullable=True
    )
    social_media: Mapped[dict | None] = mapped_column(
        "redes_sociales", JSONB, nullable=True
    )
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signature_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signature_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_dentist_name: Mapped[str | None] = mapped_column(
        "odontologo_principal_nombre", String(200), nullable=True
    )
    professional_specialty: Mapped[str | None] = mapped_column(
        "especialidad", String(150), nullable=True
    )
    professional_license: Mapped[str | None] = mapped_column(
        "registro_profesional", String(100), nullable=True
    )
    university: Mapped[str | None] = mapped_column(
        "universidad", String(200), nullable=True
    )
    experience_years: Mapped[int | None] = mapped_column(
        "anos_experiencia", nullable=True
    )
    header_text: Mapped[str | None] = mapped_column(
        "texto_encabezado", String(1000), nullable=True
    )
    footer_text: Mapped[str | None] = mapped_column(
        "texto_pie", String(1000), nullable=True
    )
    legal_observations: Mapped[str | None] = mapped_column(
        "observaciones_legales", String(2000), nullable=True
    )
    cancellation_policy: Mapped[str | None] = mapped_column(
        "politica_cancelacion", String(2000), nullable=True
    )
    thank_you_message: Mapped[str | None] = mapped_column(
        "mensaje_agradecimiento", String(1000), nullable=True
    )
    primary_color: Mapped[str] = mapped_column(
        "color_principal", String(20), nullable=False, default="#16a34a", server_default="#16a34a"
    )
    secondary_color: Mapped[str] = mapped_column(
        "color_secundario", String(20), nullable=False, default="#0f766e", server_default="#0f766e"
    )
    button_color: Mapped[str] = mapped_column(
        "color_botones", String(20), nullable=False, default="#16a34a", server_default="#16a34a"
    )
    heading_color: Mapped[str] = mapped_column(
        "color_encabezados", String(20), nullable=False, default="#0f172a", server_default="#0f172a"
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
