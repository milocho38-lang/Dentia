"""add consent production readiness and clinic content review

Revision ID: 20260801_0031
Revises: 20260801_0030
Create Date: 2026-08-18
"""
from __future__ import annotations

import hashlib
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260801_0031"
down_revision = "20260801_0030"
branch_labels = None
depends_on = None

PROCEDURE_VERSION = "DENTIA_CONSENT_PROCEDURE_V1"
REVIEW_REFERENCE = "Revisión integral registrada técnicamente el 18 de agosto de 2026; realizada antes de esa fecha."
PERMISSION = (
    "consent.template.review_content",
    "Revisar contenido de plantillas de consentimiento",
    "consent_templates",
    "Confirmar que la clínica revisó y adoptó el contenido exacto de una versión tenant.",
)

DECLARATIONS = {
    ("CONSENT_PATIENT_SELF_CO", "CO", "es-CO", "PATIENT_SELF"): (
        ("READ_DOCUMENT", "He leído completamente el documento presentado para mi revisión."),
        ("UNDERSTAND_INFORMATION", "Declaro que pude comprender la información que me fue presentada."),
        ("QUESTIONS_ANSWERED", "Tuve la oportunidad de solicitar aclaraciones a la clínica antes de continuar."),
        ("PROCEDURE_CONTEXT", "Reconozco que el documento corresponde al procedimiento y al contexto clínico mostrados."),
        ("RISKS_BENEFITS", "Revisé la información disponible sobre propósito, beneficios, riesgos y alternativas."),
        ("VOLUNTARY", "Comprendo que todavía puedo abstenerme de continuar y que esta aceptación es voluntaria."),
        ("DATA_ACCURATE", "Confirmo que los datos de identificación mostrados corresponden a mi persona."),
        ("ELECTRONIC_RECORD", "Acepto que esta interacción quede registrada electrónicamente con trazabilidad técnica."),
        ("COPY_AVAILABLE", "Entiendo que se generará una copia final para consulta y entrega."),
        ("CONTACT_CLINIC", "Sé que puedo contactar directamente a la clínica si necesito información adicional."),
    ),
    ("CONSENT_PATIENT_SELF_CL", "CL", "es-CL", "PATIENT_SELF"): (
        ("READ_DOCUMENT", "He leído en su totalidad el documento que se presenta para mi revisión."),
        ("UNDERSTAND_INFORMATION", "Declaro haber podido comprender la información presentada por la clínica."),
        ("QUESTIONS_ANSWERED", "Tuve la posibilidad de pedir aclaraciones al prestador antes de continuar."),
        ("PROCEDURE_CONTEXT", "Reconozco que el documento corresponde a la prestación y al contexto clínico informados."),
        ("RISKS_BENEFITS", "Revisé la información disponible sobre objetivo, beneficios, riesgos y alternativas."),
        ("VOLUNTARY", "Comprendo que aún puedo abstenerme de continuar y que esta aceptación es voluntaria."),
        ("DATA_ACCURATE", "Confirmo que los antecedentes de identificación mostrados corresponden a mi persona."),
        ("ELECTRONIC_RECORD", "Acepto que esta interacción sea registrada electrónicamente como evidencia técnica del proceso."),
        ("COPY_AVAILABLE", "Entiendo que se generará una copia final disponible para consulta y entrega."),
        ("CONTACT_CLINIC", "Sé que puedo comunicarme directamente con la clínica si necesito información adicional."),
    ),
    ("CONSENT_RESPONSIBLE_ADULT_CO", "CO", "es-CO", "RESPONSIBLE_ADULT"): (
        ("READ_DOCUMENT", "He leído completamente el documento presentado para mi revisión como adulto responsable."),
        ("UNDERSTAND_INFORMATION", "Declaro que pude comprender la información presentada sobre el paciente y el procedimiento."),
        ("RESPONSIBLE_IDENTITY", "Confirmo que mis datos de identificación como adulto responsable son correctos."),
        ("RELATIONSHIP", "Confirmo la relación o vínculo informado con el paciente."),
        ("QUESTIONS_ANSWERED", "Tuve la oportunidad de solicitar aclaraciones a la clínica antes de continuar."),
        ("MINOR_PARTICIPATION", "Reconozco que se registró la participación o condición del menor según fue posible."),
        ("VOLUNTARY", "Comprendo que esta aceptación se registra de forma voluntaria."),
        ("ELECTRONIC_RECORD", "Acepto que esta interacción quede registrada electrónicamente con trazabilidad técnica."),
        ("COPY_AVAILABLE", "Entiendo que se generará una copia final para consulta y entrega."),
        ("CONTACT_CLINIC", "Sé que puedo contactar directamente a la clínica si necesito información adicional."),
    ),
    ("CONSENT_RESPONSIBLE_ADULT_CL", "CL", "es-CL", "RESPONSIBLE_ADULT"): (
        ("READ_DOCUMENT", "He leído en su totalidad el documento presentado para mi revisión como adulto responsable."),
        ("UNDERSTAND_INFORMATION", "Declaro haber podido comprender la información presentada sobre el paciente y la prestación."),
        ("RESPONSIBLE_IDENTITY", "Confirmo que mis datos de identificación como adulto responsable son correctos."),
        ("RELATIONSHIP", "Confirmo la relación o vínculo informado con el paciente."),
        ("QUESTIONS_ANSWERED", "Tuve la posibilidad de pedir aclaraciones al prestador antes de continuar."),
        ("MINOR_PARTICIPATION", "Reconozco que se registró la participación o condición del menor según fue posible."),
        ("VOLUNTARY", "Comprendo que esta aceptación se registra de forma voluntaria."),
        ("ELECTRONIC_RECORD", "Acepto que esta interacción sea registrada electrónicamente como evidencia técnica del proceso."),
        ("COPY_AVAILABLE", "Entiendo que se generará una copia final disponible para consulta y entrega."),
        ("CONTACT_CLINIC", "Sé que puedo comunicarme directamente con la clínica si necesito información adicional."),
    ),
}


