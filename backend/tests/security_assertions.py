from __future__ import annotations

from typing import Any


DENIED_STATUS_CODES = {400, 401, 403, 404, 409}


def assert_denied(response, *, allowed: set[int] | None = None) -> None:
    expected = allowed or DENIED_STATUS_CODES
    assert response.status_code in expected, response.text
    assert response.status_code != 200, response.text


def _walk_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        result: list[str] = []
        for key, item in value.items():
            result.extend(_walk_values(key))
            result.extend(_walk_values(item))
        return result
    if isinstance(value, list | tuple | set):
        result: list[str] = []
        for item in value:
            result.extend(_walk_values(item))
        return result
    return [str(value)]


def assert_no_tenant_b_leak(response, tenant_b) -> None:
    sentinels = {
        str(tenant_b.company.id),
        str(tenant_b.site_1.id),
        str(tenant_b.site_2.id),
        str(tenant_b.patient.id),
        str(tenant_b.treatment.id),
        str(tenant_b.budget.id),
        str(tenant_b.payment.id),
        str(tenant_b.prescription.id),
        str(tenant_b.clinical_document.id),
        "Paciente B",
        "Tratamiento B",
        "Clínica Ficticia B",
        "CP-B-000001",
        "RX-B-1",
        "DOC-B-1",
        str(tenant_b.prescription.pdf_storage_path),
        str(tenant_b.clinical_document.pdf_storage_path),
    }
    haystack = response.text
    header_haystack = " ".join(f"{key}: {value}" for key, value in response.headers.items())
    for sentinel in sentinels:
        assert sentinel not in haystack, f"Tenant B sentinel leaked in body: {sentinel}"
        assert sentinel not in header_haystack, f"Tenant B sentinel leaked in headers: {sentinel}"


def assert_payload_has_no_tenant_b_items(payload: Any, tenant_b) -> None:
    values = "\n".join(_walk_values(payload))
    for sentinel in {
        str(tenant_b.company.id),
        str(tenant_b.site_1.id),
        str(tenant_b.patient.id),
        str(tenant_b.treatment.id),
        str(tenant_b.budget.id),
        str(tenant_b.payment.id),
        "Paciente B",
        "Tratamiento B",
        "CP-B-000001",
    }:
        assert sentinel not in values, f"Tenant B sentinel leaked in JSON: {sentinel}"
