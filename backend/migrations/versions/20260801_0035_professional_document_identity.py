"""add canonical professional document identity

Revision ID: 20260801_0035
Revises: 20260801_0034
"""

from alembic import op
import sqlalchemy as sa


revision = "20260801_0035"
down_revision = "20260801_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("odontologos", sa.Column("tipo_documento", sa.String(30), nullable=True))
    op.add_column("odontologos", sa.Column("numero_documento", sa.String(80), nullable=True))
    op.add_column("odontologos", sa.Column("especialidad", sa.String(150), nullable=True))
    op.add_column("odontologos", sa.Column("registro_profesional", sa.String(100), nullable=True))
    op.add_column("odontologos", sa.Column("signature_path", sa.String(500), nullable=True))
    op.add_column("odontologos", sa.Column("signature_filename", sa.String(255), nullable=True))

    # The former branding fields describe the institution, not an arbitrary
    # professional. They are copied only when a company has exactly one active
    # dentist, which is the only unambiguous legacy case.
    op.execute(
        """
        UPDATE odontologos AS dentist
        SET especialidad = company.especialidad,
            registro_profesional = company.registro_profesional,
            signature_path = company.signature_path,
            signature_filename = company.signature_filename
        FROM empresas AS company
        WHERE dentist.empresa_id = company.id
          AND dentist.is_active = true
          AND dentist.estado = 'Activo'
          AND (
              SELECT count(*)
              FROM odontologos AS active_dentist
              WHERE active_dentist.empresa_id = company.id
                AND active_dentist.is_active = true
                AND active_dentist.estado = 'Activo'
          ) = 1
        """
    )


def downgrade() -> None:
    op.drop_column("odontologos", "signature_filename")
    op.drop_column("odontologos", "signature_path")
    op.drop_column("odontologos", "registro_profesional")
    op.drop_column("odontologos", "especialidad")
    op.drop_column("odontologos", "numero_documento")
    op.drop_column("odontologos", "tipo_documento")
