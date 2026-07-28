from datetime import date
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.patient_service import calculate_age
from app.services.prescription_service import _snapshot_patient


class DummySession:
    def scalar(self, _statement):
        return None


def _patient(birth_date: date | None):
    return SimpleNamespace(
        id=uuid4(),
        first_names="Paciente",
        last_names="Prueba",
        document_type="CC",
        document="123",
        birth_date=birth_date,
    )


def test_age_with_birthday_already_passed() -> None:
    assert calculate_age(date(2010, 3, 15), date(2026, 7, 25)) == 16


def test_age_with_birthday_pending() -> None:
    assert calculate_age(date(2010, 12, 15), date(2026, 7, 25)) == 15


def test_age_uses_clinical_date_not_current_date() -> None:
    assert calculate_age(date(2000, 7, 26), date(2026, 7, 25)) == 25
    assert calculate_age(date(2000, 7, 26), date(2026, 7, 26)) == 26


def test_missing_birth_date_is_allowed() -> None:
    assert calculate_age(None, date(2026, 7, 25)) is None


def test_future_birth_date_does_not_return_negative_age() -> None:
    assert calculate_age(date(2027, 1, 1), date(2026, 7, 25)) is None


def test_prescription_patient_snapshot_uses_clinical_date() -> None:
    snapshot = _snapshot_patient(DummySession(), _patient(date(2000, 7, 26)), date(2026, 7, 25))
    assert snapshot["birth_date"] == "2000-07-26"
    assert snapshot["age"] == 25
    assert snapshot["is_minor"] is False


def test_prescription_patient_snapshot_allows_missing_birth_date() -> None:
    snapshot = _snapshot_patient(DummySession(), _patient(None), date(2026, 7, 25))
    assert snapshot["birth_date"] is None
    assert snapshot["age"] is None
    assert snapshot["is_minor"] is False


if __name__ == "__main__":
    test_age_with_birthday_already_passed()
    test_age_with_birthday_pending()
    test_age_uses_clinical_date_not_current_date()
    test_missing_birth_date_is_allowed()
    test_future_birth_date_does_not_return_negative_age()
    test_prescription_patient_snapshot_uses_clinical_date()
    test_prescription_patient_snapshot_allows_missing_birth_date()
    print("Prescription age snapshot tests: OK")
