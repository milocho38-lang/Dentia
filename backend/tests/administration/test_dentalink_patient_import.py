from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
from io import BytesIO
import zipfile
from uuid import uuid4

import pytest
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.agenda import Patient
from app.models.audit_event import AuditEvent
from app.models.patient_import import PatientExternalReference, PatientImportSource
from app.services.dentalink_xlsx_parser import VERIFIED_HEADERS


MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx(rows: list[dict], *, headers: list[str] | None = None) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    selected_headers = headers or list(VERIFIED_HEADERS)
    sheet.append(selected_headers)
    for row in rows:
        sheet.append([row.get(header) for header in selected_headers])
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def _add_archive_entry(content: bytes, name: str, payload: bytes = b"unsafe") -> bytes:
    source = zipfile.ZipFile(BytesIO(content))
    output = BytesIO()
    with source, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            target.writestr(item, source.read(item))
        target.writestr(name, payload)
    return output.getvalue()


def _valid_rut(source_id: str) -> str:
    body = str(10_000_000 + int(hashlib.sha256(source_id.encode()).hexdigest()[:7], 16) % 89_999_999)
    total = 0
    factor = 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    result = 11 - total % 11
    verifier = "0" if result == 11 else "K" if result == 10 else str(result)
    return f"{body}-{verifier}"


def _row(source_id: str, **overrides) -> dict:
    values = {
        "# Paciente": source_id,
        "RUT": _valid_rut(source_id),
        "Nombre": "Paciente",
        "Apellidos": f"Sintético {source_id}",
        "Fecha de nac.": date(1990, 1, 1),
        "Celular": "+56912345678",
        "Ciudad": "Santiago",
        "E-Mail": f"paciente-{source_id}@example.test",
        "Sexo": "Femenino",
    }
    values.update(overrides)
    return values


