from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.company import Company
from app.models.site import Site


FALLBACK_TIMEZONE = "America/Bogota"
MONTHS_ES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def valid_timezone_name(value: str | None) -> str:
    candidate = value or FALLBACK_TIMEZONE
    try:
        ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        return FALLBACK_TIMEZONE
    return candidate


def effective_timezone(company: Company | None, site: Site | None = None) -> str:
    return valid_timezone_name(
        (site.timezone if site else None)
        or (company.timezone if company else None)
        or FALLBACK_TIMEZONE
    )


def local_clinical_date(
    company: Company | None,
    site: Site | None = None,
    *,
    now: datetime | None = None,
) -> date:
    timezone_name = effective_timezone(company, site)
    current = now or datetime.now(ZoneInfo(timezone_name))
    if current.tzinfo is None:
        current = current.replace(tzinfo=ZoneInfo(timezone_name))
    return current.astimezone(ZoneInfo(timezone_name)).date()


def clinical_date_or_local_default(
    explicit_date: date | None,
    company: Company | None,
    site: Site | None = None,
    *,
    now: datetime | None = None,
) -> date:
    if explicit_date is not None:
        return explicit_date
    return local_clinical_date(company, site, now=now)


def format_human_local_datetime(
    value: datetime,
    company: Company | None,
    site: Site | None = None,
) -> str:
    return format_human_datetime_in_timezone(value, effective_timezone(company, site))


def format_human_datetime_in_timezone(value: datetime, timezone_name: str | None) -> str:
    timezone_name = valid_timezone_name(timezone_name)
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    local = aware.astimezone(ZoneInfo(timezone_name))
    hour = local.hour % 12 or 12
    suffix = "a. m." if local.hour < 12 else "p. m."
    return f"{local.day} de {MONTHS_ES[local.month - 1]} de {local.year}, {hour}:{local.minute:02d} {suffix}"


def format_human_date(value: date | datetime | None) -> str:
    if value is None:
        return "No registrado"
    day = value.date() if isinstance(value, datetime) else value
    return f"{day.day} de {MONTHS_ES[day.month - 1]} de {day.year}"
