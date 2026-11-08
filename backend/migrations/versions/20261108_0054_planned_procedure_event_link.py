"""link treatment procedures to explicit odontogram planning events

Revision ID: 20261108_0054
Revises: 20261108_0053
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261108_0054"
down_revision = "20261108_0053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_catalogo_proc_odontogram_behavior",
        "catalogo_procedimientos",
        type_="check",
    )
    op.create_check_constraint(
        "ck_catalogo_proc_odontogram_behavior",
        "catalogo_procedimientos",
        "odontogram_behavior IN ('UNCONFIGURED', 'NO_CHANGE', 'OPTIONAL_DIAGNOSIS', 'REQUIRES_DIAGNOSIS', 'PLANNED_RESULT')",
    )
    op.add_column(
        "tratamiento_procedimientos",
        sa.Column("odontograma_evento_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_proc_odontograma_evento_plan",
        "tratamiento_procedimientos",
        "odontograma_eventos",
        ["odontograma_evento_plan_id"],
        ["id"],
        ondelete="SET NULL",
        use_alter=True,
    )
    op.create_index(
        "ix_proc_odontograma_evento_plan",
        "tratamiento_procedimientos",
        ["odontograma_evento_plan_id"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    planned_catalog_count = connection.execute(
        sa.text(
            "SELECT count(*) FROM catalogo_procedimientos "
            "WHERE odontogram_behavior = 'PLANNED_RESULT'"
        )
    ).scalar_one()
    planned_link_count = connection.execute(
        sa.text(
            "SELECT count(*) FROM tratamiento_procedimientos "
            "WHERE odontograma_evento_plan_id IS NOT NULL"
        )
    ).scalar_one()
    if planned_catalog_count or planned_link_count:
        raise RuntimeError(
            "Downgrade 0054 rechazado: existen catálogos o vínculos odontográficos planificados; "
            "no se eliminará historia clínica."
        )
    op.drop_index("ix_proc_odontograma_evento_plan", table_name="tratamiento_procedimientos")
    op.drop_constraint(
        "fk_proc_odontograma_evento_plan",
        "tratamiento_procedimientos",
        type_="foreignkey",
    )
    op.drop_column("tratamiento_procedimientos", "odontograma_evento_plan_id")
    op.drop_constraint(
        "ck_catalogo_proc_odontogram_behavior",
        "catalogo_procedimientos",
        type_="check",
    )
    op.create_check_constraint(
        "ck_catalogo_proc_odontogram_behavior",
        "catalogo_procedimientos",
        "odontogram_behavior IN ('UNCONFIGURED', 'NO_CHANGE', 'OPTIONAL_DIAGNOSIS', 'REQUIRES_DIAGNOSIS')",
    )