def _source_id(api_client, token: str, label: str = "Dentalink principal") -> str:
    listed = api_client.get("/api/patient-imports/dentalink/sources", token=token)
    assert listed.status_code == 200, listed.text
    existing = next((item for item in listed.json()["items"] if item["label"] == label), None)
    if existing:
        return existing["id"]
    created = api_client.post(
        "/api/patient-imports/dentalink/sources",
        token=token,
        json={"label": label},
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


def _preview(api_client, token: str, content: bytes, namespace: str = "Dentalink principal"):
    source_id = _source_id(api_client, token, namespace)
    return api_client.post(
        "/api/patient-imports/dentalink/preview",
        token=token,
        files={"file": ("patients.xlsx", content, MIME)},
        data={"source_id": source_id},
    )


def _confirm(api_client, token: str, content: bytes, preview: dict, namespace: str = "clinic-main"):
    return api_client.post(
        "/api/patient-imports/dentalink/confirm",
        token=token,
        files={"file": ("patients.xlsx", content, MIME)},
        data={
            "source_id": preview["source"]["id"],
            "preview_token": preview["preview_token"],
        },
    )


def test_import_permission_is_admin_only(api_client, security_world) -> None:
    content = _xlsx([_row("permission")])
    source_id = _source_id(api_client, security_world.tenant_a.admin.token)

    def preview_as(token: str):
        return api_client.post(
            "/api/patient-imports/dentalink/preview",
            token=token,
            files={"file": ("patients.xlsx", content, MIME)},
            data={"source_id": source_id},
        )

    assert preview_as(security_world.tenant_a.admin.token).status_code == 200
    assert preview_as(security_world.tenant_a.dentist_admin.token).status_code == 200
    assert preview_as(security_world.tenant_a.secretary.token).status_code == 403
    assert preview_as(security_world.tenant_a.dentist.token).status_code == 403
    assert preview_as(security_world.platform_admin.token).status_code == 403


def test_preview_separates_incomplete_review_rejected_and_pending_fields(
    api_client, security_world
) -> None:
    rows = [
        _row("ready"),
        _row("no-rut", RUT=None, **{"E-Mail": "correo-invalido", "Observaciones": "sensible"}),
        _row("minor", **{"Fecha de nac.": date(2015, 1, 1), "# Apoderado": "123"}),
        _row("missing-name", Nombre=None),
    ]
    response = _preview(api_client, security_world.tenant_a.admin.token, _xlsx(rows))
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["counts"] == {
        "ready": 1,
        "incomplete": 1,
        "review": 1,
        "rejected": 1,
        "already_imported": 0,
    }
    incomplete = next(item for item in payload["rows"] if item["source_patient_id"] == "no-rut")
    assert set(incomplete["pending_fields"]) == {"invalid_email", "observations"}
    assert "sensible" not in response.text
    minor = next(item for item in payload["rows"] if item["source_patient_id"] == "minor")
    assert minor["status"] == "REVIEW"
    assert "responsible_source_reference" in minor["pending_fields"]


def test_confirm_imports_only_ready_and_incomplete_and_is_idempotent(
    api_client, db_session, security_world
) -> None:
    content = _xlsx(
        [
            _row("ready"),
            _row("without-rut", RUT=None, Celular=None, **{"Fecha de nac.": None}),
            _row("minor", **{"Fecha de nac.": date(2016, 2, 1)}),
        ]
    )
    preview_response = _preview(api_client, security_world.tenant_a.admin.token, content)
    result = _confirm(
        api_client,
        security_world.tenant_a.admin.token,
        content,
        preview_response.json(),
    )
    assert result.status_code == 200, result.text
    assert result.json()["imported"] == 2
    assert result.json()["skipped_review"] == 1
    db_session.expire_all()
    references = list(
        db_session.scalars(
            select(PatientExternalReference).where(
                PatientExternalReference.company_id == security_world.tenant_a.company.id
            )
        )
    )
    assert len(references) == 2
    incomplete_patient = db_session.scalar(
        select(Patient)
        .join(PatientExternalReference, PatientExternalReference.patient_id == Patient.id)
        .where(PatientExternalReference.source_patient_id == "without-rut")
    )
    assert incomplete_patient is not None
    assert incomplete_patient.document_type == "Sin documento"
    assert incomplete_patient.document is None
    assert incomplete_patient.mobile == ""
    assert incomplete_patient.birth_date is None
    assert incomplete_patient.profile_complete is False

    second_preview = _preview(api_client, security_world.tenant_a.admin.token, content)
    assert second_preview.json()["counts"]["already_imported"] == 2
    second_result = _confirm(
        api_client,
        security_world.tenant_a.admin.token,
        content,
        second_preview.json(),
    )
    assert second_result.status_code == 200
    assert second_result.json()["imported"] == 0
    assert second_result.json()["skipped_already_imported"] == 2


def test_cumulative_reload_imports_only_new_source_ids(api_client, security_world) -> None:
    first = _xlsx([_row("one", RUT=None)])
    first_preview = _preview(api_client, security_world.tenant_a.admin.token, first)
    assert _confirm(api_client, security_world.tenant_a.admin.token, first, first_preview.json()).json()["imported"] == 1

    cumulative = _xlsx([_row("one", RUT=None), _row("two", RUT=None)])
    cumulative_preview = _preview(api_client, security_world.tenant_a.admin.token, cumulative)
    assert cumulative_preview.json()["counts"]["already_imported"] == 1
    assert cumulative_preview.json()["counts"]["incomplete"] == 1
    result = _confirm(
        api_client,
        security_world.tenant_a.admin.token,
        cumulative,
        cumulative_preview.json(),
    )
    assert result.json()["imported"] == 1


def test_source_code_is_server_generated_and_typo_cannot_create_source_silently(
    api_client, security_world
) -> None:
    token = security_world.tenant_a.admin.token
    source_id = _source_id(api_client, token)
    listed = api_client.get("/api/patient-imports/dentalink/sources", token=token)
    assert len(listed.json()["items"]) == 1
    source = listed.json()["items"][0]
    assert source["id"] == source_id
    assert source["code"].startswith("dl-")

    content = _xlsx([_row("typo-guard", RUT=None)])
    typo = api_client.post(
        "/api/patient-imports/dentalink/preview",
        token=token,
        files={"file": ("patients.xlsx", content, MIME)},
        data={"source_id": "dentalink-princpal"},
    )
    assert typo.status_code == 422
    listed_again = api_client.get("/api/patient-imports/dentalink/sources", token=token)
    assert len(listed_again.json()["items"]) == 1


def test_two_explicit_dentalink_sources_can_reuse_origin_id(api_client, security_world) -> None:
    token = security_world.tenant_a.admin.token
    content = _xlsx([_row("same-origin-id", RUT=None)])
    first = _preview(api_client, token, content, "Dentalink principal")
    assert _confirm(api_client, token, content, first.json()).json()["imported"] == 1
    second = _preview(api_client, token, content, "Dentalink adquirido")
    assert second.json()["counts"]["incomplete"] == 1
    assert _confirm(api_client, token, content, second.json()).json()["imported"] == 1


def test_same_source_namespace_and_id_are_isolated_by_company(api_client, security_world) -> None:
    content = _xlsx([_row("shared", RUT=None)])
    for tenant in (security_world.tenant_a, security_world.tenant_b):
        preview = _preview(api_client, tenant.admin.token, content)
        result = _confirm(api_client, tenant.admin.token, content, preview.json())
        assert result.status_code == 200, result.text
        assert result.json()["imported"] == 1


def test_preview_token_cannot_cross_tenants_or_files(api_client, security_world) -> None:
    content = _xlsx([_row("bound", RUT=None)])
    preview = _preview(api_client, security_world.tenant_a.admin.token, content).json()
    cross_tenant = _confirm(
        api_client, security_world.tenant_b.admin.token, content, preview
    )
    assert cross_tenant.status_code == 404
    changed = _xlsx([_row("changed", RUT=None)])
    changed_file = _confirm(
        api_client, security_world.tenant_a.admin.token, changed, preview
    )
    assert changed_file.status_code == 409

    other_source_id = _source_id(
        api_client, security_world.tenant_a.admin.token, "Dentalink secundario"
    )
    wrong_source = api_client.post(
        "/api/patient-imports/dentalink/confirm",
        token=security_world.tenant_a.admin.token,
        files={"file": ("patients.xlsx", content, MIME)},
        data={
            "source_id": other_source_id,
            "preview_token": preview["preview_token"],
        },
    )
    assert wrong_source.status_code == 409


def test_duplicate_rut_is_reviewed_and_existing_patient_is_not_overwritten(
    api_client, db_session, security_world
) -> None:
    existing = security_world.tenant_a.patient
    existing.document_type = "RUT"
    existing.document = "12.345.678-5"
    existing.normalized_document = "123456785"
    original_name = existing.first_names
    db_session.commit()
    content = _xlsx([_row("rut-conflict", Nombre="Nuevo", RUT="12.345.678-5")])
    preview = _preview(api_client, security_world.tenant_a.admin.token, content)
    assert preview.json()["counts"]["review"] == 1
    result = _confirm(api_client, security_world.tenant_a.admin.token, content, preview.json())
    assert result.json()["imported"] == 0
    db_session.expire_all()
    assert db_session.get(Patient, existing.id).first_names == original_name


def test_duplicate_rut_inside_file_is_reviewed(api_client, security_world) -> None:
    content = _xlsx([_row("rut-a", RUT="12.345.678-5"), _row("rut-b", RUT="12.345.678-5")])
    response = _preview(api_client, security_world.tenant_a.admin.token, content)
    assert response.json()["counts"]["review"] == 2


def test_placeholder_dates_are_reviewed(api_client, security_world) -> None:
    content = _xlsx(
        [
            _row(f"placeholder-{index}", RUT=None, **{"Fecha de nac.": date(1999, 9, 9)})
            for index in range(20)
        ]
    )
    response = _preview(api_client, security_world.tenant_a.admin.token, content)
    assert response.status_code == 200
    assert response.json()["counts"]["review"] == 20
    assert all("placeholder" in " ".join(row["issues"]) for row in response.json()["rows"])


def test_concurrent_confirmation_creates_one_patient(api_client, security_world) -> None:
    content = _xlsx([_row("race", RUT=None)])
    preview = _preview(api_client, security_world.tenant_a.admin.token, content).json()

    def confirm():
        return _confirm(api_client, security_world.tenant_a.admin.token, content, preview)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = [executor.submit(confirm), executor.submit(confirm)]
    payloads = [response.result().json() for response in responses]
    assert sorted(item["imported"] for item in payloads) == [0, 1]
    assert sum(item["skipped_already_imported"] for item in payloads) == 1


def test_audit_contains_counts_but_not_patient_pii(api_client, db_session, security_world) -> None:
    content = _xlsx([_row("audit-source", RUT=None, Nombre="NombrePrivado")])
    preview = _preview(api_client, security_world.tenant_a.admin.token, content).json()
    result = _confirm(api_client, security_world.tenant_a.admin.token, content, preview)
    assert result.status_code == 200
    db_session.expire_all()
    events = list(
        db_session.scalars(
            select(AuditEvent).where(
                AuditEvent.company_id == security_world.tenant_a.company.id,
                AuditEvent.action.in_(["PATIENT_IMPORTED", "PATIENT_IMPORT_COMPLETED"]),
            )
        )
    )
    assert len(events) == 2
    serialized = " ".join(str(event.detail) for event in events)
    assert "NombrePrivado" not in serialized
    assert "audit-source" not in serialized
    assert "example.test" not in serialized


def test_duplicate_or_ambiguous_headers_are_rejected(api_client, security_world) -> None:
    headers = list(VERIFIED_HEADERS) + ["  nombre  "]
    response = _preview(
        api_client,
        security_world.tenant_a.admin.token,
        _xlsx([_row("headers")], headers=headers),
    )
    assert response.status_code == 422


def test_formula_workbook_is_rejected(api_client, security_world) -> None:
    content = _xlsx([_row("formula", Nombre="=1+1")])
    response = _preview(api_client, security_world.tenant_a.admin.token, content)
    assert response.status_code == 422
    assert "fórmulas" in response.text


def test_formula_like_source_id_stays_text_for_safe_report_layer(api_client, security_world) -> None:
    content = _xlsx([_row("@SUM(1,1)", RUT=None)])
    response = _preview(api_client, security_world.tenant_a.admin.token, content)
    assert response.status_code == 200, response.text
    assert response.json()["rows"][0]["source_patient_id"] == "@SUM(1,1)"


@pytest.mark.parametrize("entry", ["xl/vbaProject.bin", "xl/externalLinks/externalLink1.xml"])
def test_active_or_external_xlsx_content_is_rejected(api_client, security_world, entry) -> None:
    content = _add_archive_entry(_xlsx([_row("unsafe")]), entry)
    response = _preview(api_client, security_world.tenant_a.admin.token, content)
    assert response.status_code == 422
    assert "macros" in response.text


def test_external_reference_fk_cannot_cross_tenants(db_session, security_world) -> None:
    foreign_source = PatientImportSource(
        company_id=security_world.tenant_b.company.id,
        source_system="DENTALINK",
        code="dl-cross-tenant",
        label="Origen de otra clínica",
        created_by=security_world.tenant_b.admin.user.id,
    )
    db_session.add(foreign_source)
    db_session.commit()
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                PatientExternalReference(
                    id=uuid4(),
                    company_id=security_world.tenant_a.company.id,
                    patient_id=security_world.tenant_b.patient.id,
                    source_id=foreign_source.id,
                    source_patient_id="foreign-patient",
                    source_file_sha256="0" * 64,
                    imported_by=security_world.tenant_a.admin.user.id,
                )
            )
            db_session.flush()