def _declaration_hash(code: str, country: str, locale: str, actor: str, declarations: tuple) -> str:
    payload = {
        "code": code,
        "country_code": country,
        "locale": locale,
        "actor_type": actor,
        "version": "APPROVED_V1",
        "procedure_version": PROCEDURE_VERSION,
        "declarations": [
            {"code": item_code, "text": text, "order": order}
            for order, (item_code, text) in enumerate(declarations, 1)
        ],
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _seed_permission() -> None:
    code, name, module, description = PERMISSION
    op.execute(sa.text("""
        INSERT INTO permisos (id, code, nombre, modulo, descripcion, is_active, created_at, updated_at)
        VALUES (gen_random_uuid(), :code, :name, :module, :description, true, now(), now())
        ON CONFLICT (code) DO UPDATE SET nombre=EXCLUDED.nombre, modulo=EXCLUDED.modulo,
          descripcion=EXCLUDED.descripcion, is_active=true, updated_at=now()
    """).bindparams(code=code, name=name, module=module, description=description))
    op.execute(sa.text("""
        INSERT INTO rol_permisos (id, empresa_id, rol_id, permiso_id, is_active, created_by, created_at, updated_at)
        SELECT gen_random_uuid(), r.empresa_id, r.id, p.id, true, r.created_by, now(), now()
        FROM roles r JOIN permisos p ON p.code=:code
        WHERE r.code IN ('ADMINISTRATOR','DENTIST_ADMIN') AND NOT EXISTS (
          SELECT 1 FROM rol_permisos rp WHERE rp.rol_id=r.id AND rp.permiso_id=p.id)
    """).bindparams(code=code))


def upgrade() -> None:
    _seed_permission()
    op.create_table(
        "consentimiento_procedimientos_aprobados",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("procedure_version", sa.String(80), nullable=False),
        sa.Column("procedure_scope", postgresql.JSONB(), nullable=False),
        sa.Column("electronic_channel_reviewed", sa.Boolean(), nullable=False),
        sa.Column("paper_channel_reviewed", sa.Boolean(), nullable=False),
        sa.Column("responsible_adult_flow_reviewed", sa.Boolean(), nullable=False),
        sa.Column("declaration_flow_reviewed", sa.Boolean(), nullable=False),
        sa.Column("countries", postgresql.JSONB(), nullable=False),
        sa.Column("review_reference", sa.String(300), nullable=False),
        sa.Column("review_recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewer_roles", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("procedure_version", name="uq_consent_procedure_approval_version"),
        sa.CheckConstraint("status IN ('APPROVED','RETIRED')", name="ck_consent_procedure_approval_status"),
    )
    op.create_table(
        "consentimiento_declaracion_versiones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("actor_type", sa.String(30), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("declarations", postgresql.JSONB(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("procedure_version", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("review_reference", sa.String(300), nullable=False),
        sa.Column("approval_recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["procedure_version"], ["consentimiento_procedimientos_aprobados.procedure_version"], ondelete="RESTRICT"),
        sa.UniqueConstraint("code", "version", name="uq_consent_declaration_code_version"),
        sa.CheckConstraint("status IN ('APPROVED','RETIRED')", name="ck_consent_declaration_version_status"),
    )
    op.create_index("ix_consent_declaration_runtime", "consentimiento_declaracion_versiones", ["country_code", "locale", "actor_type", "status"])
    op.create_table(
        "consentimiento_plantilla_revisiones_contenido",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledgement_version", sa.String(40), nullable=False),
        sa.Column("acknowledgement_text", sa.Text(), nullable=False),
        sa.Column("acknowledgement_sha256", sa.String(64), nullable=False),
        sa.Column("origin", sa.String(40), nullable=False),
        sa.Column("source_library_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invalidation_reason", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_version_id"], ["consentimiento_plantilla_versiones.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["invalidated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_library_version_id"], ["consentimiento_biblioteca_versiones.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_consent_content_review_company_version", "consentimiento_plantilla_revisiones_contenido", ["empresa_id", "template_version_id"])
    op.create_index("uq_consent_content_review_active_version", "consentimiento_plantilla_revisiones_contenido", ["template_version_id"], unique=True, postgresql_where=sa.text("invalidated_at IS NULL"))

    op.execute(sa.text("""
        INSERT INTO consentimiento_procedimientos_aprobados
          (id, procedure_version, procedure_scope, electronic_channel_reviewed, paper_channel_reviewed,
           responsible_adult_flow_reviewed, declaration_flow_reviewed, countries, review_reference,
           review_recorded_at, reviewer_roles, status, created_at, updated_at)
        VALUES (gen_random_uuid(), :version, CAST(:scope AS jsonb), true, true, true, true,
          CAST(:countries AS jsonb), :reference, TIMESTAMPTZ '2026-08-18 00:00:00+00',
          CAST(:roles AS jsonb), 'APPROVED', now(), now())
    """).bindparams(
        version=PROCEDURE_VERSION,
        scope=json.dumps({"electronic": True, "paper": True, "patient_self": True, "responsible_adult": True, "otp": True, "declarations": True, "evidence": True, "final_document": True}),
        countries=json.dumps(["CO", "CL"]),
        reference=REVIEW_REFERENCE,
        roles=json.dumps(["LEGAL_REVIEWER", "CLINICAL_REVIEWER", "CLINIC_ADMIN_REVIEWER"]),
    ))
    op.execute(sa.text("""
        INSERT INTO auditoria_eventos
          (id, empresa_id, usuario_id, session_id, entidad, entidad_id, accion, resultado,
           detalle, ip_origen, user_agent, fecha, created_at, updated_at)
        SELECT gen_random_uuid(), NULL, NULL, NULL, 'consent_procedure_approval', id,
          'CONSENT_PROCEDURE_APPROVAL_RECORDED', 'SUCCESS',
          jsonb_build_object('procedure_version', procedure_version, 'countries', countries,
            'reviewer_roles', reviewer_roles, 'status', status),
          NULL, NULL, now(), now(), now()
        FROM consentimiento_procedimientos_aprobados
        WHERE procedure_version=:version
    """).bindparams(version=PROCEDURE_VERSION))
    for (code, country, locale, actor), declarations in DECLARATIONS.items():
        rows = [{"code": item_code, "text": text, "order": order} for order, (item_code, text) in enumerate(declarations, 1)]
        op.execute(sa.text("""
            INSERT INTO consentimiento_declaracion_versiones
              (id, code, country_code, locale, actor_type, version, declarations, content_sha256,
               procedure_version, status, review_reference, approval_recorded_at, effective_from, created_at, updated_at)
            VALUES (gen_random_uuid(), :code, :country, :locale, :actor, 'APPROVED_V1', CAST(:declarations AS jsonb),
              :sha256, :procedure, 'APPROVED', :reference, TIMESTAMPTZ '2026-08-18 00:00:00+00',
              DATE '2026-08-18', now(), now())
        """).bindparams(code=code, country=country, locale=locale, actor=actor, declarations=json.dumps(rows, ensure_ascii=False), sha256=_declaration_hash(code, country, locale, actor, declarations), procedure=PROCEDURE_VERSION, reference=REVIEW_REFERENCE))
        op.execute(sa.text("""
            INSERT INTO auditoria_eventos
              (id, empresa_id, usuario_id, session_id, entidad, entidad_id, accion, resultado,
               detalle, ip_origen, user_agent, fecha, created_at, updated_at)
            SELECT gen_random_uuid(), NULL, NULL, NULL, 'consent_declaration_version', id,
              'CONSENT_DECLARATION_VERSION_APPROVED', 'SUCCESS',
              jsonb_build_object('code', code, 'country_code', country_code,
                'actor_type', actor_type, 'version', version, 'procedure_version', procedure_version),
              NULL, NULL, now(), now(), now()
            FROM consentimiento_declaracion_versiones
            WHERE code=:code AND version='APPROVED_V1'
        """).bindparams(code=code))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM auditoria_eventos WHERE accion IN ('CONSENT_PROCEDURE_APPROVAL_RECORDED','CONSENT_DECLARATION_VERSION_APPROVED')"))
    op.drop_index("uq_consent_content_review_active_version", table_name="consentimiento_plantilla_revisiones_contenido")
    op.drop_index("ix_consent_content_review_company_version", table_name="consentimiento_plantilla_revisiones_contenido")
    op.drop_table("consentimiento_plantilla_revisiones_contenido")
    op.drop_index("ix_consent_declaration_runtime", table_name="consentimiento_declaracion_versiones")
    op.drop_table("consentimiento_declaracion_versiones")
    op.drop_table("consentimiento_procedimientos_aprobados")
    code = PERMISSION[0]
    op.execute(sa.text("DELETE FROM rol_permisos rp USING permisos p WHERE rp.permiso_id=p.id AND p.code=:code").bindparams(code=code))
    op.execute(sa.text("DELETE FROM permisos WHERE code=:code").bindparams(code=code))
