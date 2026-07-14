"""add company branding settings

Revision ID: 20260709_0009
Revises: 20260709_0008
Create Date: 2026-07-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260709_0009"
down_revision: str | Sequence[str] | None = "20260709_0008"
branch_labels = None
depends_on = None


PERMISSIONS = (
    (
        "branding.view",
        "Ver personalización",
        "organization",
        "Consultar identidad visual y datos documentales de la empresa.",
    ),
    (
        "branding.update",
        "Actualizar personalización",
        "organization",
        "Modificar identidad visual, textos documentales, colores, logo y firma.",
    ),
)


def _seed_permissions() -> None:
    for code, name, module, description in PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active)
                VALUES (gen_random_uuid(), :code, :name, :module, :description, true)
                ON CONFLICT (code) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    modulo = EXCLUDED.modulo,
                    descripcion = EXCLUDED.descripcion,
                    is_active = true
                """
            ).bindparams(
                code=code,
                name=name,
                module=module,
                description=description,
            )
        )

    op.execute(
        """
        INSERT INTO rol_permisos (
            id, empresa_id, rol_id, permiso_id, is_active, created_by
        )
        SELECT
            gen_random_uuid(),
            r.empresa_id,
            r.id,
            p.id,
            true,
            r.created_by
        FROM roles r
        JOIN permisos p ON p.code IN ('branding.view', 'branding.update')
        WHERE r.code = 'ADMINISTRATOR'
          AND NOT EXISTS (
            SELECT 1
            FROM rol_permisos rp
            WHERE rp.rol_id = r.id
              AND rp.permiso_id = p.id
          )
        """
    )


def upgrade() -> None:
    op.add_column("empresas", sa.Column("razon_social", sa.String(200), nullable=True))
    op.add_column("empresas", sa.Column("departamento", sa.String(100), nullable=True))
    op.add_column("empresas", sa.Column("celular", sa.String(50), nullable=True))
    op.add_column("empresas", sa.Column("sitio_web", sa.String(300), nullable=True))
    op.add_column("empresas", sa.Column("redes_sociales", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("empresas", sa.Column("logo_path", sa.String(500), nullable=True))
    op.add_column("empresas", sa.Column("logo_filename", sa.String(255), nullable=True))
    op.add_column("empresas", sa.Column("signature_path", sa.String(500), nullable=True))
    op.add_column("empresas", sa.Column("signature_filename", sa.String(255), nullable=True))
    op.add_column("empresas", sa.Column("odontologo_principal_nombre", sa.String(200), nullable=True))
    op.add_column("empresas", sa.Column("especialidad", sa.String(150), nullable=True))
    op.add_column("empresas", sa.Column("registro_profesional", sa.String(100), nullable=True))
    op.add_column("empresas", sa.Column("universidad", sa.String(200), nullable=True))
    op.add_column("empresas", sa.Column("anos_experiencia", sa.Integer(), nullable=True))
    op.add_column("empresas", sa.Column("texto_encabezado", sa.String(1000), nullable=True))
    op.add_column("empresas", sa.Column("texto_pie", sa.String(1000), nullable=True))
    op.add_column("empresas", sa.Column("observaciones_legales", sa.String(2000), nullable=True))
    op.add_column("empresas", sa.Column("politica_cancelacion", sa.String(2000), nullable=True))
    op.add_column("empresas", sa.Column("mensaje_agradecimiento", sa.String(1000), nullable=True))
    op.add_column("empresas", sa.Column("color_principal", sa.String(20), server_default="#16a34a", nullable=False))
    op.add_column("empresas", sa.Column("color_secundario", sa.String(20), server_default="#0f766e", nullable=False))
    op.add_column("empresas", sa.Column("color_botones", sa.String(20), server_default="#16a34a", nullable=False))
    op.add_column("empresas", sa.Column("color_encabezados", sa.String(20), server_default="#0f172a", nullable=False))
    _seed_permissions()


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM rol_permisos
        WHERE permiso_id IN (
            SELECT id FROM permisos WHERE code IN ('branding.view', 'branding.update')
        )
        """
    )
    op.execute("DELETE FROM permisos WHERE code IN ('branding.view', 'branding.update')")
    for column in (
        "color_encabezados",
        "color_botones",
        "color_secundario",
        "color_principal",
        "mensaje_agradecimiento",
        "politica_cancelacion",
        "observaciones_legales",
        "texto_pie",
        "texto_encabezado",
        "anos_experiencia",
        "universidad",
        "registro_profesional",
        "especialidad",
        "odontologo_principal_nombre",
        "signature_filename",
        "signature_path",
        "logo_filename",
        "logo_path",
        "redes_sociales",
        "sitio_web",
        "celular",
        "departamento",
        "razon_social",
    ):
        op.drop_column("empresas", column)
