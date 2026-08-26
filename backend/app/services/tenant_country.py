from app.models.company import Company


COUNTRY_CODES = {
    "co": "CO",
    "colombia": "CO",
    "cl": "CL",
    "chile": "CL",
}


class TenantCountryError(RuntimeError):
    pass


def company_country_code(company: Company) -> str:
    normalized = (company.country or "").strip().casefold()
    country_code = COUNTRY_CODES.get(normalized)
    if country_code is None:
        raise TenantCountryError(
            "La empresa debe tener un país compatible configurado antes de usar la Biblioteca Dentia."
        )
    return country_code
