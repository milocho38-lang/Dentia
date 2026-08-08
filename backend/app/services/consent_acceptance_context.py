"""Versioned, immutable context contract for electronic consent acceptance."""
from dataclasses import dataclass


ACCEPTANCE_CONTEXT_SCHEMA_VERSION = "C019A4_V1"
LEGACY_ACCEPTANCE_CONTEXT_UNSUPPORTED = "LEGACY_ACCEPTANCE_CONTEXT_UNSUPPORTED"
ACCEPTANCE_CONTEXT_INCONSISTENT = "ACCEPTANCE_CONTEXT_INCONSISTENT"
PUBLIC_LEGACY_MESSAGE = (
    "Este consentimiento fue preparado con una versión anterior y no puede "
    "firmarse electrónicamente. Contacte a la clínica para que genere uno nuevo."
)
PRIVATE_LEGACY_MESSAGE = (
    "Esta instancia no contiene la jurisdicción sellada requerida por el flujo "
    "de aceptación. Debe crearse una nueva instancia; el documento histórico no será modificado."
)
PRIVATE_INCONSISTENT_MESSAGE = (
    "La jurisdicción sellada de esta instancia no cumple el contrato vigente. "
    "Debe crearse una nueva instancia; el documento histórico no será modificado."
)

JURISDICTION_CODES = {
    ("CO", "es-CO"): "CO_ES_CO",
    ("CL", "es-CL"): "CL_ES_CL",
}


@dataclass(frozen=True)
class AcceptanceContextCompatibility:
    compatible: bool
    code: str | None = None
    private_message: str | None = None
    public_message: str | None = None
    country_code: str | None = None
    locale: str | None = None
    jurisdiction_code: str | None = None


def inspect_acceptance_context(instance) -> AcceptanceContextCompatibility:
    """Inspect only sealed values; never repairs or derives them from live masters."""
    context = instance.context_snapshot if isinstance(instance.context_snapshot, dict) else {}
    if context.get("schema_version") != ACCEPTANCE_CONTEXT_SCHEMA_VERSION:
        return AcceptanceContextCompatibility(
            False, LEGACY_ACCEPTANCE_CONTEXT_UNSUPPORTED, PRIVATE_LEGACY_MESSAGE, PUBLIC_LEGACY_MESSAGE
        )

    document = context.get("document")
    template = context.get("template")
    site = context.get("site")
    if not all(isinstance(value, dict) for value in (document, template, site)):
        return AcceptanceContextCompatibility(
            False, LEGACY_ACCEPTANCE_CONTEXT_UNSUPPORTED, PRIVATE_LEGACY_MESSAGE, PUBLIC_LEGACY_MESSAGE
        )

    required = (
        document.get("country"), document.get("country_code"), document.get("locale"),
        document.get("jurisdiction_code"), document.get("timezone"),
        template.get("country_code"), template.get("locale"), site.get("country_code"),
    )
    if any(not isinstance(value, str) or not value.strip() for value in required):
        return AcceptanceContextCompatibility(
            False, LEGACY_ACCEPTANCE_CONTEXT_UNSUPPORTED, PRIVATE_LEGACY_MESSAGE, PUBLIC_LEGACY_MESSAGE
        )

    country = document["country_code"]
    locale = document["locale"]
    jurisdiction = document["jurisdiction_code"]
    expected_jurisdiction = JURISDICTION_CODES.get((country, locale))
    consistent = (
        expected_jurisdiction is not None
        and jurisdiction == expected_jurisdiction
        and document["country"] == country
        and country == instance.country_code == template["country_code"] == site["country_code"]
        and locale == instance.language_code == template["locale"]
        and document["timezone"] == instance.timezone_name == site.get("timezone")
    )
    if not consistent:
        return AcceptanceContextCompatibility(
            False, ACCEPTANCE_CONTEXT_INCONSISTENT, PRIVATE_INCONSISTENT_MESSAGE, PUBLIC_LEGACY_MESSAGE,
            country, locale, jurisdiction,
        )
    return AcceptanceContextCompatibility(
        True, country_code=country, locale=locale, jurisdiction_code=jurisdiction
    )
