from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.company import Company
from app.models.site import Site


FALLBACK_TIMEZONE = "America/Bogota"


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
