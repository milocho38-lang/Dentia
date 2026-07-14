"""create odontogram historical MVP

Revision ID: 20260714_0014
Revises: 20260714_0013
Create Date: 2026-07-14 00:14:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260714_0014"
down_revision: str | Sequence[str] | None = "20260714_0013"
branch_labels = None
depends_on = None


PERMISSIONS = (
    ("odontogram.view", "Ver odontograma", "odontogram", "Consultar odontograma e historial."),
    ("odontogram.create", "Crear odontograma", "odontogram", "Crear cabecera de odontograma para pacientes con historia clínica."),
    ("odontogram.update_draft", "Actualizar borradores de odontograma", "odontogram", "Editar eventos odontográficos en borrador."),
    ("odontogram.confirm", "Confirmar eventos de odontograma", "odontogram", "Confirmar eventos odontográficos y calcular hash de integridad."),
    ("odontogram.correct", "Corregir eventos de odontograma", "odontogram", "Registrar correcciones o eventos compensatorios sobre eventos confirmados."),
    ("odontogram.history", "Ver histórico de odontograma", "odontogram", "Consultar histórico odontográfico por diente o superficie."),
)

ROLE_PERMISSIONS = {
    "DENTIST_ADMIN": [code for code, *_ in PERMISSIONS],
    "DENTIST": [code for code, *_ in PERMISSIONS],
}

CATALOG = (
    ("STRUCT_HEALTHY", "Sano", "STRUCTURAL_STATE", "Estado estructural", "Diente sin hallazgos activos registrados.", "#16a34a", "solid", "✓", ["TOOTH"], None),
    ("STRUCT_MISSING", "Ausente", "STRUCTURAL_STATE", "Estado estructural", "Ausencia dental.", "#94a3b8", "dashed", "∅", ["TOOTH"], None),
    ("STRUCT_IMPLANT", "Implante", "STRUCTURAL_STATE", "Estado estructural", "Implante dental.", "#64748b", "solid", "I", ["TOOTH"], None),
    ("STRUCT_PRIMARY", "Temporal", "STRUCTURAL_STATE", "Estado estructural", "Pieza temporal.", "#0ea5e9", "solid", "T", ["TOOTH"], None),
    ("STRUCT_PERMANENT", "Permanente", "STRUCTURAL_STATE", "Estado estructural", "Pieza permanente.", "#0f766e", "solid", "P", ["TOOTH"], None),
    ("STRUCT_UNERUPTED", "No erupcionado", "STRUCTURAL_STATE", "Estado estructural", "Pieza no erupcionada.", "#cbd5e1", "faded", "NE", ["TOOTH"], None),
    ("STRUCT_ERUPTING", "Erupcionando", "STRUCTURAL_STATE", "Estado estructural", "Pieza en erupción.", "#f59e0b", "partial", "E", ["TOOTH"], None),
    ("STRUCT_EXFOLIATED", "Exfoliado", "STRUCTURAL_STATE", "Estado estructural", "Pieza temporal exfoliada.", "#94a3b8", "dotted", "EX", ["TOOTH"], None),
    ("STRUCT_RETAINED", "Retenido", "STRUCTURAL_STATE", "Estado estructural", "Pieza retenida.", "#7c3aed", "outline", "R", ["TOOTH"], None),
    ("FIND_CARIES", "Caries", "FINDING", "Hallazgo", "Caries observada.", "#dc2626", "solid", "C", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("FIND_FRACTURE", "Fractura", "FINDING", "Hallazgo", "Fractura dental.", "#ef4444", "diagonal", "F", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("FIND_WEAR", "Desgaste", "FINDING", "Hallazgo", "Desgaste dental.", "#f97316", "stripes", "D", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("FIND_PIGMENT", "Pigmentación", "FINDING", "Hallazgo", "Pigmentación dental.", "#a16207", "dots", "P", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("FIND_RESTORATION", "Restauración existente", "FINDING", "Hallazgo", "Restauración previa existente.", "#2563eb", "solid", "R", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("FIND_CROWN", "Corona existente", "FINDING", "Hallazgo", "Corona previa existente.", "#16a34a", "solid", "Co", ["TOOTH"], None),
    ("FIND_IMPLANT", "Implante existente", "FINDING", "Hallazgo", "Implante existente.", "#64748b", "solid", "I", ["TOOTH"], None),
    ("FIND_ABSENCE", "Ausencia dental", "FINDING", "Hallazgo", "Ausencia dental observada.", "#94a3b8", "dashed", "∅", ["TOOTH"], None),
    ("DX_ACTIVE_CARIES", "Caries activa", "DIAGNOSIS", "Diagnóstico", "Diagnóstico de caries activa.", "#991b1b", "solid", "Dx", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("DX_PULPITIS", "Pulpitis", "DIAGNOSIS", "Diagnóstico", "Pulpitis.", "#7f1d1d", "solid", "Pu", ["TOOTH"], None),
    ("DX_NECROSIS", "Necrosis pulpar", "DIAGNOSIS", "Diagnóstico", "Necrosis pulpar.", "#450a0a", "solid", "N", ["TOOTH"], None),
    ("DX_PERIAPICAL", "Lesión periapical", "DIAGNOSIS", "Diagnóstico", "Lesión periapical.", "#9f1239", "solid", "LP", ["TOOTH"], None),
    ("DX_TRAUMA", "Trauma dental", "DIAGNOSIS", "Diagnóstico", "Trauma dental.", "#be123c", "solid", "Tr", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("PLAN_RESIN", "Resina", "PLANNED_PROCEDURE", "Procedimiento planificado", "Resina planificada.", "#f97316", "outline", "Re", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("PLAN_ENDO", "Endodoncia", "PLANNED_PROCEDURE", "Procedimiento planificado", "Endodoncia planificada.", "#a855f7", "outline", "En", ["TOOTH"], None),
    ("PLAN_CROWN", "Corona", "PLANNED_PROCEDURE", "Procedimiento planificado", "Corona planificada.", "#22c55e", "outline", "Co", ["TOOTH"], None),
    ("PLAN_EXTRACTION", "Extracción", "PLANNED_PROCEDURE", "Procedimiento planificado", "Extracción planificada.", "#f97316", "outline", "Ex", ["TOOTH"], None),
    ("PLAN_IMPLANT", "Implante", "PLANNED_PROCEDURE", "Procedimiento planificado", "Implante planificado.", "#f97316", "outline", "Im", ["TOOTH"], None),
    ("PLAN_SEALANT", "Sellante", "PLANNED_PROCEDURE", "Procedimiento planificado", "Sellante planificado.", "#f97316", "outline", "S", ["TOOTH_SURFACE"], ["OCCLUSAL"]),
    ("DONE_RESIN", "Resina realizada", "PERFORMED_PROCEDURE", "Procedimiento realizado", "Resina realizada.", "#2563eb", "solid", "Re", ["TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
    ("DONE_ENDO", "Endodoncia realizada", "PERFORMED_PROCEDURE", "Procedimiento realizado", "Endodoncia realizada.", "#7c3aed", "solid", "En", ["TOOTH"], None),
    ("DONE_CROWN", "Corona realizada", "PERFORMED_PROCEDURE", "Procedimiento realizado", "Corona realizada.", "#16a34a", "solid", "Co", ["TOOTH"], None),
    ("DONE_EXTRACTION", "Extracción realizada", "PERFORMED_PROCEDURE", "Procedimiento realizado", "Extracción realizada.", "#64748b", "solid", "Ex", ["TOOTH"], None),
    ("DONE_IMPLANT", "Implante realizado", "PERFORMED_PROCEDURE", "Procedimiento realizado", "Implante realizado.", "#64748b", "solid", "Im", ["TOOTH"], None),
    ("DONE_SEALANT", "Sellante realizado", "PERFORMED_PROCEDURE", "Procedimiento realizado", "Sellante realizado.", "#2563eb", "solid", "S", ["TOOTH_SURFACE"], ["OCCLUSAL"]),
    ("OBS_GENERAL", "Observación", "OBSERVATION", "Observación", "Observación odontográfica.", "#475569", "note", "●", ["GENERAL", "ZONE", "TOOTH", "TOOTH_SURFACE"], ["VESTIBULAR", "LINGUAL", "PALATAL", "MESIAL", "DISTAL", "OCCLUSAL", "INCISAL"]),
)


def _upsert_permissions() -> None:
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
            ).bindparams(code=code, name=name, module=module, description=description)
        )


def _assign_permissions() -> None:
    op.execute(
        """
        DELETE FROM rol_permisos rp
        USING permisos p
        WHERE rp.permiso_id = p.id
          AND p.code = 'odontogram.update'
        """
    )
    op.execute("DELETE FROM permisos WHERE code = 'odontogram.update'")
    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        op.execute(
            sa.text(
                """
                INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by)
                SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by
                FROM roles r
                JOIN permisos p ON p.code = ANY(:permission_codes)
                WHERE r.code = :role_code
                  AND NOT EXISTS (
                    SELECT 1
                    FROM rol_permisos rp
                    WHERE rp.rol_id = r.id
                      AND rp.permiso_id = p.id
                  )
                """
            ).bindparams(
                sa.bindparam("role_code", value=role_code),
                sa.bindparam("permission_codes", value=permission_codes, type_=postgresql.ARRAY(sa.String())),
            )
        )


def _seed_catalog() -> None:
    for code, name, item_type, category, description, color, pattern, symbol, scopes, surfaces in CATALOG:
        op.execute(
            sa.text(
                """
                INSERT INTO odontograma_catalogo (
                    id, empresa_id, codigo, nombre, tipo, categoria, descripcion,
                    color, pattern, symbol, allowed_scopes, allowed_surfaces,
                    is_active, created_at, updated_at
                )
                VALUES (
                    gen_random_uuid(), NULL, :code, :name, :item_type, :category, :description,
                    :color, :pattern, :symbol, :scopes, :surfaces,
                    true, now(), now()
                )
                ON CONFLICT (codigo) WHERE empresa_id IS NULL DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    tipo = EXCLUDED.tipo,
                    categoria = EXCLUDED.categoria,
                    descripcion = EXCLUDED.descripcion,
                    color = EXCLUDED.color,
                    pattern = EXCLUDED.pattern,
                    symbol = EXCLUDED.symbol,
                    allowed_scopes = EXCLUDED.allowed_scopes,
                    allowed_surfaces = EXCLUDED.allowed_surfaces,
                    is_active = true,
                    updated_at = now()
                """
            ).bindparams(
                sa.bindparam("code", value=code),
                sa.bindparam("name", value=name),
                sa.bindparam("item_type", value=item_type),
                sa.bindparam("category", value=category),
                sa.bindparam("description", value=description),
                sa.bindparam("color", value=color),
                sa.bindparam("pattern", value=pattern),
                sa.bindparam("symbol", value=symbol),
                sa.bindparam("scopes", value=scopes, type_=postgresql.JSONB()),
                sa.bindparam("surfaces", value=surfaces, type_=postgresql.JSONB()),
            )
        )


def upgrade() -> None:
    op.create_table(
        "odontogramas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("historia_clinica_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("denticion_preferida", sa.String(length=20), server_default="PERMANENT", nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_odontogramas_version_positive"),
        sa.CheckConstraint("estado IN ('ACTIVE', 'INACTIVE')", name="ck_odontogramas_estado"),
        sa.CheckConstraint("denticion_preferida IN ('PERMANENT', 'PRIMARY', 'MIXED')", name="ck_odontogramas_denticion_preferida"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["historia_clinica_id"], ["historias_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "paciente_id", name="uq_odontogramas_empresa_paciente"),
    )
    op.create_index("ix_odontogramas_empresa_id", "odontogramas", ["empresa_id"])
    op.create_index("ix_odontogramas_paciente_id", "odontogramas", ["paciente_id"])
    op.create_index("ix_odontogramas_historia_clinica_id", "odontogramas", ["historia_clinica_id"])
    op.create_index("ix_odontogramas_empresa_paciente", "odontogramas", ["empresa_id", "paciente_id"])

    op.create_table(
        "odontograma_catalogo",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("codigo", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("categoria", sa.String(length=120), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("pattern", sa.String(length=60), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("allowed_scopes", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("allowed_surfaces", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("tipo IN ('STRUCTURAL_STATE', 'FINDING', 'DIAGNOSIS', 'PLANNED_PROCEDURE', 'PERFORMED_PROCEDURE', 'OBSERVATION')", name="ck_odontograma_catalogo_tipo"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "codigo", name="uq_odontograma_catalogo_empresa_codigo"),
    )
    op.create_index("ix_odontograma_catalogo_empresa_id", "odontograma_catalogo", ["empresa_id"])
    op.create_index("ix_odontograma_catalogo_tipo", "odontograma_catalogo", ["tipo"])
    op.create_index("ix_odontograma_catalogo_empresa_tipo", "odontograma_catalogo", ["empresa_id", "tipo"])
    op.create_index("ix_odontograma_catalogo_codigo", "odontograma_catalogo", ["codigo"])
    op.create_index(
        "uq_odontograma_catalogo_global_codigo",
        "odontograma_catalogo",
        ["codigo"],
        unique=True,
        postgresql_where=sa.text("empresa_id IS NULL"),
    )

    op.create_table(
        "odontograma_eventos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("historia_clinica_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("odontograma_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evolucion_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cita_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tratamiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("procedimiento_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sede_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("odontologo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo_evento", sa.String(length=60), nullable=False),
        sa.Column("estado", sa.String(length=40), server_default="DRAFT", nullable=False),
        sa.Column("fecha_clinica", sa.DateTime(timezone=True), nullable=False),
        sa.Column("zona_horaria", sa.String(length=100), nullable=False),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("motivo_correccion", sa.Text(), nullable=True),
        sa.Column("parent_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("hash_contenido", sa.String(length=128), nullable=True),
        sa.Column("confirmed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_odontograma_eventos_version_positive"),
        sa.CheckConstraint("tipo_evento IN ('STRUCTURAL_STATE_CHANGED', 'FINDING_ADDED', 'DIAGNOSIS_ADDED', 'PLANNED_PROCEDURE_ADDED', 'PROCEDURE_PERFORMED', 'OBSERVATION_ADDED', 'CORRECTION', 'COMPENSATING_EVENT')", name="ck_odontograma_eventos_tipo"),
        sa.CheckConstraint("estado IN ('DRAFT', 'CONFIRMED', 'VOIDED_BY_COMPENSATING_EVENT')", name="ck_odontograma_eventos_estado"),
        sa.ForeignKeyConstraint(["cita_id"], ["citas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["confirmed_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evolucion_id"], ["evoluciones_clinicas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["historia_clinica_id"], ["historias_clinicas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["odontograma_id"], ["odontogramas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["odontologo_id"], ["odontologos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_event_id"], ["odontograma_eventos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["procedimiento_id"], ["tratamiento_procedimientos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tratamiento_id"], ["tratamientos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_odontograma_eventos_empresa_id", "odontograma_eventos", ["empresa_id"])
    op.create_index("ix_odontograma_eventos_paciente_id", "odontograma_eventos", ["paciente_id"])
    op.create_index("ix_odontograma_eventos_historia_clinica_id", "odontograma_eventos", ["historia_clinica_id"])
    op.create_index("ix_odontograma_eventos_odontograma_id", "odontograma_eventos", ["odontograma_id"])
    op.create_index("ix_odontograma_eventos_cita_id", "odontograma_eventos", ["cita_id"])
    op.create_index("ix_odontograma_eventos_sede_id", "odontograma_eventos", ["sede_id"])
    op.create_index("ix_odontograma_eventos_odontologo_id", "odontograma_eventos", ["odontologo_id"])
    op.create_index("ix_odontograma_eventos_parent_event_id", "odontograma_eventos", ["parent_event_id"])
    op.create_index("ix_odontograma_eventos_empresa_paciente_fecha", "odontograma_eventos", ["empresa_id", "paciente_id", "fecha_clinica"])
    op.create_index("ix_odontograma_eventos_empresa_paciente_estado", "odontograma_eventos", ["empresa_id", "paciente_id", "estado"])
    op.create_index("ix_odontograma_eventos_evolucion", "odontograma_eventos", ["evolucion_id"])
    op.create_index("ix_odontograma_eventos_tratamiento", "odontograma_eventos", ["tratamiento_id"])
    op.create_index("ix_odontograma_eventos_procedimiento", "odontograma_eventos", ["procedimiento_id"])

    op.create_table(
        "odontograma_evento_detalles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("catalog_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope_type", sa.String(length=30), nullable=False),
        sa.Column("zone", sa.String(length=40), nullable=True),
        sa.Column("tooth_code", sa.String(length=20), nullable=True),
        sa.Column("dentition", sa.String(length=30), nullable=True),
        sa.Column("surfaces", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("layer", sa.String(length=30), nullable=False),
        sa.Column("status_after", sa.String(length=80), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("scope_type IN ('GENERAL', 'ZONE', 'TOOTH', 'TOOTH_SURFACE')", name="ck_odontograma_detalles_scope"),
        sa.CheckConstraint("dentition IS NULL OR dentition IN ('PERMANENT', 'PRIMARY', 'SUPERNUMERARY')", name="ck_odontograma_detalles_dentition"),
        sa.CheckConstraint("layer IN ('STRUCTURAL', 'FINDING', 'DIAGNOSIS', 'PLANNED', 'PERFORMED', 'OBSERVATION')", name="ck_odontograma_detalles_layer"),
        sa.ForeignKeyConstraint(["catalog_item_id"], ["odontograma_catalogo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evento_id"], ["odontograma_eventos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_odontograma_evento_detalles_empresa_id", "odontograma_evento_detalles", ["empresa_id"])
    op.create_index("ix_odontograma_evento_detalles_evento_id", "odontograma_evento_detalles", ["evento_id"])
    op.create_index("ix_odontograma_evento_detalles_catalog_item_id", "odontograma_evento_detalles", ["catalog_item_id"])
    op.create_index("ix_odontograma_detalles_evento", "odontograma_evento_detalles", ["evento_id"])
    op.create_index("ix_odontograma_detalles_diente", "odontograma_evento_detalles", ["empresa_id", "tooth_code"])
    op.create_index("ix_odontograma_detalles_catalogo", "odontograma_evento_detalles", ["catalog_item_id"])

    _upsert_permissions()
    _assign_permissions()
    _seed_catalog()


def downgrade() -> None:
    op.drop_index("ix_odontograma_detalles_catalogo", table_name="odontograma_evento_detalles")
    op.drop_index("ix_odontograma_detalles_diente", table_name="odontograma_evento_detalles")
    op.drop_index("ix_odontograma_detalles_evento", table_name="odontograma_evento_detalles")
    op.drop_index("ix_odontograma_evento_detalles_catalog_item_id", table_name="odontograma_evento_detalles")
    op.drop_index("ix_odontograma_evento_detalles_evento_id", table_name="odontograma_evento_detalles")
    op.drop_index("ix_odontograma_evento_detalles_empresa_id", table_name="odontograma_evento_detalles")
    op.drop_table("odontograma_evento_detalles")

    op.drop_index("ix_odontograma_eventos_procedimiento", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_tratamiento", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_evolucion", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_empresa_paciente_estado", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_empresa_paciente_fecha", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_parent_event_id", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_odontologo_id", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_sede_id", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_cita_id", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_odontograma_id", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_historia_clinica_id", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_paciente_id", table_name="odontograma_eventos")
    op.drop_index("ix_odontograma_eventos_empresa_id", table_name="odontograma_eventos")
    op.drop_table("odontograma_eventos")

    op.drop_index("uq_odontograma_catalogo_global_codigo", table_name="odontograma_catalogo")
    op.drop_index("ix_odontograma_catalogo_codigo", table_name="odontograma_catalogo")
    op.drop_index("ix_odontograma_catalogo_empresa_tipo", table_name="odontograma_catalogo")
    op.drop_index("ix_odontograma_catalogo_tipo", table_name="odontograma_catalogo")
    op.drop_index("ix_odontograma_catalogo_empresa_id", table_name="odontograma_catalogo")
    op.drop_table("odontograma_catalogo")

    op.drop_index("ix_odontogramas_empresa_paciente", table_name="odontogramas")
    op.drop_index("ix_odontogramas_historia_clinica_id", table_name="odontogramas")
    op.drop_index("ix_odontogramas_paciente_id", table_name="odontogramas")
    op.drop_index("ix_odontogramas_empresa_id", table_name="odontogramas")
    op.drop_table("odontogramas")

    codes = [code for code, *_ in PERMISSIONS]
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos rp
            USING permisos p
            WHERE rp.permiso_id = p.id
              AND p.code = ANY(:codes)
            """
        ).bindparams(sa.bindparam("codes", value=codes, type_=postgresql.ARRAY(sa.String())))
    )
    op.execute(
        sa.text("DELETE FROM permisos WHERE code = ANY(:codes)").bindparams(
            sa.bindparam("codes", value=codes, type_=postgresql.ARRAY(sa.String()))
        )
    )
