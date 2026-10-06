from __future__ import annotations

import os
from io import BytesIO
from uuid import UUID, uuid4

import httpx
from openpyxl import Workbook
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.models.patient_import import PatientExternalReference
from app.models.user import User
from app.services.bootstrap_service import BootstrapInput, bootstrap_installation
from app.services.dentalink_xlsx_parser import VERIFIED_HEADERS


BASE_URL = os.environ.get("DENTIA_SMOKE_BASE_URL", "http://127.0.0.1:13101")
DATABASE_URL = os.environ["DATABASE_URL"]
PASSWORD = "DentiaImportSmokePassword2026!"
CHANGED_PASSWORD = "DentiaImportSmokeChanged2026!"
RUN_ID = uuid4().hex[:8]


def require(response: httpx.Response, status: int) -> dict:
    if response.status_code != status:
        raise RuntimeError(
            f"{response.request.method} {response.request.url}: "
            f"expected {status}, got {response.status_code}: {response.text}"
        )
    return response.json()


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(identifier: str, password: str) -> str:
    return require(
        httpx.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": identifier, "password": password},
            timeout=20,
        ),
        200,
    )["access_token"]


def workbook_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(list(VERIFIED_HEADERS))
    values = {
        "# Paciente": f"smoke-{RUN_ID}",
        "Nombre": "Paciente",
        "Apellidos": "Importación Sintética",
        "Celular": "+56912345678",
        "Observaciones": "contenido sensible sintético no importable",
    }
    sheet.append([values.get(header) for header in VERIFIED_HEADERS])
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def main() -> None:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with Session(engine) as session:
        platform = session.scalar(
            select(User).where(User.normalized_username == "platform.import.smoke")
        )
        if platform is None:
            bootstrap_installation(
                session,
                BootstrapInput(
                    company_name="Dentia Import Smoke Platform",
                    company_slug="dentia-import-smoke-platform",
                    site_name="Sede Smoke",
                    admin_name="Platform Import Smoke",
                    admin_username="platform.import.smoke",
                    admin_email="platform-import-smoke@example.test",
                    admin_password=PASSWORD,
                ),
            )

    platform_token = login("platform.import.smoke", PASSWORD)
    admin_username = f"admin.import-{RUN_ID}"
    require(
        httpx.post(
            f"{BASE_URL}/api/platform/companies",
            headers=headers(platform_token),
            json={
                "company_name": f"Import Smoke {RUN_ID}",
                "company_type": "Clínica",
                "tax_id": f"IMPORT-{RUN_ID}",
                "phone": None,
                "email": f"contact-{RUN_ID}@example.test",
                "address": "Calle Sintética 1",
                "city": "Bogotá",
                "country": "Colombia",
                "timezone": "America/Bogota",
                "admin_name": "Administradora Import Smoke",
                "admin_username": admin_username,
                "admin_email": f"admin-{RUN_ID}@example.test",
                "admin_password": PASSWORD,
            },
            timeout=30,
        ),
        201,
    )
    admin_token = login(admin_username, PASSWORD)
    admin_token = require(
        httpx.post(
            f"{BASE_URL}/api/auth/change-password",
            headers=headers(admin_token),
            json={
                "current_password": PASSWORD,
                "new_password": CHANGED_PASSWORD,
                "confirm_password": CHANGED_PASSWORD,
            },
            timeout=20,
        ),
        200,
    )["access_token"]

    content = workbook_bytes()
    source = require(
        httpx.post(
            f"{BASE_URL}/api/patient-imports/dentalink/sources",
            headers=headers(admin_token),
            json={"label": f"Dentalink Smoke {RUN_ID}"},
            timeout=20,
        ),
        201,
    )
    files = {
        "file": (
            "dentalink-smoke.xlsx",
            content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    preview = require(
        httpx.post(
            f"{BASE_URL}/api/patient-imports/dentalink/preview",
            headers=headers(admin_token),
            files=files,
            data={"source_id": source["id"]},
            timeout=30,
        ),
        200,
    )
    if preview["counts"]["incomplete"] != 1:
        raise RuntimeError(f"Unexpected preview counts: {preview['counts']}")
    confirmed = require(
        httpx.post(
            f"{BASE_URL}/api/patient-imports/dentalink/confirm",
            headers=headers(admin_token),
            files=files,
            data={
                "source_id": source["id"],
                "preview_token": preview["preview_token"],
            },
            timeout=30,
        ),
        200,
    )
    if confirmed["imported"] != 1:
        raise RuntimeError(f"Unexpected confirmation: {confirmed}")
    repeated = require(
        httpx.post(
            f"{BASE_URL}/api/patient-imports/dentalink/preview",
            headers=headers(admin_token),
            files=files,
            data={"source_id": source["id"]},
            timeout=30,
        ),
        200,
    )
    if repeated["counts"]["already_imported"] != 1:
        raise RuntimeError(f"Idempotency preview failed: {repeated['counts']}")
    if "contenido sensible sintético" in str(confirmed):
        raise RuntimeError("Sensitive pending content leaked into the import response.")

    with Session(engine) as session:
        count = session.scalar(
            select(func.count(PatientExternalReference.id)).where(
                PatientExternalReference.source_id == UUID(source["id"])
            )
        )
        if count != 1:
            raise RuntimeError("Expected exactly one external reference.")
    print("Dentalink import live smoke OK: preview, confirm, pending privacy, idempotency")


if __name__ == "__main__":
    main()
