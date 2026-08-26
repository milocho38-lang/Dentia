"""Jurisdiction-bound declaration catalog for the Dentia consent procedure.

Local and test retain the historical technical drafts and test marking.
Production resolves only immutable approved rows for the exact country,
locale, actor and configured procedure version; there is no cross-country
fallback.
"""
from dataclasses import dataclass
from datetime import date
import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.consent_template import ConsentDeclarationVersion


TEST_DOCUMENT_NOTICE = "DOCUMENTO DE PRUEBA — NO VÁLIDO PARA USO CLÍNICO"


@dataclass(frozen=True)
class ConsentDeclarationSet:
    country_code: str
    locale: str
    code: str
    version: str
    legal_status: str
    effective_from: date | None
    declarations: tuple[tuple[str, str], ...]
    procedure_version: str | None = None
    content_sha256: str | None = None
    test_document: bool = True

    @property
    def sha256(self) -> str:
        if self.content_sha256:
            return self.content_sha256
        payload = {
            "country_code": self.country_code,
            "locale": self.locale,
            "code": self.code,
            "version": self.version,
            "legal_status": self.legal_status,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "declarations": [{"code": code, "text": text} for code, text in self.declarations],
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @property
    def is_test_document(self) -> bool:
        return self.test_document


CO_DRAFT = ConsentDeclarationSet(
    country_code="CO",
    locale="es-CO",
    code="CONSENT_PATIENT_SELF_CO",
    version="DRAFT_LEGAL_REVIEW_V1",
    legal_status="DRAFT_LEGAL_REVIEW",
    effective_from=None,
    declarations=(
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
)


CL_DRAFT = ConsentDeclarationSet(
    country_code="CL",
    locale="es-CL",
    code="CONSENT_PATIENT_SELF_CL",
    version="DRAFT_LEGAL_REVIEW_V1",
    legal_status="DRAFT_LEGAL_REVIEW",
    effective_from=None,
    declarations=(
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
)


CO_RESPONSIBLE_DRAFT = ConsentDeclarationSet(
    country_code="CO",
    locale="es-CO",
    code="CONSENT_RESPONSIBLE_ADULT_CO",
    version="DRAFT_LEGAL_REVIEW_V1",
    legal_status="DRAFT_LEGAL_REVIEW",
    effective_from=None,
    declarations=(
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
)


CL_RESPONSIBLE_DRAFT = ConsentDeclarationSet(
    country_code="CL",
    locale="es-CL",
    code="CONSENT_RESPONSIBLE_ADULT_CL",
    version="DRAFT_LEGAL_REVIEW_V1",
    legal_status="DRAFT_LEGAL_REVIEW",
    effective_from=None,
    declarations=(
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
)

DECLARATION_SETS: dict[tuple[str, str] | tuple[str, str, str], ConsentDeclarationSet] = {
    (CO_DRAFT.country_code, CO_DRAFT.locale): CO_DRAFT,
    (CL_DRAFT.country_code, CL_DRAFT.locale): CL_DRAFT,
    (CO_DRAFT.country_code, CO_DRAFT.locale, "PATIENT_SELF"): CO_DRAFT,
    (CL_DRAFT.country_code, CL_DRAFT.locale, "PATIENT_SELF"): CL_DRAFT,
    (CO_RESPONSIBLE_DRAFT.country_code, CO_RESPONSIBLE_DRAFT.locale, "RESPONSIBLE_ADULT"): CO_RESPONSIBLE_DRAFT,
    (CL_RESPONSIBLE_DRAFT.country_code, CL_RESPONSIBLE_DRAFT.locale, "RESPONSIBLE_ADULT"): CL_RESPONSIBLE_DRAFT,
}


class ConsentDeclarationSetError(RuntimeError):
    pass


def _approved_declaration_hash(row: ConsentDeclarationVersion) -> str:
    payload = {
        "code": row.code,
        "country_code": row.country_code,
        "locale": row.locale,
        "actor_type": row.actor_type,
        "version": row.version,
        "procedure_version": row.procedure_version,
        "declarations": sorted(row.declarations or [], key=lambda item: item.get("order", 0)),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def declaration_set_for(country_code: str, locale: str, *, actor_type: str = "PATIENT_SELF", app_env: str, acceptance_enabled: bool, on_date: date, session: Session | None = None) -> ConsentDeclarationSet:
    country = country_code.strip().upper()
    clean_locale = locale.strip()
    actor = (actor_type or "PATIENT_SELF").strip().upper()
    if app_env.casefold() == "production":
        if not acceptance_enabled or session is None:
            raise ConsentDeclarationSetError("El catálogo productivo de declaraciones no está habilitado.")
        row = session.scalar(
            select(ConsentDeclarationVersion)
            .where(
                ConsentDeclarationVersion.country_code == country,
                ConsentDeclarationVersion.locale == clean_locale,
                ConsentDeclarationVersion.actor_type == actor,
                ConsentDeclarationVersion.procedure_version == settings.consent_procedure_version,
                ConsentDeclarationVersion.status == "APPROVED",
                ConsentDeclarationVersion.effective_from.is_not(None),
                ConsentDeclarationVersion.effective_from <= on_date,
            )
            .order_by(ConsentDeclarationVersion.effective_from.desc(), ConsentDeclarationVersion.created_at.desc())
        )
        if row is None:
            raise ConsentDeclarationSetError("No existe un conjunto de declaraciones aprobado y vigente.")
        if row.content_sha256 != _approved_declaration_hash(row):
            raise ConsentDeclarationSetError("El conjunto de declaraciones no supera la verificación de integridad.")
        ordered = sorted(row.declarations or [], key=lambda item: item.get("order", 0))
        return ConsentDeclarationSet(
            country_code=row.country_code,
            locale=row.locale,
            code=row.code,
            version=row.version,
            legal_status=row.status,
            effective_from=row.effective_from,
            declarations=tuple((item["code"], item["text"]) for item in ordered),
            procedure_version=row.procedure_version,
            content_sha256=row.content_sha256,
            test_document=False,
        )
    base_set = DECLARATION_SETS.get((country, clean_locale))
    declaration_set = base_set if actor == "PATIENT_SELF" else (DECLARATION_SETS.get((country, clean_locale, actor)) or base_set)
    if declaration_set is None:
        raise ConsentDeclarationSetError("No existe un conjunto de declaraciones compatible con el país y el idioma sellados.")
    if declaration_set.legal_status == "RETIRED":
        raise ConsentDeclarationSetError("El conjunto de declaraciones ya no está vigente.")
    if declaration_set.legal_status == "APPROVED":
        if declaration_set.effective_from is None or declaration_set.effective_from > on_date:
            raise ConsentDeclarationSetError("El conjunto de declaraciones todavía no está vigente.")
        return declaration_set
    if declaration_set.legal_status == "DRAFT_LEGAL_REVIEW" and acceptance_enabled and app_env.casefold() in {"local", "development", "test"}:
        return declaration_set
    raise ConsentDeclarationSetError("El conjunto de declaraciones no está aprobado para este entorno.")
