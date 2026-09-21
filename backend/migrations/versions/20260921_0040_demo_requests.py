"""add public demo requests and platform follow-up

Revision ID: 20260921_0040
Revises: 20260914_0039
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260921_0040"
down_revision = "20260914_0039"
branch_labels = None
depends_on = None


PERMISSIONS = (
    (
        "platform.demo_requests.view",
        "Ver solicitudes de demo",
        "Consultar solicitudes comerciales recibidas desde la website.",
    ),
    (
        "platform.demo_requests.manage",
        "Gestionar solicitudes de demo",
        "Asignar, agendar y registrar el seguimiento de solicitudes de demo.",
    ),
)


def upgrade() -> None:
    op.create_table(
        "demo_requests",
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("normalized_email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(50), nullable=False),
        sa.Column("country", sa.String(80), nullable=False),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("practice_type", sa.String(40), nullable=False),
        sa.Column("dentist_count", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("source", sa.String(40), server_default="WEBSITE", nullable=False),
        sa.Column("status", sa.String(30), server_default="NEW", nullable=False),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(80), nullable=True),
        sa.Column("meeting_url", sa.String(500), nullable=True),
        sa.Column("contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consent_version", sa.String(80), nullable=False),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("submission_fingerprint", sa.String(64), nullable=False),
        sa.Column("notification_status", sa.String(30), server_default="PENDING", nullable=False),
        sa.Column("notification_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_error_code", sa.String(80), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('NEW', 'CONTACTED', 'DEMO_SCHEDULED', "
            "'DEMO_COMPLETED', 'CONVERTED', 'NOT_CONTINUING')",
            name="demo_request_status",
        ),
        sa.CheckConstraint(
            "practice_type IN ('INDEPENDENT_DENTIST', 'DENTAL_OFFICE', 'DENTAL_CLINIC')",
            name="demo_request_practice_type",
        ),
        sa.CheckConstraint(
            "source = 'WEBSITE'",
            name="demo_request_source",
        ),
        sa.CheckConstraint(
            "notification_status IN ('PENDING', 'SENT', 'FAILED', 'NOT_CONFIGURED')",
            name="demo_request_notification_status",
        ),
        sa.CheckConstraint(
            "dentist_count >= 1",
            name="demo_request_dentist_count_positive",
        ),
        sa.CheckConstraint(
            "row_version >= 1",
            name="demo_request_row_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_user_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_demo_requests_created_at", "demo_requests", ["created_at"])
    op.create_index(
        "ix_demo_requests_status_created", "demo_requests", ["status", "created_at"]
    )
    op.create_index(
        "ix_demo_requests_country_created", "demo_requests", ["country", "created_at"]
    )
    op.create_index(
        "ix_demo_requests_assigned_created",
        "demo_requests",
        ["assigned_to_user_id", "created_at"],
    )
    op.create_index(
        "ix_demo_requests_submission_fingerprint",
        "demo_requests",
        ["submission_fingerprint"],
    )

    op.create_table(
        "demo_request_notes",
        sa.Column("demo_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_user_id"], ["usuarios.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["demo_request_id"], ["demo_requests.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_demo_request_notes_request_created",
        "demo_request_notes",
        ["demo_request_id", "created_at"],
    )

    for code, name, description in PERMISSIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO permisos (
                    id, code, nombre, modulo, descripcion, is_active,
                    created_at, updated_at
                )
                VALUES (
                    gen_random_uuid(), :code, :name, 'platform', :description,
                    true, now(), now()
                )
                ON CONFLICT (code) DO UPDATE
                SET nombre = EXCLUDED.nombre,
                    modulo = EXCLUDED.modulo,
                    descripcion = EXCLUDED.descripcion,
                    is_active = true,
                    updated_at = now()
                """
            ).bindparams(code=code, name=name, description=description)
        )
        op.execute(
            sa.text(
                """
                INSERT INTO rol_permisos (
                    id, empresa_id, rol_id, permiso_id, is_active,
                    created_by, created_at, updated_at
                )
                SELECT gen_random_uuid(), role.empresa_id, role.id,
                       permission.id, true, role.created_by, now(), now()
                FROM roles AS role
                JOIN permisos AS permission ON permission.code = :permission_code
                WHERE role.code = 'PLATFORM_ADMIN'
                  AND NOT EXISTS (
                      SELECT 1 FROM rol_permisos AS existing
                      WHERE existing.rol_id = role.id
                        AND existing.permiso_id = permission.id
                  )
                """
            ).bindparams(permission_code=code)
        )


def downgrade() -> None:
    codes = tuple(code for code, _, _ in PERMISSIONS)
    op.execute(
        sa.text(
            "DELETE FROM rol_permisos "
            "WHERE permiso_id IN (SELECT id FROM permisos WHERE code IN :codes)"
        ).bindparams(sa.bindparam("codes", expanding=True, value=codes))
    )
    op.execute(
        sa.text("DELETE FROM permisos WHERE code IN :codes").bindparams(
            sa.bindparam("codes", expanding=True, value=codes)
        )
    )
    op.drop_index(
        "ix_demo_request_notes_request_created", table_name="demo_request_notes"
    )
    op.drop_table("demo_request_notes")
    op.drop_index("ix_demo_requests_submission_fingerprint", table_name="demo_requests")
    op.drop_index("ix_demo_requests_assigned_created", table_name="demo_requests")
    op.drop_index("ix_demo_requests_country_created", table_name="demo_requests")
    op.drop_index("ix_demo_requests_status_created", table_name="demo_requests")
    op.drop_index("ix_demo_requests_created_at", table_name="demo_requests")
    op.drop_table("demo_requests")
