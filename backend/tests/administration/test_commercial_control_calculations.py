from datetime import date

from app.services.commercial_control_service import add_months, coverage_end


def test_year_subscription_uses_inclusive_end_date() -> None:
    assert coverage_end(date(2026, 11, 1), 12) == date(2027, 10, 31)
    assert add_months(date(2026, 11, 1), 12) == date(2027, 11, 1)


def test_end_of_month_is_clamped() -> None:
    assert add_months(date(2027, 1, 31), 1) == date(2027, 2, 28)
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)


def test_leap_year_full_year() -> None:
    assert coverage_end(date(2028, 2, 29), 12) == date(2029, 2, 27)
